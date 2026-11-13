#!/usr/bin/env bash
# Crea el Python local (.venv) la primera vez y abre la aplicación web.
set -e
cd "$(dirname "$0")"
PY=""
for c in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)'; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then echo "No se encontró Python 3.11, 3.12 ni 3.13. Ver el README."; exit 1; fi
[ -d .venv ] || "$PY" -m venv .venv
if [ ! -f .venv/.listo ]; then
  echo "Instalando dependencias (solo la primera vez)..."
  OPC=""; [ -d wheels ] && OPC="--no-index --find-links wheels"
  .venv/bin/python -m pip install --quiet --disable-pip-version-check $OPC -r requirements.txt
  touch .venv/.listo
fi
exec .venv/bin/python cupos_app.py web "$@"
