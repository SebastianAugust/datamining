# UTS Data Mining - Industrial IoT

Analisis karakteristik data sensor Industrial IoT (data understanding, ACF, PCA preview).

## Struktur folder

```
.
├── README.md
├── requirements.txt
├── data/                 # dataset mentah (Industrial_IOT_Dataset.csv)
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

Jalankan dari root project (script juga bisa dijalankan dari folder mana saja,
path sudah relatif terhadap lokasi script):

1. **Data understanding** - statistik deskriptif, korelasi, outlier, histogram,
   time-series, ACF, PCA preview:
   ```bash
   python notebooks/data_understanding.py
   ```
2. **ACF multi-skala** - autokorelasi setelah resample ke 1m/5m/15m/30m/60m:
   ```bash
   python notebooks/acf_multiscale.py
   ```

Semua gambar tersimpan ke `outputs/figures/`, tabel ke `outputs/tables/`.
