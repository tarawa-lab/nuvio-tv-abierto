# TDT España + Mundo en abierto (add-on para Nuvio / Stremio)

Add-on estático con canales de TV que se emiten **gratis y en abierto** por internet:

- **TDT España**: nacionales, autonómicos y locales, informativos, deportivos, infantiles… a partir de la lista pública de [TDTChannels](https://github.com/LaQuay/TDTChannels).
- **Mundo**: canales públicos de todo el mundo por país, a partir de la lista de [IPTV-org](https://github.com/iptv-org/iptv) (la misma que usa TV Garden). Sin canales para adultos ni bloqueados.

No afiliado a TDTChannels ni a IPTV-org. Este repositorio solo contiene enlaces a emisiones públicas; no aloja vídeo.

## Instalar
Añade en Nuvio (Ajustes → Addons → Add Addon) esta URL:

```
https://raw.githubusercontent.com/tarawa-lab/nuvio-tv-abierto/main/manifest.json
```

## Regenerar
Los scripts de `tools/` generan los archivos a partir de `TELEVISION.md` de TDTChannels y de las carpetas `streams/` y `data/` de iptv-org.
