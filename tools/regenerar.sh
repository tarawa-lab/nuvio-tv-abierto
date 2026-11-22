#!/bin/sh
# Uso: sh tools/regenerar.sh TELEVISION.md iptv/streams iptv-database/data
# Regenera siempre desde cero (paginate.py une cada catálogo en un solo archivo).
set -e
cd "$(dirname "$0")/.."
rm -rf /tmp/site_new catalog meta stream manifest*.json sudamerica mexico-* norteamerica-* europa-* africa-* asia-* deportes
python3 tools/build.py "$1" /tmp/site_new
python3 tools/build_iptvorg.py "$2" "$3" /tmp/site_new
python3 tools/catalogs.py /tmp/site_new
python3 tools/limpiar.py /tmp/site_new
cp -r /tmp/site_new/. .
python3 tools/m3u.py .
