@echo off
rem Crea el Python local (.venv) la primera vez y abre la aplicacion web.
setlocal
cd /d "%~dp0"
title Continuidad de cohortes

set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo No se encontro Python 3.11, 3.12 ni 3.13. Ver el README, seccion Si el PC no tiene Python.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creando el Python local en la carpeta .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo No se pudo crear .venv. Ver el README.
    pause
    exit /b 1
  )
)

set "OPC="
if exist "wheels" set "OPC=--no-index --find-links wheels"
if not exist ".venv\listo.txt" (
  echo Instalando dependencias, solo la primera vez ...
  ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check %OPC% -r requirements.txt
  if errorlevel 1 (
    echo Fallo la instalacion. Ver el README, seccion Sin internet.
    pause
    exit /b 1
  )
  echo ok> ".venv\listo.txt"
)

echo Abriendo http://127.0.0.1:8000 - para cerrar, Ctrl+C en esta ventana
".venv\Scripts\python.exe" cupos_app.py web %*
pause
