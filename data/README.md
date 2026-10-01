# Data

File di folder ini lebih dari 50 MB dan tidak ikut git (lihat `.gitignore`).

## Dataset mentah

Pump Sensor Data (Kaggle): https://www.kaggle.com/datasets/nphantawee/pump-sensor-data

```bash
pip install kaggle          # perlu API token Kaggle di ~/.kaggle/kaggle.json
kaggle datasets download -d nphantawee/pump-sensor-data -p data --unzip
```

Nama file yang diharapkan: `data/sensor.csv` (220.320 baris, interval 1 menit, 2018-04-01 s/d 2018-08-31).

## File hasil cleaning

| File | Dibuat oleh | Keterangan |
|---|---|---|
| `cleaned_sensor_v2.csv` | `notebooks/data_cleaning.py` | Versi aktif. Sensor_15/50/51 dibuang, celah <= `BATAS_MENIT` diinterpolasi, celah panjang tetap NaN. |
| `cleaned_sensor.csv` | `data_cleaning.py` versi lama (commit `ca055e0`) | Versi lama, interpolasi penuh. Hanya dibaca oleh script arsip v1 (`data_understanding.py`, `acf_multiscale.py`). `before_after_evidence.py` merekonstruksinya dari data mentah. |

Menghasilkan `cleaned_sensor_v2.csv` dari `sensor.csv`:

```bash
python notebooks/data_cleaning.py
```
