"""
Verifica che l'ambiente sia pronto per eseguire gli script di ricerca.
Controlla dipendenze Python, GDAL, e file di dati locali.

Esegui: python3 scripts/setup_ambiente.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "output"

print("=" * 60)
print("  VERIFICA AMBIENTE — Val d'Agri Research")
print("=" * 60)

# ── Dipendenze Python ─────────────────────────────────────────
print("\n[1/4] Librerie Python:")
libs = {
    "numpy":      "numpy",
    "cv2":        "opencv-python-headless",
    "PIL":        "pillow",
    "matplotlib": "matplotlib",
    "rasterio":   "rasterio",
    "geopandas":  "geopandas",
}
missing_pip = []
for mod, pkg in libs.items():
    try:
        __import__(mod)
        print(f"  ✓ {mod}")
    except ImportError:
        print(f"  ✗ {mod}  (installa: pip install {pkg} --break-system-packages)")
        missing_pip.append(pkg)

# ── GDAL ──────────────────────────────────────────────────────
print("\n[2/4] GDAL:")
try:
    r = subprocess.run(["gdal_translate", "--version"], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  ✓ {r.stdout.strip()}")
    else:
        print("  ✗ gdal_translate non trovato — installa: sudo apt install gdal-bin")
except FileNotFoundError:
    print("  ✗ gdal_translate non trovato — installa: sudo apt install gdal-bin")

# ── File AMS ──────────────────────────────────────────────────
print("\n[3/4] Fogli AMS 1:50,000 (JPEG):")
ams_files = {
    "ams_montemurro_211iv.jpg": "211-IV Montemurro (40°10'-20'N, 15°57'-16°12'E)",
    "ams_arcangelo_211i.jpg":   "211-I  S. Arcangelo (40°10'-20'N, 16°12'-16°27'E)",
    "ams_laurenzana_200iii.jpg":"200-III Laurenzana (40°20'-30'N, 15°57'-16°12'E)",
    "ams_stigliano_200ii.jpg":  "200-II  Stigliano (40°20'-30'N, 16°12'-16°27'E)",
    "ams_tursi_212iv.jpg":      "212-IV  Tursi (40°10'-20'N, 16°27'-16°42'E)",
}
missing_ams = []
for fname, desc in ams_files.items():
    p = DATA / fname
    if p.exists():
        mb = p.stat().st_size / 1048576
        print(f"  ✓ {fname}  ({mb:.1f} MB)")
    else:
        print(f"  ✗ {fname}  — {desc}")
        print(f"      → Scarica da Wayback Machine: cerca '{fname}' su web.archive.org")
        missing_ams.append(fname)

# ── DBSN ──────────────────────────────────────────────────────
print("\n[4/4] DBSN IGM (geodatabase vettoriali):")
dbsn = {
    "dbsn_potenza/Potenza_dbsn.gdb": "Potenza (PZ) — da IGM portale",
    "dbsn_matera/Matera_dbsn.gdb":   "Matera (MT) — da IGM portale",
}
missing_dbsn = []
for rel, desc in dbsn.items():
    p = DATA / rel
    if p.exists():
        print(f"  ✓ {rel}")
    else:
        print(f"  ✗ {rel}  — {desc}")
        print(f"      → Scarica *_dbsn_*.zip da igmi.esercito.difesa.it/porta-magna/data/dbsn/")
        missing_dbsn.append(rel)

# ── Output dirs ───────────────────────────────────────────────
for d in [OUT / "geotiff", OUT / "vettori", OUT / "ams_thumbnails"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Riepilogo ─────────────────────────────────────────────────
print("\n" + "=" * 60)
problems = len(missing_pip) + len(missing_ams) + len(missing_dbsn)
if problems == 0:
    print("  TUTTO OK — puoi eseguire gli script in questo ordine:")
    print("    1. python3 scripts/georeferenzia_fogli_ams.py")
    print("    2. python3 scripts/estrai_sentieri_grotte.py")
    print("    3. python3 scripts/mappa_overlay.py")
else:
    print(f"  {problems} PROBLEMI DA RISOLVERE prima di procedere.")
    if missing_pip:
        print(f"\n  Installa librerie mancanti:")
        print(f"  pip install {' '.join(missing_pip)} --break-system-packages")
    if missing_ams:
        print(f"\n  Scarica {len(missing_ams)} foglio/i AMS mancante/i (vedi README).")
    if missing_dbsn:
        print(f"\n  Scarica {len(missing_dbsn)} DBSN mancante/i (vedi README).")
print("=" * 60)
