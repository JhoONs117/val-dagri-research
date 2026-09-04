"""
Analizza i fogli AMS scaricati:
- produce thumbnail 800px per ispezionare la copertura
- stima i bounds geografici da titolo e griglia visibile
- salva in output/ams_thumbnails/
"""
from PIL import Image
from pathlib import Path
import os

Image.MAX_IMAGE_PIXELS = None

DATA = Path("/home/miki/val-dagri-research/data")
OUT  = Path("/home/miki/val-dagri-research/output/ams_thumbnails")
OUT.mkdir(parents=True, exist_ok=True)

sheets = {
    "ams_montemurro_211iv.jpg": {
        "nome": "AMS 211-IV Montemurro",
        "comuni_attesi": ["Montemurro","Spinoso","Missanello","Gallicchio","S. Chirico Raparo"],
        "copertura_approx": "lat 40°10'–40°30'N  lon 15°55'–16°17'E",
    },
    "ams_stigliano_200ii.jpg": {
        "nome": "AMS 200-II Stigliano",
        "comuni_attesi": ["Stigliano","Cirigliano","Gorgoglione","Aliano","Craco"],
        "copertura_approx": "lat 40°20'–40°42'N  lon 16°05'–16°28'E  (stima)",
    },
}

for fname, info in sheets.items():
    p = DATA / fname
    if not p.exists():
        print(f"  MANCANTE: {p}")
        continue

    img = Image.open(p)
    W, H = img.size
    print(f"\n{'='*60}")
    print(f"  {info['nome']}")
    print(f"  File: {fname}  ({W}×{H} px, {p.stat().st_size//1024} KB)")
    print(f"  Copertura attesa: {info['copertura_approx']}")
    print(f"  Comuni attesi sul foglio: {', '.join(info['comuni_attesi'])}")

    # Thumbnail intera mappa
    scale = 800 / max(W, H)
    thumb = img.resize((int(W*scale), int(H*scale)), Image.LANCZOS)
    out_thumb = OUT / f"{p.stem}_thumb.jpg"
    thumb.save(out_thumb, "JPEG", quality=88)
    print(f"  Thumbnail → {out_thumb}  ({int(W*scale)}×{int(H*scale)} px)")

    # Crop angolo in alto a sinistra (titolo + bordo)
    crop_tl = img.crop((0, 0, min(1800, W), min(1200, H)))
    out_tl = OUT / f"{p.stem}_crop_titolo.jpg"
    crop_tl.save(out_tl, "JPEG", quality=88)
    print(f"  Crop titolo → {out_tl}")

    # Crop angolo in alto a destra (griglia metrica)
    crop_tr = img.crop((max(0, W-1800), 0, W, min(1200, H)))
    out_tr = OUT / f"{p.stem}_crop_griglia_dx.jpg"
    crop_tr.save(out_tr, "JPEG", quality=88)
    print(f"  Crop griglia dx → {out_tr}")

    # Crop centro (corpo principale della carta)
    cx, cy = W//2, H//2
    crop_c = img.crop((cx-1000, cy-800, cx+1000, cy+800))
    out_c = OUT / f"{p.stem}_crop_centro.jpg"
    crop_c.save(out_c, "JPEG", quality=88)
    print(f"  Crop centro → {out_c}")

print("\n\n=== RIEPILOGO COPERTURA ===")
print("""
FOGLIO 211-IV MONTEMURRO  (già verificato con screenshot precedente)
  Copre sicuramente: Montemurro, Spinoso, Gallicchio, Missanello, S. Chirico Raparo
  Target su questo foglio: Montemurro ✓  Missanello ✓  Spinoso ✓
  Target MANCANTI: Aliano, Cirigliano, Gorgoglione, Roccanova, S. Martino d'Agri,
                   Sant'Arcangelo, Stigliano

FOGLIO 200-II STIGLIANO  (da verificare oggi)
  Target probabili: Stigliano ✓ (nome del foglio)
                    Cirigliano (40°37'N 16°19'E) — probabile ✓
                    Gorgoglione (40°33'N 16°15'E) — possibile
                    Aliano (40°33'N 16°23'E) — possibile
  Target improbabili: Sant'Arcangelo (40°25'N, 16°31'E) — latitudine troppo bassa

ANCORA DA TROVARE (probabilmente foglio 212 area Sant'Arcangelo):
  Sant'Arcangelo (40°25'N, 16°31'E)
  Roccanova (40°22'N, 16°21'E)
  San Martino d'Agri (40°15'N, 16°04'E)

  → San Martino potrebbe essere su 211-IV (lat 40°15' è sul bordo inferiore del foglio)
  → Roccanova e Sant'Arcangelo → foglio Tursi (212-IV) o foglio Sant'Arcangelo

AZIONE NECESSARIA per Tursi/Sant'Arcangelo:
  URL (download manuale da browser):
  https://maps.lib.utexas.edu/maps/ams/italy_50k/txu-pclmaps-oclc-6540719-tursi-212-4.jpg
""")
