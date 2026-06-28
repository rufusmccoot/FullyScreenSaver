@echo off
cd %~dp0

:: wait for HASS and AdGuardDNS to come up after reboot
timeout /t 120

call venv\scripts\activate.bat && python app.py