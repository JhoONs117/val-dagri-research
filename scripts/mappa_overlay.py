"""
Mappa overlay Val d'Agri — brigantaggio post-unitario 1860-1870.  v2.0

Sfondo: 5 fogli AMS 1:50,000 (IGM 1895-1943) georeferenziati.
Overlay vettoriale: confini comunali + idrografia + viabilità (DBSN PZ+MT 2025).
Nuovi layer v2.0: sentieri storici (mulattiere AMS, verde), target drone/LiDAR.

Output: output/mappa_valdagri_overlay.png  (300 dpi, stampa A3)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import rasterio
from rasterio.enums import Resampling
from rasterio.plot import reshape_as_image
import geopandas as gpd
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA   = Path("/home/miki/val-dagri-research/data")
GEODIR = Path("/home/miki/val-dagri-research/output/geotiff")
OUTDIR = Path("/home/miki/val-dagri-research/output")
VECDIR = Path("/home/miki/val-dagri-research/output/vettori")

DBSN_PZ = str(DATA / "dbsn_potenza/Potenza_dbsn.gdb")
DBSN_MT = str(DATA / "dbsn_matera/Matera_dbsn.gdb")

# ── Bounding box: 5 fogli AMS ────────────────────────────────────────────────
LON_W = 15 + 57/60   # 15.950°E  (Laurenzana/Montemurro ovest)
LON_E = 16 + 42/60   # 16.700°E  (Tursi est)
LAT_S = 40 + 10/60   # 40.167°N
LAT_N = 40 + 30/60   # 40.500°N

# ── 10 comuni target ─────────────────────────────────────────────────────────
COMUNI_TARGET = {
    "Montemurro":         (40 + 16/60, 15 + 59/60, "PZ"),
    "Spinoso":            (40 + 15/60, 16 +  6/60, "PZ"),
    "Missanello":         (40 + 13/60, 16 +  4/60, "PZ"),
    "San Martino d'Agri": (40 + 13/60, 16 +  3/60, "PZ"),
    "Sant'Arcangelo":     (40 + 14/60, 16 + 19/60, "PZ"),
    "Roccanova":          (40 + 21/60, 16 + 22/60, "PZ"),
    "Stigliano":          (40 + 23/60, 16 + 14/60, "MT"),
    "Aliano":             (40 + 20/60, 16 + 14/60, "MT"),
    "Cirigliano":         (40 + 23/60, 16 +  6/60, "MT"),
    "Gorgoglione":        (40 + 24/60, 16 +  8/60, "MT"),
}
COLORI = {"PZ": "#c0392b", "MT": "#1565C0"}

# ── 5 fogli AMS ───────────────────────────────────────────────────────────────
GEOTIFFS = [
    GEODIR / "ams_montemurro_211iv_geo.tif",
    GEODIR / "ams_arcangelo_211i_geo.tif",
    GEODIR / "ams_laurenzana_200iii_geo.tif",
    GEODIR / "ams_stigliano_200ii_geo.tif",
    GEODIR / "ams_tursi_212iv_geo.tif",
]

# ── Figura ────────────────────────────────────────────────────────────────────
lon_span = LON_E - LON_W   # 0.75°
lat_span = LAT_N - LAT_S   # 0.333°
# A 40°N: 1° lon ≈ 0.766 × 1° lat → rapporto km ~0.75×0.766/0.333 = 1.72:1
km_ratio = lon_span * 0.766 / lat_span
fig_w = 22
fig_h = fig_w / km_ratio
fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
ax.set_xlim(LON_W, LON_E)
ax.set_ylim(LAT_S, LAT_N)
ax.set_aspect('equal')

# ── 1. Sfondo raster AMS ──────────────────────────────────────────────────────
print("Carico fogli AMS...")
DOWNSAMPLE = 4
for gtf_path in GEOTIFFS:
    if not gtf_path.exists():
        print(f"  mancante: {gtf_path.name}")
        continue
    with rasterio.open(gtf_path) as ds:
        h = ds.height // DOWNSAMPLE
        w = ds.width  // DOWNSAMPLE
        bands = min(ds.count, 3)
        data = ds.read(list(range(1, bands+1)),
                       out_shape=(bands, h, w),
                       resampling=Resampling.average)
        b = ds.bounds
    if bands == 1:
        data = np.repeat(data, 3, axis=0)
    img = np.clip(reshape_as_image(data[:3]) / 255.0, 0, 1)
    ax.imshow(img, extent=[b.left, b.right, b.bottom, b.top],
              origin='upper', interpolation='bilinear', zorder=1, aspect='auto')
    print(f"  ✓ {gtf_path.name}")

# ── 2. Confini comunali PZ + MT ───────────────────────────────────────────────
print("Carico confini comunali...")
PZ_TARGET = {n for n,(la,lo,p) in COMUNI_TARGET.items() if p=="PZ"}
MT_TARGET = {n for n,(la,lo,p) in COMUNI_TARGET.items() if p=="MT"}

for dbsn_path, prov_label, target_set, fill_color, edge_color in [
    (DBSN_PZ, "PZ", PZ_TARGET, "#e74c3c", "#922b21"),
    (DBSN_MT, "MT", MT_TARGET, "#2196F3", "#0d47a1"),
]:
    try:
        gdf = gpd.read_file(dbsn_path, layer="comune").to_crs("EPSG:4326")
        gdf_area = gdf.cx[LON_W:LON_E, LAT_S:LAT_N]
        # tutti i comuni dell'area: bordo sottile grigio
        gdf_area.plot(ax=ax, facecolor='none', edgecolor='#555555',
                      linewidth=0.5, zorder=3)
        # comuni target: riempiti con colore provincia
        gdf_tgt = gdf_area[gdf_area['comune_nom'].isin(target_set)]
        gdf_tgt.plot(ax=ax, facecolor=fill_color, edgecolor=edge_color,
                     linewidth=1.0, alpha=0.30, zorder=4)
        print(f"  ✓ {prov_label}: {len(gdf_area)} comuni area, "
              f"{len(gdf_tgt)} target evidenziati")
    except Exception as e:
        print(f"  ERRORE {prov_label}: {e}")

# ── 3. Idrografia DBSN (PZ + MT) ─────────────────────────────────────────────
print("Carico idrografia...")
for dbsn_path, label in [(DBSN_PZ,"PZ"),(DBSN_MT,"MT")]:
    try:
        gdf = gpd.read_file(dbsn_path, layer="el_idr").to_crs("EPSG:4326")
        clip = gdf.cx[LON_W:LON_E, LAT_S:LAT_N]
        clip.plot(ax=ax, color='#1565C0', linewidth=0.6, alpha=0.80, zorder=5)
        print(f"  ✓ idr {label}: {len(clip)} tratti")
    except Exception as e:
        print(f"  ERRORE idr {label}: {e}")

# ── 4. Rete stradale moderna DBSN ─────────────────────────────────────────────
print("Carico viabilità moderna...")
for dbsn_path, label in [(DBSN_PZ,"PZ"),(DBSN_MT,"MT")]:
    try:
        gdf = gpd.read_file(dbsn_path, layer="tr_str").to_crs("EPSG:4326")
        clip = gdf.cx[LON_W:LON_E, LAT_S:LAT_N]
        # Strade principali (sed=01): linea scura più spessa
        pri = clip[clip['tr_str_sed'].astype(str) == '01']
        pri.plot(ax=ax, color='#FF6F00', linewidth=0.9, alpha=0.75, zorder=6)
        # Strade secondarie (sed=02): linea più sottile
        sec = clip[clip['tr_str_sed'].astype(str) == '02']
        sec.plot(ax=ax, color='#FF8F00', linewidth=0.5, alpha=0.60, zorder=6)
        print(f"  ✓ strade {label}: {len(pri)} principali, {len(sec)} secondarie")
    except Exception as e:
        print(f"  ERRORE strade {label}: {e}")

# ── 5a. Sentieri storici (mulattiere AMS 1895-1902) ──────────────────────────
print("Carico sentieri storici AMS...")
mule_path = VECDIR / "mule_tracks_ams.geojson"
if mule_path.exists():
    with open(mule_path) as f:
        mule_gj = json.load(f)
    n_drawn = 0
    for feat in mule_gj["features"]:
        coords = feat["geometry"]["coordinates"]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        if LON_W <= lons[1] <= LON_E and LAT_S <= lats[1] <= LAT_N:
            ax.plot(lons, lats, color='#1B8000', linewidth=0.55, alpha=0.70,
                    linestyle='--', zorder=7, solid_capstyle='round')
            n_drawn += 1
    print(f"  ✓ sentieri AMS: {n_drawn} segmenti tracciati")

# ── 5b. Target drone/LiDAR ───────────────────────────────────────────────────
print("Carico target drone/LiDAR...")
tgt_path = VECDIR / "target_drone_lidar.geojson"
if tgt_path.exists():
    with open(tgt_path) as f:
        tgt_gj = json.load(f)
    COLORI_TARGET = {
        "dolina_carsica":      ("#9C27B0", "*", 9),   # viola, stella
        "parete_rocciosa":     ("#FF5722", "^", 7),   # arancio scuro, triangolo
        "struttura_abbandonata": ("#795548", "s", 6), # marrone, quadrato
        "depressioni_multiple": ("#9C27B0", "D", 6),  # viola, rombo
        "bosco_rifugio":       ("#2E7D32", "P", 7),   # verde scuro, croce+
        "gola_fluviale":       ("#0288D1", "v", 7),   # azzurro, triangolo inv.
    }
    for feat in tgt_gj["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        p = feat["properties"]
        tipo = p.get("tipo", "")
        nome = p.get("nome", "")
        prio = p.get("priorita", "MEDIA")
        col, marker, ms = COLORI_TARGET.get(tipo, ("#FF0000", "o", 6))
        edge_w = 1.5 if prio == "ALTA" else 0.8
        ax.plot(lon, lat, marker=marker, color=col, markersize=ms,
                markeredgecolor='white', markeredgewidth=edge_w,
                zorder=12, clip_on=True)
        ax.annotate(nome, xy=(lon, lat), xytext=(5, 5),
                    textcoords='offset points', fontsize=4.5,
                    color=col, fontweight='bold',
                    path_effects=[pe.withStroke(linewidth=2, foreground='white')],
                    zorder=13)
    print(f"  ✓ {len(tgt_gj['features'])} target drone/LiDAR")

# ── 6. Etichette comuni target ────────────────────────────────────────────────
shadow = [pe.withStroke(linewidth=2.8, foreground='white')]
for nome, (lat, lon, prov) in COMUNI_TARGET.items():
    c = COLORI[prov]
    ax.plot(lon, lat, 'o', color=c, markersize=4.5,
            markeredgecolor='white', markeredgewidth=0.8, zorder=9)
    ax.annotate(nome, xy=(lon, lat), xytext=(4, 4),
                textcoords='offset points', fontsize=5.5,
                fontweight='bold', color=c,
                path_effects=shadow, zorder=10)

# ── 6. Griglia geografica ─────────────────────────────────────────────────────
import matplotlib.ticker as ticker
ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
ax.grid(True, linestyle='--', linewidth=0.25, alpha=0.4, color='gray', zorder=7)

def fmt_lon(x, pos):
    d = int(x); m = int(round((x-d)*60))
    return f"{d}°{m:02d}'E"
def fmt_lat(x, pos):
    d = int(x); m = int(round((x-d)*60))
    return f"{d}°{m:02d}'N"
ax.xaxis.set_major_formatter(ticker.FuncFormatter(fmt_lon))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_lat))
ax.tick_params(labelsize=7)

# ── 7. Titolo ─────────────────────────────────────────────────────────────────
ax.set_title(
    "Val d'Agri — Sentieri storici, viabilità e target per survey  |  Brigantaggio 1860–1870  [v2.0]\n"
    "Sfondo AMS 1:50,000 (IGM 1895–1943) · DBSN PZ+MT 2025 · Sentieri estratti AMS · Target drone/LiDAR",
    fontsize=10, fontweight='bold', pad=9
)

# ── 9. Legenda ────────────────────────────────────────────────────────────────
legend_elements = [
    mpatches.Patch(facecolor='#e74c3c', alpha=0.45,
                   edgecolor='#922b21', label='Comuni target – Potenza (6)'),
    mpatches.Patch(facecolor='#2196F3', alpha=0.45,
                   edgecolor='#0d47a1', label='Comuni target – Matera (4)'),
    Line2D([0],[0], color='#1565C0', linewidth=1.0, label='Idrografia (DBSN PZ+MT)'),
    Line2D([0],[0], color='#FF6F00', linewidth=1.2, label='Viabilità moderna principale (DBSN)'),
    Line2D([0],[0], color='#FF8F00', linewidth=0.7, linestyle='--',
           label='Viabilità secondaria (DBSN)'),
    Line2D([0],[0], color='#1B8000', linewidth=0.8, linestyle='--',
           label='Sentieri storici / mulattiere (estratti AMS 1895-1902)'),
    Line2D([0],[0], color='#555555', linewidth=0.6, label='Confini comunali'),
    mpatches.Patch(facecolor='#f5f0e8', edgecolor='#aaaaaa',
                   label='AMS 1:50,000 IGM 1895–1943'),
    Line2D([0],[0], marker='*', color='#9C27B0', linewidth=0,
           markersize=8, label='Target LiDAR – dolina carsica'),
    Line2D([0],[0], marker='^', color='#FF5722', linewidth=0,
           markersize=7, label='Target LiDAR – parete rocciosa (timpa)'),
    Line2D([0],[0], marker='P', color='#2E7D32', linewidth=0,
           markersize=7, label='Target LiDAR – bosco rifugio'),
    Line2D([0],[0], marker='v', color='#0288D1', linewidth=0,
           markersize=7, label='Target LiDAR – gola fluviale'),
    Line2D([0],[0], marker='s', color='#795548', linewidth=0,
           markersize=6, label='Target LiDAR – struttura abbandonata'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=5.8,
          framealpha=0.93, edgecolor='#888888', fancybox=True)

# ── 10. Nota metodologica ─────────────────────────────────────────────────────
note = (
    "Fogli AMS: Montemurro 211-IV (1896), S. Arcangelo 211-I (1896), "
    "Laurenzana 200-III (1895),\nStigliano 200-II (1902), Tursi 212-IV (1943). "
    "Georef. 4-GCP corner, EPSG:4326, errore <3 m.\n"
    "DBSN PZ+MT: dati vettoriali IGM 2025 (EPSG:7794→4326). "
    "Sentieri storici estratti automaticamente da AMS (HSV + morfologia). "
    "v2.0 — target drone/LiDAR identificati da analisi visiva."
)
ax.text(0.01, 0.01, note, transform=ax.transAxes, fontsize=5.3,
        verticalalignment='bottom', style='italic', color='#333333',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  alpha=0.85, edgecolor='#aaaaaa'))

plt.tight_layout(pad=0.5)

out_path = OUTDIR / "mappa_valdagri_overlay.png"
print(f"\nSalvo {out_path} ...")
fig.savefig(out_path, dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close(fig)

sz = out_path.stat().st_size / 1048576
print(f"✓ Salvato: {out_path.name}  ({sz:.1f} MB)")
