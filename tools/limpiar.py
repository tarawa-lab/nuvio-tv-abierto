# Borra catálogos que no están en el manifiesto (restos de versiones anteriores).
import json, os, sys, shutil
root = sys.argv[1]
ids = {c['id'] for c in json.load(open(os.path.join(root, 'manifest.json'), encoding='utf-8'))['catalogs']}
d = os.path.join(root, 'catalog', 'tv'); n = 0
for f in os.listdir(d):
    base = f[:-5] if f.endswith('.json') else f
    if base not in ids:
        p = os.path.join(d, f); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p); n += 1
print('restos borrados:', n)
