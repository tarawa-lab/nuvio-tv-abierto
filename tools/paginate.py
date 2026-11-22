import json, os, sys, glob, urllib.parse
root = sys.argv[1]; PAGE = 100
mp = os.path.join(root, 'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
for c in m['catalogs']:
    c['extra'] = [e for e in c.get('extra', []) if e['name'] != 'skip'] + [{"name": "skip"}]
    c['extraSupported'] = [e['name'] for e in c['extra']]
json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False)
n = 0
for f in glob.glob(os.path.join(root, 'catalog/tv/**/*.json'), recursive=True):
    if 'skip=' in os.path.basename(f): os.remove(f); continue
for f in glob.glob(os.path.join(root, 'catalog/tv/**/*.json'), recursive=True):
    metas = json.load(open(f, encoding='utf-8'))['metas']
    if len(metas) <= PAGE: continue
    base = f[:-5]; d, b = os.path.dirname(f), os.path.basename(base)
    json.dump({"metas": metas[:PAGE]}, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    for s in range(PAGE, len(metas), PAGE):
        if b.startswith('genre='):   # catalog/tv/<id>/genre=X.json -> catalog/tv/<id>/genre=X&skip=N.json
            out = os.path.join(d, f'{b}&skip={s}.json')
        else:                        # catalog/tv/<id>.json -> catalog/tv/<id>/skip=N.json
            os.makedirs(base, exist_ok=True); out = os.path.join(base, f'skip={s}.json')
        json.dump({"metas": metas[s:s+PAGE]}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); n += 1
print('páginas extra:', n)

# Página final vacía (skip = total) para que la app sepa que no hay más, en vez de recibir un 404
t = 0
for f in glob.glob(os.path.join(root, 'catalog/tv/**/*.json'), recursive=True):
    b = os.path.basename(f)[:-5]
    if 'skip=' in b: continue
    d = os.path.dirname(f)
    total = 0; pages = [f]
    if b.startswith('genre='):
        pages += glob.glob(os.path.join(d, glob.escape(b) + '&skip=*.json'))
        total = sum(len(json.load(open(p, encoding='utf-8'))['metas']) for p in pages)
        out = os.path.join(d, f'{b}&skip={total}.json')
    else:
        base = f[:-5]
        pages += glob.glob(os.path.join(glob.escape(base), 'skip=*.json'))
        total = sum(len(json.load(open(p, encoding='utf-8'))['metas']) for p in pages)
        os.makedirs(base, exist_ok=True); out = os.path.join(base, f'skip={total}.json')
    if not os.path.exists(out):
        json.dump({"metas": []}, open(out, 'w', encoding='utf-8')); t += 1
print('páginas finales vacías:', t)
