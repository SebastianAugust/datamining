# UTS Data Mining - Pump Sensor Data

Analisis karakteristik dan klasterisasi regime operasi pada data sensor pompa, Pump Sensor Data (data understanding, cleaning, windowing, K-Means, DBSCAN).

## Struktur folder

```
.
├── README.md
├── requirements.txt
├── data/                 # dataset (tidak di-commit, lihat data/README.md)
├── notebooks/            # script analisis Python
├── outputs/
│   ├── figures/          # gambar hasil analisis (.png)
│   └── tables/           # tabel hasil analisis (.csv, .txt)
└── docs/                 # diagram PRISMA, Gap Analysis (.xlsx), laporan (.docx)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Cara menjalankan (berurutan)

Unduh dataset dulu (lihat `data/README.md`), lalu dari root project:

```bash
python notebooks/data_cleaning.py              # sensor.csv -> cleaned_sensor_v2.csv (NaN pada celah panjang dipertahankan)
python notebooks/missing_analysis.py           # analisis data kosong mentah, batas celah (BATAS_MENIT di common.py)
python notebooks/analysis_nan_aware.py         # statistik, korelasi, ACF, PCA, plot (output v2_*)
python notebooks/acf_multiscale_nan_aware.py   # ACF multi-skala
python notebooks/acf_all_sensors.py            # ACF 49 sensor, ADF, ACF setelah diff
python notebooks/before_after_evidence.py      # bukti sebelum/sesudah
python notebooks/compare_missing_vs_status.py  # analisis pembanding (terpisah dari pipeline)
```

## Tahap 3 (klasterisasi)

Prasyarat: `data/cleaned_sensor_v2.csv` dari `data_cleaning.py`. Hasil dan keputusan: `docs/TAHAP3_HASIL.md`.

```bash
python notebooks/t3_windowing.py     # retensi window (tau 0 / 0,20 / 0,50; 15 / 30 / 60 menit), daftar window dibuang
python notebooks/t3_features.py      # 196 fitur, log1p + RobustScaler + PCA 90%
python notebooks/t3_kmeans.py        # K-Means K=2..10, pilih K menurut aturan, stabilitas 10 seed
python notebooks/t3_dbscan.py        # DBSCAN pembanding
python notebooks/t3_sensitivity.py   # ulang untuk window 15 dan 60 menit
python notebooks/t3_diagnostics.py   # waktu, drift/detrend, artefak celah, profil klaster
# terakhir, setelah label final tersimpan (satu-satunya yang membaca machine_status):
python notebooks/t3_compare_clusters_vs_status.py
```

Urutan itu wajib (skrip berikutnya membaca `t3_labels_30m.csv`). Tidak ada paket baru. Semua output berawalan `t3_`.

Script dan hasil analisis versi lama (data diinterpolasi penuh): dihapus pada branch chore/cleanup-repo; versi terakhir tersedia di git tag archive-cleaning-v1. Ringkasan perubahan dan keputusan: `docs/CHANGES_K2_K3.md`.
