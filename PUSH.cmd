@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0PUSH.ps1"
if errorlevel 1 echo PUSH FAILED - please read the error above.
pause
