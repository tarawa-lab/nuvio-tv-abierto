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
    if i['logo']: m.update(poster=i['logo'], logo=i['logo'])
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

# --- Filas de 100 canales como máximo (mismo formato que los add-ons de canales que la app de LG muestra bien) ---
import csv as _csv
ROW = 100
big = []
def add_rows(base_id, title, sel, tag):
    for k in range(0, len(sel), ROW):
        part = sel[k:k+ROW]; n = k//ROW + 1
        rid = base_id if n == 1 else f'{base_id}-{n}'
        name = title if len(sel) <= ROW else f'{title} ({n})'
        big.append((rid, name, [(i, tag(i)) for i in part]))
ORD_ES = [('Generalistas','es-generalistas','España · Generalistas'),('Noticias','es-noticias','España · Noticias'),('Deportes','es-deportes','España · Deportes'),('Infantil','es-infantil','España · Infantil')]
es_all = [i for i in items if i['cc']=='ES']; usados = set()
for t, rid, title in ORD_ES:
    sel = sorted((i for i in es_all if i['id'] not in usados and t in i['tipos'] and 'Autonómicos y locales' not in i['tipos']), key=lambda i: (i.get('pr',9), i['name'].lower()))
    usados |= {i['id'] for i in sel}; add_rows(rid, title, sel, lambda i, t=t: t)
# Autonómicos: por comunidad (TDTChannels guarda la comunidad en genre)
tdt_by_id = {c['id']: c for c in tdt}
auto = [i for i in es_all if 'Autonómicos y locales' in i['tipos']]
usados |= {i['id'] for i in auto}
auto.sort(key=lambda i: (tdt_by_id[i['id']]['genre'], i['name'].lower()))
add_rows('es-autonomicos', 'España · Autonómicos y locales', auto, lambda i: tdt_by_id[i['id']]['genre'])
resto_es = sorted((i for i in es_all if i['id'] not in usados), key=lambda i: (i['tipos'][0], i['name'].lower()))
add_rows('es-otros', 'España · Música, cine y otros', resto_es, lambda i: i['tipos'][0])
PRIMEROS = ['MX','AR','CO','CL','PE','VE','EC','UY','PY','BO','CU','DO','PR','CR','PA','GT','HN','SV','NI','PT','AD','FR','IT','UK','DE','US']
todos = sorted({i['cc'] for i in items} - {'ES'}, key=lambda cc: (PRIMEROS.index(cc) if cc in PRIMEROS else len(PRIMEROS), unicodedata.normalize('NFKD', pais(cc)).encode('ascii','ignore').decode()))
for cc in todos:
    sel = sorted((i for i in items if i['cc']==cc), key=lambda i: (i['tipos'][0], i['name'].lower()))
    add_rows('pais-'+cc.lower(), pais(cc), sel, lambda i: i['tipos'][0])
for rid, name, sel in big:
    metas = []
    for i, tag in sel:
        mm = meta(i, tag); mm['name'] = f'[{tag}] ' + i['name']; metas.append(mm)
    w(f'catalog/tv/{rid}.json', {"metas": metas})
mp = os.path.join(out,'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
m['catalogs'] = [dict(type='tv', id=rid, name=name) for rid, name, sel in big] + [
  dict(type='tv', id='por-pais', name='TV en abierto · Por país', genres=paises, extra=[{"name":"genre","options":paises,"isRequired":False}]),
  dict(type='tv', id='por-tipo', name='TV en abierto · Por tipo de contenido', genres=tipos, extra=[{"name":"genre","options":tipos,"isRequired":False}]),
]
m['version'] = '4.0.0'
json.dump(m, open(mp,'w',encoding='utf-8'), ensure_ascii=False)
os.remove(os.path.join(out,'_index_tdt.json')); os.remove(os.path.join(out,'_index_iptv.json'))
print(len(items), 'canales;', len(paises), 'países;', 'tipos:', {t: sum(t in i['tipos'] for i in items) for t in tipos})
print('filas:', [(n, len(x)) for _, n, x in rows])
print('filas:', len(big), 'max por fila:', max(len(x) for _,_,x in big), 'total:', sum(len(x) for _,_,x in big))
print('España:', sum(i['cc']=='ES' for i in items))
