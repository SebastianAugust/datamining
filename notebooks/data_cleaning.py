"""                                                                                                                                    
    Tahap 2: Data Cleaning                                                                                                
    UTS Data Mining - Analisis Karakteristik Data Sensor Industrial IoT                                                                    
                                                                                                                                           
    Skrip ini menangani missing values pada dataset sensor menggunakan                                                                     
    pendekatan penghapusan kolom dan interpolasi time-series linier,                                                                       
    serta menyimpan dataset yang sudah dibersihkan.                                                                                        
                                                                                                                                           
    Cara pakai:                                                                                                                            
        pip install pandas                                                                                                                 
        python notebooks/data_cleaning.py                                                                                                  
"""

import numpy as np
import pandas as pd
from pathlib import Path
from common import BATAS_MENIT, SENSOR_DIBUANG

# ============================================================                                                                         
# KONFIGURASI                                                                                                                          
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "sensor.csv"
CLEANED_DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor_v2.csv"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================                                                                         
# 1. LOAD DATA & PENGURUTAN WAKTU                                                                                                 
# ============================================================

print(f"Memuat dataset dari {DATASET_PATH}...")
# machine_status tidak ikut dibaca sama sekali (dibuang sebelum preprocessing apa pun)
df = pd.read_csv(DATASET_PATH, usecols=lambda c: c != 'machine_status')

df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)
df_duplicates = df.duplicated().sum()

print("===========================================")
print(f"Jumlah Baris Awal         : {df.shape[0]}")
print(f"Total Missing Values Awal : {df.isna().sum().sum()}")
print(f"Total Baris Duplikat      : {df_duplicates}")
print("===========================================")

# ============================================================
# 2. DROP KOLOM (berdasarkan pola data kosong, BUKAN machine_status)
# ============================================================
# sensor_15 : kosong 100% (220320 menit) -> tidak ada informasi
# sensor_50 : satu celah 76.996 menit, mati permanen sejak 2018-07-09 (35% kosong)
# sensor_51 : celah 15.356 menit (~10,7 hari) di tengah data (Juni) -> tidak dapat diimputasi
# Unnamed: 0 : kolom indeks tanpa nama
# machine_status dibuang sejak awal: tidak boleh dipakai di preprocessing/analisis
cols_to_drop = ["Unnamed: 0", *SENSOR_DIBUANG, "machine_status"]
df = df.drop(columns=cols_to_drop, errors='ignore')

print("===========================================")
print(f"Kolom yang Dihapus        : {cols_to_drop}")
print(f"Jumlah Kolom Tersisa      : {df.shape[1]}")
print("===========================================")

# ============================================================
# 3. CEK DUPLIKASI & KERAPATAN TIMESTAMP
# ============================================================

df = df.drop_duplicates(subset='timestamp')

# Reindex ke grid 1 menit penuh agar panjang celah = menit nyata (bukan jumlah baris).
# Baris yang hilang (jika ada) menjadi NaN; pada dataset ini jumlahnya 0.
n_before = len(df)
df = df.set_index('timestamp').asfreq('min').reset_index()
print(f"Baris ditambahkan oleh reindex grid 1 menit: {len(df) - n_before}")

# ============================================================
# 4. IMPUTASI PER SENSOR (run-length)
# ============================================================
# Interpolasi linier hanya untuk celah <= BATAS_MENIT menit. Celah lebih panjang
# dikosongkan lagi (NaN); TIDAK diisi mean/median/ffill/bfill. limit_area='inside'
# memastikan tidak ada ekstrapolasi di ujung data.
# TODO (Tahap 3): window yang memuat terlalu banyak NaN harus dibuang saat windowing.

print(f"Interpolasi linier untuk celah <= {BATAS_MENIT} menit...")
sensor_cols = [col for col in df.columns if col.startswith("sensor_")]

def isi_celah_pendek(s):
    mask = s.isna()
    run_id = (mask != mask.shift()).cumsum()
    run_len = mask.groupby(run_id).transform('sum')   # panjang celah (menit) tiap baris kosong
    filled = s.interpolate(method='linear', limit_area='inside')
    filled[mask & (run_len > BATAS_MENIT)] = np.nan
    return filled

n_kosong_awal = df[sensor_cols].isna().sum().sum()
df[sensor_cols] = df[sensor_cols].apply(isi_celah_pendek)

# ============================================================                                                                         
# 5. VALIDASI & SIMPAN HASIL                                                                                                           
# ============================================================ 

sisa_missing = int(df[sensor_cols].isna().sum().sum())
n_diinterpolasi = int(n_kosong_awal - sisa_missing)
sisa_duplicate = df.duplicated().sum()
print(f"Sel diinterpolasi (celah <= {BATAS_MENIT} mnt) : {n_diinterpolasi}")
print(f"Sel tetap NaN (celah panjang)          : {sisa_missing}")
print(f"Total baris duplikasi setelah cleaning : {sisa_duplicate}")

summary_file = TABLE_DIR / "cleaning_summary_v2.txt"
with open(summary_file, 'w') as f:
    f.write("=== RINGKASAN DATA CLEANING ===\n")                                                                                       
    f.write(f"Dataset Sumber        : {DATASET_PATH.name}\n")                                                                          
    f.write(f"Kolom Dihapus         : {', '.join(cols_to_drop)}\n")                                                                    
    f.write(f"Total Baris Akhir     : {df.shape[0]}\n")                                                                                
    f.write(f"Total Kolom Akhir     : {df.shape[1]}\n")                                                                                
    f.write(f"BATAS_MENIT           : {BATAS_MENIT}\n")
    f.write(f"Sel Diinterpolasi     : {n_diinterpolasi}\n")
    f.write(f"Sel Tetap NaN         : {sisa_missing}\n")
    f.write(f"Total Baris Duplikasi : {sisa_duplicate}")  

print(f"Menyimpan Dataset Bersih ke {CLEANED_DATASET_PATH.name} (membutuhkan waktu sejenak)...")
df.to_csv(CLEANED_DATASET_PATH, index=False)

# ============================================================                                                                         
# 6. RINGKASAN AKHIR                                                                                                                   
# ============================================================                                                                         
print("\n=== SELESAI ===")                                                                                                             
print("File yang dihasilkan:")                                                                                                         
print(f"  - {CLEANED_DATASET_PATH.name} (Dataset yang sudah dibersihkan dan siap dipakai)")                                                    
print(f"  - {summary_file.name} (Ringkasan proses cleaning)")

