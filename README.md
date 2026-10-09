# playgta5 Source Code
This code is grabbed from playgta5.com before it got took down. You can run this locally or make it public hehe.

# Credits
Shoutout to Sebas Furbastian on Telegram for scrapping this code. Idk what is his GitHub but here's the Telegram and X.

Telegram: @SebasKitten

X: @Sebas_Kitten

# Link
Telegram: https://t.me/playgta5regen


# Disclaimer
I don't host the `.\mirror` folder since it has copyrighted content from Rockstar Games. Please find the files by yourself.

No copyrighted file is included in this repo. If Rockstar Games or any affiliated group think this repo has copyright infringement things, email me at shadany7824@gmail.com for me to took it down.

And don't email me for asking the mirror folder. I will not reply to the email.

# Run locally
1. Download the source ZIP or clone this repository.
2. Make sure you already have an authorized site snapshot on your computer. The
   selected folder must contain `index.html`, `data/manifest.json`, and
   `b/<build>/loader.js`, `game.js`, and `game.wasm`. You can select the site
   root or its parent `mirror` folder.

   A standard Steam, Epic, or Rockstar GTA V installation is not the format this
   browser snapshot reads.

3. Run `Launch-Local.cmd` (or `Start-Local.ps1`). A native folder picker asks
   where your snapshot is. The server reads it in place from your disk; it does
   not upload, copy, or download the snapshot. It binds only to `127.0.0.1`.
4. The launcher opens `http://localhost:8000/`. Press Ctrl+C in the launcher
   window to stop the local server.

The launcher does not include or fetch the `.mirror` payload. Use only files
you are authorized to use.

# Requirement
The Windows launcher uses the built-in folder picker and the included Python
runtime. If running `serve_local.py` directly, use Python 3.11 or newer;
`--root <path>` selects a snapshot without opening a picker.
