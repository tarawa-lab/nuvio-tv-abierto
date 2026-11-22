# Listas extra de otros agregadores de TV gratuita y legal (Free-TV, Pluto TV, Samsung TV Plus, Plex, Roku).
# Uso: python3 tools/extras.py <carpeta_con_m3u_descargados> <raíz_del_repo>
import os, re, sys
from babel import Locale
src, root = sys.argv[1], sys.argv[2]
EN = {v.lower(): k for k, v in Locale('en').territories.items()}
ES = Locale('es').territories
def pais_es(nombre):
    cc = EN.get(nombre.strip().lower())
    return ES.get(cc, nombre) if cc else nombre
def leer(fn):
    out = []; cur = None; extra = []
    for ln in open(os.path.join(src, fn), encoding='utf-8', errors='ignore').read().splitlines():
        if ln.startswith('#EXTINF'): cur = ln; extra = []
        elif ln.startswith('#EXTVLCOPT') or ln.startswith('#KODIPROP'): extra.append(ln)
        elif ln.startswith('http') and cur:
            g = re.search(r'group-title="([^"]*)"', cur); out.append((cur, g.group(1) if g else '', extra, ln.strip())); cur = None
    return out
def regrupa(inf, grupo):
    inf = re.sub(r'\s*group-title="[^"]*"', '', inf)
    return inf.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{grupo}"', 1)
vistos = set()
for f in ['todos.m3u']:
    for ln in open(os.path.join(root, 'listas', f), encoding='utf-8'):
        if ln.startswith('http'): vistos.add(ln.strip())
listas = {}
def add(nombre, inf, extra, url):
    if url in vistos: return
    vistos.add(url); listas.setdefault(nombre, []).append('\n'.join([inf] + extra + [url]))
# España: Pluto, Samsung TV Plus y Plex de España (grupo = servicio · categoría)
for fn, srv in [('plutotv_es.m3u','Pluto TV'), ('samsungtvplus_es.m3u','Samsung TV Plus'), ('plex_es.m3u','Plex')]:
    for inf, g, ex, u in leer(fn):
        add('plataformas-espana', regrupa(inf, f'{srv} España · {g if g and g.lower() not in ("spain","españa") else "Varios"}'), ex, u)
# Mundo: resto de regiones de cada servicio (grupo = servicio · país)
for fn, srv in [('plutotv_all.m3u','Pluto TV'), ('samsungtvplus_all.m3u','Samsung TV Plus'), ('plex_all.m3u','Plex'), ('roku_all.m3u','Roku')]:
    for inf, g, ex, u in leer(fn):
        grupo = f'{srv} · {pais_es(g)}' if srv != 'Roku' else f'Roku (EE. UU.) · {g}'
        add('plataformas-mundo', regrupa(inf, grupo), ex, u)
# Free-TV: canales oficialmente gratuitos (grupo = país); sin VOD
for inf, g, ex, u in leer('playlist.m3u8'):
    if g.startswith('VOD'): continue
    add('free-tv', regrupa(inf, f'Free-TV · {pais_es(g)}'), ex, u)
os.makedirs(os.path.join(root, 'listas'), exist_ok=True)
for n, items in listas.items():
    open(os.path.join(root, 'listas', n + '.m3u'), 'w', encoding='utf-8').write('#EXTM3U\n' + '\n'.join(items) + '\n')
# Lista total: nuestros canales + todos los extras
base = open(os.path.join(root, 'listas', 'todos.m3u'), encoding='utf-8').read().rstrip('\n')
extra_all = '\n'.join(x for n in ['plataformas-espana', 'free-tv', 'plataformas-mundo'] for x in listas.get(n, []))
open(os.path.join(root, 'listas', 'todo-completo.m3u'), 'w', encoding='utf-8').write(base + '\n' + extra_all + '\n')
print({n: len(v) for n, v in listas.items()}, 'total extra:', sum(len(v) for v in listas.values()))
