# Tahap 3: analisis tambahan pasca-hasil (varian penskalaan)

**Status: analisis tambahan pasca-hasil. Dua varian ini dipilih SETELAH melihat hasil utama (PCA 1 komponen, `docs/TAHAP3_HASIL.md`), jadi tidak boleh menggantikan hasil utama.** Hasil utama (`t3_*`) tidak diubah. Semua output berawalan `t3x_`, dan setiap judul gambar diberi label "[Analisis tambahan pasca-hasil]".

Pipeline sama persis dengan hasil utama (window 30 menit, tau 0,20, 6.960 window, 196 fitur, log1p untuk std dan std-selisih, PCA 90%, K-Means K = 2..10, `random_state` 42, aturan pemilihan K yang sama, stabilitas 10 seed), kecuali langkah penskalaan:

- **Varian A**: winsorizing tiap fitur (setelah log1p) di persentil 1 dan 99, lalu RobustScaler.
- **Varian B**: `QuantileTransformer(output_distribution="normal", n_quantiles=1000)` sebagai pengganti RobustScaler.

Skrip: `notebooks/t3x_variants.py` (tidak membaca `machine_status`) dan `notebooks/t3x_compare_vs_status.py` (mandiri, dijalankan setelah label tersimpan).

## Ringkasan

| | Utama (`t3_`) | Varian A | Varian B |
|---|---|---|---|
| Komponen PCA 90% | 1 | **1** | **86** |
| Varians PC1 | 0,940 | 0,981 | 0,182 |
| K terpilih | 2 | 2 | 2 |
| Silhouette K terpilih | 0,955 | 0,955 | **0,354** |
| DBI K terpilih | 0,143 | 0,143 | 1,284 |
| Ukuran klaster | 6.128 / 832 | 6.128 / 832 | 6.350 / 610 |
| Stabilitas ARI (rata-rata / min) | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 |
| ARI terhadap label utama | (acuan) | **1,000** | **0,796** |
| ARI setelah detrend | 0,239 | 0,247 | **0,003** |

Satu kalimat: winsorizing p1/p99 tidak mengubah apa pun, sedangkan transformasi kuantil menghilangkan masalah satu-komponen, tetapi klaster yang tersisa lemah dan tetap dipicu level lambat.

## Varian A (winsorizing p1/p99 + RobustScaler)

- **PCA:** tetap **1 komponen** (varians 0,9805, lebih ekstrem dari utama). Winsorizing di p1/p99 tidak memangkas nilai ekstrem karena window level rendah berjumlah sekitar 12% (> 1%), jadi persentil 1 sudah berada di dalam kelompok level rendah itu. Winsorizing p1/p99 tidak menyentuh struktur masalahnya.
- **10 fitur dengan kontribusi varians terbesar** (varians kolom terskala / total; `t3x_top_features.csv`): sensor_20 mean 27,5%, sensor_14 mean 24,0%, sensor_19 mean 22,4%, sensor_21 mean 13,7%, sensor_16 mean 10,5%, sensor_09 mean 0,7%, sensor_17 mean 0,6%, sensor_18 mean 0,2%, sensor_04 mean 0,1%, sensor_00 slope < 0,1%. Lima fitur pertama menyumbang 98%.
- **Metrik K = 2..10** (`t3x_varianA_kmeans_metrics.csv`):

| K | Silhouette | DBI | Klaster terkecil | % |
|---|---|---|---|---|
| **2** | **0,9549** | 0,143 | 832 | 11,95 |
| 3 | 0,9502 | 0,319 | 224 | 3,22 |
| 4 | 0,9420 | 0,333 | 121 | 1,74 |
| 5 | 0,8848 | 0,400 | 117 | 1,68 |
| 6 | 0,8830 | 0,432 | 81 | 1,16 |
| 7 | 0,8767 | 0,434 | 60 | 0,86 |
| 8 | 0,8752 | 0,409 | 61 | 0,88 |
| 9 | 0,8750 | 0,421 | 42 | 0,60 |
| 10 | 0,8768 | 0,380 | 42 | 0,60 |

- **K terpilih = 2** (kandidat K = 2..6). Elbow menunjuk K = 4, DBI terbaik K = 2. K sekunder (>= 3) = 3.
- **Stabilitas:** ARI rata-rata 1,000, minimum 1,000.
- **ARI terhadap label utama: 1,000.** Label identik.
- **Per bulan (proporsi klaster 1):** April 5,5%, Mei 44,7%, Juni 6,8%, Juli 0,1%, Agustus 1,1% (sama dengan utama).
- **ARI setelah detrend:** 0,247 (1 komponen setelah detrend).
- **Kesimpulan A:** tidak menambah informasi. Hasilnya sama dengan hasil utama.

## Varian B (QuantileTransformer normal)

- **PCA:** **86 komponen** untuk 90% varians (kumulatif 0,902; PC1 0,182). Dominasi satu sumbu hilang karena setiap fitur dipetakan ke distribusi normal, sehingga nilai ekstrem tidak lagi menghasilkan |z| ratusan.
- **10 fitur dengan kontribusi varians terbesar:** sensor_19 std, sensor_19 mean, sensor_19 dstd, sensor_18 dstd, sensor_18 std, sensor_17 mean, sensor_18 mean, sensor_17 dstd, sensor_17 std, sensor_22 std, masing-masing 1,1 sampai 1,2% dari varians total. Daftar ini hampir datar dengan sendirinya: setelah transformasi kuantil semua fitur berbasis varians sekitar 1, dan perbedaannya hanya soal banyaknya nilai kembar. Daftar ini **tidak bermakna sebagai "pendorong" klaster**; ini bukan ukuran yang sebanding dengan varian A.
- **Metrik K = 2..10** (`t3x_varianB_kmeans_metrics.csv`):

| K | WCSS | Silhouette | DBI | Klaster terkecil | % |
|---|---|---|---|---|---|
| **2** | 1,20e6 | **0,3538** | 1,284 | 610 | 8,76 |
| 3 | 1,11e6 | 0,0956 | 2,509 | 606 | 8,71 |
| 4 | 1,06e6 | 0,1004 | 2,258 | 131 | 1,88 |
| 5 | 1,03e6 | 0,0897 | 2,663 | 129 | 1,85 |
| 6 | 1,01e6 | 0,0829 | 2,754 | 126 | 1,81 |
| 7 | 9,84e5 | 0,0657 | 2,925 | 129 | 1,85 |
| 8 | 9,64e5 | 0,0630 | 2,976 | 128 | 1,84 |
| 9 | 9,53e5 | 0,0569 | 3,047 | 126 | 1,81 |
| 10 | 9,39e5 | 0,0569 | 3,008 | 124 | 1,78 |

- **K terpilih = 2** (semua K lolos ambang 1%; Silhouette tertinggi di K = 2). Elbow menunjuk K = 5, DBI terbaik K = 2. K sekunder menurut aturan (K >= 3) = 4 dengan Silhouette hanya 0,100, jadi tidak ada sub-struktur yang berarti.
- **Silhouette 0,354 >= 0,25**, sehingga aturan (e) tidak menyebut struktur lemah. Namun nilainya sedang, dan turun tajam ke 0,096 pada K = 3, jadi hanya pemisahan 2 kelompok yang punya dukungan.
- **Stabilitas:** ARI rata-rata 1,000, minimum 1,000 (K-Means dengan `n_init=10` konvergen ke solusi yang sama pada 10 seed).
- **ARI terhadap label utama: 0,796.** Klaster kecil B (610 window) seluruhnya berada di dalam klaster kecil utama (832 window); 222 window klaster kecil utama jatuh ke klaster besar B (tabel silang di bawah).

| Utama \ B | B klaster 0 (610) | B klaster 1 (6.350) |
|---|---|---|
| Utama 0 (6.128) | 0 | 6.128 |
| Utama 1 (832) | 610 | 222 |

- **Per bulan** (proporsi klaster 0 / klaster kecil): April 0%, **Mei 38,1%**, Juni 3,9%, Juli 0%, Agustus 0,1% (`t3x_monthly.csv`). Terkonsentrasi di Mei sama seperti utama, tetapi lebih ketat.
- **ARI setelah detrend:** **0,003** (103 komponen setelah detrend). Struktur klaster hilang sepenuhnya begitu level lambat dibuang.

## Pembanding machine_status (`t3x_compare_vs_status.py`, `t3x_cluster_vs_status.csv`)

Skrip mandiri, dijalankan setelah label tersimpan, tanpa tuning ulang.

| Varian | Klaster | NORMAL | RECOVERING | BROKEN | Total |
|---|---|---|---|---|---|
| A | 0 | 6.010 | 118 | 0 | 6.128 |
| A | 1 | 828 | 4 | 0 | 832 |
| B | 0 | 610 | 0 | 0 | 610 |
| B | 1 | 6.228 | 122 | 0 | 6.350 |

- Varian A: purity 0,9825 (baseline 0,9825), ARI -0,019, NMI 0,004 (identik dengan hasil utama).
- Varian B: purity 0,9825 (baseline 0,9825), ARI -0,027, NMI 0,008. Klaster kecil B berisi **0 window RECOVERING**; 122 window RECOVERING seluruhnya berada di klaster besar.
- Penanda "memuat >= 1 menit BROKEN/RECOVERING": A ARI -0,020 / NMI 0,004; B ARI -0,028 / NMI 0,009.
- BROKEN hanya 7 menit dan tidak ada window dengan status mayoritas BROKEN, jadi tidak ada kesimpulan untuk BROKEN. Window yang dibuang di langkah 1 (94% RECOVERING) tidak berubah dan tidak dihitung ulang di sini.

## Kesimpulan dan batasan

Terukur:
- Winsorizing p1/p99 (A) tidak mengubah hasil. Transformasi kuantil (B) menghilangkan dominasi satu sumbu (86 komponen) tetapi memberi K = 2 yang sama, dengan klaster kecil yang adalah himpunan bagian dari klaster kecil utama dan terkonsentrasi di Mei.
- Di kedua varian struktur klaster nyaris hilang setelah detrend (A 0,247, B 0,003) dan tidak berhubungan dengan `machine_status` (ARI mendekati 0, purity sama dengan baseline).

Tafsiran:
- Temuan hasil utama bahwa klaster ini terutama episode level lambat tidak diperlemah oleh koreksi penskalaan; varian B memperkuatnya. Fakta bahwa K = 2 bertahan di tiga skema penskalaan menambah keyakinan pada keberadaan episode itu, bukan pada struktur multi-regime.
- Silhouette B (0,354) dan A (0,955) tidak sebanding karena ruang PCA berbeda dimensi (86 vs 1).

Batasan:
- Varian dipilih setelah melihat hasil utama, jadi pemilihan ini tidak independen. Hasilnya tidak boleh dipakai untuk menggantikan hasil utama atau untuk memilih "angka terbaik".
- Winsorizing diterapkan setelah log1p dan sebelum RobustScaler (urutan ini pilihan implementasi). Persentil dihitung pada seluruh window (tanpa pemisahan latih/uji).
- Detrend sama dengan hasil utama: pada tingkat fitur (setelah log1p, median bergulir 7 hari terpusat), lalu transformasi varian yang sama diterapkan ulang.
- Kontribusi varians kolom (A dan B) adalah varians kolom terskala dibagi total, bukan beban PCA.

## File output

Skrip: `notebooks/t3x_variants.py`, `notebooks/t3x_compare_vs_status.py`.
Tabel (`outputs/tables/`): `t3x_variants_summary.csv`, `t3x_varianA_kmeans_metrics.csv`, `t3x_varianB_kmeans_metrics.csv`, `t3x_varianA_stability.csv`, `t3x_varianB_stability.csv`, `t3x_top_features.csv`, `t3x_monthly.csv`, `t3x_labels_30m.csv`, `t3x_cluster_vs_status.csv`.
Gambar (`outputs/figures/`): `t3x_silhouette_dbi.png`, `t3x_cluster_timeline.png`, `t3x_cluster_vs_status.png`.
