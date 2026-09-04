"""
Download e assemblaggio della mappa David Rumsey via IIIF.
Mappa: da configurare con IIIF_ID sotto.
Uso: python3 scripts/download_rumsey_map.py [--half-res]
  --half-res  scarica a metà risoluzione (risparmia RAM: ~230 MB invece di ~900 MB)
"""
import urllib.request, math, sys, os, time
from PIL import Image

# ── Configurazione ──────────────────────────────────────────────────────────
IIIF_BASE = "https://www.davidrumsey.com/luna/servlet/iiif"
IIIF_ID   = "RUMSEY~8~1~377330~90143441"   # Carta topografica Basilicata 1:250.000
IMG_W, IMG_H = 15208, 20224                 # da info.json
TILE_SRC  = 1536                            # dimensione tile sorgente (px)
HEADERS   = {"User-Agent": "Mozilla/5.0 (research/historical-cartography)"}
OUT_DIR   = os.path.join(os.path.dirname(__file__), "../data/rumsey_tiles")
OUT_FILE  = os.path.join(os.path.dirname(__file__), "../data/rumsey_basilicata_1250000.jpg")
# ────────────────────────────────────────────────────────────────────────────

half_res = "--half-res" in sys.argv
scale    = 2 if half_res else 1
tile_out = TILE_SRC // scale   # dimensione output di ogni tile

cols = math.ceil(IMG_W / TILE_SRC)
rows = math.ceil(IMG_H / TILE_SRC)
total = cols * rows
final_w = math.ceil(IMG_W / scale)
final_h = math.ceil(IMG_H / scale)

print(f"Risoluzione: {'METÀ' if half_res else 'PIENA'}")
print(f"Immagine finale: {final_w} × {final_h} px")
print(f"Tile da scaricare: {cols} × {rows} = {total}")
print(f"RAM stimata per assemblaggio: ~{final_w*final_h*3//1e6:.0f} MB")
print()

os.makedirs(OUT_DIR, exist_ok=True)

# Crea canvas vuoto
canvas = Image.new("RGB", (final_w, final_h))

for row in range(rows):
    for col in range(cols):
        x = col * TILE_SRC
        y = row * TILE_SRC
        w = min(TILE_SRC, IMG_W - x)
        h = min(TILE_SRC, IMG_H - y)

        # Dimensione output del tile (ridotta di scale)
        out_w = math.ceil(w / scale)
        out_h = math.ceil(h / scale)

        tile_path = os.path.join(OUT_DIR, f"tile_{col:02d}_{row:02d}.jpg")
        n = row * cols + col + 1

        if os.path.exists(tile_path):
            print(f"[{n:3d}/{total}] tile {col},{row} — già scaricato, salto")
        else:
            url = f"{IIIF_BASE}/{IIIF_ID}/{x},{y},{w},{h}/{out_w},{out_h}/0/default.jpg"
            print(f"[{n:3d}/{total}] tile {col},{row} — scarico...", end=" ", flush=True)
            req = urllib.request.Request(url, headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                with open(tile_path, "wb") as f:
                    f.write(data)
                print(f"OK ({len(data)//1024} KB)")
            except Exception as e:
                print(f"ERRORE: {e}")
                continue
            time.sleep(0.3)   # pausa cortesia verso il server

        # Incolla tile nel canvas
        try:
            tile_img = Image.open(tile_path)
            canvas.paste(tile_img, (col * tile_out, row * tile_out))
        except Exception as e:
            print(f"  ATTENZIONE: impossibile aprire {tile_path}: {e}")

print()
print(f"Assemblaggio completato. Salvataggio in: {OUT_FILE}")
canvas.save(OUT_FILE, "JPEG", quality=92, optimize=True)
print(f"File salvato: {os.path.getsize(OUT_FILE)//1024//1024} MB")
print("Fatto.")
