"""
Tahap 3 langkah 1: windowing (tidak tumpang tindih, jangkar 2018-04-01 00:00).
Retensi untuk tau = 0 / 0,20 / 0,50 dan window 15 / 30 / 60 menit; daftar window dibuang
(window utama 30 menit, tau 0,20).
"""
import numpy as np
import pandas as pd
from t3_common import *

df = load_clean()
rows, dropped = [], None
for w in (WINDOW_UTAMA, *WINDOW_SENSITIVITAS):
    x, n = to_windows(df, w)
    nan_cnt = np.isnan(x).sum(axis=1)                       # (n, sensor)
    for tau in (0.0, 0.20, 0.50):
        keep = ~(nan_cnt > tau * w + 1e-9).any(axis=1)
        rows.append(dict(window_menit=w, tau=tau, total=n, dipertahankan=int(keep.sum()),
                         dibuang=int((~keep).sum()), persen_dipertahankan=round(100 * keep.mean(), 2),
                         utama=(w == WINDOW_UTAMA and tau == TAU)))
    if w == WINDOW_UTAMA:
        keep = ~(nan_cnt > TAU * w + 1e-9).any(axis=1)
        i = np.flatnonzero(~keep)
        worst = nan_cnt[i].max(axis=1) / w
        dropped = pd.DataFrame(dict(
            window_idx=i, mulai=ANCHOR + pd.to_timedelta(i * w, unit="min"),
            selesai=ANCHOR + pd.to_timedelta((i + 1) * w - 1, unit="min"),
            n_sensor_melebihi_tau=(nan_cnt[i] > TAU * w + 1e-9).sum(axis=1),
            frac_nan_maks=worst.round(3)))

ret = pd.DataFrame(rows)
ret.to_csv(TABLE_DIR / "t3_window_retention.csv", index=False)
dropped.to_csv(TABLE_DIR / "t3_windows_dropped.csv", index=False)
print(ret.to_string(index=False))
print(f"\nWindow dibuang (30 mnt, tau 0,20): {len(dropped)}")
