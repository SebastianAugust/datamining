"""
Tahap 2 (K3): Analisis data kosong pada sensor.csv MENTAH (sebelum drop & imputasi).
Tanpa machine_status. Output: missing_per_column.csv, missing_by_month.csv,
missing_heatmap.png, timestamp_check.txt, gap_lengths_per_sensor.csv,
gap_summary_per_sensor.csv, gap_length_histogram.png, sensitivity_batas_menit.csv

Cara pakai:  python notebooks/missing_analysis.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from common import BATAS_MENIT, SENSOR_DIBUANG

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "sensor.csv"
FIG_DIR = BASE_DIR / "outputs" / "figures"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# machine_status sengaja tidak dibaca (aturan: tidak dipakai di pipeline)
df = pd.read_csv(DATASET_PATH, usecols=lambda c: c not in ('Unnamed: 0', 'machine_status'),
                 parse_dates=['timestamp'])
sensors = [c for c in df.columns if c.startswith('sensor_')]

# ============================================================
# 1.4 Verifikasi timestamp
# ============================================================
ts = df['timestamp']
grid = pd.date_range(ts.min(), ts.max(), freq='min')
n_dup = int(ts.duplicated().sum())
n_hilang = len(grid.difference(ts))
n_selisih = int((ts.sort_values().diff().dropna() != pd.Timedelta(minutes=1)).sum())
with open(TABLE_DIR / "timestamp_check.txt", 'w') as f:
    f.write(f"Rentang          : {ts.min()} s/d {ts.max()}\n")
    f.write(f"Baris di file    : {len(df)}\n")
    f.write(f"Baris grid 1 mnt : {len(grid)}\n")
    f.write(f"Baris hilang     : {n_hilang}\n")
    f.write(f"Timestamp duplikat: {n_dup}\n")
    f.write(f"Selisih != 1 menit: {n_selisih}\n")
    f.write("Panjang celah diukur dari grid 1 menit (timestamp), bukan jumlah baris.\n")
print(open(TABLE_DIR / "timestamp_check.txt").read())

# Reindex ke grid penuh: baris yang hilang (jika ada) menjadi NaN, panjang run = menit nyata
s_df = df.drop_duplicates('timestamp').set_index('timestamp').reindex(grid)[sensors]
na = s_df.isna()

# ============================================================
# 1.1 / 1.2 Missing per kolom dan per bulan
# ============================================================
pd.DataFrame({'n_missing': na.sum(), 'pct_missing': (na.mean() * 100).round(3)}) \
    .rename_axis('sensor').to_csv(TABLE_DIR / "missing_per_column.csv")
(na.groupby(na.index.to_period('M')).mean().T * 100).round(2) \
    .rename_axis('sensor').to_csv(TABLE_DIR / "missing_by_month.csv")

# ============================================================
# 1.3 Heatmap: fraksi kosong per sensor per blok 6 jam (agar 220 ribu menit terbaca)
# ============================================================
blok = na.resample('6h').mean().T
fig, ax = plt.subplots(figsize=(14, 11))
im = ax.imshow(blok.values, aspect='auto', cmap='magma_r', vmin=0, vmax=1, interpolation='nearest')
ax.set_yticks(range(len(sensors)))
ax.set_yticklabels(sensors, fontsize=6)
bulan = pd.date_range(grid.min().normalize(), grid.max(), freq='MS')
ax.set_xticks([blok.columns.get_indexer([b], method='nearest')[0] for b in bulan])
ax.set_xticklabels([b.strftime('%Y-%m') for b in bulan])
ax.set_title('Data kosong per sensor (blok 6 jam, data mentah; gelap = kosong)')
fig.colorbar(im, ax=ax, shrink=0.6, label='fraksi kosong dalam blok')
plt.tight_layout()
plt.savefig(FIG_DIR / "missing_heatmap.png", dpi=150)
plt.close()

# ============================================================
# 1.5 Celah kosong berurutan per sensor
# ============================================================
rows = []
for c in sensors:
    m = na[c]
    run_id = (m != m.shift()).cumsum()
    for _, g in m[m].groupby(run_id[m]):
        awal, akhir = g.index[0], g.index[-1]
        rows.append((c, awal, akhir, int((akhir - awal) / pd.Timedelta(minutes=1)) + 1))
gaps = pd.DataFrame(rows, columns=['sensor', 'awal', 'akhir', 'panjang_menit'])
gaps.to_csv(TABLE_DIR / "gap_lengths_per_sensor.csv", index=False)
(gaps.groupby('sensor')['panjang_menit']
     .agg(jumlah_celah='count', median='median', p90=lambda x: x.quantile(0.9), terpanjang='max')
     .reindex(sensors).fillna(0).rename_axis('sensor')
     .to_csv(TABLE_DIR / "gap_summary_per_sensor.csv"))

# ============================================================
# 1.6 Histogram panjang celah (x log)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(gaps['panjang_menit'], bins=np.logspace(0, np.log10(gaps['panjang_menit'].max() + 1), 45),
        edgecolor='white')
ax.axvline(BATAS_MENIT, color='crimson', linestyle='--', label=f'BATAS_MENIT = {BATAS_MENIT}')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('panjang celah (menit, skala log)')
ax.set_ylabel('jumlah celah (skala log)')
ax.set_title(f'Distribusi panjang celah kosong, semua sensor (n={len(gaps)} celah)')
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "gap_length_histogram.png", dpi=150)
plt.close()

# ============================================================
# 2. Sensitivitas BATAS_MENIT (hanya sensor yang dipertahankan)
# ============================================================
keep = gaps[~gaps['sensor'].isin(SENSOR_DIBUANG)]
sens = []
for b in sorted({5, 10, 30, 60, BATAS_MENIT}):
    pendek, panjang = keep[keep['panjang_menit'] <= b], keep[keep['panjang_menit'] > b]
    sens.append({'BATAS_MENIT': b, 'celah_diinterpolasi': len(pendek),
                 'sel_diinterpolasi': int(pendek['panjang_menit'].sum()),
                 'celah_tetap_kosong': len(panjang),
                 'sel_tetap_kosong': int(panjang['panjang_menit'].sum()),
                 'dipilih': b == BATAS_MENIT})
sens = pd.DataFrame(sens)
sens.to_csv(TABLE_DIR / "sensitivity_batas_menit.csv", index=False)
print(sens.to_string(index=False))

print("\nPanjang celah (sensor yang dipertahankan), frekuensi per panjang <= 100 menit:")
print(keep[keep['panjang_menit'] <= 100]['panjang_menit'].value_counts().sort_index().to_string())
