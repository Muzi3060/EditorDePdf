@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 "%~dp0windows_setup.py" %*
goto finish
:use_python
where python >nul 2>nul
if errorlevel 1 goto missing
python "%~dp0windows_setup.py" %*
goto finish
:missing
echo Instale Python 3.12 ou 3.13 de 64 bits em https://www.python.org/downloads/windows/
echo Marque a opcao de adicionar Python ao PATH.
pause
exit /b 1
:finish
set "EDITOR_EXIT=%ERRORLEVEL%"
if not "%EDITOR_EXIT%"=="0" pause
endlocal & exit /b %EDITOR_EXIT%
