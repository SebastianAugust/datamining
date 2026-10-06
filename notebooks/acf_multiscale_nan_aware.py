"""
Tahap 2 (v2): ACF multi-skala pada cleaned_sensor_v2.csv (mengandung NaN).
Pengganti acf_multiscale.py (arsip v1). Output berawalan "v2_".

Penanganan NaN:
  - Resample mean per skala; window dianggap valid jika >= MIN_VALID_FRAC sampel 1 menit di dalamnya
    ada (selain itu NaN). Tidak ada dropna() yang menyambung data lintas celah.
  - ACF dihitung di dalam segmen kontigu tanpa NaN pada deret hasil resample (segmen >= MIN_SEG_TITIK
    titik), dirata-ratakan berbobot panjang segmen.
  - Batas signifikansi: +-1.96/sqrt(n) dengan n = total titik dipakai (pendekatan white noise,
    lebih sederhana daripada Bartlett pada versi lama; angka tidak identik dengan v1).

Cara pakai:  python notebooks/acf_multiscale_nan_aware.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from common import acf_segmen

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor_v2.csv"
FIG_DIR = BASE_DIR / "outputs" / "figures"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

SENSORS = ['sensor_00', 'sensor_01', 'sensor_02', 'sensor_03', 'sensor_04']
SCALES = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '60m': '60min'}
MAX_LAG = 24            # satuan skala waktu masing-masing
MIN_VALID_FRAC = 0.8
MIN_SEG_TITIK = 100     # titik per segmen pada deret hasil resample

df = pd.read_csv(DATASET_PATH, parse_dates=['timestamp']).set_index('timestamp')

rows, acfs = [], {}
for col in SENSORS:
    for label, rule in SCALES.items():
        r = df[col].resample(rule)
        agg = r.mean().where(r.count() >= MIN_VALID_FRAC * pd.Timedelta(rule) / pd.Timedelta('1min'))
        a, n_seg, n_pts = acf_segmen(agg, nlags=MAX_LAG, min_len=MIN_SEG_TITIK)
        if a is None:
            rows.append({'nama_variabel': col, 'skala_waktu': label, 'n_segmen': 0})
            continue
        ci = 1.96 / np.sqrt(n_pts)
        sig = np.abs(a[1:]) > ci
        acfs[(col, label)] = (a[1:], ci, n_pts)
        rows.append({'nama_variabel': col, 'skala_waktu': label, 'n_segmen': n_seg, 'titik_dipakai': n_pts,
                     'lag_signifikan_pertama': int(np.argmax(sig)) + 1 if sig.any() else 'tidak ada',
                     'nilai_acf_lag1': round(float(a[1]), 4)})
summary = pd.DataFrame(rows)
summary.to_csv(TABLE_DIR / "v2_acf_multiscale_summary.csv", index=False)

for col in SENSORS:
    fig, axes = plt.subplots(1, len(SCALES), figsize=(4.2 * len(SCALES), 4), sharey=True)
    for ax, label in zip(axes, SCALES):
        if (col, label) not in acfs:
            ax.set_title(f'{label}: tidak ada segmen'); continue
        a, ci, n = acfs[(col, label)]
        ax.vlines(range(1, MAX_LAG + 1), 0, a, linewidth=1.2)
        ax.axhspan(-ci, ci, color='gray', alpha=0.25)
        ax.axhline(0, color='black', linewidth=0.6)
        ax.set_title(f'{col}\nskala {label} (n={n})', fontsize=10)
        ax.set_xlabel(f'lag (x {label})')
    axes[0].set_ylabel('autocorr (dalam segmen)')
    fig.suptitle(f'ACF Multi-Skala v2 - {col}', fontsize=13)
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"v2_acf_multiscale_{col}.png", dpi=150)
    plt.close()
print(summary.to_string(index=False))
