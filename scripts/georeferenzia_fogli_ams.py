"""
Georeferenziamento automatico dei 4 fogli AMS 1:50,000 — area Val d'Agri.

Come funziona:
  1. Ogni foglio ha un codice che dice esattamente dove si trova (es. N4010-E1557/10x15)
  2. Lo script trova i bordi del contenuto cartografico nell'immagine (la "neatline")
  3. Associa i 4 angoli in pixel alle loro coordinate geografiche reali (WGS84)
  4. Usa GDAL per produrre un GeoTIFF — la mappa con coordinate cucite dentro

Output: output/geotiff/{nome}_geo.tif  (un file per ogni foglio)
"""
import subprocess, sys, os
import numpy as np
from PIL import Image
from pathlib import Path

Image.MAX_IMAGE_PIXELS = None

DATA   = Path("/home/miki/val-dagri-research/data")
OUTPUT = Path("/home/miki/val-dagri-research/output/geotiff")
OUTPUT.mkdir(parents=True, exist_ok=True)

# ── Definizione dei 4 fogli: angoli SW e NE in gradi decimali WGS84 ──────────
# lon_W = longitudine bordo Ovest, lat_S = latitudine bordo Sud, ecc.
SHEETS = {
    "ams_montemurro_211iv.jpg": {
        "name":  "Montemurro 211-IV",
        "lon_W": 15 + 57/60,   # N4010-E1557/10x15
        "lat_S": 40 + 10/60,
        "lon_E": 16 + 12/60,
        "lat_N": 40 + 20/60,
        "igm":   "1896",
    },
    "ams_arcangelo_211i.jpg": {
        "name":  "S. Arcangelo 211-I",
        "lon_W": 16 + 12/60,   # N4010-E1612/10x15
        "lat_S": 40 + 10/60,
        "lon_E": 16 + 27/60,
        "lat_N": 40 + 20/60,
        "igm":   "1896",
    },
    "ams_laurenzana_200iii.jpg": {
        "name":  "Laurenzana 200-III",
        "lon_W": 15 + 57/60,   # N4020-E1557/10x15
        "lat_S": 40 + 20/60,
        "lon_E": 16 + 12/60,
        "lat_N": 40 + 30/60,
        "igm":   "1895",
    },
    "ams_stigliano_200ii.jpg": {
        "name":  "Stigliano 200-II",
        "lon_W": 16 + 12/60,   # N4020-E1612/10x15
        "lat_S": 40 + 20/60,
        "lon_E": 16 + 27/60,
        "lat_N": 40 + 30/60,
        "igm":   "1902",
    },
    "ams_tursi_212iv.jpg": {
        "name":  "Tursi 212-IV",
        "lon_W": 16 + 27/60,   # N4010-E1627/10x15
        "lat_S": 40 + 10/60,
        "lon_E": 16 + 42/60,
        "lat_N": 40 + 20/60,
        "igm":   "1943",
    },
}


def find_neatline(img_path):
    """
    Trova i pixel (top, left, bottom, right) della neatline geografica.

    Proporzioni calibrate analizzando visivamente i fogli AMS:
    - La legenda occupa il ~26% destro del foglio stampato
    - I margini testo sono circa il 12% in alto, 15% in basso, 9% a sinistra
    - Verificato su Stigliano: scala risultante ~1:50,000 a ~200 dpi

    Struttura foglio AMS Italy 1:50,000:
      [margine sx] [CONTENUTO GEOGRAFICO ~63%] [legenda ~26%] [margine dx]
      [margine sup ~12%]
      [CONTENUTO GEOGRAFICO ~72%]
      [margine testo/scala ~15%]
    """
    img = Image.open(img_path).convert('L')
    arr = np.array(img, dtype=np.float32)
    H, W = arr.shape

    # Proporzioni calibrate (verificate su foglio Stigliano e Montemurro)
    TOP_FRAC    = 0.120   # margine superiore
    BOTTOM_FRAC = 0.845   # fine contenuto geografico (dalla cima)
    LEFT_FRAC   = 0.089   # margine sinistro
    RIGHT_FRAC  = 0.736   # bordo destro geografico (prima della legenda)

    # Affiniamo con rilevamento della linea nera del bordo (neatline)
    # cercando una riga/colonna dove >75% dei pixel sono molto scuri (<60)
    # nell'intervallo atteso ± 5% di tolleranza

    def find_dark_line_row(arr, start_frac, direction=1, band_x=(0.15, 0.65)):
        x0 = int(W * band_x[0])
        x1 = int(W * band_x[1])
        start = int(H * start_frac)
        search_range = int(H * 0.07)  # ±7% di tolleranza
        step = direction
        for i in range(start, start + step * search_range, step):
            if 0 <= i < H:
                row = arr[i, x0:x1]
                if (row < 60).mean() > 0.70:
                    # Trovata la linea del bordo, prendi il bordo INTERNO
                    for i2 in range(i, i + step * 10, step):
                        if 0 <= i2 < H:
                            if (arr[i2, x0:x1] < 60).mean() < 0.25:
                                return i2
                    return i + step * 3
        return int(H * start_frac)

    def find_dark_line_col(arr, start_frac, direction=1, band_y=(0.20, 0.75)):
        y0 = int(H * band_y[0])
        y1 = int(H * band_y[1])
        start = int(W * start_frac)
        search_range = int(W * 0.06)
        step = direction
        for j in range(start, start + step * search_range, step):
            if 0 <= j < W:
                col = arr[y0:y1, j]
                if (col < 60).mean() > 0.70:
                    for j2 in range(j, j + step * 10, step):
                        if 0 <= j2 < W:
                            if (arr[y0:y1, j2] < 60).mean() < 0.25:
                                return j2
                    return j + step * 3
        return int(W * start_frac)

    top    = find_dark_line_row(arr, TOP_FRAC,     direction=+1)
    bottom = find_dark_line_row(arr, BOTTOM_FRAC,  direction=-1)
    left   = find_dark_line_col(arr, LEFT_FRAC,    direction=+1)
    right  = find_dark_line_col(arr, RIGHT_FRAC,   direction=-1)

    return top, left, bottom, right


def georeference(src_jpg, info):
    name  = info["name"]
    lon_W = info["lon_W"]
    lat_S = info["lat_S"]
    lon_E = info["lon_E"]
    lat_N = info["lat_N"]

    print(f"\n{'='*62}")
    print(f"  {name}  (IGM {info['igm']})")
    print(f"  Copertura: {lat_S:.4f}°N–{lat_N:.4f}°N,  {lon_W:.4f}°E–{lon_E:.4f}°E")

    # Trova bordi della mappa nell'immagine
    print("  Cerco bordi neatline nell'immagine...", end=" ", flush=True)
    top, left, bottom, right = find_neatline(src_jpg)
    h_map = bottom - top
    w_map = right - left
    print("trovati")
    print(f"  Neatline: top={top}px left={left}px bottom={bottom}px right={right}px")
    print(f"  Area mappa: {w_map}×{h_map} px")

    stem    = Path(src_jpg).stem
    tmp_crop = OUTPUT / f"{stem}_crop.jpg"
    tmp_tif  = OUTPUT / f"{stem}_gcps.tif"
    out_tif  = OUTPUT / f"{stem}_geo.tif"

    # ── Passo 0: ritaglia il JPEG alla sola area geografica ────────────────
    # Questo evita che gdalwarp estrapoli le coordinate nella legenda/margini
    print("  Passo 1/3: ritaglia alla neatline...", end=" ", flush=True)
    img = Image.open(src_jpg)
    crop = img.crop((left, top, right, bottom))
    crop.save(tmp_crop, "JPEG", quality=95)
    img.close()
    print(f"OK ({w_map}×{h_map} px)")

    # ── Passo 1: gdal_translate — GCP agli angoli dell'immagine ritagliata ──
    # Il crop va da (0,0) in alto-sinistra a (w_map, h_map) in basso-destra
    gcps = [
        (0,     0,     lon_W, lat_N),  # angolo NW
        (w_map, 0,     lon_E, lat_N),  # angolo NE
        (0,     h_map, lon_W, lat_S),  # angolo SW
        (w_map, h_map, lon_E, lat_S),  # angolo SE
    ]
    gcp_args = []
    for px, py, lon, lat in gcps:
        gcp_args += ["-gcp", str(px), str(py), f"{lon:.6f}", f"{lat:.6f}"]

    cmd1 = ["gdal_translate"] + gcp_args + [
        "-a_srs", "EPSG:4326",
        "-of", "GTiff",
        str(tmp_crop), str(tmp_tif)
    ]
    print("  Passo 2/3: assegno GCP...", end=" ", flush=True)
    r1 = subprocess.run(cmd1, capture_output=True, text=True)
    if r1.returncode != 0:
        print(f"ERRORE\n{r1.stderr[:400]}")
        tmp_crop.unlink(missing_ok=True)
        return None
    print("OK")

    # ── Passo 2: gdalwarp — riproietta in GeoTIFF WGS84 ────────────────────
    cmd2 = [
        "gdalwarp",
        "-r", "bilinear",
        "-t_srs", "EPSG:4326",
        "-order", "1",
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        "-dstalpha",
        "-overwrite",
        str(tmp_tif), str(out_tif)
    ]
    print("  Passo 3/3: riproietto in WGS84...", end=" ", flush=True)
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"ERRORE\n{r2.stderr[:400]}")
        tmp_crop.unlink(missing_ok=True)
        tmp_tif.unlink(missing_ok=True)
        return None
    print("OK")

    tmp_crop.unlink(missing_ok=True)
    tmp_tif.unlink(missing_ok=True)

    sz_mb = out_tif.stat().st_size / 1048576
    print(f"  → {out_tif.name}  ({sz_mb:.1f} MB)")
    return out_tif


# ── Esecuzione ────────────────────────────────────────────────────────────────
print("=== GEOREFERENZIAMENTO FOGLI AMS 1:50,000 — Val d'Agri ===\n")
print("Questo crea file GeoTIFF nella cartella output/geotiff/")
print("Non modifica i JPEG originali.\n")

results = []
for fname, info in SHEETS.items():
    src = DATA / fname
    if not src.exists():
        print(f"\nMancante: {src.name} — salto")
        results.append((fname, "MANCANTE", None))
        continue
    out = georeference(src, info)
    results.append((fname, "OK" if out else "ERRORE", out))

print("\n\n=== RIEPILOGO FINALE ===")
print(f"{'Foglio':<40} {'Stato':<10} {'Output'}")
print("-" * 90)
for fname, stato, out in results:
    out_name = out.name if out else "—"
    print(f"{fname:<40} {stato:<10} {out_name}")

print(f"\nCartella output: {OUTPUT}/")
