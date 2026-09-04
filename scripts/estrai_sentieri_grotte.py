"""
Estrazione automatica da fogli AMS 1:50,000:
  1. Rete stradale rossa (categorie 1-5 nella legenda)
  2. Mule Tracks (linee nere tratteggiate)
  3. Ricerca testuale di grotte/caverne

Output:
  output/vettori/strade_ams_1895.geojson
  output/vettori/mule_tracks_ams.geojson
  output/vettori/grotte_ams.geojson
  output/mappa_estrazione.png   (verifica visiva)
"""
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

Image.MAX_IMAGE_PIXELS = None

DATA   = Path("/home/miki/val-dagri-research/data")
OUT    = Path("/home/miki/val-dagri-research/output")
VECDIR = OUT / "vettori"
VECDIR.mkdir(exist_ok=True)

# Proporzioni neatline calibrate (verificate su tutti i fogli)
TOP_FRAC    = 0.120
BOTTOM_FRAC = 0.845
LEFT_FRAC   = 0.089
RIGHT_FRAC  = 0.736

SHEETS = {
    "ams_montemurro_211iv.jpg": {
        "lon_W": 15+57/60, "lat_N": 40+20/60,
        "lon_E": 16+12/60, "lat_S": 40+10/60,
    },
    "ams_arcangelo_211i.jpg": {
        "lon_W": 16+12/60, "lat_N": 40+20/60,
        "lon_E": 16+27/60, "lat_S": 40+10/60,
    },
    "ams_laurenzana_200iii.jpg": {
        "lon_W": 15+57/60, "lat_N": 40+30/60,
        "lon_E": 16+12/60, "lat_S": 40+20/60,
    },
    "ams_stigliano_200ii.jpg": {
        "lon_W": 16+12/60, "lat_N": 40+30/60,
        "lon_E": 16+27/60, "lat_S": 40+20/60,
    },
}

def px_to_geo(px, py, w_map, h_map, lon_W, lat_N, lon_E, lat_S):
    lon = lon_W + (px / w_map) * (lon_E - lon_W)
    lat = lat_N - (py / h_map) * (lat_N - lat_S)
    return lon, lat

def get_neatline_crop(img_path):
    img = Image.open(img_path)
    W, H = img.size
    top    = int(H * TOP_FRAC)
    bottom = int(H * BOTTOM_FRAC)
    left   = int(W * LEFT_FRAC)
    right  = int(W * RIGHT_FRAC)
    crop = img.crop((left, top, right, bottom))
    return np.array(crop), left, top, right-left, bottom-top

def extract_red_roads(arr_bgr, min_area=200):
    """Pixel ROSSI → rete stradale principale (categorie 1-5 legenda AMS)."""
    hsv = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2HSV)
    # Rosso: due intervalli in HSV (avvolge intorno a 0/180)
    m1 = cv2.inRange(hsv, np.array([0,  90, 80]), np.array([10, 255, 220]))
    m2 = cv2.inRange(hsv, np.array([168, 90, 80]), np.array([180,255, 220]))
    mask = cv2.bitwise_or(m1, m2)
    # Pulizia morfologica: rimuovi puntini isolati, consolida linee
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask

def extract_mule_tracks(arr_bgr):
    """
    Mule Tracks: linee nere tratteggiate.
    Strategia:
      1. Isola i pixel molto scuri (nero)
      2. Rimuovi le linee di contorno brune con maschera colore
      3. Thinning → scheletro delle linee
      4. Cerca pattern tratteggiato: alternanza chiaro/scuro su segmento
    """
    hsv = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2HSV)

    # Maschera pixel neri/molto scuri (V < 80, S qualsiasi)
    dark = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))

    # Maschera pixel marroni/seppia (curve di livello): da escludere
    brown = cv2.inRange(hsv, np.array([8, 20, 90]), np.array([28, 160, 210]))

    # Maschera pixel rossi (strade): da escludere
    red1 = cv2.inRange(hsv, np.array([0,  90, 80]), np.array([10, 255, 220]))
    red2 = cv2.inRange(hsv, np.array([168, 90, 80]), np.array([180,255, 220]))
    red  = cv2.bitwise_or(red1, red2)

    # Pixel neri puri, senza il marrone delle curve e il rosso delle strade
    black_only = cv2.bitwise_and(dark, cv2.bitwise_not(cv2.bitwise_or(brown, red)))

    # Dilata leggermente per collegare i trattini
    k3 = np.ones((3,3), np.uint8)
    k_line_h = np.zeros((1, 25), np.uint8); k_line_h[0, :] = 1  # 25px orizzontale
    k_line_v = np.zeros((25, 1), np.uint8); k_line_v[:, 0] = 1  # 25px verticale
    k_line_d = np.eye(15, dtype=np.uint8)                        # diagonale

    # Connetti trattini con kernel lineare (cattura linee tratteggiate)
    connected  = cv2.dilate(black_only, k_line_h, iterations=1)
    connected  = cv2.bitwise_or(connected, cv2.dilate(black_only, k_line_v, iterations=1))
    connected  = cv2.bitwise_or(connected, cv2.dilate(black_only, k_line_d, iterations=1))

    # Apri con kernel piccolo per rimuovere testo/simboli (non lineari)
    opened = cv2.morphologyEx(connected, cv2.MORPH_OPEN, k3, iterations=1)

    # Maschera finale: solo zone connesse ≥ 400px (linee, non puntini)
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    result = np.zeros_like(opened)
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= 400:
            result[labels == i] = 255

    return result

def mask_to_geojson(mask, w_map, h_map, geo, label, min_area=100):
    """
    Converte una maschera binaria in GeoJSON FeatureCollection di linee.
    Usa le componenti connesse come proxy per i segmenti.
    """
    features = []
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < min_area:
            continue
        cx, cy = centroids[i]
        lon, lat = px_to_geo(cx, cy, w_map, h_map,
                             geo["lon_W"], geo["lat_N"],
                             geo["lon_E"], geo["lat_S"])
        # Bounding box in geo
        x0 = stats[i, cv2.CC_STAT_LEFT]
        y0 = stats[i, cv2.CC_STAT_TOP]
        x1 = x0 + stats[i, cv2.CC_STAT_WIDTH]
        y1 = y0 + stats[i, cv2.CC_STAT_HEIGHT]
        lo0, la0 = px_to_geo(x0, y0, w_map, h_map, geo["lon_W"], geo["lat_N"], geo["lon_E"], geo["lat_S"])
        lo1, la1 = px_to_geo(x1, y1, w_map, h_map, geo["lon_W"], geo["lat_N"], geo["lon_E"], geo["lat_S"])
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString",
                         "coordinates": [[lo0, la0], [lon, lat], [lo1, la1]]},
            "properties": {"tipo": label, "area_px": int(stats[i, cv2.CC_STAT_AREA]),
                           "lon_c": round(lon, 6), "lat_c": round(lat, 6)}
        })
    return features

def search_grotte_text(arr_bgr, w_map, h_map, geo):
    """
    Cerca pixel corrispondenti a testo scuro in zone non stradali.
    Identifica cluster che potrebbero essere etichette 'Grotta'.
    Ritorna punti candidati in aree isolate (lontano da strade rosse).
    """
    # Maschera testo nero in zone non stradali
    hsv = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2HSV)
    dark = cv2.inRange(hsv, np.array([0,0,0]), np.array([180,80,100]))

    # Escludi strade rosse
    red1 = cv2.inRange(hsv, np.array([0,  90, 80]), np.array([10, 255, 220]))
    red2 = cv2.inRange(hsv, np.array([168, 90, 80]), np.array([180,255, 220]))
    red  = cv2.bitwise_or(red1, red2)
    red_dilated = cv2.dilate(red, np.ones((15,15), np.uint8))

    text_mask = cv2.bitwise_and(dark, cv2.bitwise_not(red_dilated))

    # Componenti connesse di testo (dimensioni tipiche etichetta: 50-600px)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(text_mask, 8)
    candidates = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        w    = stats[i, cv2.CC_STAT_WIDTH]
        h_s  = stats[i, cv2.CC_STAT_HEIGHT]
        if 30 < area < 800 and w > h_s * 0.5:  # forma allungata = testo
            cx, cy = centroids[i]
            lon, lat = px_to_geo(cx, cy, w_map, h_map,
                                 geo["lon_W"], geo["lat_N"],
                                 geo["lon_E"], geo["lat_S"])
            # Solo zone lontane da strade principali (proxy per luoghi isolati)
            x0 = int(stats[i, cv2.CC_STAT_LEFT])
            y0 = int(stats[i, cv2.CC_STAT_TOP])
            if red_dilated[y0, x0] == 0:
                candidates.append((lon, lat, area))
    return candidates


# ── Elaborazione per foglio ───────────────────────────────────────────────────
all_roads  = []
all_mules  = []
all_grotte = []

for fname, geo in SHEETS.items():
    src = DATA / fname
    if not src.exists():
        print(f"  mancante: {fname}")
        continue
    print(f"\nElabora {fname}...")

    arr_rgb, left, top, w_map, h_map = get_neatline_crop(src)
    arr_bgr = cv2.cvtColor(arr_rgb, cv2.COLOR_RGB2BGR)

    # 1. Strade rosse
    mask_red = extract_red_roads(arr_bgr)
    feats_red = mask_to_geojson(mask_red, w_map, h_map, geo, "strada_ams", min_area=150)
    all_roads.extend(feats_red)
    print(f"  strade: {len(feats_red)} segmenti")

    # 2. Mule tracks
    mask_mule = extract_mule_tracks(arr_bgr)
    feats_mule = mask_to_geojson(mask_mule, w_map, h_map, geo, "mule_track", min_area=400)
    all_mules.extend(feats_mule)
    print(f"  mule tracks: {len(feats_mule)} segmenti")

    # 3. Candidati grotte (testo in zone isolate)
    candidates = search_grotte_text(arr_bgr, w_map, h_map, geo)
    for lon, lat, area in candidates[:50]:  # max 50 per foglio
        all_grotte.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon,6), round(lat,6)]},
            "properties": {"tipo": "etichetta_isolata", "area_px": area,
                           "nota": "testo in zona lontana da strade – verifica visiva"}
        })
    print(f"  etichette in zone isolate: {len(candidates)}")

    # ── Salva immagine di verifica per questo foglio ──────────────────────────
    vis = arr_bgr.copy()
    vis[mask_red  > 0] = [0, 0, 255]      # rosso → strade
    vis[mask_mule > 0] = [0, 200, 0]      # verde → mule tracks
    out_vis = OUT / "ams_thumbnails" / f"{src.stem}_estrazione.jpg"
    cv2.imwrite(str(out_vis),
                cv2.resize(vis, (vis.shape[1]//3, vis.shape[0]//3)))
    print(f"  → verifica: {out_vis.name}")

# ── Salva GeoJSON ─────────────────────────────────────────────────────────────
class _NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        return super().default(obj)

def save_geojson(features, path):
    gj = {"type": "FeatureCollection", "features": features}
    with open(path, "w") as f:
        json.dump(gj, f, indent=2, cls=_NpEncoder)
    print(f"Salvato: {path.name}  ({len(features)} feature)")

save_geojson(all_roads,  VECDIR / "strade_ams_1895.geojson")
save_geojson(all_mules,  VECDIR / "mule_tracks_ams.geojson")
save_geojson(all_grotte, VECDIR / "etichette_isolate_ams.geojson")

print(f"\nTotale strade AMS:    {len(all_roads)}")
print(f"Totale mule tracks:   {len(all_mules)}")
print(f"Totale zone isolate:  {len(all_grotte)}")
print(f"\nFile in: {VECDIR}/")
