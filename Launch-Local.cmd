@echo off
cd /d "%~dp0"
if not exist "runtime\python.exe" (
    echo Bundled runtime is missing. Extract the entire ZIP before launching.
    pause
    exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Local.ps1"
if errorlevel 1 (
    echo.
    echo The server could not start. Check the error above.
    pause
)
