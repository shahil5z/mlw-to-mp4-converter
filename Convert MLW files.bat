@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
    echo Drag one or more .mlw or .zip files onto this BAT file.
    pause
    exit /b 0
)
call "%~dp0Open Converter.bat" %*
endlocal
