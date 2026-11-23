# Simulacro: comprueba si responde cada enlace de las listas y genera un informe (no borra nada).
import asyncio, csv, os, re, sys, time, collections
import aiohttp
LISTAS = {'101': 'generos-espanol', '102': 'por-paises', '103': 'por-generos', '104': 'espana',
          '105': 'deportes', '106': 'hd-espanol-deportes', '108': '4k'}
def leer(fn):
    out = []; cur = None; hdr = {}
    for ln in open(fn, encoding='utf-8').read().splitlines():
        if ln.startswith('#EXTINF'): cur = ln; hdr = {}
        elif ln.startswith('#EXTVLCOPT:http-referrer='): hdr['Referer'] = ln.split('=', 1)[1]
        elif ln.startswith('#EXTVLCOPT:http-user-agent='): hdr['User-Agent'] = ln.split('=', 1)[1]
        elif ln.startswith('http') and cur:
            g = re.search(r'group-title="([^"]*)"', cur); c = re.search(r'tvg-country="([^"]*)"', cur)
            out.append(dict(name=cur.rsplit(',', 1)[-1], grupo=g.group(1) if g else '', cc=c.group(1) if c else '', url=ln.strip(), hdr=dict(hdr))); cur = None
    return out
UA = 'Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/6.0 TV Safari/537.36'
async def probar(sess, sem, c):
    async with sem:
        h = {'User-Agent': UA, **c['hdr']}
        for intento in range(2):
            try:
                async with sess.get(c['url'], headers=h, timeout=aiohttp.ClientTimeout(total=12, sock_connect=6), allow_redirects=True, ssl=False) as r:
                    if r.status >= 400: res = f'HTTP {r.status}'
                    else:
                        chunk = await r.content.read(2048)
                        if not chunk: res = 'vacío'
                        elif b'<html' in chunk[:600].lower() and b'#EXTM3U' not in chunk: res = 'devuelve web, no vídeo'
                        else: return None
            except asyncio.TimeoutError: res = 'no responde (tiempo agotado)'
            except aiohttp.ClientConnectorError: res = 'servidor no existe o rechaza'
            except Exception as e: res = type(e).__name__
            if intento == 0: await asyncio.sleep(2)
        return res
async def main():
    todos = leer('listas/por-paises.m3u')
    sem = asyncio.Semaphore(150); conn = aiohttp.TCPConnector(limit=150, ttl_dns_cache=600)
    async with aiohttp.ClientSession(connector=conn) as sess:
        t0 = time.time(); res = await asyncio.gather(*(probar(sess, sem, c) for c in todos))
    caidos = {c['url']: (c, r) for c, r in zip(todos, res) if r}
    os.makedirs('informe', exist_ok=True)
    with open('informe/caidos.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['canal', 'país', 'motivo', 'enlace'])
        for c, r in sorted(caidos.values(), key=lambda x: (x[0]['grupo'], x[0]['name'].lower())): w.writerow([c['name'], c['grupo'], r, c['url']])
    lin = [f'# Simulacro de limpieza de enlaces caídos', '', f'Comprobados {len(todos)} canales en {int(time.time()-t0)} s desde un servidor de GitHub (EE. UU.).', '',
           f'**Se borrarían {len(caidos)} canales ({100*len(caidos)//max(1,len(todos))} %). Quedarían {len(todos)-len(caidos)}.**', '',
           'Aviso: algunos canales solo funcionan desde su país (p. ej. España) y aquí pueden salir como caídos aunque en tu tele se vean.', '',
           '## Por lista', '', '| Lista | Canales | Se borrarían | Quedarían |', '|---|---|---|---|']
    for num, fn in LISTAS.items():
        p = f'listas/{fn}.m3u'
        if not os.path.exists(p): continue
        urls = [c['url'] for c in leer(p)]; n = sum(1 for u in urls if u in caidos)
        lin.append(f'| {num} | {len(urls)} | {n} | {len(urls)-n} |')
    lin += ['', '## Motivos', '', '| Motivo | Canales |', '|---|---|']
    for m, n in collections.Counter(r for _, r in caidos.values()).most_common(): lin.append(f'| {m} | {n} |')
    esp = sorted((c for c, _ in caidos.values() if c['grupo'] == 'España'), key=lambda c: c['name'].lower())
    lin += ['', f'## Canales de España que se borrarían ({len(esp)})', ''] + [f'- {c["name"]} — {caidos[c["url"]][1]}' for c in esp]
    lin += ['', '## Por país (top 30)', '', '| País | Se borrarían |', '|---|---|']
    for g, n in collections.Counter(c['grupo'] for c, _ in caidos.values()).most_common(30): lin.append(f'| {g} | {n} |')
    lin += ['', 'Lista completa en caidos.csv.']
    open('informe/README.md', 'w', encoding='utf-8').write('\n'.join(lin) + '\n')
    print(len(todos), len(caidos))
asyncio.run(main())
