# CLEANUP_PLAN (Tahap 1: inventaris, belum ada file yang diubah)

File ini jangan di-commit. Dibuat setelah pemeriksaan pada branch `fix/k2-k3-missing-values`, HEAD `efb3c99`.

Catatan awal: HEAD sekarang `efb3c99` ("revisi data EDA"), satu commit setelah `c945f2e`. Commit itu hanya menambah `docs/PENJELASAN_PROJECT.txt` dan `docs/RANGKUMAN_PERUBAHAN.txt`. Working tree bersih saat inventaris dimulai.

Cakupan: seluruh repo kecuali `.git/` dan `venv/`. Total 95 entri di working tree, 90 tracked. Ukuran repo di luar `.git` dan `venv` sekitar 338 MB (hampir semuanya tiga CSV di `data/`), `.git` 11 MB.

Hasil pemeriksaan otomatis:
- File 0 byte: tidak ada. Folder kosong: tidak ada.
- Duplikat berdasarkan hash MD5: tidak ada.
- Nama mengandung copy / (1) / _old / _backup: tidak ada. `.DS_Store`, `Thumbs.db`, `.ipynb_checkpoints`, `*.tmp`, `*.log`: tidak ada.
- File dataset lama Industrial IoT di working tree: tidak ada. Hanya ada di riwayat git (`data/Industrial_IOT_Dataset.csv`, commit pertama `55fad8c`).
- File di `outputs/` (non-arsip) yang tidak dihasilkan script mana pun: tidak ada. Semua 43 file cocok dengan nama di script (termasuk yang dibuat lewat f-string).

---

## Kategori A (aman dihapus setelah disetujui)

| Path | Ukuran | Status git | Dirujuk oleh | Alasan |
|---|---|---|---|---|
| `notebooks/__pycache__/common.cpython-314.pyc` (dan foldernya) | 3.187 B | ignored (`.gitignore`) | tidak ada | Cache bytecode, dibuat ulang otomatis saat script jalan |

Total A: 1 file (+1 folder), 3.187 B.
Karena aturan Anda, file ignored ini akan dicadangkan dulu ke `../backup_cleanup_<tanggal>/` sebelum dihapus (murah, ukurannya kecil).

---

## Kategori B (perlu keputusan Anda)

### B1. Paket arsip v1 (satu paket)

| Path | Ukuran | Status git | Dirujuk oleh | Alasan |
|---|---|---|---|---|
| `notebooks/data_understanding.py` | 14.374 B | tracked | `README.md:41`, `data/README.md:21`, `docs/CHANGES_K2_K3.md:51`, `docs/RANGKUMAN_PERUBAHAN.txt:52` | Script arsip v1, membaca `cleaned_sensor.csv` |
| `notebooks/acf_multiscale.py` | 4.645 B | tracked | `README.md:41`, `data/README.md:21`, `docs/CHANGES_K2_K3.md:47,51`, `docs/RANGKUMAN_PERUBAHAN.txt:52`, docstring `notebooks/acf_multiscale_nan_aware.py:3` | Script arsip v1 |
| `outputs/archive_cleaning_v1/` (20 gambar + 8 tabel = 28 file) | 2.723.530 B (2,6 MB) | tracked | `README.md:42`, `docs/CHANGES_K2_K3.md:51,53`, `docs/PENJELASAN_PROJECT.txt:93`, `docs/RANGKUMAN_PERUBAHAN.txt:53,59`, serta `FIG_DIR`/`TABLE_DIR` di kedua script arsip | Output hasil data diinterpolasi penuh, sudah dinyatakan tidak berlaku |
| `outputs/archive_cleaning_v1/tables/cleaning_summary.txt` (bagian dari baris di atas) | 249 B | tracked | tidak ada | Yatim: pembuatnya (`data_cleaning.py` versi lama) sudah diganti, tidak ada script sekarang yang menulis nama ini |
| `data/cleaned_sensor.csv` | 113.063.387 B (108 MB) | ignored/untracked, diubah 2026-09-30 | `.gitignore:10`, `data/README.md:21`, `docs/CHANGES_K2_K3.md:49,51,95`, `docs/RANGKUMAN_PERUBAHAN.txt:26,53`, dan 2 script arsip | Input script arsip. Tidak dibaca lagi oleh `before_after_evidence.py` |

Total B1: 31 file (2 script + 28 output + 1 CSV), sekitar 115,8 MB. Yang tracked: 30 file, 2,7 MB. Yang untracked: 1 file, 108 MB.

Tidak ada kode aktif (Kategori C) yang meng-import atau membaca paket ini. Rujukan yang tersisa hanya dokumentasi dan docstring.

Pro menghapus: paket ini sudah digantikan v2, hasilnya dinyatakan tidak berlaku, dan memberi dua cara menjalankan analisis yang membingungkan. Tracked file tetap ada di riwayat git.
Kontra: angka "lama" yang dikutip di `docs/CHANGES_K2_K3.md` (mis. 201 pasangan korelasi, PC1 0,350, PC2 0,222) tidak lagi bisa dicek tanpa checkout commit lama; `cleaned_sensor.csv` tidak ada di git, jadi hanya bisa dipulihkan dari cadangan atau dibuat ulang dengan script cleaning lama di `ca055e0` (saya sudah memverifikasi rekonstruksinya dari data mentah, selisih maksimum 2e-13).

Rekomendasi: hapus paket arsip dengan `git rm` untuk 30 file tracked, dan pindahkan `data/cleaned_sensor.csv` ke folder cadangan di luar repo (jangan dihapus permanen). Alasan: paket sudah usang dan hanya dirujuk dokumentasi; tracked file aman di riwayat, sedangkan satu-satunya file yang tidak bisa dipulihkan dari git (CSV 108 MB) tetap tersimpan di cadangan.
Opsi lebih konservatif jika angka lama masih perlu dilihat: pertahankan `outputs/archive_cleaning_v1/` saja (2,6 MB) dan hapus dua script serta CSV. Konsekuensinya: output arsip tidak bisa dibuat ulang.

Dampak dokumentasi bila paket dihapus (akan saya perbarui di Tahap 2): `README.md`, `data/README.md`, `docs/CHANGES_K2_K3.md`, `.gitignore` (entri `data/cleaned_sensor.csv`), serta docstring `acf_multiscale_nan_aware.py:3`. Dua file lain yang merujuk paket ini, `docs/PENJELASAN_PROJECT.txt` dan `docs/RANGKUMAN_PERUBAHAN.txt`, tidak ada di daftar pembaruan Anda dan berada di `docs/` (Kategori C). Lihat pertanyaan 2.

### B2. Sisa dataset lama Industrial IoT

Tidak ada file di working tree. Hanya `data/Industrial_IOT_Dataset.csv` di riwayat commit `55fad8c`. Tidak ada tindakan yang diperlukan.
Namun ada rujukan teks yang usang: `README.md:1,3` (judul dan deskripsi menyebut "Industrial IoT" padahal datasetnya Pump Sensor Data) dan docstring di `data_cleaning.py:3` serta dua script arsip. Rekomendasi: perbaiki judul dan deskripsi di `README.md` saja (diizinkan di Tahap 2 poin 5); docstring `data_cleaning.py` adalah Kategori C, jadi tidak saya ubah kecuali Anda izinkan.

### B3. File yatim di outputs/ (non-arsip)

Tidak ada. Satu-satunya yatim adalah `cleaning_summary.txt` di dalam arsip (lihat B1).

### B4. Script di notebooks/ yang tidak dipanggil siapa pun dan tidak ada di README

Tidak ada. Semua script aktif tercantum di `README.md`; dua script arsip juga disebut di README sebagai arsip (B1).

### B5. Dokumen yang tumpang tindih

Tidak ada duplikat file. Catatan: `docs/RANGKUMAN_PERUBAHAN.txt` dan `docs/CHANGES_K2_K3.md` sebagian tumpang tindih (keduanya merangkum perubahan commit K2/K3), tetapi isi dan tujuannya berbeda (changelog ringkas berbahasa santai vs laporan keputusan). Keduanya di `docs/` (Kategori C), jadi saya tidak mengusulkan penghapusan.

---

## Kategori C (dilarang disentuh, hanya konfirmasi keberadaan)

| Item | Ukuran | Status |
|---|---|---|
| `data/sensor.csv` | 124.058.460 B | ignored |
| `data/cleaned_sensor_v2.csv` | 110.605.966 B | ignored |
| `data/README.md` | 1.058 B | tracked |
| `notebooks/common.py`, `data_cleaning.py`, `missing_analysis.py`, `analysis_nan_aware.py`, `acf_multiscale_nan_aware.py`, `acf_all_sensors.py`, `before_after_evidence.py`, `compare_missing_vs_status.py` | total 36.444 B (8 file) | tracked |
| `docs/CHANGES_K2_K3.md`, `Gap_Analysis.xlsx`, `prisma_flow.png`, `PENJELASAN_PROJECT.txt`, `RANGKUMAN_PERUBAHAN.txt` | total 190.397 B (5 file) | tracked |
| `README.md`, `requirements.txt`, `.gitignore` | 1.995 B (3 file) | tracked |
| `outputs/figures/` + `outputs/tables/` (semua berawalan v2_, missing_, gap_, evidence_, sensitivity_, acf_all_sensors, timestamp_check, missing_vs_status_comparison, cleaning_summary_v2) | 43 file, 2.902.671 B | tracked |
| `venv/`, `.git/` | tidak dihitung | venv ignored |
| `REVIEW_EDA.md` | 18.529 B, diubah 2026-09-30 | ignored/untracked. Hanya dilaporkan. Dirujuk oleh `.gitignore:6`, `docs/CHANGES_K2_K3.md:55`, `docs/RANGKUMAN_PERUBAHAN.txt:69,70` |

Catatan C: `docs/Gap_Analysis.xlsx` dan `docs/prisma_flow.png` tidak dirujuk file lain selain baris struktur folder di `README.md` yang menyebut "diagram PRISMA, Gap Analysis". Tidak ada tindakan.
Catatan: `REVIEW_EDA.md` tidak bisa dipulihkan bila hilang (tidak tracked). Saya tidak menyentuhnya.

---

## Ringkasan per kategori

| Kategori | File | Ukuran |
|---|---|---|
| A | 1 (+1 folder) | 3.187 B |
| B1 (tracked) | 30 | 2,7 MB |
| B1 (untracked) | 1 | 108 MB |
| B2 s.d. B5 | 0 | 0 |
| C | ~62 file + 3 CSV data + venv/.git | tidak dihapus |

## Pertanyaan untuk Anda

1. A: setuju hapus `notebooks/__pycache__/` (dicadangkan dulu)?
2. B1: pilih (a) hapus seluruh paket, `cleaned_sensor.csv` ke cadangan (rekomendasi), (b) hapus script + CSV, pertahankan `outputs/archive_cleaning_v1/`, atau (c) pertahankan semuanya?
3. Bila B1 dihapus: izinkah saya juga memperbarui `docs/PENJELASAN_PROJECT.txt` dan `docs/RANGKUMAN_PERUBAHAN.txt` (hanya baris yang merujuk paket arsip), padahal itu di `docs/`? Tanpa izin, kedua file ini akan menyisakan rujukan menggantung.
4. README.md:1,3 menyebut "Industrial IoT": perbaiki ke Pump Sensor Data?
5. Tidak ada kandidat B2 s.d. B5 yang ditemukan; tidak perlu keputusan kecuali Anda ingin cakupan dicari lebih luas.
