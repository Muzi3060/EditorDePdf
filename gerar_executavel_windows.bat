@echo off
setlocal
cd /d "%~dp0"
call "%~dp0iniciar_windows.bat" --install
if errorlevel 1 goto finish
"%~dp0.venv\Scripts\python.exe" "%~dp0build_windows.py"
:finish
pause
endlocal
