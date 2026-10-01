# Perubahan K2 dan K3: penanganan missing values

Branch: `fix/k2-k3-missing-values` (belum di-push).

## 1. Ringkasan keputusan dan alasan

| Keputusan | Alasan (dari data mentah, bukan machine_status) |
|---|---|
| Buang `sensor_15` | Kosong 100% (220.320 menit). |
| Buang `sensor_50` | Satu celah 76.996 menit, dari 2018-07-09 12:44 sampai akhir data (35% kosong). Mati sejak 9 Juli, bukan Agustus. |
| Buang `sensor_51` | Satu celah 15.356 menit (~10,7 hari), 2018-06-20 07:58 sampai 06-30 23:53. |
| Buang `Unnamed: 0` | Kolom indeks tanpa nama. |
| `machine_status` tidak dibaca sama sekali di pipeline | Aturan proyek. `read_csv` memakai `usecols` yang mengecualikannya. |
| Interpolasi linier hanya untuk celah <= `BATAS_MENIT` | Celah pendek = glitch; celah panjang = sensor mati. Celah panjang tetap NaN, tanpa mean/median/ffill/bfill. |
| Interpolasi memakai run-length, bukan `limit=N` | Menghindari potongan garis lurus buatan di ujung celah panjang. |
| `is_missing_<sensor>` tidak dibuat | Saran pengembangan saja. |

Timestamp (`timestamp_check.txt`): rentang 2018-04-01 00:00 s/d 2018-08-31 23:59, 220.320 baris = 220.320 menit pada grid 1 menit. Baris hilang 0, duplikat 0, selisih bukan 1 menit 0. Panjang celah tetap diukur dari grid timestamp (menit), sehingga kode tetap benar jika data lain punya baris hilang.

## 2. BATAS_MENIT = 15 (dapat Anda ubah)

Ubah satu konstanta `BATAS_MENIT` di `notebooks/common.py`, lalu jalankan ulang urutan script di bagian 3.

Argumen dari `outputs/figures/gap_length_histogram.png`: ekor distribusi panjang celah **kontinu** (tidak ada jurang yang memisahkan glitch dari sensor mati). Namun 440 dari 456 celah (96%) panjangnya <= 15 menit, dengan puncak di 1, 3, 8, dan 15 menit; di atas 15 menit tiap panjang hanya muncul 0 sampai 4 kali. Nilai 15 dipilih sebagai batas praktis di mana massa distribusi berakhir, bukan sebagai pemisah alami.

Tabel sensitivitas (49 sensor yang dipertahankan, `sensitivity_batas_menit.csv`):

| BATAS_MENIT | Sel diinterpolasi | Sel tetap kosong | Celah tetap kosong |
|---|---|---|---|
| 5 | 515 | 31.339 | 100 |
| 10 | 1.032 | 30.822 | 35 |
| **15 (dipilih)** | **1.171** | **30.683** | **25** |
| 30 | 1.244 | 30.610 | 22 |
| 60 | 1.465 | 30.389 | 17 |

Hasil tidak sensitif terhadap pilihan ini: dari 15 ke 60 menit hanya 294 sel yang berubah status, dari sekitar 10,8 juta sel (220.320 baris x 49 sensor). Di bawah 15 menit perubahannya lebih besar (5 menit: 656 sel lebih sedikit diinterpolasi).

## 3. File dibuat atau diubah

Urutan jalan: `data_cleaning.py`, lalu `analysis_nan_aware.py`, `acf_multiscale_nan_aware.py`, `acf_all_sensors.py`, `before_after_evidence.py`. `missing_analysis.py` boleh kapan saja. `compare_missing_vs_status.py` berdiri sendiri.

Kode (`notebooks/`):
- `common.py` (baru): `BATAS_MENIT`, `SENSOR_DIBUANG`, ACF per segmen (dengan opsi diff).
- `data_cleaning.py` (diubah): drop sensor, reindex grid 1 menit, imputasi run-length. Output `cleaned_sensor_v2.csv`, `cleaning_summary_v2.txt`.
- `missing_analysis.py` (baru): Bagian 1 dan 2.
- `analysis_nan_aware.py` (baru): statistik, outlier, korelasi, ACF, PCA, overview, histogram, boxplot, scatter, time-series. Semua berawalan `v2_`.
- `acf_multiscale_nan_aware.py` (baru): pengganti `acf_multiscale.py`.
- `acf_all_sensors.py` (baru): ACF 49 sensor, ADF, ACF setelah diff.
- `before_after_evidence.py` (baru): bukti sebelum/sesudah; cleaning lama direkonstruksi dari data mentah (selisih maks dengan `cleaned_sensor.csv` 2e-13).
- `compare_missing_vs_status.py` (baru): satu-satunya yang membaca `machine_status`; tidak di-import siapa pun.
- `data_understanding.py`, `acf_multiscale.py` (diarsipkan): tetap membaca `cleaned_sensor.csv` (v1) tetapi sekarang menulis ke `outputs/archive_cleaning_v1/`, sehingga tidak ada nama output yang bentrok dengan v2.

Output: hasil lama dipindahkan (tidak dihapus) ke `outputs/archive_cleaning_v1/`. Output baru ada di `outputs/tables/` dan `outputs/figures/`. Daftar lengkap: lihat `git status` pada commit ini atau isi folder tersebut.

Dokumentasi: `data/README.md` (cara mengunduh dataset dan membuat file cleaned), `.gitignore` (venv, `__pycache__`, `REVIEW_EDA.md`, tiga file CSV di `data/` yang masing-masing > 50 MB), `README.md` (diperbarui).

## 4. Angka kunci

- Sensor dibuang: 3 (sensor_15, 50, 51). Sensor tersisa: 49.
- Sel kosong mentah pada 49 sensor tersebut: 31.854.
- Sel diinterpolasi (baru): 1.171. Cleaning lama menginterpolasi seluruh 31.854 sel.
- Sel tetap NaN: 30.683. Semuanya sel yang diinterpolasi cleaning lama lalu dikosongkan lagi (30.683). Dua angka ini sama karena tidak ada NaN di ujung data.
- Metode NaN per analisis:
  - Statistik deskriptif dan outlier IQR: nilai tersedia per kolom (kolom `n_valid` ditambahkan).
  - Korelasi: pairwise. Pasangan |r| > 0.7: 183 (lama: 201).
  - ACF: dalam segmen kontigu tanpa NaN, segmen >= 200 menit, rata-rata berbobot panjang segmen, tanpa interpolasi. Semua 49 sensor punya segmen yang memenuhi syarat.
  - PCA: baris lengkap di 49 sensor = **208.962 dari 220.320 (94,84%)**. Jumlah ini cukup, jadi PCA dijalankan: PC1 = 0,361, PC2 = 0,169, total 0,530; 15 komponen untuk 90% varians. Lama: PC1 0,350, PC2 0,222, total 0,572 (data berbeda dan sensor_51 ikut, jadi tidak murni sebanding).
- ACF lag-1 sensor_00 (metode segmen sama untuk ketiganya; `evidence_sensor_00_acf_lag1.csv`):

| Kondisi | ACF lag-1 (segmen) | Pearson pairwise `autocorr(1)` |
|---|---|---|
| Mentah | 0,9890 (9 segmen) | 0,9993 |
| Cleaning lama | 0,9997 (1 segmen) | 0,9997 |
| Cleaning baru | 0,9945 (5 segmen) | 0,9994 |

Perubahan lag-1 sensor_00: 0,9997 menjadi 0,9945 (turun 0,0052). Penurunan ini kecil karena sensor_00 sangat persisten per menit. Klaim review bahwa lag-1 "mendekati 1,0" benar untuk cleaning lama (0,9997), tetapi efek koreksinya pada lag-1 sendiri kecil. Dampak yang lebih nyata ada pada plot (panel 2 vs 3 di `evidence_sensor_00_3panel.png`: dua garis lurus buatan di cleaning lama hilang) dan pada lag lebih panjang, yang tidak saya ukur untuk perbandingan ini.

### ACF seluruh sensor, ADF, dan diff orde 1

Sumber: `acf_all_sensors.csv` dan `acf_all_sensors_summary.txt`. ACF dalam segmen kontigu >= 200 menit; ADF pada segmen terpanjang tiap sensor (maxlag 24, AIC); diff di dalam segmen.

- ACF lag-1 > 0,9: 49 dari 49 sensor (minimum 0,930; median 0,997). ACF lag-60 minimum 0,3125.
- ADF: 1 sensor tidak stasioner (sensor_02, p = 0,205); 48 stasioner (p < 0,05). ADF pada n sekitar 220 ribu mudah menolak H0, jadi "stasioner" di sini berarti tidak ada bukti unit root, bukan berarti tanpa tren atau perubahan level.
- Setelah diff orde 1, ACF lag-1 turun lebih dari 0,5 pada 38 sensor (median lag-1 level 0,997 menjadi -0,076 setelah diff). Ambang 0,5 adalah pilihan saya.
- 11 sensor (sensor_38 sampai 49 kecuali sensor_44) ACF lag-1 setelah diff tetap 0,66 sampai 0,81. Untuk sensor ini ketergantungan jangka pendek tidak hilang setelah tren dibuang. Saya tidak menafsirkan penyebabnya.
- ACF multi-skala (`v2_acf_multiscale_summary.csv`, 5 sensor): lag-1 tertinggi ada di skala 1m atau 5m, dan menurun pada skala lebih kasar (sensor_00: 0,9945 pada 1m menjadi 0,9277 pada 60m). Lag pertama selalu signifikan.

## 5. Hal tidak pasti atau butuh keputusan Anda

1. Ambang "turun drastis setelah diff" (0,5) dan ambang ACF tinggi (0,9) adalah pilihan saya. Apakah diubah?
2. Mengapa sensor_38 sampai 49 mempertahankan ACF diff tinggi? Belum diselidiki; apakah perlu?
3. ADF memakai segmen terpanjang dan maxlag 24. Apakah cukup, atau perlu uji tambahan (mis. KPSS)?
4. Ambang NaN per window untuk Tahap 3 (TODO di `data_cleaning.py`) belum diputuskan.
5. BROKEN hanya 7 baris, jadi persentase per sensor di `missing_vs_status_comparison.csv` kasar; jangan disimpulkan darinya.
6. Script arsip v1 masih butuh `cleaned_sensor.csv`, yang tidak ikut git; pembuatnya adalah versi `data_cleaning.py` di commit `ca055e0`. Apakah arsip v1 perlu dipertahankan sebagai script?
