$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Choose an existing authorized playgta5.com site snapshot'
$dialog.ShowNewFolderButton = $false
if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host 'Folder selection cancelled; nothing was uploaded or copied.'
    exit 0
}
$siteRoot = $dialog.SelectedPath
$dialog.Dispose()

$pythonExe = Join-Path $PSScriptRoot 'runtime\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}
& $pythonExe (Join-Path $PSScriptRoot 'serve_local.py') --root $siteRoot --open
exit $LASTEXITCODE
