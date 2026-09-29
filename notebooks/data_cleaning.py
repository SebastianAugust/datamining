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

import pandas as pd
from pathlib import Path

# ============================================================                                                                         
# KONFIGURASI                                                                                                                          
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "sensor.csv"
CLEANED_DATASET_PATH = BASE_DIR / "data" / "cleaned_sensor.csv"
TABLE_DIR = BASE_DIR / "outputs" / "tables"

# ============================================================                                                                         
# 1. LOAD DATA & PENGURUTAN WAKTU                                                                                                 
# ============================================================

print(f"Memuat dataset dari {DATASET_PATH}...")
df = pd.read_csv(DATASET_PATH)

df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)
df_duplicates = df.duplicated().sum()

print("===========================================")
print(f"Jumlah Baris Awal         : {df.shape[0]}")
print(f"Total Missing Values Awal : {df.isna().sum().sum()}")
print(f"Total Baris Duplikat      : {df_duplicates}")
print("===========================================")

# ============================================================                                                                         
# 2. DROP KOLOM DENGAN MISSING VALUE EKSTREM                                                                                           
# ============================================================   
# Dari analisis sebelumnya: sensor_15 kosong 100%, sensor_50 kosong ~35%

cols_to_drop = ["sensor_15", "sensor_50", "machine_status"]
df = df.drop(columns=cols_to_drop, errors='ignore')

print("===========================================")
print(f"Kolom yang Dihapus        : {cols_to_drop}")
print(f"Jumlah Kolom Tersisa      : {df.shape[1]}")
print("===========================================")

# ============================================================                                                                         
# 3. CEK DUPLIKASI BARIS                                                                                        
# ============================================================ 

# Drop baris yang memiliki duplikasi pada timestamp
df = df.drop_duplicates(subset='timestamp')

# ============================================================                                                                         
# 4. INTERPOLASI TIME-SERIES & FILLNA                                                                                                  
# ============================================================ 

print("Melakukan Interpolasi Linier pada Data Sensor...")

# Ambil hanya kolom sensor (Kolom timestamp dan machine_status tidak perlu)
sensor_cols = [col for col in df.columns if col.startswith("sensor_")]

# Interpolasi linier untuk mengisi data data kosong di tengah dataset
df[sensor_cols] = df[sensor_cols].interpolate(method='linear')

# Back-fill dan Forward-fill untuk sisa data kosong di baris paling awal atau akhir
df[sensor_cols] = df[sensor_cols].bfill().ffill()

# ============================================================                                                                         
# 5. VALIDASI & SIMPAN HASIL                                                                                                           
# ============================================================ 

sisa_missing = df.isna().sum().sum()
sisa_duplicate = df.duplicated().sum()
print(f"Total missing values setelah cleaning  : {sisa_missing}")
print(f"Total baris duplikasi setelah cleaning : {sisa_duplicate}")

summary_file = TABLE_DIR / "cleaning_summary.txt"
with open(summary_file, 'w') as f:
    f.write("=== RINGKASAN DATA CLEANING ===\n")                                                                                       
    f.write(f"Dataset Sumber        : {DATASET_PATH.name}\n")                                                                          
    f.write(f"Kolom Dihapus         : {', '.join(cols_to_drop)}\n")                                                                    
    f.write(f"Total Baris Akhir     : {df.shape[0]}\n")                                                                                
    f.write(f"Total Kolom Akhir     : {df.shape[1]}\n")                                                                                
    f.write(f"Sisa Missing Values   : {sisa_missing}\n") 
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

