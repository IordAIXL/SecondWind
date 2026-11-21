@echo off
rem Starts Second Wind in your system tray (bottom right, near the clock).
rem Needs nothing installed: it uses Windows PowerShell, which every Windows 10/11 PC has.
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0SecondWind.ps1"
