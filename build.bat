@echo off
setlocal
cd /d "%~dp0"
py -m pip install --upgrade pip
if errorlevel 1 goto error
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto error
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "Kontra AutoJump" --collect-all pynput main.py
if errorlevel 1 goto error
echo.
echo Build complete: dist\Kontra AutoJump.exe
pause
exit /b 0
:error
echo.
echo Build failed. Check the error above.
pause
exit /b 1
