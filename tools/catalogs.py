# Crea dos catálogos con los mismos canales: "Por país" y "Por tipo de contenido".
import json, os, sys, shutil, re, unicodedata
slugify = lambda x: re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()).strip('-')
from babel import Locale
out = sys.argv[1]
tdt = json.load(open(os.path.join(out,'_index_tdt.json'), encoding='utf-8'))
iptv = json.load(open(os.path.join(out,'_index_iptv.json'), encoding='utf-8'))
T = Locale('es').territories
pais = lambda cc: T.get('GB' if cc=='UK' else cc, cc)
TIPOS = {'general':'Generalistas','news':'Noticias','sports':'Deportes','entertainment':'Entretenimiento','movies':'Cine',
 'series':'Series','kids':'Infantil','animation':'Infantil','family':'Infantil','music':'Música','documentary':'Documentales',
 'culture':'Cultura','education':'Educación','science':'Documentales','religious':'Religión','lifestyle':'Estilo de vida',
 'cooking':'Cocina','travel':'Viajes','outdoor':'Viajes','auto':'Motor','comedy':'Humor','classic':'Clásicos','business':'Economía',
 'legislative':'Institucional','public':'Institucional','weather':'Tiempo','shop':'Teletienda','relax':'Relax','interactive':'Otros'}
TDT_TIPO = {'nacionales':'Generalistas','autonomicos':'Autonómicos y locales','informativos':'Noticias','deportivos':'Deportes','infantiles':'Infantil'}
OTROS_TDT = {'Musicales':'Música','Religiosos':'Religión'}
norm = lambda s: re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
items = []
seen_es = set()
for c in tdt:
    t = TDT_TIPO.get(c['sec']) or OTROS_TDT.get(c['genre'], 'Otros')
    items.append(dict(id=c['id'], name=c['name'], logo=c['logo'], cc='ES', tipos=[t], tdt=True, pr=['nacionales','informativos','deportivos','infantiles','autonomicos','otros'].index(c['sec']))); seen_es.add(norm(c['name']))
for c in iptv:
    if c['cc']=='ES' and norm(c['name']) in seen_es: continue
    tipos = sorted({TIPOS.get(x,'Otros') for x in c['cats'].split(';') if x and x!='xxx'}) or ['Otros']
    items.append(dict(id=c['id'], name=c['name'], logo=c['logo'], cc=c['cc'], tipos=tipos, tdt=False))
HISP = ['ES','MX','AR','CO','CL','PE','VE','EC','UY','PY','BO','CR','PA','DO','CU','GT','HN','SV','NI','PR','AD','PT']
rank = lambda i: (HISP.index(i['cc']) if i['cc'] in HISP else len(HISP), pais(i['cc']), i.get('pr', 9), i['name'].lower())
items.sort(key=rank)
def meta(i, g):
    m = dict(id=i['id'], type='tv', name=i['name'], genres=[g], posterShape='square')
    lg = i['logo'] or ''
    if lg.startswith('https://') and not lg.lower().split('?')[0].endswith('.svg'): m.update(poster=lg, logo=lg)
    m['name'] = re.sub(r'[\x00-\x1f]', '', m['name'])
    return m
shutil.rmtree(os.path.join(out,'catalog'), ignore_errors=True)
def w(path, obj):
    p = os.path.join(out, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
# Por país
paises = sorted({pais(i['cc']) for i in items}, key=lambda p: (p!='España', unicodedata.normalize('NFKD',p).encode('ascii','ignore').decode()))
for p in paises:
    w(f'catalog/tv/por-pais/genre={p}.json', {"metas":[meta(i, p) for i in items if pais(i['cc'])==p]})
w('catalog/tv/por-pais.json', {"metas":[meta(i,'España') for i in items if i['cc']=='ES']})
# Por tipo
orden = ['Generalistas','Autonómicos y locales','Noticias','Deportes','Infantil','Cine','Series','Entretenimiento','Música','Documentales','Cultura','Educación','Humor','Clásicos','Cocina','Viajes','Motor','Estilo de vida','Economía','Religión','Institucional','Tiempo','Relax','Teletienda','Otros']
tipos = [t for t in orden if any(t in i['tipos'] for i in items)]
for t in tipos:
    w(f'catalog/tv/por-tipo/genre={t}.json', {"metas":[meta(i, t) for i in items if t in i['tipos']]})
w('catalog/tv/por-tipo.json', {"metas":[meta(i,'Generalistas') for i in items if 'Generalistas' in i['tipos']]})

# Filas separadas para la pantalla de inicio (la app de LG no muestra el filtro de género)
rows = []
es = [i for i in items if i['cc']=='ES']
used = set()
def es_row(rid, name, pred):
    sel = [i for i in es if i['id'] not in used and pred(i)]
    used.update(i['id'] for i in sel); rows.append((rid, name, sel))
es_row('es-generalistas', 'España · Generalistas', lambda i: 'Generalistas' in i['tipos'] and not ('Autonómicos y locales' in i['tipos']))
es_row('es-autonomicos', 'España · Autonómicos y locales', lambda i: 'Autonómicos y locales' in i['tipos'])
es_row('es-noticias', 'España · Noticias', lambda i: 'Noticias' in i['tipos'])
es_row('es-deportes', 'España · Deportes', lambda i: 'Deportes' in i['tipos'])
es_row('es-infantil', 'España · Infantil', lambda i: 'Infantil' in i['tipos'])
es_row('es-otros', 'España · Música, cine y otros', lambda i: True)
for t, name in [('Noticias','Mundo · Noticias'),('Deportes','Mundo · Deportes'),('Infantil','Mundo · Infantil'),('Cine','Mundo · Cine'),('Series','Mundo · Series'),('Entretenimiento','Mundo · Entretenimiento'),('Música','Mundo · Música'),('Documentales','Mundo · Documentales y cultura')]:
    sel = [i for i in items if i['cc']!='ES' and (t in i['tipos'] or (t=='Documentales' and 'Cultura' in i['tipos']))]
    rows.append(('mundo-'+slugify(t), name, sel))
PRIMEROS = ['MX','AR','CO','CL','PE','VE','EC','UY','PT','UK','FR','IT','DE','US']
resto = sorted({i['cc'] for i in items} - set(PRIMEROS) - {'ES'}, key=lambda cc: unicodedata.normalize('NFKD', pais(cc)).encode('ascii','ignore').decode())
for cc in PRIMEROS + resto:
    rows.append(('pais-'+cc.lower(), 'País · '+pais(cc), [i for i in items if i['cc']==cc]))
for rid, name, sel in rows:
    w(f'catalog/tv/{rid}.json', {"metas":[meta(i, name.split(' · ')[-1]) for i in sel]})

# --- Guía TV de Nuvio (LG): lee solo las 4 primeras filas de cada add-on y agrupa por la etiqueta "genres".
# Por eso: 4 filas con TODOS los canales, servidas en páginas de 100 (skip), y la categoría en genres.
import csv as _csv
REG = {r['code']: set(r['countries'].split(';')) for r in _csv.DictReader(open(os.environ.get('IPTV_DB','/tmp/iptvdb/data')+'/regions.csv', encoding='utf-8'))}
EUR = REG['EUR'] | {'UK'}; LAT = REG['LATAM'] | {'PR'}
tdt_by_id = {c['id']: c for c in tdt}
ORDT = ['Generalistas','Noticias','Deportes','Infantil']
def cat_es(i):
    if 'Autonómicos y locales' in i['tipos']: return 'Autonómicos · ' + tdt_by_id[i['id']]['genre']
    t = next((x for x in ORDT if x in i['tipos']), None)
    if t: return t
    t = i['tipos'][0]
    return {'Cine':'Cine y series','Series':'Cine y series','Humor':'Cine y series','Clásicos':'Cine y series','Otros':'Locales y varios'}.get(t, t)
ORD_CAT = ['Generalistas','Noticias','Deportes','Infantil']
es_items = sorted((i for i in items if i['cc']=='ES'), key=lambda i: (ORD_CAT.index(cat_es(i)) if cat_es(i) in ORD_CAT else (5 if cat_es(i).startswith('Autonómicos') else 9), cat_es(i), i.get('pr',9), i['name'].lower()))
def world(pred):
    return sorted((i for i in items if i['cc']!='ES' and pred(i['cc'])), key=lambda i: (HISP.index(i['cc']) if i['cc'] in HISP else len(HISP), unicodedata.normalize('NFKD', pais(i['cc'])).encode('ascii','ignore').decode(), i['name'].lower()))
# Varios add-ons: la Guía TV de Nuvio en LG carga unos 2.200 canales por add-on y solo sus 4 primeras filas.
# Cada add-on: hasta 2.000 canales en 4 filas como máximo (filas de hasta 500, por países seguidos), en páginas de 100.
EUROPA_PRI = ['PT','AD','FR','IT','UK','DE']
def kpais(cc):
    if cc in HISP: return (0, HISP.index(cc), '')
    if cc in LAT: return (1, 0, pais(cc))
    if cc in EUR: return (2, EUROPA_PRI.index(cc) if cc in EUROPA_PRI else 99, unicodedata.normalize('NFKD', pais(cc)).encode('ascii','ignore').decode())
    return (3, 0 if cc=='US' else 1, unicodedata.normalize('NFKD', pais(cc)).encode('ascii','ignore').decode())
ADDON_MAX, ROW_MAX = 2000, 500
bloques = [('España', [(i, cat_es(i)) for i in es_items])]
for cc in sorted({i['cc'] for i in items} - {'ES'}, key=kpais):
    sel = sorted((i for i in items if i['cc']==cc), key=lambda i: i['name'].lower())
    for k in range(0, len(sel), ROW_MAX):   # países enormes (EE. UU.) en trozos de 500
        bloques.append((pais(cc), [(i, pais(cc)) for i in sel[k:k+ROW_MAX]]))
addons = []; cur = []; rows = []; row = []; rown = []
def cerrar_fila():
    global row, rown
    if row:
        ns = list(dict.fromkeys(rown))
        cur.append((' · '.join(ns) if len(ns) <= 3 else f'{ns[0]} … {ns[-1]}', row)); row = []; rown = []
for nombre, sel in bloques:
    if nombre == 'España':
        cur.append(('España', sel)); continue
    if len(row) + len(sel) > ROW_MAX: cerrar_fila()
    if len(cur) == 4 or sum(len(r) for _, r in cur) + len(row) + len(sel) > ADDON_MAX:
        cerrar_fila(); addons.append(cur); cur = []
    row += sel; rown.append(nombre)
cerrar_fila(); addons.append(cur)
PAGE = 100
big = []
for a, filas in enumerate(addons, 1):
    for r, (nombre, sel) in enumerate(filas, 1):
        rid = f'a{a}-f{r}'
        metas = [meta(i, cat) for i, cat in sel]
        for k in range(0, len(metas), PAGE):
            w(f'catalog/tv/{rid}.json' if k == 0 else f'catalog/tv/{rid}/skip={k}.json', {"metas": metas[k:k+PAGE]})
        w(f'catalog/tv/{rid}/skip={len(metas)}.json', {"metas": []})
        big.append((rid, nombre, sel))
base = json.load(open(os.path.join(out,'manifest.json'), encoding='utf-8'))
for a, filas in enumerate(addons, 1):
    paises_a = [n for n, _ in filas]
    m2 = dict(base)
    m2['id'] = base['id'] if a == 1 else f"{base['id']}.{a}"
    primero = filas[0][1][0][0]['cc']; ultimo = filas[-1][1][-1][0]['cc']
    m2['name'] = f'TV abierta {a} · ' + ('España' if primero == 'ES' else pais(primero)) + ' – ' + pais(ultimo)
    m2['catalogs'] = [dict(type='tv', id=f'a{a}-f{r}', name=n, extra=[{"name":"skip"}], extraSupported=['skip']) for r, (n, _) in enumerate(filas, 1)]
    m2['version'] = '6.0.0'
    json.dump(m2, open(os.path.join(out, 'manifest.json' if a == 1 else f'manifest-{a}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('addons:', [(a, sum(len(r) for _, r in f), [n for n, _ in f]) for a, f in enumerate(addons, 1)])
mp = os.path.join(out,'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
m = json.load(open(mp, encoding='utf-8'))
json.dump(m, open(mp,'w',encoding='utf-8'), ensure_ascii=False)
os.remove(os.path.join(out,'_index_tdt.json')); os.remove(os.path.join(out,'_index_iptv.json'))
print(len(items), 'canales;', len(paises), 'países;', 'tipos:', {t: sum(t in i['tipos'] for i in items) for t in tipos})
print('filas:', [(n, len(x)) for _, n, x in rows])
print('filas4:', [(n, len(x)) for _, n, x in big]); print('filas:', len(big), 'max por fila:', max(len(x) for _,_,x in big), 'total:', sum(len(x) for _,_,x in big))
print('España:', sum(i['cc']=='ES' for i in items))
