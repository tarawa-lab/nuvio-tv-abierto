# Crea dos catálogos con los mismos canales: "Por país" y "Por tipo de contenido".
import json, os, sys, shutil, re, unicodedata
from babel import Locale
out = sys.argv[1]
tdt = json.load(open(os.path.join(out,'_index_tdt.json'), encoding='utf-8'))
iptv = json.load(open(os.path.join(out,'_index_iptv.json'), encoding='utf-8'))
T = Locale('es').territories
pais = lambda cc: T.get(cc, cc)
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
    items.append(dict(id=c['id'], name=c['name'], logo=c['logo'], cc='ES', tipos=[t], tdt=True)); seen_es.add(norm(c['name']))
for c in iptv:
    if c['cc']=='ES' and norm(c['name']) in seen_es: continue
    tipos = sorted({TIPOS.get(x,'Otros') for x in c['cats'].split(';') if x and x!='xxx'}) or ['Otros']
    items.append(dict(id=c['id'], name=c['name'], logo=c['logo'], cc=c['cc'], tipos=tipos, tdt=False))
HISP = ['ES','MX','AR','CO','CL','PE','VE','EC','UY','PY','BO','CR','PA','DO','CU','GT','HN','SV','NI','PR','AD','PT']
rank = lambda i: (HISP.index(i['cc']) if i['cc'] in HISP else len(HISP), pais(i['cc']), not i['tdt'], i['name'].lower())
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
mp = os.path.join(out,'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
m['catalogs'] = [
  dict(type='tv', id='por-pais', name='TV en abierto · Por país', genres=paises, extra=[{"name":"genre","options":paises,"isRequired":False}]),
  dict(type='tv', id='por-tipo', name='TV en abierto · Por tipo de contenido', genres=tipos, extra=[{"name":"genre","options":tipos,"isRequired":False}]),
]
m['version'] = '2.0.0'
json.dump(m, open(mp,'w',encoding='utf-8'), ensure_ascii=False)
os.remove(os.path.join(out,'_index_tdt.json')); os.remove(os.path.join(out,'_index_iptv.json'))
print(len(items), 'canales;', len(paises), 'países;', 'tipos:', {t: sum(t in i['tipos'] for i in items) for t in tipos})
print('España:', sum(i['cc']=='ES' for i in items))
