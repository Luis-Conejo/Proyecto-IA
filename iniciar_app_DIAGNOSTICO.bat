@echo off
title Certificados - Diagnostico
cd /d "%~dp0"
echo ============================================
echo   DIAGNOSTICO - App de Certificados
echo   Carpeta: %CD%
echo ============================================
echo.
echo [1/4] Buscando Python...
set "PYCMD="
python --version >nul 2>&1
if not errorlevel 1 set "PYCMD=python"
if not defined PYCMD (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYCMD=py -3"
)
if not defined PYCMD (
    echo   ERROR: No se encontro Python en esta computadora.
    echo   Solucion: instalar desde https://www.python.org/downloads/
    echo   y marcar la casilla "Add Python to PATH".
    goto fin
)
echo   Python encontrado: %PYCMD%
%PYCMD% --version
echo.
echo [2/4] Verificando librerias (flask, pandas, openpyxl)...
%PYCMD% -c "import flask, pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo   Faltan librerias. Instalando, espere un momento...
    %PYCMD% -m pip install flask pandas openpyxl
) else (
    echo   Librerias OK
)
echo.
echo [3/4] Verificando los Excel de Insumos...
if exist "Insumos\Maestro_Estudiantes.xlsx" (echo   Maestro_Estudiantes.xlsx OK) else (echo   ERROR: falta Insumos\Maestro_Estudiantes.xlsx)
if exist "Insumos\Registro_Evaluaciones.xlsx" (echo   Registro_Evaluaciones.xlsx OK) else (echo   ERROR: falta Insumos\Registro_Evaluaciones.xlsx)
echo.
echo [4/4] Arrancando la app...
echo   En unos segundos se abrira http://localhost:5000
echo   Si no carga a la primera, espere 3 segundos y actualice con F5.
echo   Para DETENER la app: Ctrl + C en esta ventana.
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"
%PYCMD% app.py
:fin
echo.
echo ============================================
echo  La app se detuvo o hubo un error.
echo  NO cierre esta ventana sin leer el mensaje de arriba.
echo ============================================
pause
