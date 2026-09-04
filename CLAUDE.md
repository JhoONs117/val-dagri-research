# Val d'Agri — Briefing progetto (caricato automaticamente)

## Chi è l'utente

Ricercatore storico (non esperto GIS) che studia il brigantaggio post-unitario in
Basilicata (1860-1870). Obiettivo: ricostruire la viabilità storica (trazzere,
mulattiere, sentieri di crinale) usata dalle bande brigantesche e dall'esercito
piemontese, tramite carte militari ottocentesche e survey drone+LiDAR.

**Regole di comunicazione:**
- Spiega ogni termine tecnico GIS/cartografico la prima volta che lo usi
- Chiedi conferma prima di operazioni lunghe (>2 min) o distruttive
- NON scaricare file da siti a pagamento o che richiedono login
- NON inventare URL o numeri di foglio senza verifica reale
- NON acquistare nulla

## Area di studio

**10 comuni target** nella Val d'Agri, Basilicata:

| Comune | Provincia | Lat | Lon |
|--------|-----------|-----|-----|
| Montemurro | PZ | 40°16'N | 15°59'E |
| Spinoso | PZ | 40°15'N | 16°06'E |
| Missanello | PZ | 40°13'N | 16°04'E |
| San Martino d'Agri | PZ | 40°13'N | 16°03'E |
| Sant'Arcangelo | PZ | 40°14'N | 16°19'E |
| Roccanova | PZ | 40°21'N | 16°22'E |
| Stigliano | MT | 40°23'N | 16°14'E |
| Aliano | MT | 40°20'N | 16°14'E |
| Cirigliano | MT | 40°23'N | 16°06'E |
| Gorgoglione | MT | 40°24'N | 16°08'E |

**Bounding box totale:** 40°10'–40°30'N, 15°57'–16°42'E

## Stato del progetto (aggiornato 2026-09-04)

| Fase | Stato |
|------|-------|
| FASE 0 — DBSN PZ+MT | COMPLETATA |
| FASE 1b — 5 fogli AMS georeferenziati | COMPLETATA |
| FASE 3 — Georeferenziamento (errore <3m) | COMPLETATA |
| FASE 4 — Mappa overlay v2.0 | COMPLETATA |
| FASE 5 — Sentieri estratti (462 segmenti) + 6 target LiDAR | COMPLETATA |
| FASE 6 — OCR toponimi grotte | DA FARE |
| FASE 7 — Documentazione storica archivi | DA FARE |

## File chiave nel progetto

```
scripts/georeferenzia_fogli_ams.py   # AMS JPEG → GeoTIFF (4-GCP corner)
scripts/estrai_sentieri_grotte.py    # Estrazione sentieri da AMS (HSV+morfologia)
scripts/mappa_overlay.py             # Mappa finale (v2.0, 300 dpi)
scripts/setup_ambiente.py            # Verifica dipendenze e dati locali
output/vettori/mule_tracks_ams.geojson     # 462 sentieri georeferenziati
output/vettori/target_drone_lidar.geojson  # 6 target drone/LiDAR
```

## Dati locali (non in git)

I seguenti file DEVONO essere presenti localmente ma non sono nel repository:

| Path | Come ottenerlo |
|------|---------------|
| `data/ams_montemurro_211iv.jpg` | Wayback Machine / UT PCL Map Collection |
| `data/ams_arcangelo_211i.jpg` | idem |
| `data/ams_laurenzana_200iii.jpg` | idem |
| `data/ams_stigliano_200ii.jpg` | idem |
| `data/ams_tursi_212iv.jpg` | idem |
| `data/dbsn_potenza/Potenza_dbsn.gdb` | IGM portale DBSN (gratuito) |
| `data/dbsn_matera/Matera_dbsn.gdb` | IGM portale DBSN (gratuito) |

Esegui `python3 scripts/setup_ambiente.py` per verificare cosa manca.

## Parametri tecnici georeferenziamento (non modificare)

```python
TOP_FRAC    = 0.120   # proporzioni neatline calibrate su tutti i fogli
BOTTOM_FRAC = 0.845
LEFT_FRAC   = 0.089
RIGHT_FRAC  = 0.736
# Metodo: crop JPEG alla neatline PRIMA di assegnare GCP
# GCP: 4 angoli dell'immagine ritagliata → WGS84 EPSG:4326
# Accuratezza verificata: <3m su tutti e 5 i fogli
```

## Target drone+LiDAR identificati

| Target | Tipo | Coordinate | Priorità |
|--------|------|------------|----------|
| Dolina Myrtoappio | Depressione carsica | 40.421°N 16.082°E | ALTA |
| Timpa d'Emma | Parete calcarea verticale | 40.413°N 16.063°E | ALTA |
| Bosco di Montemurro | Bosco rifugio brigantaggio | 40.283°N 15.983°E | ALTA |
| Gole del Fiume Agri | Gola con pareti verticali | 40.250°N 16.100°E | ALTA |
| S. Chihico / depressioni | Depressioni multiple | 40.167°N 16.091°E | MEDIA |
| Mulino (Laurenzana nord) | Struttura abbandonata | 40.448°N 16.089°E | MEDIA |

## GitHub

- Repository: `https://github.com/JhoONs117/val-dagri-research`
- Account: JhoONs117
- GitHub CLI: `~/.local/bin/gh` (autenticato)
- Credential helper: esegui `~/.local/bin/gh auth setup-git` se git push fallisce
