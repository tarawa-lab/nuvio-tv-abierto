# Tres listas M3U para apps IPTV con TODOS los canales (propios + agregadores):
#   listas/por-generos.m3u, listas/por-paises.m3u, listas/generos-espanol.m3u
# Uso: python3 tools/clasificar.py <raíz_repo> <iptv-org/database/data> <carpeta_extras>
import csv, json, os, re, sys, unicodedata
from babel import Locale
root, db, extra = sys.argv[1], sys.argv[2], sys.argv[3]
ES_T = Locale('es').territories; EN = {v.lower(): k for k, v in Locale('en').territories.items()}
def pais(cc): return ES_T.get('GB' if cc == 'UK' else cc, cc) if cc else 'Sin país'
HISP = {'ES','MX','AR','CO','CL','PE','VE','EC','UY','PY','BO','CU','DO','PR','CR','PA','GT','HN','SV','NI','GQ'}
chan = {r['id']: r for r in csv.DictReader(open(os.path.join(db, 'channels.csv'), encoding='utf-8'))}
lang = {}
for r in csv.DictReader(open(os.path.join(db, 'feeds.csv'), encoding='utf-8')):
    if r['is_main'] == 'TRUE' or r['channel'] not in lang: lang[r['channel']] = r['languages']
CAT = {'general':'Generalistas','news':'Noticias','sports':'Deportes','entertainment':'Entretenimiento','movies':'Cine','series':'Series',
 'kids':'Infantil','animation':'Infantil','family':'Infantil','music':'Música','documentary':'Documentales','culture':'Cultura',
 'education':'Educación','science':'Documentales','religious':'Religión','lifestyle':'Estilo de vida','cooking':'Cocina','travel':'Viajes',
 'outdoor':'Viajes','auto':'Motor','comedy':'Humor','classic':'Clásicos','business':'Economía','legislative':'Institucional','public':'Institucional',
 'weather':'Tiempo','shop':'Teletienda','relax':'Relax'}
TXT = [('Noticias', r'news|noticia|informa|24h|cnn|bbc world|euronews|actualidad'), ('Deportes', r'sport|deport|f[uú]tbol|football|soccer|nba|nfl|golf|tennis|racing|fight|ufc|wwe|motogp|olymp'),
 ('Infantil', r'kids|ni[ñn]os|infantil|junior|cartoon|toon|anime|baby|clan|boing|disney|nick'), ('Cine', r'movie|cine|film|pel[ií]cula|cinema'),
 ('Series', r'series?\b|sitcom|drama|novela|crime|crimen|policiac|misterio|mystery|detective'), ('Música', r'music|m[uú]sica|hits|radio|mtv|vevo|karaoke|concert|dj\b'),
 ('Documentales', r'docu|history|historia|nature|naturaleza|science|ciencia|wild|animal|discovery|geographic'), ('Humor', r'comed|humor|laugh|risa'),
 ('Cocina', r'cook|cocina|food|chef|gourmet|kitchen'), ('Viajes', r'travel|viaje|tourism|outdoor'), ('Religión', r'church|iglesia|god\b|dios|catholic|cat[oó]lic|gospel|islam|quran|bible|biblia'),
 ('Entretenimiento', r'reality|game|juego|entertain|entreten|show|tv\b')]
def genero_texto(*t):
    s = ' '.join(x for x in t if x).lower()
    for g, rx in TXT:
        if re.search(rx, s): return g
    return 'Otros'
def esc(s): return (s or '').replace('"', "'")
canales = []; vistos = set()
def add(name, url, logo, cc, genero, espanol, extra_lines=(), hd=False, uhd=None):
    if not url or url in vistos: return
    if uhd is None: uhd = bool(re.search(r'\b(4K|UHD|2160p)\b', name or '', re.I))
    vistos.add(url); canales.append(dict(name=name, url=url, logo=logo, cc=cc, genero=genero, es=espanol, extra=list(extra_lines), hd=hd, uhd=uhd))
def res(t):
    m = re.findall(r'(\d{3,4})[pi]\b', t or ''); return max(map(int, m)) if m else 0
feed_hd = {}
for r_ in csv.DictReader(open(os.path.join(db, 'feeds.csv'), encoding='utf-8')):
    if res(r_['format']) >= 720 or r_['id'].upper() in ('HD','FHD','UHD','4K'): feed_hd[r_['channel']] = True
def nombre_hd(n): return bool(re.search(r'\b(HD|FHD|UHD|4K)\b', n or '', re.I))

# 1) Propios (TDT + IPTV-org), con su género y país del índice
idx = json.load(open(os.environ.get('CANALES_INDEX', '/tmp/_canales_index.json'), encoding='utf-8'))
for i in idx:
    st = json.load(open(os.path.join(root, 'stream/tv', i['id'] + '.json'), encoding='utf-8'))['streams']
    if not st: continue
    s = st[0]; hdr = s.get('behaviorHints', {}).get('proxyHeaders', {}).get('request', {})
    ex = ([f'#EXTVLCOPT:http-referrer={hdr["Referer"]}'] if hdr.get('Referer') else []) + ([f'#EXTVLCOPT:http-user-agent={hdr["User-Agent"]}'] if hdr.get('User-Agent') else [])
    g = i['tipos'][0]
    if g == 'Autonómicos y locales': g = 'Autonómicos y locales (España)'
    if g == 'Otros': g = genero_texto(i['name'])
    cid = i['id'].split(':', 1)[1] if i['id'].startswith('iptvorg:') else None
    lg = lang.get(cid, '') if cid else ''
    es = ('spa' in lg.split(';')) if lg else (i['cc'] in HISP)
    meta = json.load(open(os.path.join(root, 'meta/tv', i['id'] + '.json'), encoding='utf-8'))['meta']
    r0 = max([res(x.get('title','')) for x in st] + [0])
    hd = r0 >= 720 or (r0 == 0 and (feed_hd.get(cid, False) or nombre_hd(i['name'])))
    add(i['name'], s['url'], meta.get('poster') or meta.get('logo'), i['cc'], g, es, ex, hd, r0 >= 2160 or bool(re.search(r'\b(4K|UHD)\b', i['name'], re.I)))
# 2) Agregadores
def leer(fn):
    out = []; cur = None; exl = []
    p = os.path.join(extra, fn)
    if not os.path.exists(p): return out
    for ln in open(p, encoding='utf-8', errors='ignore').read().splitlines():
        if ln.startswith('#EXTINF'): cur = ln; exl = []
        elif ln.startswith('#EXTVLCOPT') or ln.startswith('#KODIPROP'): exl.append(ln)
        elif ln.startswith('http') and cur: out.append((cur, exl, ln.strip())); cur = None
    return out
def attr(inf, k):
    m = re.search(k + r'="([^"]*)"', inf); return m.group(1) if m else ''
def nombre(inf): return inf.rsplit(',', 1)[-1].strip()
CAT_ES = {'anime':'Infantil','cine':'Cine','comedia':'Humor','crimen y misterio':'Series','crimen':'Series','cultura':'Cultura','deporte':'Deportes','deportes':'Deportes',
 'documentales':'Documentales','entretenimiento':'Entretenimiento','infantil':'Infantil','niños':'Infantil','música & ambiente':'Música','música':'Música',
 'mtv en pluto tv':'Música','noticias':'Noticias','policiacas':'Series','reality':'Entretenimiento','serie':'Series','series':'Series','telenovela':'Series','viajes y cocina':'Viajes'}
for fn in ['plutotv_es.m3u','samsungtvplus_es.m3u','plex_es.m3u']:
    for inf, exl, u in leer(fn):
        g = CAT_ES.get(attr(inf, 'group-title').lower()) or genero_texto(nombre(inf))
        add(nombre(inf), u, attr(inf, 'tvg-logo'), 'ES', g, True, exl, True)
for fn in ['plutotv_all.m3u','samsungtvplus_all.m3u','plex_all.m3u','roku_all.m3u']:
    for inf, exl, u in leer(fn):
        grp = attr(inf, 'group-title'); cc = EN.get(grp.lower(), 'US' if fn.startswith('roku') else '')
        n = nombre(inf)
        es = cc in HISP or bool(re.search(r'español|espanol|latino|en espa', n.lower()))
        g = CAT_ES.get(grp.lower()) or genero_texto(n, grp if fn.startswith('roku') else '')
        add(n, u, attr(inf, 'tvg-logo'), cc, g, es, exl, True)
for inf, exl, u in leer('playlist.m3u8'):
    if attr(inf, 'group-title').startswith('VOD'): continue
    tid = attr(inf, 'tvg-id').split('@')[0]; c = chan.get(tid)
    cc = (attr(inf, 'tvg-country') or (c['country'] if c else '')).upper()
    cats = [CAT[x] for x in (c['categories'].split(';') if c else []) if x in CAT]
    g = cats[0] if cats else genero_texto(nombre(inf))
    lg = lang.get(tid, '')
    es = ('spa' in lg.split(';')) if lg else (cc in HISP)
    full_id = attr(inf, 'tvg-id'); fid = full_id.split('@')[1].upper() if '@' in full_id else ''
    hd = res(nombre(inf)) >= 720 or fid in ('HD','FHD','UHD','4K') or feed_hd.get(tid, False) or nombre_hd(nombre(inf))
    add(re.sub(r'\s*[ⒼⓈⓎ]+\s*$', '', nombre(inf)), u, attr(inf, 'tvg-logo'), cc, g, es, exl, hd)
# 3) Escribir listas
ORD = ['Generalistas','Autonómicos y locales (España)','Noticias','Deportes','Infantil','Cine','Series','Entretenimiento','Humor','Música','Documentales','Cultura',
       'Educación','Clásicos','Cocina','Viajes','Motor','Estilo de vida','Economía','Institucional','Tiempo','Religión','Relax','Teletienda','Otros']
def key_gen(c): return (ORD.index(c['genero']) if c['genero'] in ORD else 99, c['cc'] != 'ES', c['cc'] not in HISP, pais(c['cc']), c['name'].lower())
def norm(s): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
def escribir(fn, sel, grupo):
    lines = ['#EXTM3U']
    for c in sel:
        lines.append(f'#EXTINF:-1 tvg-name="{esc(c["name"])}"' + (f' tvg-logo="{esc(c["logo"])}"' if c['logo'] else '') + (f' tvg-country="{c["cc"]}"' if c['cc'] else '') + f' group-title="{esc(grupo(c))}",{c["name"]}')
        lines += c['extra']; lines.append(c['url'])
    open(os.path.join(root, 'listas', fn), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    return len(sel)
r = {}
r['por-generos'] = escribir('por-generos.m3u', sorted(canales, key=key_gen), lambda c: c['genero'])
r['por-paises'] = escribir('por-paises.m3u', sorted(canales, key=lambda c: (c['cc'] != 'ES', c['cc'] not in HISP, norm(pais(c['cc'])), c['name'].lower())), lambda c: pais(c['cc']))
esp = [c for c in canales if c['es']]
r['generos-espanol'] = escribir('generos-espanol.m3u', sorted(esp, key=key_gen), lambda c: c['genero'])
import collections
print(r); print('géneros (todos):', collections.Counter(c['genero'] for c in canales).most_common()); print('géneros (español):', collections.Counter(c['genero'] for c in esp).most_common(12))
dep = [c for c in canales if c['genero'] == 'Deportes']
r['deportes'] = escribir('deportes.m3u', sorted(dep, key=lambda c: (c['cc'] != 'ES', not c['es'], c['cc'] not in HISP, pais(c['cc']), c['name'].lower())), lambda c: 'Deportes · ' + pais(c['cc']))
print('deportes:', r['deportes'])

# HD y (en español o deportivo)
hdsel = [c for c in canales if c['hd'] and (c['es'] or c['genero'] == 'Deportes')]
def k_hd(c):
    if c['genero'] != 'Deportes': return (0,) + key_gen(c)
    return (1, c['cc'] != 'ES', not c['es'], c['cc'] not in HISP, norm(pais(c['cc'])), c['name'].lower())
r['hd'] = escribir('hd-espanol-deportes.m3u', sorted(hdsel, key=k_hd), lambda c: ('Deportes · ' + pais(c['cc'])) if c['genero'] == 'Deportes' else c['genero'])
print('hd:', r['hd'], collections.Counter(c['genero'] for c in hdsel).most_common(8))

uhd = [c for c in canales if c['uhd']]
r['4k'] = escribir('4k.m3u', sorted(uhd, key=key_gen), lambda c: c['genero'])
print('4k:', r['4k'], [c['name'] for c in uhd][:40])
