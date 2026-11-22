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
    m = dict(id=i['id'], type='tv', name=i['name'], genres=[g])   # ficha ligera
    lg = i['logo'] or ''
    if lg.startswith('https://') and lg.isascii() and len(lg) < 200 and not lg.lower().split('?')[0].endswith(('.svg','.gif')): m['poster'] = lg
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

# --- 4 filas grandes (la app de LG solo carga las 4 primeras filas del inicio) ---
import csv as _csv
REG = {r['code']: set(r['countries'].split(';')) for r in _csv.DictReader(open(os.environ.get('IPTV_DB','/tmp/iptvdb/data')+'/regions.csv', encoding='utf-8'))}
EUR = REG['EUR'] | {'UK'}; LAT = REG['LATAM'] | {'PR'}
ORD_ES = ['Generalistas','Noticias','Deportes','Infantil','Autonómicos y locales']
def es_key(i):
    t = next((x for x in ORD_ES if x in i['tipos']), 'Otros')
    return (ORD_ES.index(t) if t in ORD_ES else len(ORD_ES), i.get('pr', 9), i['name'].lower()), t
big = []
es_items = sorted((i for i in items if i['cc']=='ES'), key=lambda i: es_key(i)[0])
_tdt = {c['id']: c for c in tdt}
big.append(('tv-espana', 'Canales de España', [(i, ('Autonómicos · ' + _tdt[i['id']]['genre']) if es_key(i)[1]=='Autonómicos y locales' and i['id'] in _tdt else es_key(i)[1]) for i in es_items]))
def by_country(pred):
    sel = sorted((i for i in items if i['cc']!='ES' and pred(i['cc'])), key=lambda i: (HISP.index(i['cc']) if i['cc'] in HISP else len(HISP), unicodedata.normalize('NFKD', pais(i['cc'])).encode('ascii','ignore').decode(), i['name'].lower()))
    return [(i, pais(i['cc'])) for i in sel]
big.append(('tv-latam', 'Canales de Latinoamérica', by_country(lambda cc: cc in LAT)))
big.append(('tv-europa', 'Canales de Europa', by_country(lambda cc: cc in EUR)))
big.append(('tv-mundo', 'Canales del resto del mundo', by_country(lambda cc: cc not in LAT and cc not in EUR)))
for rid, name, sel in big:
    metas = []
    for i, tag in sel:
        metas.append(meta(i, tag))
    w(f'catalog/tv/{rid}.json', {"metas": metas})
mp = os.path.join(out,'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
m['catalogs'] = [dict(type='tv', id=rid, name=name) for rid, name, sel in big]
m['version'] = '3.0.0'
json.dump(m, open(mp,'w',encoding='utf-8'), ensure_ascii=False)
os.remove(os.path.join(out,'_index_tdt.json')); os.remove(os.path.join(out,'_index_iptv.json'))
print(len(items), 'canales;', len(paises), 'países;', 'tipos:', {t: sum(t in i['tipos'] for i in items) for t in tipos})
print('filas:', [(n, len(x)) for _, n, x in rows])
print('grandes:', [(n, len(x)) for _, n, x in big])
print('España:', sum(i['cc']=='ES' for i in items))

# --- Add-on aparte solo con deportes (duplicados), en su carpeta con su propio manifest.json ---
import csv as _csv2
_REG = {r['code']: set(r['countries'].split(';')) for r in _csv2.DictReader(open(os.environ.get('IPTV_DB','/tmp/iptvdb/data')+'/regions.csv', encoding='utf-8'))}
_LAT = _REG['LATAM'] | _REG['CENAMER'] | _REG['CARIB'] | {'PR'}; _EUR = _REG['EUR'] | {'UK'}
dep = [i for i in items if 'Deportes' in i['tipos']]
def _zona(i): return 0 if i['cc']=='ES' else 1 if i['cc'] in _LAT else 2 if i['cc'] in _EUR else 3
_ND = ['España', 'Latinoamérica', 'Europa', 'Resto del mundo']
dm = json.load(open(mp, encoding='utf-8')); dm['catalogs'] = []
dm['id'] = dm['id'] + '.deportes'; dm['name'] = 'TV abierta · Deportes'
dm['description'] = 'Solo canales deportivos en abierto (duplicados del add-on principal).'
for z in range(4):
    sel = sorted((i for i in dep if _zona(i)==z), key=lambda i: (pais(i['cc']), i['name'].lower()))
    if not sel: continue
    rid = f'dep-f{z+1}'
    w(f'deportes/catalog/tv/{rid}.json', {"metas": [meta(i, 'España' if i['cc']=='ES' else pais(i['cc'])) for i in sel]})
    dm['catalogs'].append(dict(type='tv', id=rid, name=f'Deportes · {_ND[z]}'))
    for i in sel:
        for res in ('meta', 'stream'):
            src = os.path.join(out, res, 'tv', i['id'] + '.json'); dst = os.path.join(out, 'deportes', res, 'tv', i['id'] + '.json')
            os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copyfile(src, dst)
json.dump(dm, open(os.path.join(out, 'deportes', 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('deportes:', [(c['name'], len(json.load(open(os.path.join(out,'deportes/catalog/tv',c['id']+'.json')))['metas'])) for c in dm['catalogs']])
