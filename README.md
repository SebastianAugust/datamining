# UTS Data Mining - Pump Sensor Data

Analisis karakteristik data sensor pompa, Pump Sensor Data (data understanding, ACF, PCA preview).

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

Script dan hasil analisis versi lama (data diinterpolasi penuh): dihapus pada branch chore/cleanup-repo; versi terakhir tersedia di git tag archive-cleaning-v1. Ringkasan perubahan dan keputusan: `docs/CHANGES_K2_K3.md`.
