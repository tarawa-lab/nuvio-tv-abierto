# Antes partía cada catálogo en páginas de 100 (extra "skip"), pero la guía de Nuvio
# solo carga la primera página. Ahora cada catálogo va entero en un solo archivo.
# Es idempotente: si encuentra páginas skip= de una salida antigua, las une y las borra.
import json, os, sys, glob, re
root = sys.argv[1]
mp = os.path.join(root, 'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
for c in m['catalogs']:
    c['extra'] = [e for e in c.get('extra', []) if e['name'] != 'skip']
    c['extraSupported'] = [e['name'] for e in c['extra']]
    if not c['extra']: del c['extra']; del c['extraSupported']
json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False)

def skipnum(p):
    return int(re.search(r'skip=(\d+)\.json$', p).group(1))

n = 0
for f in glob.glob(os.path.join(root, 'catalog/tv/**/*.json'), recursive=True):
    b = os.path.basename(f)[:-5]
    if 'skip=' in b: continue
    d = os.path.dirname(f)
    if b.startswith('genre='):
        pages = glob.glob(os.path.join(d, glob.escape(b) + '&skip=*.json'))
    else:
        pages = glob.glob(os.path.join(glob.escape(f[:-5]), 'skip=*.json'))
    if not pages: continue
    metas = json.load(open(f, encoding='utf-8'))['metas']
    seen = {x['id'] for x in metas}
    for p in sorted(pages, key=skipnum):
        for x in json.load(open(p, encoding='utf-8'))['metas']:
            if x['id'] not in seen: seen.add(x['id']); metas.append(x)
        os.remove(p)
    json.dump({"metas": metas}, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if not b.startswith('genre=') and os.path.isdir(f[:-5]) and not os.listdir(f[:-5]): os.rmdir(f[:-5])
    n += 1
print('catálogos unidos:', n)
