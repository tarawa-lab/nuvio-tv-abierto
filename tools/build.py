import re, json, os, sys, shutil, unicodedata
src, out = sys.argv[1], sys.argv[2]
shutil.rmtree(out, ignore_errors=True)
SPAIN = {"Nacionales":"nacionales","Informativos":"informativos","Deportivos":"deportivos","Infantiles":"infantiles",
         "Autonómicos":"autonomicos","Eventuales":"otros","Streaming":"otros","Musicales":"otros","Religiosos":"otros"}
NAMES = {"nacionales":"TDT · Nacionales","autonomicos":"TDT · Autonómicos y locales","informativos":"TDT · Informativos",
         "deportivos":"TDT · Deportivos","infantiles":"TDT · Infantiles","otros":"TDT · Musicales, religiosos y otros"}
link = re.compile(r'\[([^\]]*)\]\((https?://[^)\s]+)\)')
def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')
sec = sub = None; chans = []; seen=set()
for line in open(src, encoding='utf-8'):
    if line.startswith('## '): sec = line[3:].strip(); sub=None; continue
    if line.startswith('### '): sub = line[4:].strip(); continue
    if sec not in SPAIN or not line.startswith('| ') or line.startswith('| Canal') or line.startswith('| -'): continue
    cols = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cols) < 4: continue
    name = cols[0]
    streams = [(t,u) for t,u in link.findall(cols[1]) if ('m3u8' in t.lower() or u.split('?')[0].endswith('.m3u8')) and '[' not in u and 'mpd' not in t.lower()]
    if not streams: continue
    logo = (link.findall(cols[3]) or [(None,None)])[0][1]
    web = (link.findall(cols[2]) or [(None,None)])[0][1]
    cid = 'tdtch:' + slug((sub or sec)+'-'+name)
    if cid in seen: continue
    seen.add(cid)
    cat = SPAIN[sec]
    genre = sub if cat=='autonomicos' else sec
    chans.append(dict(id=cid, name=name, cat=cat, genre=genre, logo=logo, web=web, streams=streams))
def w(path, obj):
    p = os.path.join(out, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p,'w',encoding='utf-8'), ensure_ascii=False)
def meta(c, full=False):
    m = dict(id=c['id'], type='tv', name=c['name'], genres=[c['genre']], posterShape='square')
    if c['logo']: m.update(poster=c['logo'], logo=c['logo'])
    if full:
        m['description'] = f"{c['name']} · {c['genre']}. Emisión en abierto (lista de TDTChannels)."
        if c['logo']: m['background'] = c['logo']
        if c['web']: m['website'] = c['web']
    return m
catalogs=[]
for cat, title in NAMES.items():
    items=[c for c in chans if c['cat']==cat]
    if not items: continue
    genres = sorted({c['genre'] for c in items})
    catalogs.append(dict(type='tv', id='tdt-'+cat, name=title, genres=genres, extra=[{"name":"genre","options":genres,"isRequired":False}]))
    w(f'catalog/tv/tdt-{cat}.json', {"metas":[meta(c) for c in items]})
    for g in genres:
        w(f'catalog/tv/tdt-{cat}/genre={g}.json', {"metas":[meta(c) for c in items if c['genre']==g]})
for c in chans:
    w(f"meta/tv/{c['id']}.json", {"meta":meta(c,True)})
    w(f"stream/tv/{c['id']}.json", {"streams":[{"url":u,"name":"TDTChannels","title":f"{c['name']} · {t}","behaviorHints":{"notWebReady":True}} for t,u in c['streams']]})
manifest = dict(id='org.tdtchannels.nuvio.es', version='1.0.0', name='TDT España en abierto',
    description='Canales de TV de España que se emiten gratis y en abierto por internet (nacionales, autonómicos y locales), a partir de la lista pública de TDTChannels. No afiliado a TDTChannels.',
    resources=['catalog','meta','stream'], types=['tv'], idPrefixes=['tdtch:'], catalogs=catalogs,
    behaviorHints={"configurable":False})
w('manifest.json', manifest)
json.dump([dict(id=c['id'],name=c['name'],logo=c['logo'],cc='ES',sec=c['cat'],genre=c['genre'],cats='') for c in chans], open(os.path.join(out,'_index_tdt.json'),'w',encoding='utf-8'), ensure_ascii=False)
print(len(chans), {k:sum(1 for c in chans if c['cat']==k) for k in NAMES})
