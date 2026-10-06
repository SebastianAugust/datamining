# Tahap 3: windowing, fitur, klasterisasi, evaluasi, diagnostik

Branch `feature/tahap3-clustering`. Input hanya `data/cleaned_sensor_v2.csv` (49 sensor, NaN di celah panjang dipertahankan). Semua aturan keputusan ditetapkan sebelum angka dilihat dan tidak diubah sesudahnya. `machine_status` hanya dibaca oleh `t3_compare_clusters_vs_status.py` (langkah 7), yang dijalankan setelah label final tersimpan. Hasil disebut **regime operasi**, bukan kondisi kerusakan atau deteksi anomali.

## Ringkasan satu paragraf

Pipeline spesifikasi berjalan lengkap, tetapi hasilnya **degenerate secara struktural**: PCA 90% hanya membutuhkan **1 komponen** (94,0% varians), sehingga K-Means bekerja pada ruang 1 dimensi. Komponen itu adalah satu sumbu "level rata-rata sangat rendah" pada beberapa sensor (sensor_14, 16, 19, 20, 21 dan tetangganya). Aturan memilih K = 2 (Silhouette 0,955, stabilitas ARI 1,000), tetapi angka setinggi itu mencerminkan sumbu tunggal yang didominasi nilai ekstrem, bukan struktur multi-dimensi yang kaya. Klaster 1 (11,9% window) adalah episode level rendah yang menggumpal di waktu (terutama Mei), dan hampir tidak berhubungan dengan `machine_status`.

## 1. Windowing (`t3_windowing.py`)

Window 30 menit, tidak tumpang tindih, jangkar 2018-04-01 00:00. 220.320 menit habis dibagi 15, 30, dan 60, jadi tidak ada baris sisa. Window dibuang jika ADA sensor dengan NaN > tau (tepat 20% masih lolos). Fitur dihitung dari nilai tersedia.

Retensi (`t3_window_retention.csv`):

| Window | tau | Total | Dipertahankan | Dibuang | % dipertahankan |
|---|---|---|---|---|---|
| 30 | 0 | 7.344 | 6.955 | 389 | 94,70 |
| **30** | **0,20** | **7.344** | **6.960** | **384** | **94,77** |
| 30 | 0,50 | 7.344 | 6.966 | 378 | 94,85 |
| 15 | 0 / 0,20 / 0,50 | 14.688 | 13.921 / 13.925 / 13.932 | 767 / 763 / 756 | 94,78 / 94,81 / 94,85 |
| 60 | 0 / 0,20 / 0,50 | 3.672 | 3.473 / 3.475 / 3.483 | 199 / 197 / 189 | 94,58 / 94,64 / 94,85 |

Gerbang 80% terlewati (94,77%). Hasil nyaris tidak bergantung pada tau: NaN terkonsentrasi di celah panjang (window hampir seluruhnya kosong), bukan di window yang setengah kosong. Window dibuang per bulan: April 137, Mei 30, Juni 80, Juli 137, Agustus 0. Daftar: `t3_windows_dropped.csv`.

## 2. Fitur dan PCA (`t3_features.py`)

Per sensor per window: mean, std (populasi), slope (regresi linier terhadap menit, satuan per menit), std selisih menit-ke-menit (hanya pasangan menit yang keduanya ada). 49 x 4 = 196 fitur. log1p untuk std dan std-selisih, lalu RobustScaler untuk semua fitur.

- Komponen PCA untuk 90% varians: **1** (varians 0,9401). Spesifikasi menyebut PCA 2D hanya untuk visualisasi, jadi scatter memakai PCA 2 komponen terpisah.
- Penyebab (terukur): RobustScaler membagi dengan IQR. Fitur mean sejumlah sensor punya IQR sempit tetapi ekor panjang ke bawah. Contoh sensor_20 mean: median 399,6, IQR 0,45, minimum 7,8, sehingga |z| mencapai 864. Lima fitur (sensor_20, 14, 19, 21, 16 mean) menyumbang 94% varians total terskala (26%, 23%, 21%, 13%, 10%). Ini akibat langsung kombinasi RobustScaler + ekor ekstrem, bukan bug kode.
- Matriks fitur: `data/t3_features_30m.csv` (tidak di-commit, dibuat ulang oleh skrip). Varians: `t3_pca_variance.csv`.

## 3. K-Means (`t3_kmeans.py`)

K = 2..10, n_init = 10, random_state = 42, ruang PCA 90%. Silhouette memakai semua window (n = 6.960 < 20.000).

| K | WCSS | Silhouette | DBI | Klaster terkecil | % terkecil | Kandidat (>= 1%) |
|---|---|---|---|---|---|---|
| **2** | 6,34e7 | **0,9548** | 0,143 | 832 | 11,95 | ya |
| 3 | 1,87e7 | 0,9501 | 0,318 | 224 | 3,22 | ya |
| 4 | 8,85e6 | 0,9417 | 0,330 | 118 | 1,70 | ya |
| 5 | 6,42e6 | 0,8909 | 0,419 | 112 | 1,61 | ya |
| 6 | 4,36e6 | 0,8839 | 0,428 | 81 | 1,16 | ya |
| 7 | 3,23e6 | 0,8772 | 0,431 | 61 | 0,88 | tidak |
| 8 | 2,23e6 | 0,8700 | 0,412 | 61 | 0,88 | tidak |
| 9 | 1,76e6 | 0,8699 | 0,426 | 42 | 0,60 | tidak |
| 10 | 1,49e6 | 0,8688 | 0,427 | 30 | 0,43 | tidak |

**K terpilih = 2**, aturan (a)+(b): kandidat K = 2..6, Silhouette tertinggi di K = 2. Ukuran klaster: 6.128 (klaster 0) dan 832 (klaster 1).

- Konfirmasi (c): DBI terbaik juga K = 2 (sepakat). Elbow (titik terjauh dari garis ujung-ke-ujung kurva WCSS, aturan lutut yang saya tetapkan) menunjuk K = 4 (tidak sepakat). Pilihan tetap K = 2.
- Sekunder (d), K terbaik untuk K >= 3 dengan aturan sama: **K = 3** (Silhouette 0,9501; klaster 6.031 / 705 / 224). Stabilitas K = 3 tidak diukur.
- Silhouette terbaik 0,955 >= 0,25, jadi tidak ada pernyataan "struktur lemah" menurut aturan (e). Lihat catatan di Hal yang tidak pasti: aturan ini tidak mendeteksi masalah dimensi.
- Stabilitas (10 seed, 45 pasang): ARI rata-rata **1,000**, minimum **1,000**. Stabil menurut ambang 0,80. Stabilitas sempurna wajar untuk ruang 1 dimensi dengan pemisahan jelas.

## 4. DBSCAN pembanding (`t3_dbscan.py`)

Ruang PCA 90% yang sama. eps dari lutut kurva k-distance (k = min_samples, titik itu sendiri ikut dihitung). min_samples = 2 x komponen PCA = 2.

| min_samples | eps | Klaster | Noise | Silhouette (tanpa noise) | DBI (tanpa noise) | ARI vs K-Means (noise = label sendiri) | ARI (tanpa noise) |
|---|---|---|---|---|---|---|---|
| 2 | 0,582 | 121 | 4,12% | 0,736 | 0,182 | 0,453 | 0,452 |
| 5 | 1,177 | 25 | 6,02% | 0,751 | 0,220 | 0,562 | 0,584 |
| 10 | 1,137 | 14 | 7,84% | 0,819 | 0,180 | 0,455 | 0,473 |

DBSCAN memecah satu sumbu tunggal menjadi banyak klaster kecil, yaitu satu klaster besar (5.002 sampai 5.335 window) plus potongan-potongan. Metrik DBSCAN dihitung tanpa titik noise, jadi tidak sebanding dengan K-Means. Hanya pembanding; hasil K-Means tidak diganti.

## 5. Sensitivitas ukuran window (`t3_sensitivity.py`)

Silhouette dan DBI antar window tidak sebanding dan tidak dipakai untuk memilih window.

| Window | Window dipertahankan | PCA | K terpilih | K sekunder | Klaster terkecil | ARI stabilitas (rata-rata / min) | ARI vs 30 menit (per menit) |
|---|---|---|---|---|---|---|---|
| 15 | 13.925 | 1 | 2 | 3 | 11,91% | 1,000 / 1,000 | 0,991 |
| 30 | 6.960 | 1 | 2 | 3 | 11,95% | 1,000 / 1,000 | (acuan) |
| 60 | 3.475 | 1 | 2 | 3 | 11,94% | 1,000 / 1,000 | 0,991 |

K terpilih sama (2) di ketiga ukuran, dan label per menit hampir identik (ARI 0,991). Kesimpulan K = 2 tidak bergantung pada ukuran window. Ketiganya memakai pipeline yang sama sehingga ketiganya mewarisi masalah satu-komponen.

## 6. Diagnostik klaster semu (`t3_diagnostics.py`)

**a. Kedekatan waktu (terukur).** Proporsi pasangan window bersebelahan berlabel sama: **0,9954** (K = 2). Rata-rata 1000 permutasi label: 0,789 (persentil 95: 0,793); p = 0,001 (batas bawah 1/1001). Perlu dicatat: baseline permutasi sudah tinggi (0,79) karena klaster 0 berisi 88% window, jadi kedekatan waktu harus dibaca terhadap baseline itu, bukan terhadap 0,5. Panjang run rata-rata: klaster 0 = 235,7 window (26 run), klaster 1 = 48,9 window (17 run). Untuk K = 3: observasi 0,9938 vs permutasi 0,762; run rata-rata 262,2 / 70,5 / 10,7 window.

**b. Drift (terukur).** Proporsi klaster 1 per bulan: April 5,5%, **Mei 44,7%**, Juni 6,8%, Juli 0,07%, Agustus 1,1%. Klaster 1 terkonsentrasi pada satu episode (akhir April sampai pertengahan Mei) dan sekitar 27 Juni, plus beberapa window terpencil (`t3_cluster_timeline.png`). Setelah fitur di-detrend (log1p lalu dikurangi median bergulir 7 hari terpusat per kolom, lalu RobustScaler dan PCA 90% yang sama, 2 komponen), K-Means K = 2 menghasilkan **ARI 0,239** terhadap hasil asli (K = 3: 0,343). Struktur klaster **sebagian besar hilang** setelah level lambat dibuang, artinya klaster asli sebagian besar adalah perbedaan level jangka panjang, bukan pola jangka pendek.

**c. Artefak celah (terukur).** Window yang berjarak <= 60 menit dari sel NaN (sensor mana pun) atau yang memuat sel hasil interpolasi, di antara 6.960 window yang dipertahankan:

| Kriteria | Keseluruhan | Klaster 0 | Klaster 1 |
|---|---|---|---|
| Dekat celah NaN <= 60 menit | 0,65% | 0,65% | 0,60% |
| Memuat sel interpolasi | 0,42% | 0,31% | 1,20% |
| Salah satu | 0,98% | 0,90% | 1,56% |

Persentasenya kecil dan klaster tidak diperkaya secara berarti pada kriteria jarak. Pada interpolasi klaster 1 sekitar 3,9x lebih tinggi, tetapi dari hanya 10 window (1,2% x 832), jadi tidak cukup untuk menyimpulkan apa pun. Artefak celah bukan penjelasan utama klaster.

**d. Profil klaster (terukur; satuan asli di `t3_cluster_profile_features.csv`, `t3_cluster_top_sensors.csv`).** 10 sensor paling membedakan (maks eta-kuadrat antar 4 fitur, pada fitur terskala): sensor_21, 20, 19, 24, 22, 25, 23, 14, 16, 26 (eta2 0,87 sampai 0,96). Pembedanya adalah fitur **mean**, hampir tidak ada yang lain (eta2 fitur std, slope, dstd mayoritas < 0,2):

| Sensor (mean) | Klaster 0 | Klaster 1 |
|---|---|---|
| sensor_21 | 876,0 | 179,5 |
| sensor_20 | 396,6 | 83,5 |
| sensor_19 | 660,8 | 49,4 |
| sensor_24 | 618,9 | 67,1 |
| sensor_14 | 415,5 | 76,8 |

Klaster 1 = window ketika level rata-rata banyak sensor turun jauh ke bawah (sekitar 10 sampai 20% dari level klaster 0) dengan variabilitas dalam-window biasa saja. Heatmap: `t3_cluster_profile.png`.

## 7. Pembanding machine_status (`t3_compare_clusters_vs_status.py`)

Skrip mandiri, dijalankan setelah label final. Tanpa tuning ulang.

| Klaster | NORMAL | RECOVERING | BROKEN | Total | Memuat >= 1 menit BROKEN/RECOVERING |
|---|---|---|---|---|---|
| 0 | 6.010 | 118 | 0 | 6.128 | 123 |
| 1 | 828 | 4 | 0 | 832 | 4 |

Purity 0,9825, **sama persis dengan baseline** (semua window ditebak NORMAL = 0,9825). ARI = -0,019, NMI = 0,004 (untuk penanda "memuat >= 1 menit BROKEN/RECOVERING": ARI -0,020, NMI 0,004). Klaster 1 hampir seluruhnya berstatus NORMAL (99,5%), jadi episode level rendah **bukan** periode RECOVERING/BROKEN menurut label. Hasil K = 3 serupa (ARI -0,019, NMI 0,004). Baris BROKEN tidak ditafsirkan (7 menit saja; tidak ada window dengan status mayoritas BROKEN).

**Window yang dibuang di langkah 1** (384 window): NORMAL 23, **RECOVERING 361**, BROKEN 0 (mayoritas). Per menit: NORMAL 699, RECOVERING 10.820, BROKEN 1 dari 11.520 menit. Jadi 94% window yang dibuang berada di periode RECOVERING; data kosong sangat terkonsentrasi di status itu (sejalan dengan temuan Tahap 2). Dari window yang dipertahankan, 122 berstatus mayoritas RECOVERING dari 6.960 (1,75%) dan 127 memuat minimal satu menit abnormal. Akibatnya klasterisasi nyaris tidak melihat periode RECOVERING sama sekali.

## 8. Hal yang tidak pasti

Terukur:
- Retensi, jumlah komponen PCA, tabel metrik, stabilitas, hasil DBSCAN, ARI sensitivitas, keempat diagnostik, dan tabel silang status semuanya dihitung langsung dari skrip. Hasil dapat direproduksi (seed 42; permutasi memakai `default_rng(42)`).

Tafsiran dan keterbatasan:
1. **Ruang 1 dimensi.** Aturan (e) hanya menguji Silhouette < 0,25 dan tidak mendeteksi PCA 1 komponen. Silhouette 0,955, DBI 0,143, dan ARI stabilitas 1,000 sangat bagus tetapi menggambarkan pemisahan di satu sumbu yang didominasi beberapa fitur mean ekstrem. Jangan dibaca sebagai "klaster sangat kuat". Saya tidak mengganti scaler atau fitur setelah melihat ini (aturan tetap); apakah itu perlu diubah adalah keputusan Anda, misalnya scaler berbasis kuantil atau winsorizing sebelum PCA, sebagai analisis tambahan yang diberi label jelas.
2. **Sebagian besar perbedaan klaster adalah level lambat.** ARI 0,239 setelah detrend dan konsentrasi di Mei menunjukkan klaster 1 sebagian besar adalah episode level rendah, yang bisa saja perubahan setpoint atau beban. Penyebab fisiknya tidak diketahui; label status tidak menjelaskannya.
3. **Detrend adalah pilihan implementasi saya**: dilakukan di tingkat fitur (median bergulir 7 hari terpusat atas window yang dipertahankan, `min_periods=1`), bukan pada deret mentah per menit. Detrend pada deret mentah bisa memberi angka berbeda.
4. **Aturan lutut** (elbow dan k-distance) adalah pilihan saya: titik terjauh dari garis ujung-ke-ujung. Elbow menunjuk K = 4, DBSCAN eps sangat bergantung pada aturan ini.
5. **Window yang dibuang berasal dari periode RECOVERING.** Hasil klaster tidak berlaku untuk periode itu, dan ini memengaruhi apa arti "regime" di sini.
6. K sekunder (K = 3) tidak diuji stabilitasnya. DBSCAN dan K-Means tidak sebanding secara metrik.
7. ARI sensitivitas dihitung per menit pada menit yang tercakup oleh kedua window yang dipertahankan (sekitar 208 ribu menit).
8. Hasil ini adalah "regime operasi" menurut pengelompokan fitur statistik 30 menit, bukan diagnosis kerusakan.

## 9. File output

Skrip (`notebooks/`): `t3_common.py`, `t3_windowing.py`, `t3_features.py`, `t3_kmeans.py`, `t3_dbscan.py`, `t3_sensitivity.py`, `t3_diagnostics.py`, `t3_compare_clusters_vs_status.py`.

Tabel (`outputs/tables/`): `t3_window_retention.csv`, `t3_windows_dropped.csv`, `t3_pca_variance.csv`, `t3_kmeans_metrics.csv` (+ `_15m`, `_60m`), `t3_kmeans_stability.csv`, `t3_labels_30m.csv`, `t3_dbscan_results.csv`, `t3_window_sensitivity.csv`, `t3_diagnostics.csv`, `t3_cluster_profile_features.csv`, `t3_cluster_top_sensors.csv`, `t3_cluster_vs_status.csv`.

Gambar (`outputs/figures/`): `t3_elbow.png`, `t3_silhouette_dbi.png`, `t3_pca_scatter_kmeans.png`, `t3_cluster_timeline.png`, `t3_kdistance.png`, `t3_cluster_profile.png`, `t3_diag_monthly.png`, `t3_diag_gap.png`, `t3_cluster_vs_status.png`.

Tidak di-commit: `data/t3_features_30m.csv`.
