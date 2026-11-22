# Genera listas M3U para apps IPTV a partir de los catálogos y streams del add-on.
import json, os, sys
root = sys.argv[1]
m = json.load(open(os.path.join(root, 'manifest.json'), encoding='utf-8'))
ZONA = {'tv-espana': 'España', 'tv-latam': 'Latinoamérica', 'tv-europa': 'Europa', 'tv-mundo': 'Mundo'}
def esc(s): return s.replace('"', "'").replace(',', ' ')
total = 0; listas = {}
for c in m['catalogs']:
    metas = json.load(open(os.path.join(root, 'catalog/tv', c['id'] + '.json'), encoding='utf-8'))['metas']
    for x in metas:
        st = json.load(open(os.path.join(root, 'stream/tv', x['id'] + '.json'), encoding='utf-8'))['streams']
        if not st: continue
        s = st[0]; z = ZONA.get(c['id'], 'Otros'); g = x['genres'][0]
        grupo = f'España · {g}' if z == 'España' else f'{z} · {g}'
        hdr = s.get('behaviorHints', {}).get('proxyHeaders', {}).get('request', {})
        lines = [f'#EXTINF:-1 tvg-id="{esc(x["id"])}" tvg-name="{esc(x["name"])}"' + (f' tvg-logo="{x["poster"]}"' if x.get('poster') else '') + f' group-title="{esc(grupo)}",{x["name"]}']
        if hdr.get('Referer'): lines.append(f'#EXTVLCOPT:http-referrer={hdr["Referer"]}')
        if hdr.get('User-Agent'): lines.append(f'#EXTVLCOPT:http-user-agent={hdr["User-Agent"]}')
        lines.append(s['url'])
        for nombre in ('todos', z.lower().replace('españa','espana').replace('latinoamérica','latinoamerica')):
            listas.setdefault(nombre, []).append('\n'.join(lines))
        total += 1
os.makedirs(os.path.join(root, 'listas'), exist_ok=True)
for nombre, items in listas.items():
    open(os.path.join(root, 'listas', nombre + '.m3u'), 'w', encoding='utf-8').write('#EXTM3U\n' + '\n'.join(items) + '\n')
print('canales:', total, {k: len(v) for k, v in listas.items()})
