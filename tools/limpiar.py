# Borra catálogos que no están en el manifiesto (restos de versiones anteriores).
import json, os, sys, shutil
root = sys.argv[1]
import glob
ids = {c['id'] for f in glob.glob(os.path.join(root, 'manifest*.json')) for c in json.load(open(f, encoding='utf-8'))['catalogs']}
d = os.path.join(root, 'catalog', 'tv'); n = 0
for f in os.listdir(d):
    base = f[:-5] if f.endswith('.json') else f
    if base not in ids:
        p = os.path.join(d, f); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p); n += 1
print('restos borrados:', n)
