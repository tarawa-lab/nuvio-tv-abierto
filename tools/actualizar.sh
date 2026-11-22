#!/bin/sh
# Actualización completa: descarga las fuentes públicas y regenera add-ons y listas M3U.
# Uso (desde la raíz del repo): sh tools/actualizar.sh
set -e
cd "$(dirname "$0")/.."
pip install --break-system-packages -q babel >/dev/null 2>&1 || pip install -q babel >/dev/null 2>&1 || true
W=/tmp/actualizar_tv; rm -rf "$W"; mkdir -p "$W/extra"
curl -sfL --retry 3 -o "$W/TELEVISION.md" https://raw.githubusercontent.com/LaQuay/TDTChannels/master/TELEVISION.md
git clone -q --depth 1 --filter=blob:none --sparse https://github.com/iptv-org/iptv.git "$W/iptv"
git -C "$W/iptv" sparse-checkout set streams >/dev/null
git clone -q --depth 1 https://github.com/iptv-org/database.git "$W/iptvdb"
for f in playlist.m3u8; do curl -sfL --retry 3 -o "$W/extra/$f" "https://raw.githubusercontent.com/Free-TV/IPTV/master/$f"; done
for f in plutotv_es plutotv_all samsungtvplus_es samsungtvplus_all plex_es plex_all roku_all; do
  curl -sfL --retry 3 -o "$W/extra/$f.m3u" "https://raw.githubusercontent.com/BuddyChewChew/app-m3u-generator/main/playlists/$f.m3u"
done
# Comprobaciones mínimas antes de tocar nada
[ "$(grep -c '^| ' "$W/TELEVISION.md")" -gt 200 ] || { echo "TDTChannels vacío"; exit 1; }
[ "$(ls "$W/iptv/streams" | wc -l)" -gt 100 ] || { echo "iptv-org vacío"; exit 1; }
export IPTV_DB="$W/iptvdb/data"
sh tools/regenerar.sh "$W/TELEVISION.md" "$W/iptv/streams" "$W/iptvdb/data"
python3 tools/extras.py "$W/extra" .
echo "OK"
