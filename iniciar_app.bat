@echo off
REM iniciar_app.bat - Arranca la app de certificados de Academia Horizonte
title Academia Horizonte - Emision de Certificados
cd /d "%~dp0"
echo.
echo  Arrancando la aplicacion...
echo  Abre http://localhost:5000 en tu navegador.
echo  Para DETENERLA: vuelve a esta ventana y presiona Ctrl + C.
echo.
python app.py
pause
