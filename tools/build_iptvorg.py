import csv, json, os, re, sys, glob, hashlib
streams_dir, db, out = sys.argv[1], sys.argv[2], sys.argv[3]
rd = lambda f: list(csv.DictReader(open(os.path.join(db, f), encoding='utf-8')))
chan = {r['id']: r for r in rd('channels.csv')}
block = {r['channel'] for r in rd('blocklist.csv')}
logos = {}
for r in rd('logos.csv'):
    if r['channel'] not in logos or (r['in_use']=='TRUE' and not r['feed']): logos.setdefault(r['channel'], r['url'])
countries = {r['code'].upper(): r['name'] for r in rd('countries.csv')}
items = {}
ext = re.compile(r'#EXTINF:[^,]*?(?:tvg-id="([^"]*)")?[^,]*,(.*)')
for f in sorted(glob.glob(os.path.join(streams_dir, '*.m3u'))):
    fcc = os.path.basename(f).split('_')[0].split('.')[0].upper()
    lines = open(f, encoding='utf-8', errors='ignore').read().splitlines()
    cur = None; opts = {}
    for ln in lines:
        if ln.startswith('#EXTINF'):
            m = ext.match(ln); cur = m.groups() if m else None; opts = {}
        elif ln.startswith('#EXTVLCOPT'):
            k, _, v = ln[11:].partition('='); opts[k] = v
        elif ln.startswith('http') and cur:
            tid, title = cur; cid = (tid or '').split('@')[0]
            c = chan.get(cid)
            if cid in block or (c and (c['is_nsfw']=='TRUE' or c['closed'])): cur=None; continue
            name = c['name'] if c else re.sub(r'\s*\(\d+p\)|\s*\[[^\]]*\]', '', title).strip()
            cc = (c['country'] if c else fcc).upper()
            if cc not in countries: cur=None; continue
            key = cid or ('x-'+hashlib.md5((cc+name).encode()).hexdigest()[:10])
            it = items.setdefault(key, dict(id='iptvorg:'+re.sub(r'[^A-Za-z0-9._-]','_',key), name=name, cc=cc, logo=logos.get(cid), web=(c or {}).get('website'), cats=(c or {}).get('categories',''), streams=[]))
            hdr = {}
            if opts.get('http-referrer'): hdr['Referer']=opts['http-referrer']
            if opts.get('http-user-agent'): hdr['User-Agent']=opts['http-user-agent']
            s = {"url": ln.strip(), "name": "IPTV-org", "title": title.strip()}
            bh = {"notWebReady": True}
            if hdr: bh["proxyHeaders"] = {"request": hdr}
            s["behaviorHints"] = bh
            if all(x['url']!=s['url'] for x in it['streams']): it['streams'].append(s)
            cur = None
def w(path, obj):
    p = os.path.join(out, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
def meta(it, full=False):
    g = countries[it['cc']]
    m = dict(id=it['id'], type='tv', name=it['name'], genres=[g], posterShape='square')
    if it['logo']: m.update(poster=it['logo'], logo=it['logo'])
    if full:
        cats = ', '.join(x for x in it['cats'].split(';') if x)
        m['description'] = f"{it['name']} · {g}" + (f" · {cats}" if cats else '') + ". Emisión pública en abierto (lista de IPTV-org, la misma que usa TV Garden)."
        if it['web']: m['website'] = it['web']
    return m
allit = sorted(items.values(), key=lambda x: (x['cc'], x['name'].lower()))
genres = sorted({countries[i['cc']] for i in allit}, key=lambda g: (g!='Spain', g))
w('catalog/tv/iptvorg-mundo.json', {"metas":[meta(i) for i in allit if i['cc']=='ES']})
for g in genres:
    w(f'catalog/tv/iptvorg-mundo/genre={g}.json', {"metas":[meta(i) for i in allit if countries[i['cc']]==g]})
for i in allit:
    w(f"meta/tv/{i['id']}.json", {"meta":meta(i,True)})
    w(f"stream/tv/{i['id']}.json", {"streams":i['streams']})
mp = os.path.join(out,'manifest.json'); m = json.load(open(mp, encoding='utf-8'))
m['catalogs'] = [c for c in m['catalogs'] if c['id']!='iptvorg-mundo'] + [dict(type='tv', id='iptvorg-mundo', name='Mundo · Canales de TV Garden (por país)', genres=genres, extra=[{"name":"genre","options":genres,"isRequired":False}])]
m['idPrefixes'] = ['tdtch:','iptvorg:']
m['name'] = 'TDT España + Mundo en abierto'
m['description'] = 'Canales de TV que se emiten gratis y en abierto por internet: TDT de España (nacionales, autonómicos y locales, lista pública de TDTChannels) y canales de todo el mundo por país (lista pública de IPTV-org, la que usa TV Garden). No afiliado a TDTChannels ni a IPTV-org.'
json.dump(m, open(mp,'w',encoding='utf-8'), ensure_ascii=False)
print(len(allit), 'canales,', sum(len(i['streams']) for i in allit), 'enlaces,', len(genres), 'países; España:', sum(1 for i in allit if i['cc']=='ES'))
