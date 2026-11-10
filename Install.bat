@echo off
rem Iron Sights for Sniper Elite 4 - menu: install / change rifle / uninstall
cd /d "%~dp0"
echo Close Sniper Elite 4 before continuing.
echo.
where py >nul 2>nul && (py -3 IronSights.py %* & goto end)
where python >nul 2>nul && (python IronSights.py %* & goto end)
echo Python 3 was not found. Install it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" in the installer), then run this file again.
:end
pause
