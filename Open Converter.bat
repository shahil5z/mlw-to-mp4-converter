@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python 3 was not found.
        echo Install Python 3 from https://www.python.org/downloads/windows/
        echo During setup, enable "Add python.exe to PATH".
        pause
        exit /b 1
    )
    set "PY=python"
)

%PY% -c "import cryptography" >nul 2>nul
if errorlevel 1 (
    echo Installing the required cryptography package...
    %PY% -m pip install --user -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

if "%~1"=="" (
    %PY% "%~dp0mlw_to_mp4.py"
) else (
    %PY% "%~dp0mlw_to_mp4.py" %*
)
if errorlevel 1 pause
endlocal
