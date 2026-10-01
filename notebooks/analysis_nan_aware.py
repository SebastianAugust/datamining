"""
Tahap 2 (v2): Analisis hilir pada cleaned_sensor_v2.csv dengan penanganan NaN EKSPLISIT.
Menggantikan hasil lama (descriptive_stats, correlation, ACF, PCA, dst.) yang dihitung
pada data yang diinterpolasi penuh. Semua output berawalan "v2_" agar tidak tertukar.

Metode per analisis:
  - Statistik deskriptif & outlier IQR : nilai yang tersedia per kolom (NaN diabaikan).
  - Korelasi                           : pairwise (pandas default), laporan |r| > 0.7.
  - ACF                                : di dalam segmen kontigu tanpa NaN, segmen >= 200 menit,
                                         dirata-ratakan berbobot panjang segmen. Tanpa interpolasi.
  - PCA                                : hanya baris lengkap di semua sensor tersisa.
  - Histogram, boxplot, scatter, time-series : NaN dibuang per kolom/pasangan sebelum digambar;
                                         garis time-series terputus di celah (tidak disambung).

Cara pakai:  python notebooks/analysis_nan_aware.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from common import acf_segmen, MIN_SEGMEN

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor_v2.csv"
FIG_DIR = BASE_DIR / "outputs" / "figures"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
MAX_LAG = 60

df = pd.read_csv(DATASET_PATH, parse_dates=['timestamp']).set_index('timestamp')
print(f"Baris: {len(df)}, sensor: {df.shape[1]}, sel NaN: {int(df.isna().sum().sum())}")

# ---- Statistik deskriptif (nilai tersedia per kolom) ----
stats = pd.DataFrame({'n_valid': df.count(), 'mean': df.mean(), 'std': df.std(), 'skewness': df.skew(),
                      'min': df.min(), 'max': df.max()}).round(3)
stats.to_csv(TABLE_DIR / "v2_descriptive_stats.csv")

# ---- Outlier IQR (nilai tersedia per kolom) ----
q1, q3 = df.quantile(0.25), df.quantile(0.75)
iqr = q3 - q1
out = ((df < q1 - 1.5 * iqr) | (df > q3 + 1.5 * iqr)).sum()
pd.DataFrame({'n_outliers': out, 'n_valid': df.count()}).sort_values('n_outliers', ascending=False) \
    .to_csv(TABLE_DIR / "v2_outlier_counts.csv")

# ---- Korelasi pairwise ----
corr = df.corr()
plt.figure(figsize=(16, 14))
sns.heatmap(corr, cmap='coolwarm', center=0, square=True, cbar_kws={'shrink': 0.6})
plt.title('Matriks Korelasi Pairwise (v2, data dengan NaN)', fontsize=14)
plt.tight_layout()
plt.savefig(FIG_DIR / "v2_correlation_heatmap.png", dpi=150)
plt.close()
pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().reset_index()
pairs.columns = ['var1', 'var2', 'corr']
high = pairs[pairs['corr'].abs() > 0.7].sort_values('corr', key=abs, ascending=False)
high.to_csv(TABLE_DIR / "v2_high_correlation_pairs.csv", index=False)
print(f"Pasangan |r| > 0.7: {len(high)}")

# ---- ACF dalam segmen kontigu ----
rows, acf_cols = [], {}
for c in df.columns:
    a, n_seg, n_pts = acf_segmen(df[c], nlags=MAX_LAG)
    rows.append({'sensor': c, 'n_segmen_dipakai': n_seg, 'titik_dipakai': n_pts,
                 'persen_data_dipakai': round(100 * n_pts / df[c].count(), 2),
                 'acf_lag1': None if a is None else round(float(a[1]), 4)})
    if a is not None:
        acf_cols[c] = a[1:]
acf_sum = pd.DataFrame(rows)
acf_sum.to_csv(TABLE_DIR / "v2_acf_segment_summary.csv", index=False)
pd.DataFrame(acf_cols, index=pd.Index(range(1, MAX_LAG + 1), name='lag')).round(4) \
    .to_csv(TABLE_DIR / "v2_acf_values.csv")
print(f"ACF: sensor tanpa segmen >= {MIN_SEGMEN} menit: {int(acf_sum['acf_lag1'].isna().sum())}")

five = list(df.columns[:5])   # sama dengan 5 sensor pertama pada plot ACF lama
fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
for ax, c in zip(axes, five):
    ax.vlines(range(1, MAX_LAG + 1), 0, acf_cols[c], linewidth=1.2)
    ax.axhline(0, color='black', linewidth=0.6)
    ax.set_title(f'ACF v2 (dalam segmen kontigu) - {c}', fontsize=10)
axes[-1].set_xlabel('lag (menit)')
plt.tight_layout()
plt.savefig(FIG_DIR / "v2_acf_plot.png", dpi=150)
plt.close()

# ---- PCA pada baris lengkap ----
lengkap = df.dropna()
persen = 100 * len(lengkap) / len(df)
with open(TABLE_DIR / "v2_pca_explained_variance.txt", 'w') as f:
    f.write(f"Baris lengkap (semua {df.shape[1]} sensor ada): {len(lengkap)} dari {len(df)} ({persen:.2f}%)\n")
    if len(lengkap) < 10 * df.shape[1]:
        f.write("Terlalu sedikit baris lengkap untuk PCA yang andal; PCA tidak dijalankan.\n")
    else:
        pca = PCA().fit(StandardScaler().fit_transform(lengkap))
        evr = pca.explained_variance_ratio_
        f.write(f"PC1={evr[0]:.4f}, PC2={evr[1]:.4f}, PC1+PC2={evr[:2].sum():.4f}\n")
        f.write(f"Komponen utk 90% varians: {int(np.searchsorted(np.cumsum(evr), 0.90) + 1)}\n")
        z = pca.transform(StandardScaler().fit_transform(lengkap))[:, :2]
        idx = np.random.default_rng(0).choice(len(z), min(20000, len(z)), replace=False)
        plt.figure(figsize=(7, 6))
        plt.scatter(z[idx, 0], z[idx, 1], s=4, alpha=0.3)
        plt.xlabel('PC1'); plt.ylabel('PC2')
        plt.title(f'PCA v2 (baris lengkap n={len(lengkap)}; plot sampel {len(idx)})')
        plt.tight_layout()
        plt.savefig(FIG_DIR / "v2_pca_preview.png", dpi=150)
        plt.close()
print(open(TABLE_DIR / "v2_pca_explained_variance.txt").read())

# ---- Data overview ----
ts = df.index.to_series()
with open(TABLE_DIR / "v2_data_overview.txt", 'w') as f:
    f.write(f"Jumlah baris          : {len(df)}\n")
    f.write(f"Jumlah sensor         : {df.shape[1]}\n")
    f.write(f"Total sel NaN         : {int(df.isna().sum().sum())} ({100 * df.isna().mean().mean():.3f}% dari sel)\n")
    f.write(f"Timestamp duplikat    : {int(ts.duplicated().sum())}\n")
    f.write(f"Interval != 1 menit   : {int((ts.diff().dropna() != pd.Timedelta(minutes=1)).sum())}\n")
    f.write(f"Rentang waktu         : {ts.min()} s/d {ts.max()}\n\n")
    f.write(pd.DataFrame({'n_missing': df.isna().sum(), 'n_unique': df.nunique()}).to_string())
    f.write("\n")

# ---- Histogram per grup (nilai tersedia per kolom) ----
sensor_cols = list(df.columns)
GROUP = 12
n_groups = int(np.ceil(len(sensor_cols) / GROUP))
for g in range(n_groups):
    cols = sensor_cols[g * GROUP:(g + 1) * GROUP]
    nrow = int(np.ceil(len(cols) / 4))
    fig, axes = plt.subplots(nrow, 4, figsize=(12, 2.5 * nrow), squeeze=False)
    for ax, col in zip(axes.flatten(), cols):
        ax.hist(df[col].dropna(), bins=50, edgecolor='none')
        ax.set_title(col, fontsize=9)
    for ax in axes.flatten()[len(cols):]:
        ax.set_visible(False)
    fig.suptitle(f'Histogram v2 (NaN dibuang per kolom) - Grup {g + 1}', fontsize=13)
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"v2_histogram_group{g + 1}.png", dpi=150)
    plt.close()

# ---- Boxplot Z-score per grup (mean/std dari nilai tersedia, NaN dibuang per kolom) ----
z = (df - df.mean()) / df.std()
for g in range(n_groups):
    cols = sensor_cols[g * GROUP:(g + 1) * GROUP]
    plt.figure(figsize=(14, 6))
    plt.boxplot([z[c].dropna() for c in cols], tick_labels=cols)
    plt.xticks(rotation=60)
    plt.title(f'Boxplot v2 (Z-score, NaN dibuang per kolom) - Grup {g + 1}')
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"v2_boxplot_group{g + 1}.png", dpi=150)
    plt.close()

# ---- Scatter 4 pasangan korelasi tertinggi (hanya baris dengan kedua nilai ada) ----
top = high.head(4)
if len(top):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, (_, r) in zip(axes.flatten(), top.iterrows()):
        pair = df[[r['var1'], r['var2']]].dropna()
        pair = pair.iloc[::10]   # tiap 10 baris, agar plot ringan
        ax.scatter(pair.iloc[:, 0], pair.iloc[:, 1], alpha=0.3, s=8)
        ax.set_xlabel(r['var1']); ax.set_ylabel(r['var2'])
        ax.set_title(f"r = {r['corr']:.2f} (pairwise)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "v2_scatter_highcorr.png", dpi=150)
    plt.close()

# ---- Time-series 5 sensor pertama; rolling mean 60 menit (min 30 nilai), celah tetap terputus ----
fig, axes = plt.subplots(5, 1, figsize=(14, 13), sharex=True)
for ax, c in zip(axes, five):
    ax.plot(df.index, df[c], linewidth=0.4, alpha=0.6, label='nilai per menit')
    ax.plot(df.index, df[c].rolling(60, min_periods=30).mean(), linewidth=1.5, label='rolling mean 60 menit')
    ax.set_title(c, fontsize=10)
    ax.legend(loc='upper right', fontsize=7)
axes[-1].set_xlabel('timestamp')
plt.tight_layout()
plt.savefig(FIG_DIR / "v2_timeseries_plot.png", dpi=150)
plt.close()
print("Selesai: overview, histogram, boxplot, scatter, time-series (v2_*)")
