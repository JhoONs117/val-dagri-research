"""
Crop con bound VERIFICATI dal codice AMS:
  Foglio 200-II Stigliano: N4020-E1612/10x15
  → copre esattamente 40°20'–40°30'N, 16°12'–16°27'E
"""
from PIL import Image
from pathlib import Path
Image.MAX_IMAGE_PIXELS = None

img = Image.open("/home/miki/val-dagri-research/data/ams_stigliano_200ii.jpg")
W, H = img.size
OUT = Path("/home/miki/val-dagri-research/output/ams_thumbnails")

# Bound VERIFICATI
LAT_TOP = 40 + 30/60   # 40°30'N = 40.5000
LAT_BOT = 40 + 20/60   # 40°20'N = 40.3333
LON_L   = 16 + 12/60   # 16°12'E = 16.2000
LON_R   = 16 + 27/60   # 16°27'E = 16.4500

def ll_px(lat, lon):
    x = int((lon - LON_L) / (LON_R - LON_L) * W)
    y = int((LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * H)
    return max(0, min(W, x)), max(0, min(H, y))

# Coordinate DMS→decimale dei comuni target
# (fonte: coordinate ufficiali centroidi comunali ISTAT)
comuni = {
    "Stigliano":     (40+23/60, 16+13/60),   # 40°23'N 16°13'E
    "Cirigliano":    (40+23/60, 16+ 6/60),   # 40°23'N 16°06'E — OVEST del foglio!
    "Gorgoglione":   (40+24/60, 16+ 8/60),   # 40°24'N 16°08'E — OVEST del foglio!
    "Aliano":        (40+20/60, 16+14/60),   # 40°20'N 16°14'E — bordo SUD
    "SantArcangelo": (40+14/60, 16+19/60),   # 40°14'N 16°19'E — SUD del foglio!
    "Roccanova":     (40+21/60, 16+22/60),   # 40°21'N 16°22'E
}

print(f"Foglio Stigliano: {W}×{H} px")
print(f"Bounds: {LAT_BOT:.4f}°N–{LAT_TOP:.4f}°N, {LON_L:.4f}°E–{LON_R:.4f}°E")
print()

for nome, (lat, lon) in comuni.items():
    x, y = ll_px(lat, lon)
    sul = (LON_L <= lon <= LON_R) and (LAT_BOT <= lat <= LAT_TOP)
    stato = "✓ SUL FOGLIO" if sul else "✗ FUORI"
    print(f"{nome}: {lat:.4f}°N {lon:.4f}°E  → px({x},{y})  {stato}")

    if sul and 0 < x < W and 0 < y < H:
        # Crop 1200×900 px centrato sul comune
        x0 = max(0, x - 600)
        y0 = max(0, y - 450)
        x1 = min(W, x + 600)
        y1 = min(H, y + 450)
        crop = img.crop((x0, y0, x1, y1))
        fname = f"s200ii_{nome.lower()}.jpg"
        crop.save(OUT / fname, "JPEG", quality=92)
        print(f"  → {fname} ({x1-x0}×{y1-y0} px)")
