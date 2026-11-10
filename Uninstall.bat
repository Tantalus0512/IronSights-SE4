@echo off
rem Iron Sights for Sniper Elite 4 - put the scopes back (restores the original game files)
cd /d "%~dp0"
echo Close Sniper Elite 4 before continuing.
echo.
where py >nul 2>nul && (py -3 IronSights.py uninstall %* & goto end)
where python >nul 2>nul && (python IronSights.py uninstall %* & goto end)
echo Python 3 was not found. Install it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH" in the installer), then run this file again.
:end
pause
