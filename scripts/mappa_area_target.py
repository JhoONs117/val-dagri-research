"""
Produce due mappe dell'area Val d'Agri:
1. mappa_moderna.png  — DBSN moderno: comuni, idrografia, viabilità minore
2. mappa_overlay.png  — storica 1:250.000 sovrapposta ai confini moderni
"""
import warnings; warnings.filterwarnings('ignore')
import geopandas as gpd, matplotlib.pyplot as plt, matplotlib.patches as mpatches
import numpy as np
from PIL import Image
from pathlib import Path
import os

Image.MAX_IMAGE_PIXELS = None

GDB     = '/home/miki/val-dagri-research/data/dbsn_potenza/Potenza_dbsn.gdb'
STORICA = '/home/miki/val-dagri-research/data/rumsey_basilicata_1250000.jpg'
OUT     = '/home/miki/val-dagri-research/output'
os.makedirs(OUT, exist_ok=True)

TARGET = ['Missanello','Montemurro','Roccanova',
          "San Martino d'Agri","Sant'Arcangelo",'Spinoso']
# Area di interesse (con margine intorno ai 6 comuni)
LON_MIN, LON_MAX = 15.80, 16.45
LAT_MIN, LAT_MAX = 40.10, 40.50

print('Carico layer DBSN...')
CRS = 'EPSG:4326'

comuni   = gpd.read_file(GDB, layer='comune').to_crs(CRS)
el_idr   = gpd.read_file(GDB, layer='el_idr').to_crs(CRS)
el_vms   = gpd.read_file(GDB, layer='el_vms').to_crs(CRS)
tr_str   = gpd.read_file(GDB, layer='tr_str').to_crs(CRS)
cv_liv   = gpd.read_file(GDB, layer='cv_liv').to_crs(CRS)

# Clip all'area di interesse
from shapely.geometry import box
aoi = box(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)

comuni_target = comuni[comuni['comune_nom'].isin(TARGET)]
altri_comuni  = comuni[~comuni['comune_nom'].isin(TARGET)]

def clip(gdf):
    return gdf[gdf.intersects(aoi)]

idr_clip = clip(el_idr)
vms_clip = clip(el_vms)
str_clip = clip(tr_str)
liv_clip = clip(cv_liv)

print(f'  Fiumi/torrenti nell area: {len(idr_clip)}')
print(f'  Viabilità minore:         {len(vms_clip)}')
print(f'  Strade principali:        {len(str_clip)}')
print(f'  Curve di livello:         {len(liv_clip)}')

# ── MAPPA 1: moderna ─────────────────────────────────────────────────────────
print('\nProduco mappa_moderna.png...')
fig, ax = plt.subplots(figsize=(14, 10), facecolor='#f5f0e8')
ax.set_facecolor('#e8f4f8')

# Curve di livello (grigio chiaro)
if len(liv_clip):
    liv_clip.plot(ax=ax, color='#c8b89a', linewidth=0.3, alpha=0.6)

# Tutti i comuni (grigio neutro)
altri_comuni.plot(ax=ax, color='#ddd5c5', edgecolor='#a09880', linewidth=0.5, alpha=0.7)

# Idrografia (blu)
if len(idr_clip):
    idr_clip.plot(ax=ax, color='#4a90c4', linewidth=0.6, alpha=0.7)

# Viabilità minore (grigio)
if len(vms_clip):
    vms_clip.plot(ax=ax, color='#8a7a6a', linewidth=0.4, alpha=0.5)

# Strade principali (marrone)
if len(str_clip):
    str_clip.plot(ax=ax, color='#b06030', linewidth=0.8, alpha=0.7)

# Comuni target (evidenziati)
comuni_target.plot(ax=ax, color='#d4a843', edgecolor='#7a5010', linewidth=1.2, alpha=0.75)

# Etichette comuni target
for _, row in comuni_target.iterrows():
    cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
    ax.annotate(row['comune_nom'], xy=(cx, cy),
                fontsize=8, fontweight='bold', color='#3a2000',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec='none'))

ax.set_xlim(LON_MIN, LON_MAX)
ax.set_ylim(LAT_MIN, LAT_MAX)
ax.set_xlabel('Longitudine', fontsize=9)
ax.set_ylabel('Latitudine', fontsize=9)
ax.set_title('Area Val d\'Agri — Base moderna DBSN (IGM 2025)\n'
             '6 comuni target (provincia PZ) · idrografia · viabilità · curve di livello',
             fontsize=11, fontweight='bold', pad=12)

# Legenda
legenda = [
    mpatches.Patch(color='#d4a843', label='Comuni target (6 su PZ)'),
    mpatches.Patch(color='#ddd5c5', label='Altri comuni'),
    plt.Line2D([0],[0], color='#4a90c4', lw=1.5, label='Idrografia'),
    plt.Line2D([0],[0], color='#b06030', lw=1.5, label='Strade principali'),
    plt.Line2D([0],[0], color='#8a7a6a', lw=1, label='Viabilità minore'),
    plt.Line2D([0],[0], color='#c8b89a', lw=0.8, label='Curve di livello'),
]
ax.legend(handles=legenda, loc='lower left', fontsize=8, framealpha=0.9)

# Griglia coordinate
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
fig.tight_layout()
out1 = f'{OUT}/mappa_moderna.png'
fig.savefig(out1, dpi=200, bbox_inches='tight')
plt.close()
print(f'  Salvata: {out1}')

# ── MAPPA 2: overlay storica ──────────────────────────────────────────────────
print('\nProduco mappa_overlay.png...')

# Georeferenziamento approssimativo della 1:250.000
# Bounds reali Basilicata da DBSN
BAS_LON_MIN, BAS_LAT_MIN = 15.3355, 39.8946
BAS_LON_MAX, BAS_LAT_MAX = 16.3991, 41.1395

# Carica immagine storica (ridotta per RAM: 1/4 della risoluzione)
print('  Carico immagine storica (ridotta a 1/4)...')
img_full = Image.open(STORICA)
W, H = img_full.size
img_small = img_full.resize((W//4, H//4), Image.LANCZOS)
img_arr = np.array(img_small)
print(f'  Dimensione ridotta: {img_small.width}×{img_small.height} px')

fig, ax = plt.subplots(figsize=(14, 10), facecolor='#f5f0e8')

# Sfondo: mappa storica georeferenziata approssimativamente
ax.imshow(img_arr,
          extent=[BAS_LON_MIN, BAS_LON_MAX, BAS_LAT_MIN, BAS_LAT_MAX],
          origin='upper', alpha=0.55, aspect='auto')

# Sovrascrivi con layer vettoriali moderni
altri_comuni.plot(ax=ax, color='none', edgecolor='#606060', linewidth=0.5, alpha=0.6)
if len(idr_clip):
    idr_clip.plot(ax=ax, color='#1a5fa8', linewidth=0.7, alpha=0.8)
comuni_target.plot(ax=ax, color='none', edgecolor='#cc3300', linewidth=1.8, alpha=0.9)

for _, row in comuni_target.iterrows():
    cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
    ax.annotate(row['comune_nom'], xy=(cx, cy),
                fontsize=8.5, fontweight='bold', color='white',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.25', fc='#cc3300', alpha=0.85, ec='none'))

ax.set_xlim(LON_MIN, LON_MAX)
ax.set_ylim(LAT_MIN, LAT_MAX)
ax.set_xlabel('Longitudine', fontsize=9)
ax.set_ylabel('Latitudine', fontsize=9)
ax.set_title('Overlay storico/moderno — Carta topografica Basilicata 1:250.000 (~1880, Richter)\n'
             'Confini moderni sovrapposti · Comuni target in rosso\n'
             '⚠ Georeferenziamento APPROSSIMATIVO (bounding box regionale)',
             fontsize=10, fontweight='bold', pad=12)

legenda2 = [
    mpatches.Patch(facecolor='none', edgecolor='#cc3300', lw=2, label='Comuni target'),
    mpatches.Patch(facecolor='none', edgecolor='#606060', lw=0.8, label='Altri comuni (confini moderni)'),
    plt.Line2D([0],[0], color='#1a5fa8', lw=1.5, label='Idrografia moderna'),
]
ax.legend(handles=legenda2, loc='lower left', fontsize=8, framealpha=0.9)
ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.5)

fig.tight_layout()
out2 = f'{OUT}/mappa_overlay.png'
fig.savefig(out2, dpi=200, bbox_inches='tight')
plt.close()
print(f'  Salvata: {out2}')

print('\nFatto. File prodotti:')
for f in [out1, out2]:
    mb = os.path.getsize(f)/1024/1024
    print(f'  {f}  ({mb:.1f} MB)')
