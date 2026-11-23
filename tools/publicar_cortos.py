# Copia las listas a los enlaces cortos (repo tarawa-lab.github.io) añadiendo a cada URL
# un fragmento "#lNNN" (no se envía al servidor) para que la app de la tele no fusione
# los canales repetidos entre listas: así cada lista muestra todos sus canales y grupos.
# Uso: python3 tools/publicar_cortos.py <raíz_repo_listas> <raíz_repo_cortos>
import os, sys
src, dst = sys.argv[1], sys.argv[2]
MAPA = {'101': 'generos-espanol', '102': 'por-paises', '103': 'por-generos', '104': 'espana',
        '105': 'deportes', '106': 'hd-espanol-deportes', '108': '4k'}
for num, nombre in MAPA.items():
    out = []
    for ln in open(os.path.join(src, 'listas', nombre + '.m3u'), encoding='utf-8').read().splitlines():
        if ln.startswith('http'):
            ln = ln + ('&' if '#' in ln else '#') + 'l' + num
        out.append(ln)
    open(os.path.join(dst, num + '.m3u'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(num, sum(1 for l in out if l.startswith('#EXTINF')))
