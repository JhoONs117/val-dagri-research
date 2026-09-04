# Val d'Agri — Ricerca Storico-Cartografica sul Brigantaggio (1860-1870)

> Georeferenziamento di carte militari ottocentesche, estrazione di sentieri storici
> e identificazione di target per survey drone+LiDAR per la ricerca sul brigantaggio
> post-unitario in Basilicata (10 comuni target: Aliano, Cirigliano, Gorgoglione,
> Missanello, Montemurro, Roccanova, San Martino d'Agri, Sant'Arcangelo, Spinoso, Stigliano).

## Mappa output (v2.0)

[![Mappa overlay Val d'Agri](docs/mappa_valdagri_preview.jpg)](docs/mappa_valdagri_preview.jpg)

*5 fogli AMS 1:50,000 (IGM 1895–1943) · confini comunali DBSN 2025 · sentieri storici estratti in verde (462 segmenti) · target drone/LiDAR marcati. Risoluzione originale: 6443×3847 px, 300 dpi.*

---

## Stato del progetto

| Fase | Descrizione | Stato |
|------|-------------|-------|
| FASE 0 | Ispezione dati DBSN (Potenza + Matera) | COMPLETATA ✓ |
| FASE 1 | Ricerca mappe storiche 1860-1870 | PARZIALE ⚠️ |
| FASE 1b | Download fogli AMS 1:50,000 (5 fogli) | COMPLETATA ✓ |
| FASE 2 | Setup ambiente tecnico Python/GDAL | COMPLETATA ✓ |
| FASE 3 | Georeferenziamento (5 fogli → GeoTIFF) | COMPLETATA ✓ |
| FASE 4 | Mappa overlay AMS + DBSN PZ+MT | COMPLETATA ✓ |
| FASE 5 | Estrazione sentieri + target drone/LiDAR | COMPLETATA ✓ |
| FASE 6 | OCR per toponimi "Grotta/Buco/Caverna" su AMS | DA FARE |
| FASE 7 | Ricerca documentazione storica (Massari, GMU) | DA FARE |

---

## Come riprendere il lavoro da zero (clone fresco)

### 1. Clona il repository

```bash
git clone https://github.com/JhoONs117/val-dagri-research.git
cd val-dagri-research
```

### 2. Installa dipendenze Python

```bash
pip install numpy opencv-python-headless pillow matplotlib rasterio geopandas --break-system-packages
# GDAL deve essere già installato nel sistema:
gdal_translate --version   # deve mostrare GDAL 3.x
```

### 3. Scarica i dati locali (non in git — troppo grandi)

I file vanno messi esattamente nei path indicati. Tutti gratuiti e liberi.

#### Fogli AMS 1:50,000 (da Wayback Machine / University of Texas)

Scarica dalla Wayback Machine (Internet Archive) i JPEG originali del PCL Map
Collection dell'Università del Texas. Cerca il nome del foglio su:
`https://web.archive.org/web/*/https://maps.lib.utexas.edu/maps/ams/italy_50k/*`

| File da salvare in `data/` | Foglio AMS | Copertura |
|---------------------------|-----------|-----------|
| `ams_montemurro_211iv.jpg` | 211-IV Montemurro | 40°10'–20'N, 15°57'–16°12'E |
| `ams_arcangelo_211i.jpg` | 211-I S. Arcangelo | 40°10'–20'N, 16°12'–16°27'E |
| `ams_laurenzana_200iii.jpg` | 200-III Laurenzana | 40°20'–30'N, 15°57'–16°12'E |
| `ams_stigliano_200ii.jpg` | 200-II Stigliano | 40°20'–30'N, 16°12'–16°27'E |
| `ams_tursi_212iv.jpg` | 212-IV Tursi | 40°10'–20'N, 16°27'–16°42'E |

Tutti i fogli sono basati su rilevamenti IGM 1895-1902. Dimensioni tipiche: 5000–5200×4000–4024 px, ~6 MB ciascuno.

#### DBSN IGM (dati vettoriali moderni — gratuiti)

Portale IGM: `https://igmi.esercito.difesa.it/porta-magna/data/dbsn/`

```bash
# Provincia di Potenza
# Cerca: PZ_dbsn_{data}.zip  (es. PZ_dbsn_2025-07-28.zip)
# Estrai in: data/dbsn_potenza/  →  deve contenere Potenza_dbsn.gdb

# Provincia di Matera
# Cerca: MT_dbsn_{data}.zip  (es. MT_dbsn_2025-07-28.zip)
# Estrai in: data/dbsn_matera/  →  deve contenere Matera_dbsn.gdb
```

Per estrarre da Python (se `unzip` non disponibile):
```python
import zipfile
with zipfile.ZipFile("MT_dbsn_2025-07-28.zip", "r") as z:
    z.extractall("data/dbsn_matera/")
```

### 4. Riproduci gli output

Esegui in ordine dalla directory di progetto:

```bash
# Passo A: Georeferenzia i 5 fogli AMS → produce output/geotiff/*.tif
python3 scripts/georeferenzia_fogli_ams.py

# Passo B: Estrai sentieri e strade dai fogli AMS → produce output/vettori/*.geojson
python3 scripts/estrai_sentieri_grotte.py

# Passo C: Genera mappa overlay completa → produce output/mappa_valdagri_overlay.png
python3 scripts/mappa_overlay.py
```

I GeoJSON dei sentieri e dei target sono già in git (`output/vettori/`), quindi il
Passo B può essere saltato se non si vuole rieseguire l'estrazione.

---

## File nel repository

```
val-dagri-research/
├── scripts/
│   ├── georeferenzia_fogli_ams.py     # Georeferenziamento AMS JPEG → GeoTIFF
│   ├── estrai_sentieri_grotte.py      # Estrazione sentieri/strade da AMS (HSV+morfologia)
│   ├── mappa_overlay.py               # Mappa overlay con tutti i layer (v2.0)
│   ├── analizza_fogli_ams.py          # Analisi visiva / thumbnail fogli AMS
│   ├── crop_stigliano_corrette.py     # Crop mirate foglio Stigliano (analisi)
│   ├── crop_stigliano_detail.py       # Dettagli specifici foglio Stigliano
│   ├── download_rumsey_map.py         # Download tiles carta Rumsey 1880
│   └── mappa_area_target.py          # Mappa area target (versione precedente)
├── output/vettori/
│   ├── mule_tracks_ams.geojson        # 462 segmenti sentieri storici georeferenziati
│   ├── strade_ams_1895.geojson        # 30 segmenti strade (linee rosse AMS)
│   ├── target_drone_lidar.geojson     # 6 target prioritari per survey drone+LiDAR
│   └── etichette_isolate_ams.geojson  # Candidati etichette testo (vuoto — serve OCR vero)
├── data/
│   ├── basilicata_boundary_wgs84.gpkg # Confine regionale Basilicata (GeoPackage)
│   └── comuni_target_wgs84.gpkg      # 10 comuni target (GeoPackage)
├── docs/
│   └── mappa_valdagri_preview.jpg    # Preview mappa per GitHub (1800px)
├── .gitignore                         # Esclude JPEG AMS, DBSN, GeoTIFF, PNG grandi
└── README.md                          # Questo file
```

**Non in git (troppo grandi, vedi sezione "Scarica i dati locali"):**
- `data/ams_*.jpg` — 5 fogli AMS (~6 MB ciascuno)
- `data/dbsn_potenza/` — geodatabase PZ (~500 MB)
- `data/dbsn_matera/` — geodatabase MT (~300 MB)
- `output/geotiff/` — 5 GeoTIFF georeferenziati (~26-44 MB ciascuno)
- `output/mappa_valdagri_overlay.png` — mappa finale (~39 MB)

---

## Dettagli tecnici: georeferenziamento

### Struttura foglio AMS

Ogni JPEG ha questa struttura (proporzioni calibrate su tutti e 5 i fogli):

```
[margine testo sup  ~12%]
[marg. sx ~9%] [CONTENUTO GEOGRAFICO ~63%] [LEGENDA ~26%] [marg. dx ~1%]
[margine testo inf  ~15%]
```

**Proporzioni neatline (calibrate, verificate):**
- `TOP_FRAC    = 0.120`
- `BOTTOM_FRAC = 0.845`
- `LEFT_FRAC   = 0.089`
- `RIGHT_FRAC  = 0.736`

**Metodo GCP:** Il JPEG viene ritagliato alla neatline PRIMA di assegnare i GCP.
I 4 GCP sono agli angoli dell'immagine ritagliata (0,0)→(w,h). Questo evita che
`gdalwarp` estrapoli le coordinate della legenda nello spazio geografico (bug critico
che causava errori di ~2 km nella versione precedente).

**Accuratezza verificata:** errore < 3 m su tutti e 5 i fogli.

### Coordinate fogli

| File | lon_W | lon_E | lat_S | lat_N | IGM |
|------|-------|-------|-------|-------|-----|
| `ams_montemurro_211iv.jpg` | 15°57'E | 16°12'E | 40°10'N | 40°20'N | 1896 |
| `ams_arcangelo_211i.jpg` | 16°12'E | 16°27'E | 40°10'N | 40°20'N | 1896 |
| `ams_laurenzana_200iii.jpg` | 15°57'E | 16°12'E | 40°20'N | 40°30'N | 1895 |
| `ams_stigliano_200ii.jpg` | 16°12'E | 16°27'E | 40°20'N | 40°30'N | 1902 |
| `ams_tursi_212iv.jpg` | 16°27'E | 16°42'E | 40°10'N | 40°20'N | 1943 |

---

## Risultati dell'estrazione automatica

### Sentieri storici (mulattiere)

Lo script `estrai_sentieri_grotte.py` analizza i fogli AMS in HSV:
- **Strade rosse** (categoria 1-5 legenda AMS): H=0-10 o 168-180, S>90, V=80-220
- **Mule Tracks** (linee nere tratteggiate): pixel scuri (V<80) meno curve di livello
  brune (H=8-28) e strade rosse, poi dilatazione direzionale (kernel 1×25, 25×1,
  diagonale 15×15) per collegare i trattini delle linee tratteggiate

**Output:** 462 segmenti mulattiere + 30 segmenti strade, tutti georeferenziati in
GeoJSON (EPSG:4326), pronti per importazione in QGIS o software GIS.

**Nota colori per foglio:** Il foglio Laurenzana 200-III (1895) usa il BLU per i
sentieri, non il nero. L'estrazione cattura solo il nero — il foglio Laurenzana ha
sentieri parzialmente non estratti. Da correggere in FASE 6.

---

## Target drone + LiDAR identificati

6 target identificati da analisi visiva dei fogli AMS. Tutti nel file
`output/vettori/target_drone_lidar.geojson`.

| # | Nome | Tipo | Coordinate | Priorità | Foglio AMS |
|---|------|------|------------|----------|-----------|
| 1 | Dolina Myrtoappio | Depressione carsica | 40.421°N 16.082°E | **ALTA** | Laurenzana 200-III |
| 2 | Timpa d'Emma | Parete rocciosa calcarea | 40.413°N 16.063°E | **ALTA** | Laurenzana 200-III |
| 3 | Bosco di Montemurro | Bosco rifugio brigantaggio | 40.283°N 15.983°E | **ALTA** | Montemurro 211-IV |
| 4 | Gole del Fiume Agri | Gola fluviale con pareti | 40.250°N 16.100°E | **ALTA** | Montemurro 211-IV |
| 5 | S. Chihico / depressioni | Depressioni multiple | 40.167°N 16.091°E | MEDIA | Montemurro 211-IV |
| 6 | Mulino (Laurenzana nord) | Struttura abbandonata | 40.448°N 16.089°E | MEDIA | Laurenzana 200-III |

**Legenda simboli nella mappa:**
- ★ Viola = dolina carsica (potenziale ingresso grotta)
- ▲ Arancio = parete rocciosa / timpa (cavità nelle pareti)
- ✚ Verde scuro = bosco rifugio (LiDAR sotto chioma per sentieri nascosti)
- ▽ Azzurro = gola fluviale (pareti verticali inaccessibili da terra)
- ■ Marrone = struttura abbandonata (fotogrammetria drone)

**Cosa si può vedere con drone+LiDAR:**
- Depressioni/doline nel DTM (LiDAR ground-filtered)
- Sentieri sepolti sotto vegetazione (differenza CHM–DTM)
- Ruderi di masserie e mulini (punto nuvola densa)
- Ingressi di grotte (negative relief nelle pareti)

**Cosa NON si può vedere:** l'interno delle grotte (serve SLAM terrestre).

---

## Legenda fogli AMS GSGS 4229 (serie Italy 1:50,000)

| Simbolo | Colore | Significato |
|---------|--------|-------------|
| Linea continua rossa | Rosso | Strade carrozzabili (cat. 1-5) |
| Linea tratteggiata lunga nera | Nero | Mule Tracks (mulattiere) |
| Linea puntinata nera | Nero | Footpaths (sentieri a piedi) |
| Linea tratteggiata rossa | Rosso | Confine provinciale |
| Linea tratteggiata nera fine | Nero | Confine comunale |
| Oval/cerchio chiuso su curve | Marrone | Dolina/depressione carsica |
| Simbolo "pettine" su curva | Marrone | Scarpata / rupe (cliff) |

**Nota importante:** La serie GSGS 4229 NON ha un simbolo dedicato per le grotte.
Le cavità vengono indicate solo tramite etichetta testuale ("Grotta di X") o
associazione con simboli di rupe/scarpata. OCR necessario per trovarle.

---

## Prossimi passi (FASE 6-7)

### FASE 6 — OCR per ricerca toponimi grotte

**Obiettivo:** trovare etichette "Grotta", "Buco", "Caverna", "Antro" sui fogli AMS.

**Approccio suggerito:** usare `pytesseract` (Tesseract OCR) su patch ritagliate
dei fogli in scala di grigi, poi filtrare per parole chiave:

```python
import pytesseract
from PIL import Image
img = Image.open("data/ams_laurenzana_200iii.jpg").convert("L")
# Isola la sola area mappa (neatline crop)
# Poi OCR su patch di 300×100 px con stride di 50px
text = pytesseract.image_to_data(patch, lang="ita", config="--psm 6")
```

**Zona prioritaria per grotte:** foglio Laurenzana 200-III (calcare/karst).

**Catasto Speleologico Basilicata:** contattare il Gruppo Speleologico Lucano
(GSL) o cercare il catasto regionale presso Regione Basilicata — Ufficio Parchi.
URL da verificare: `https://www.regione.basilicata.it` (sezione ambiente/parchi).

### FASE 7 — Documentazione storica

**Fonti primarie da cercare:**

| Fonte | Dove | Contenuto |
|-------|------|-----------|
| Relazione Massari (1863) | Google Books / Archive.org | Prima indagine parlamentare sul brigantaggio |
| Giornale Militare Ufficiale 1861-1870 | Archivio di Stato Roma | Ordini del giorno, operazioni militari |
| Atti della Commissione Parlamentare 1863 | Camera dei Deputati (archivio) | Testimonianze su Basilicata |
| Fondo Questura Potenza | Archivio di Stato Potenza | Rapporti di polizia, localizzazioni bande |
| Corrispondenza Prefettura PZ | Archivio di Stato Potenza | Segnalazioni e operazioni locali |

**Archivio di Stato di Potenza:**
- Via Nazario Sauro 28, 85100 Potenza
- Fondo cartografico: ~20 mappe topografiche 1854-1911 (solo consultazione fisica)
- Contatto per appuntamento necessario

### Acquisto carta storica ITM 1876-1878 (facoltativo)

Il **Foglio 85 "Montemurro"** della Carta dell'Italia Meridionale (ITM, 1877)
copre tutti e 10 i comuni target a 1:50,000. Disponibile su cartageo.com a ~€36
in formato fisico. Richiederebbe scansione ad almeno 400 DPI per uso digitale.

### Migliorie tecniche pendenti

- [ ] Estrazione sentieri BLU dal foglio Laurenzana (colore diverso dal nero)
- [ ] Distinzione linee rosse solide (strade) vs tratteggiate (confini provinciali)
- [ ] Aggiungere layer `el_vms` DBSN (viabilità minore moderna) alla mappa
- [ ] Confronto quantitativo: sentieri AMS 1895 vs strade moderne DBSN 2025
- [ ] Impostare QGIS con tutti i layer per navigazione interattiva

---

## Note tecniche ambiente

- **OS:** Linux WSL2 (Ubuntu) su Windows
- **Python:** 3.12.3
- **GDAL:** 3.8.4
- **GitHub CLI:** `~/.local/bin/gh` (v2.100.0) — autenticato come JhoONs117
- **Git credential helper:** `gh auth setup-git` (necessario dopo nuovo login)
- **DBSN CRS:** EPSG:7794 (RDN2008/Italy zone E-N) → convertire in EPSG:4326 per overlay

## Fonti cartografiche gratuite usate

| Fonte | Contenuto | Uso nel progetto |
|-------|-----------|-----------------|
| University of Texas PCL (via Wayback Machine) | Fogli AMS 1:50,000 GSGS 4229 | Sfondo principale — viabilità storica 1895-1943 |
| IGM DBSN (Potenza + Matera) | Dati vettoriali moderni | Confini comunali, idrografia, viabilità moderna |
| David Rumsey Map Collection | Carta Richter Basilicata 1:250,000 ~1880 | Contesto regionale (analisi completata, non in mappa principale) |
