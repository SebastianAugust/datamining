"""
Konstanta dan fungsi bersama untuk pipeline v2 (penanganan missing values K2/K3).
Dipakai oleh missing_analysis.py, data_cleaning.py, analysis_nan_aware.py,
before_after_evidence.py. TIDAK dipakai oleh compare_missing_vs_status.py.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf

# ============================================================
# BATAS_MENIT: celah kosong berurutan <= nilai ini diinterpolasi (glitch sesaat),
# celah yang lebih panjang dibiarkan NaN (sensor mati). UBAH DI SINI SAJA.
# Alasan pemilihan: lihat CHANGES_K2_K3.md dan outputs/figures/gap_length_histogram.png
# ============================================================
BATAS_MENIT = 15

# Sensor yang dibuang (alasan: lihat data_cleaning.py bagian 2)
SENSOR_DIBUANG = ["sensor_15", "sensor_50", "sensor_51"]

MIN_SEGMEN = 200   # panjang minimal segmen kontigu (menit) untuk dihitung ACF-nya


def segmen_kontigu(s: pd.Series):
    """Kembalikan list segmen (np.ndarray) tanpa NaN dari series bertimestamp rapat."""
    ok = s.notna()
    run_id = (ok != ok.shift()).cumsum()
    return [g.to_numpy() for _, g in s[ok].groupby(run_id[ok])]


def acf_segmen(s: pd.Series, nlags: int = 60, min_len: int = MIN_SEGMEN, diff: bool = False):
    """
    ACF di dalam segmen kontigu tanpa NaN (tidak melintasi celah, tanpa interpolasi).
    Segmen dengan panjang >= min_len dirata-ratakan, berbobot panjang segmen.
    diff=True: segmen di-diff orde 1 (dalam segmen, tidak melintasi celah) sebelum ACF.
    Return (acf_array lag 0..nlags atau None, jumlah segmen dipakai, total titik dipakai).
    """
    assert min_len > nlags + 1
    segs = [np.diff(g) if diff else g for g in segmen_kontigu(s) if len(g) >= min_len]
    segs = [g for g in segs if g.std() > 0]
    if not segs:
        return None, 0, 0
    w = np.array([len(g) for g in segs], dtype=float)
    vals = np.array([acf(g, nlags=nlags, fft=True) for g in segs])   # min_len > nlags, aman
    return np.average(vals, axis=0, weights=w), len(segs), int(w.sum())
