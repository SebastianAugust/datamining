"""
Tahap 2 (v2): ACF seluruh sensor, uji ADF, dan ACF setelah diff orde 1, pada cleaned_sensor_v2.csv.

Penanganan NaN:
  - ACF: dalam segmen kontigu tanpa NaN (>= 200 menit), rata-rata berbobot panjang segmen;
    tidak melintasi celah, tanpa interpolasi.
  - Diff orde 1: dilakukan di dalam tiap segmen, lalu ACF dengan cara yang sama.
  - ADF: pada segmen kontigu TERPANJANG tiap sensor (uji ini butuh deret tanpa celah).
    regression='c', autolag='AIC', maxlag=ADF_MAXLAG (dibatasi agar tidak lambat; pilihan, bukan baku).
    H0 = ada unit root (tidak stasioner); p < 0.05 -> H0 ditolak (dianggap stasioner).

Output: acf_all_sensors.csv, acf_all_sensors_summary.txt (berawalan tidak "v2_" karena baru;
tidak ada padanannya di v1)

Cara pakai:  python notebooks/acf_all_sensors.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.tsa.stattools import adfuller
from common import acf_segmen, segmen_kontigu

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor_v2.csv"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

LAGS = [1, 5, 15, 60]
ADF_MAXLAG = 24
ALPHA = 0.05
TINGGI = 0.9          # ACF lag-1 > TINGGI dianggap tinggi
TURUN_DRASTIS = 0.5   # lag-1 level - lag-1 diff > nilai ini dianggap turun drastis (ambang bebas, ubah bila perlu)

df = pd.read_csv(DATASET_PATH, parse_dates=['timestamp']).set_index('timestamp')

rows = []
for c in df.columns:
    row = {'sensor': c}
    a, n_seg, n_pts = acf_segmen(df[c], nlags=max(LAGS))
    d, _, _ = acf_segmen(df[c], nlags=max(LAGS), diff=True)
    row['n_segmen'] = n_seg
    for lag in LAGS:
        row[f'acf_lag{lag}'] = np.nan if a is None else round(float(a[lag]), 4)
    for lag in LAGS:
        row[f'acf_diff_lag{lag}'] = np.nan if d is None else round(float(d[lag]), 4)
    longest = max(segmen_kontigu(df[c]), key=len)
    row['adf_n'] = len(longest)
    try:
        stat, p, *_ = adfuller(longest, maxlag=ADF_MAXLAG, autolag='AIC')
        row['adf_stat'], row['adf_p'] = round(float(stat), 3), round(float(p), 4)
    except Exception as e:   # mis. deret hampir konstan
        row['adf_stat'], row['adf_p'] = np.nan, np.nan
        print(f"{c}: ADF gagal ({e})")
    rows.append(row)
    print(c, flush=True)

res = pd.DataFrame(rows)
res['stasioner_adf'] = np.where(res['adf_p'].isna(), 'n/a', np.where(res['adf_p'] < ALPHA, 'ya', 'tidak'))
res['turun_drastis_setelah_diff'] = (res['acf_lag1'] - res['acf_diff_lag1']) > TURUN_DRASTIS
res.to_csv(TABLE_DIR / "acf_all_sensors.csv", index=False)

n = len(res)
tinggi = res['acf_lag1'] > TINGGI
nonstat = res['stasioner_adf'] == 'tidak'
turun = res['turun_drastis_setelah_diff']
txt = f"""Ringkasan ACF seluruh sensor (n sensor = {n}); angka apa adanya, belum ditafsirkan.
ACF lag-1 > {TINGGI}                         : {int(tinggi.sum())} sensor
ADF: tidak stasioner (p >= {ALPHA})           : {int(nonstat.sum())} sensor; stasioner: {int((res['stasioner_adf'] == 'ya').sum())}; n/a: {int((res['stasioner_adf'] == 'n/a').sum())}
ACF lag-1 turun > {TURUN_DRASTIS} setelah diff     : {int(turun.sum())} sensor
Irisan: lag-1 tinggi DAN turun drastis        : {int((tinggi & turun).sum())} sensor
Irisan: lag-1 tinggi DAN tidak stasioner      : {int((tinggi & nonstat).sum())} sensor
Median ACF lag-1 level / diff                 : {res['acf_lag1'].median():.4f} / {res['acf_diff_lag1'].median():.4f}
Catatan: ADF dihitung pada segmen terpanjang tiap sensor (adf_n); pada n sangat besar uji ini cenderung
menolak H0 untuk penyimpangan kecil. Ambang 'turun drastis' ({TURUN_DRASTIS}) adalah pilihan, bukan baku.
"""
(TABLE_DIR / "acf_all_sensors_summary.txt").write_text(txt)
print(txt)
