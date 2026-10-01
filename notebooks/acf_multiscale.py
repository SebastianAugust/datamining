"""
ARSIP v1: membaca cleaned_sensor.csv (interpolasi penuh, versi lama) dan menulis ke
outputs/archive_cleaning_v1/. Hasilnya tidak berlaku lagi; pakai analysis_nan_aware.py
dan acf_multiscale_nan_aware.py untuk data v2. Dipertahankan agar hasil lama dapat direproduksi.

Tahap 2 (lanjutan): ACF Multi-Skala Waktu
UTS Data Mining - Analisis Karakteristik Data Sensor Industrial IoT

Menguji apakah temporal dependency lebih terlihat setelah data di-resample
(agregasi mean) ke skala waktu yang lebih kasar.

Cara pakai:
    pip install pandas matplotlib numpy statsmodels
    python notebooks/acf_multiscale.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend, aman buat run tanpa GUI
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf
from statsmodels.graphics.tsaplots import plot_acf

# ============================================================
# KONFIGURASI
# ============================================================
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent   # root project (bisa dijalankan dari folder mana saja)
DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor.csv"
FIG_DIR = BASE_DIR / "outputs" / "archive_cleaning_v1" / "figures"          # gambar .png
TABLE_DIR = BASE_DIR / "outputs" / "archive_cleaning_v1" / "tables"         # tabel .csv / .txt
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

SENSORS = ['sensor_00', 'sensor_01', 'sensor_02', 'sensor_03', 'sensor_04']
SCALES = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '60m': '60min'}
MAX_LAG = 24     # dalam satuan skala waktu masing-masing (bukan menit)
ALPHA = 0.05     # interval kepercayaan 95%

# ============================================================
# 1. LOAD DATA, timestamp -> index datetime
# ============================================================
df = pd.read_csv(DATASET_PATH)
time_col = 'timestamp'
df[time_col] = pd.to_datetime(df[time_col])
df = df.set_index(time_col).sort_index()

print(f"Jumlah baris: {len(df)}  ({df.index.min()} s/d {df.index.max()})")
print()

# ============================================================
# 2. RESAMPLING (mean) per skala waktu
# ============================================================
resampled = {label: df[SENSORS].resample(rule).mean().dropna() for label, rule in SCALES.items()}
for label, data in resampled.items():
    print(f"Skala {label:>3}: {len(data)} titik data")
print()

# ============================================================
# 3. ACF per kolom per skala + ringkasan
#    Lag dianggap signifikan jika CI 95% (Bartlett, sama dengan area arsir
#    di plot_acf) tidak memuat 0.
# ============================================================
rows = []
for col in SENSORS:
    for label, data in resampled.items():
        acf_vals, confint = acf(data[col], nlags=MAX_LAG, alpha=ALPHA, result_object=False)
        half_width = confint[:, 1] - acf_vals
        signif = np.abs(acf_vals[1:]) > half_width[1:]   # lag 1..MAX_LAG
        first_sig = int(np.argmax(signif)) + 1 if signif.any() else 'tidak ada'
        rows.append({
            'nama_variabel': col,
            'skala_waktu': label,
            'lag_signifikan_pertama': first_sig,
            'nilai_acf_lag1': round(float(acf_vals[1]), 4),
        })

summary = pd.DataFrame(rows)
summary.to_csv(f"{TABLE_DIR}/acf_multiscale_summary.csv", index=False)

# ============================================================
# 4. VISUALISASI: 1 figure per kolom, 5 subplot (1 per skala)
# ============================================================
for col in SENSORS:
    fig, axes = plt.subplots(1, len(SCALES), figsize=(4.2 * len(SCALES), 4), sharey=True)
    for ax, (label, data) in zip(axes, resampled.items()):
        plot_acf(data[col], lags=MAX_LAG, alpha=ALPHA, zero=False, auto_ylims=True, fft=True, ax=ax,
                 title=f'{col}\nskala {label} (n={len(data)})')
        ax.set_xlabel(f'lag (x {label})')
        ax.title.set_fontsize(10)
    axes[0].set_ylabel('autocorr')
    fig.suptitle(f'ACF Multi-Skala Waktu - {col}', fontsize=13)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/acf_multiscale_{col}.png", dpi=150)
    plt.close()
    print(f"Plot tersimpan di {FIG_DIR}/acf_multiscale_{col}.png")
print()

# ============================================================
# 5. RINGKASAN
# ============================================================
print(f"Ringkasan tersimpan di {TABLE_DIR}/acf_multiscale_summary.csv")
print()
print("=== RINGKASAN ACF MULTI-SKALA ===")
print(summary.to_string(index=False))
