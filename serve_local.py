"""Serve an existing local site snapshot with isolation headers and byte ranges."""
import argparse, gzip, io, json, mimetypes, re, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

DEFAULT_ROOT = Path(__file__).resolve().parent / 'mirror' / 'playgta5.com'
ROOT = DEFAULT_ROOT
mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('text/javascript', '.js')


def is_snapshot_root(path):
    """Return whether path has the files this browser snapshot needs."""
    if not (path / 'index.html').is_file():
        return False
    if not (path / 'data' / 'manifest.json').is_file():
        return False
    build_root = path / 'b'
    if not build_root.is_dir():
        return False
    try:
        return any(
            (build / 'loader.js').is_file()
            and (build / 'game.js').is_file()
            and (build / 'game.wasm').is_file()
            for build in build_root.iterdir()
            if build.is_dir()
        )
    except OSError:
        return False


def resolve_site_root(selected_path):
    """Accept the site root or a parent mirror folder without copying it."""
    selected = Path(selected_path).expanduser().resolve()
    candidates = (
        selected,
        selected / 'playgta5.com',
        selected / 'mirror' / 'playgta5.com',
        selected / '.mirror' / 'playgta5.com',
    )
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_snapshot_root(candidate):
            return candidate
    raise ValueError(
        'That folder is not a compatible site snapshot. Select the folder '
        'containing index.html, data/manifest.json, and b/<build>/loader.js, '
        'game.js, and game.wasm, or select its parent mirror folder.'
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.byte_range = None
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def translate_path(self, path):
        translated = Path(super().translate_path(path)).resolve()
        root = ROOT.resolve()
        if not translated.is_relative_to(root):
            return str(root / '__blocked__')
        return str(translated)

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def send_head(self):
        if not self.headers.get('Range'):
            return super().send_head()
        try:
            path = Path(self.translate_path(self.path)).resolve(strict=True)
        except (OSError, RuntimeError):
            self.send_error(404)
            return None
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            self.send_error(404)
            return None
        size = path.stat().st_size
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers['Range'])
        if not match or not any(match.groups()):
            self.send_error(416)
            return None
        start = int(match[1]) if match[1] else max(0, size - int(match[2]))
        end = min(size - 1, int(match[2])) if match[1] and match[2] else size - 1
        if start >= size or end < start:
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.byte_range = (start, end)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        source = path.open('rb')
        source.seek(start)
        return source

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        remaining = self.byte_range[1] - self.byte_range[0] + 1
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != '/data/batch':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > 1024 * 1024:
                self.send_error(413)
                return
            runs = json.loads(self.rfile.read(length))
            if not isinstance(runs, list) or len(runs) > 1000:
                raise ValueError('invalid batch')
            selected = []
            data_root = (ROOT / 'data').resolve()
            for run in runs:
                if not isinstance(run, list) or len(run) != 3:
                    raise ValueError('invalid run')
                name, start, end = run
                if (
                    not isinstance(name, str)
                    or not isinstance(start, int) or isinstance(start, bool)
                    or not isinstance(end, int) or isinstance(end, bool)
                ):
                    raise ValueError('invalid file/range')
                file = (data_root / name).resolve()
                if not file.is_relative_to(data_root) or start < 0 or end < start:
                    raise ValueError('invalid file/range')
                size = file.stat().st_size
                selected.append((file, start, max(0, min(end + 1, size) - start)))
            total = sum(n for _, _, n in selected)
            if total > 64 * 1024 * 1024:
                raise ValueError('batch exceeds 64 MiB')
            output = io.BytesIO()
            for file, start, n in selected:
                with file.open('rb') as source:
                    source.seek(start)
                    output.write(source.read(n))
            body = output.getvalue()
            compressed = parse_qs(url.query).get('gz') == ['1']
            if compressed:
                body = gzip.compress(body, compresslevel=1)
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Run-Lengths', ','.join(str(n) for _, _, n in selected))
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--root',
        type=Path,
        help='site snapshot root or its parent mirror folder (served in place)',
    )
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--open', action='store_true', help='open the browser after binding')
    options = parser.parse_args()

    try:
        ROOT = resolve_site_root(options.root or DEFAULT_ROOT)
    except ValueError as exc:
        parser.error(str(exc))

    server = ThreadingHTTPServer(('127.0.0.1', options.port), Handler)
    address = 'http://localhost:%d/' % server.server_port
    print('Serving local snapshot from %s at %s (Ctrl+C to stop)' % (ROOT, address), flush=True)
    if options.open:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
