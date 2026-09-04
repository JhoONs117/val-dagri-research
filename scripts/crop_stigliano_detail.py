"""
Crop mirate del foglio Stigliano 200-II per verificare:
- Bordo inferiore (latitudine sud)
- Area Sant'Arcangelo (stima: circa 16°31'E, 40°25'N)
- Area Roccanova (stima: circa 16°21'E, 40°22'N)
- Area Stigliano town (centroide)
"""
from PIL import Image
from pathlib import Path
Image.MAX_IMAGE_PIXELS = None

img = Image.open("/home/miki/val-dagri-research/data/ams_stigliano_200ii.jpg")
W, H = img.size
OUT = Path("/home/miki/val-dagri-research/output/ams_thumbnails")

print(f"Foglio Stigliano 200-II: {W}×{H} px")

# ── Bordo inferiore (latitudine sud) ────────────────────────────────────────
# L'angolo in basso a sinistra riporta la latitudine del bordo inferiore
crop_bl = img.crop((0, H-900, 1600, H))
crop_bl.save(OUT / "stigliano_bordo_inferiore.jpg", "JPEG", quality=90)
print("Salvato: stigliano_bordo_inferiore.jpg")

# ── Bordo inferiore destro ────────────────────────────────────────────────
crop_br = img.crop((W-1600, H-900, W, H))
crop_br.save(OUT / "stigliano_bordo_inf_dx.jpg", "JPEG", quality=90)
print("Salvato: stigliano_bordo_inf_dx.jpg")

# ── Area Sant'Arcangelo ──────────────────────────────────────────────────────
# Stima posizione sul foglio:
# Foglio: lat 40°10'–40°30'N, lon 16°12'–16°42'E  (20'×30' = 4010×5163 px)
LAT_TOP = 40.50   # 40°30'
LAT_BOT = 40.167  # 40°10' (stima)
LON_L   = 16.20   # 16°12' (stima)
LON_R   = 16.70   # 16°42' (stima)

def ll_to_px(lat, lon):
    # proporzione lineare (approssimativa)
    x = int((lon - LON_L) / (LON_R - LON_L) * W)
    y = int((LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * H)
    return max(0,x), max(0,y)

targets = {
    "sant_arcangelo": (40.252, 16.310),   # 40°15'N, 16°19'E (da Treccani)
    "roccanova":       (40.220, 16.207),  # 40°13'N, 16°12'E
    "stigliano_town":  (40.390, 16.230),  # 40°23'N - ma è NORD di 40°30' !
    "aliano":          (40.330, 16.228),  # 40°20'N, 16°14'E
}

# Coordinate più precise (WGS84):
# Sant'Arcangelo: 40°14'N 16°19'E  → 40.233, 16.317
# Roccanova:      40°21'N 16°21'E  → 40.349... no
# Usiamo coordinate più accurate

precise = {
    "sant_arcangelo": (40.233, 16.317),
    "roccanova":      (40.349, 16.207),  # potrebbe non essere sul foglio
    "stigliano_c":    (40.393, 16.225),  # SOPRA 40°30' → non su questo foglio!
}
# NOTE: Stigliano a 40°23'N → devo correggere

# Coordinate corrette da verifica geografica:
correct_coords = {
    "Sant Arcangelo 40.23N 16.32E": (40.233, 16.317),
    "Roccanova 40.22N 16.22E":      (40.220, 16.220),
    "Stigliano 40.39N 16.23E":      (40.393, 16.230),  # 40°23'N = 40.39? No!
}
# Stigliano = 40°23'N → in decimale = 40 + 23/60 = 40.383 N
# Ma il bordo sup è 40°30' = 40.50 N → Stigliano (40.383) è SUD di 40.50 → sul foglio ✓

# Coordinate corrette in decimale:
towns = {
    "Sant_Arcangelo": (40 + 15/60, 16 + 19/60),   # 40.250N, 16.317E — fonte: varie
    "Roccanova":      (40 + 21/60, 16 + 21/60),   # 40.350N, 16.350E — da verificare
    "Stigliano":      (40 + 23/60, 16 + 14/60),   # 40.383N, 16.233E
    "Aliano":         (40 + 20/60, 16 + 14/60),   # 40.333N, 16.233E
}

print("\nPosizioni stimate sul foglio:")
for nome, (lat, lon) in towns.items():
    x, y = ll_to_px(lat, lon)
    sul_foglio = (0 <= x < W) and (0 <= y < H)
    print(f"  {nome}: lat={lat:.3f}N lon={lon:.3f}E → px({x},{y}) {'✓ sul foglio' if sul_foglio else '✗ FUORI BORDO'}")
    if sul_foglio:
        c = img.crop((max(0,x-700), max(0,y-600), min(W,x+700), min(H,y+600)))
        fname = f"stigliano_{nome.lower().replace(' ','_')}.jpg"
        c.save(OUT / fname, "JPEG", quality=90)
        print(f"    → crop salvato: {fname}")
