"""
    Tahap 2: Data Understanding & Preprocessing Plan
    UTS Data Mining - Analisis Karakteristik Data Sensor Industrial IoT

    Cara pakai:
        pip install pandas matplotlib seaborn numpy scikit-learn
        python notebooks/data_understanding.py

"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ============================================================
# KONFIGURASI
# ============================================================
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent   # root project (bisa dijalankan dari folder mana saja)
DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor.csv"
FIG_DIR = BASE_DIR / "outputs" / "figures"          # gambar .png
TABLE_DIR = BASE_DIR / "outputs" / "tables"         # tabel .csv / .txt

# ============================================================
# 1. LOAD DATA
# ============================================================
df = pd.read_csv(DATASET_PATH)
num_df = df.select_dtypes(include='number')   # ambil kolom numerik saja

print(f"Jumlah baris: {num_df.shape[0]}")
print(f"Jumlah kolom numerik: {num_df.shape[1]}")
print()

# ============================================================
# 2. ANALISIS TAKSONOMI & SKALA
#    -> statistik deskriptif: mean, std, skewness, min, max
# ============================================================
stats = pd.DataFrame({
    'mean': num_df.mean(),
    'std': num_df.std(),
    'skewness': num_df.skew(),
    'min': num_df.min(),
    'max': num_df.max()
}).round(3)

print("=== Statistik Deskriptif (5 kolom pertama) ===")
print(stats.head())
print()

# Simpan ke CSV biar bisa dilampirkan di paper
stats.to_csv(f"{TABLE_DIR}/descriptive_stats.csv")
print(f"Statistik deskriptif tersimpan di {TABLE_DIR}/descriptive_stats.csv")
print()

# ============================================================
# 3. ANALISIS KORELASI
#    -> matriks korelasi antar semua kolom numerik (heatmap)
# ============================================================
corr = num_df.corr()

plt.figure(figsize=(16, 14))
sns.heatmap(corr, cmap='coolwarm', center=0, square=True, cbar_kws={'shrink': 0.6})
plt.title('Matriks Korelasi Antar Fitur Sensor', fontsize=14)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/correlation_heatmap.png", dpi=150)
plt.close()
print(f"Heatmap korelasi tersimpan di {FIG_DIR}/correlation_heatmap.png")

# Cari pasangan kolom dengan korelasi tinggi (kandidat redundan)
corr_pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().reset_index()
corr_pairs.columns = ['var1', 'var2', 'corr']
high_corr = corr_pairs[corr_pairs['corr'].abs() > 0.7].sort_values('corr', key=abs, ascending=False)

print()
print("=== Pasangan kolom dengan |korelasi| > 0.7 (kandidat redundan) ===")
print(high_corr.to_string(index=False))
high_corr.to_csv(f"{TABLE_DIR}/high_correlation_pairs.csv", index=False)
print()

# Scatter plot untuk beberapa pasangan berkorelasi tinggi (ambil 4 teratas)
top_pairs = high_corr.head(4)
if len(top_pairs) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, (_, row) in zip(axes.flatten(), top_pairs.iterrows()):
        x, y = row['var1'], row['var2']
        ax.scatter(num_df[x], num_df[y], alpha=0.3, s=8)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"r = {row['corr']:.2f}")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/scatter_highcorr.png", dpi=150)
    plt.close()
    print(f"Scatter plot korelasi tinggi tersimpan di {FIG_DIR}/scatter_highcorr.png")
print()

# ============================================================
# 4. ANALISIS OUTLIER
#    -> deteksi outlier per kolom pakai metode IQR
#    -> visualisasi boxplot
# ============================================================
outlier_counts = {}
for col in num_df.columns:
    Q1, Q3 = num_df[col].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    n_out = ((num_df[col] < lower) | (num_df[col] > upper)).sum()
    outlier_counts[col] = n_out

outlier_summary = pd.Series(outlier_counts).sort_values(ascending=False)
print("=== Top 10 kolom dengan outlier terbanyak (metode IQR) ===")
print(outlier_summary.head(10))
outlier_summary.to_csv(f"{TABLE_DIR}/outlier_counts.csv", header=['n_outliers'])
print()

# Boxplot: kolom di-Z-score dulu biar bisa dibandingkan dalam satu grafik
# (karena skalanya beda-beda jauh -- lihat statistik deskriptif di atas)
z_df = (num_df - num_df.mean()) / num_df.std()

# Bagi jadi beberapa grup kolom biar boxplot tidak terlalu padat
n_cols = z_df.shape[1]
group_size = 12
n_groups = int(np.ceil(n_cols / group_size))

for g in range(n_groups):
    cols_subset = z_df.columns[g * group_size: (g + 1) * group_size]
    plt.figure(figsize=(14, 6))
    z_df[cols_subset].boxplot(rot=60)
    plt.title(f'Boxplot Kolom Sensor (Z-score normalized) - Grup {g+1}')
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/boxplot_group{g+1}.png", dpi=150)
    plt.close()

print(f"Boxplot per grup kolom tersimpan sebagai {FIG_DIR}/boxplot_group*.png ({n_groups} file)")
print()

# ============================================================
# 5. DATA OVERVIEW
#    -> ukuran data, tipe data, missing values, duplikat, keteraturan timestamp
# ============================================================
TIME_COL = 'timestamp'
ts = pd.to_datetime(df[TIME_COL])
ts_diff = ts.diff().dropna()

n_missing_total = int(df.isna().sum().sum())
n_dup_rows = int(df.duplicated().sum())
n_dup_rows_no_ts = int(df.drop(columns=TIME_COL).duplicated().sum())
n_dup_ts = int(ts.duplicated().sum())
n_irregular = int((ts_diff != pd.Timedelta(minutes=1)).sum())

overview = pd.DataFrame({
    'dtype': df.dtypes.astype(str),
    'n_missing': df.isna().sum(),
    'n_unique': df.nunique(),
})

with open(f"{TABLE_DIR}/data_overview.txt", 'w') as f:
    f.write(f"Jumlah baris                          : {df.shape[0]}\n")
    f.write(f"Jumlah kolom total                    : {df.shape[1]}\n")
    f.write(f"Jumlah kolom numerik                  : {num_df.shape[1]}\n")
    f.write(f"Total missing values                  : {n_missing_total}\n")
    f.write(f"Baris duplikat (semua kolom)          : {n_dup_rows}\n")
    f.write(f"Baris duplikat (tanpa timestamp)      : {n_dup_rows_no_ts}\n")
    f.write(f"Timestamp duplikat                    : {n_dup_ts}\n")
    f.write(f"Rentang waktu                         : {ts.min()} s/d {ts.max()}\n")
    f.write(f"Interval antar baris != 1 menit       : {n_irregular}\n\n")
    f.write("Tipe data, missing, dan jumlah nilai unik per kolom:\n")
    f.write(overview.to_string())
    f.write("\n")
print(f"Data overview tersimpan di {TABLE_DIR}/data_overview.txt")
print()

# ============================================================
# 6. HISTOGRAM DISTRIBUSI
#    -> dikelompokkan per kategori sensor
# ============================================================

sensor_cols = [c for c in num_df.columns if c.startswith('sensor_')]
group_size = 12
n_groups = int(np.ceil(len(sensor_cols) / group_size))

for g in range(n_groups):
    cols = sensor_cols[g * group_size : (g+1) * group_size]
    ncol = 4
    nrow = int(np.ceil(len(cols) / ncol))

    fig, axes = plt.subplots(nrow, ncol, figsize=(3* ncol, 2.5 * nrow), squeeze=False)
    for ax, col in zip(axes.flatten(), cols):                                                                                          
        ax.hist(num_df[col], bins=50, edgecolor='none')                                                                                
        ax.set_title(col, fontsize=9)                                                                                                  
    for ax in axes.flatten()[len(cols):]:                                                                                              
        ax.set_visible(False)                                                                                                          
                                                                                                                                           
    fig.suptitle(f'Histogram Distribusi - Grup {g+1}', fontsize=13)                                                                    
    plt.tight_layout()                                                                                                                 
    plt.savefig(f"{FIG_DIR}/histogram_group{g+1}.png", dpi=150)                                                                        
    plt.close()                                                                                                                        
                                                                                                                                           
print(f"Histogram tersimpan sebagai {FIG_DIR}/histogram_group*.png")                                                                   
print()

# ============================================================
# 7. ANALISIS TIME-SERIES
#    -> line chart terhadap waktu + autocorrelation function (ACF)
# ============================================================

sensor_cols = [c for c in num_df.columns if c.startswith('sensor_')]
TS_SENSORS = {
    f"Sample {i + 1}" : col for i, col in enumerate(sensor_cols[:5])
}
ROLL_WINDOW = 60   # rolling mean 60 menit, untuk memperlihatkan tren di balik noise
MAX_LAG = 60       # ACF sampai lag 60 menit

ts_df = num_df.set_index(ts)

fig, axes = plt.subplots(len(TS_SENSORS), 1, figsize=(14, 2.6 * len(TS_SENSORS)), sharex=True)
for ax, (cat, col) in zip(axes, TS_SENSORS.items()):
    ax.plot(ts_df.index, ts_df[col], linewidth=0.4, alpha=0.6, label='nilai per menit')
    ax.plot(ts_df.index, ts_df[col].rolling(ROLL_WINDOW).mean(), linewidth=1.5,
            label=f'rolling mean {ROLL_WINDOW} menit')
    ax.set_title(f'{cat}: {col}', fontsize=10)
    ax.legend(loc='upper right', fontsize=7)
axes[-1].set_xlabel('timestamp')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/timeseries_plot.png", dpi=150)
plt.close()
print(f"Plot time-series tersimpan di {FIG_DIR}/timeseries_plot.png")

# ACF dihitung pakai pandas Series.autocorr (korelasi Pearson antara x_t dan x_{t-lag})
lags = np.arange(1, MAX_LAG + 1)
acf_table = pd.DataFrame({col: [num_df[col].autocorr(lag) for lag in lags] for col in TS_SENSORS.values()},
                         index=pd.Index(lags, name='lag'))
acf_table.round(4).to_csv(f"{TABLE_DIR}/acf_values.csv")
conf = 1.96 / np.sqrt(len(num_df))   # batas signifikansi 95% (asumsi white noise)

fig, axes = plt.subplots(len(TS_SENSORS), 1, figsize=(12, 2.4 * len(TS_SENSORS)), sharex=True)
for ax, (cat, col) in zip(axes, TS_SENSORS.items()):
    ax.vlines(lags, 0, acf_table[col], linewidth=1.2)
    ax.axhline(0, color='black', linewidth=0.6)
    ax.axhspan(-conf, conf, color='gray', alpha=0.2, label='95% CI')
    ax.set_title(f'ACF - {cat}: {col}', fontsize=10)
    ax.set_ylabel('autocorr')
    ax.legend(loc='upper right', fontsize=7)
axes[-1].set_xlabel('lag (menit)')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/acf_plot.png", dpi=150)
plt.close()
print(f"Plot ACF tersimpan di {FIG_DIR}/acf_plot.png (nilai di acf_values.csv)")
print()

# ============================================================
# 8. PCA PREVIEW
#    -> StandardScaler + PCA 2 komponen, scatter PC1 vs PC2
# ============================================================
X_scaled = StandardScaler().fit_transform(num_df)
pca = PCA(n_components=2)
pcs = pca.fit_transform(X_scaled)
evr = pca.explained_variance_ratio_

plt.figure(figsize=(9, 7))
plt.scatter(pcs[:, 0], pcs[:, 1], s=6, alpha=0.4)
plt.xlabel(f'PC1 ({evr[0]:.2%} variance)')
plt.ylabel(f'PC2 ({evr[1]:.2%} variance)')
plt.title('PCA Preview (StandardScaler, 2 komponen)')
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/pca_preview.png", dpi=150)
plt.close()

with open(f"{TABLE_DIR}/pca_explained_variance.txt", 'w') as f:
    f.write(f"PC1 explained variance ratio : {evr[0]:.6f}\n")
    f.write(f"PC2 explained variance ratio : {evr[1]:.6f}\n")
    f.write(f"Kumulatif PC1+PC2            : {evr.sum():.6f}\n")
print(f"PCA preview tersimpan di {FIG_DIR}/pca_preview.png (variance di pca_explained_variance.txt)")
print()
print("=== SELESAI ===")
print("File yang dihasilkan:")
print("  - descriptive_stats.csv       (statistik deskriptif tiap kolom)")
print("  - correlation_heatmap.png     (matriks korelasi)")
print("  - high_correlation_pairs.csv  (pasangan kolom korelasi tinggi)")
print("  - scatter_highcorr.png        (scatter plot korelasi tinggi)")
print("  - outlier_counts.csv          (jumlah outlier per kolom)")
print("  - boxplot_group*.png          (boxplot per grup kolom)")
print("  - data_overview.txt           (ukuran, tipe data, missing, duplikat)")
print("  - histogram_group*.png        (histogram per kategori sensor)")
print("  - timeseries_plot.png         (line chart sensor terhadap waktu)")
print("  - acf_plot.png / acf_values.csv (autocorrelation function)")
print("  - pca_preview.png             (scatter PC1 vs PC2)")
print("  - pca_explained_variance.txt  (explained variance ratio PCA)")

# ============================================================
# 9. RINGKASAN AKHIR (angka kunci saja)
# ============================================================
print()
print("=== RINGKASAN ===")
print(f"Total missing values             : {n_missing_total}")
print(f"Baris duplikat                   : {n_dup_rows} (tanpa timestamp: {n_dup_rows_no_ts})")
print(f"Pasangan |korelasi| > 0.7        : {len(high_corr)}")
print(f"Rata-rata outlier per kolom (IQR): {outlier_summary.mean():.2f}")
print(f"ACF lag-1                        : " +
      ", ".join(f"{c}={acf_table.loc[1, c]:.3f}" for c in acf_table.columns))
print(f"PCA explained variance           : PC1={evr[0]:.4f}, PC2={evr[1]:.4f}, total={evr.sum():.4f}")
