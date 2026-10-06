"""
Bukti sebelum/sesudah K2: mentah vs cleaning lama (interpolasi penuh, direkonstruksi dari mentah)
vs cleaning baru (cleaned_sensor_v2.csv). Output berawalan "evidence_".

Cara pakai:  python notebooks/before_after_evidence.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from common import acf_segmen

BASE_DIR = Path(__file__).resolve().parent.parent
FIG_DIR = BASE_DIR / "outputs" / "figures"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
SENSOR = 'sensor_00'

load = lambda name, **kw: pd.read_csv(BASE_DIR / "data" / name, parse_dates=['timestamp'],
                                      index_col='timestamp', **kw)
raw = load("sensor.csv", usecols=lambda c: c not in ('Unnamed: 0', 'machine_status'))
# cleaning lama (v1) direkonstruksi dari data mentah: interpolasi linier penuh + bfill/ffill,
# sensor_15/50 dibuang (sensor_51 masih ikut pada v1, tetapi tidak dibandingkan di sini)
old = raw.drop(columns=['sensor_15', 'sensor_50']).interpolate(method='linear').bfill().ffill()
new = load("cleaned_sensor_v2.csv")
kondisi = {'mentah': raw[SENSOR], 'cleaning lama (interpolasi penuh)': old[SENSOR],
           'cleaning baru (v2)': new[SENSOR]}

# ---- plot 3 panel ----
fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True, sharey=True)
for ax, (nama, s) in zip(axes, kondisi.items()):
    ax.plot(s.index, s, linewidth=0.5)
    ax.set_title(f'{SENSOR} - {nama}', fontsize=10)
axes[-1].set_xlabel('timestamp')
plt.tight_layout()
plt.savefig(FIG_DIR / "evidence_sensor_00_3panel.png", dpi=150)
plt.close()

# ---- ACF lag-1: metode sama (segmen kontigu >= 200 menit) + Pearson pairwise sebagai pembanding ----
rows = []
for nama, s in kondisi.items():
    a, n_seg, _ = acf_segmen(s, nlags=1)
    rows.append({'kondisi': nama, 'acf_lag1_segmen': round(float(a[1]), 4), 'n_segmen': n_seg,
                 'autocorr_pairwise': round(float(s.autocorr(1)), 4)})
pd.DataFrame(rows).to_csv(TABLE_DIR / "evidence_sensor_00_acf_lag1.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))

# ---- hitungan sel per sensor (sensor yang dipertahankan) ----
cols = list(new.columns)
nan_raw = raw[cols].isna().sum()
nan_new = new.isna().sum()
nan_old = old[cols].isna().sum()
tab = pd.DataFrame({
    'nan_mentah': nan_raw,
    'diinterpolasi_lama': nan_raw - nan_old,
    'diinterpolasi_baru': nan_raw - nan_new,
    'tetap_nan_baru': nan_new,
    'diisi_lama_dikosongkan_lagi': (old[cols].notna() & raw[cols].isna() & new.isna()).sum(),
}).rename_axis('sensor')
tab.loc['TOTAL'] = tab.sum()
tab.to_csv(TABLE_DIR / "evidence_cell_counts_per_sensor.csv")
print(tab.loc[['TOTAL']].to_string())
