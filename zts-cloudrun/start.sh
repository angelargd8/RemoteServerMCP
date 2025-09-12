#!/bin/sh
set -eu
# Cloud Run te inyecta PORT; si no existe, usa 1969
: "${PORT:=1969}"
echo "[ZTS] starting on 0.0.0.0:${PORT}"
# Pasamos los flags explícitos al server de ZTS
exec npm start -- --port "${PORT}" --host 0.0.0.0
