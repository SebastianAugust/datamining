"""
Tahap 3 langkah 5: ulangi langkah 1-3 untuk window 15 dan 60 menit.
Silhouette/DBI antar ukuran window tidak sebanding, jadi tidak dipakai untuk memilih window.
Dibandingkan: K terpilih dan ARI label (dipetakan ke menit) terhadap hasil 30 menit.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from t3_common import *
from t3_kmeans import analisis

r30 = build(WINDOW_UTAMA)
lab30 = pd.read_csv(TABLE_DIR / "t3_labels_30m.csv")["label"].to_numpy()
m30 = label_per_menit(r30, lab30)

rows = []
for w in (WINDOW_UTAMA, *WINDOW_SENSITIVITAS):
    r = r30 if w == WINDOW_UTAMA else build(w)
    a = analisis(r)
    if w != WINDOW_UTAMA:
        a["metrics"].to_csv(TABLE_DIR / f"t3_kmeans_metrics_{w}m.csv", index=False)
    mm = label_per_menit(r, a["labels"])
    both = ~np.isnan(m30) & ~np.isnan(mm)
    mk = a["metrics"].set_index("K")
    rows.append(dict(window_menit=w, window_dipertahankan=len(r["idx"]), window_total=r["n_total"],
                     komponen_pca=r["ncomp"], K_terpilih=a["K"], K_sekunder=a["K_sekunder"],
                     K_elbow=a["K_elbow"], K_dbi_terbaik=a["K_dbi"],
                     silhouette_K_terpilih=mk.Silhouette[a["K"]], dbi_K_terpilih=mk.DBI[a["K"]],
                     ukuran_klaster_min_persen=round(100 * mk.frac_min[a["K"]], 2),
                     ARI_stabilitas_rata2=a["stab"].ARI.mean(), ARI_stabilitas_min=a["stab"].ARI.min(),
                     menit_dibandingkan=int(both.sum()),
                     ARI_vs_30m_menit=adjusted_rand_score(m30[both], mm[both])))
res = pd.DataFrame(rows)
res.to_csv(TABLE_DIR / "t3_window_sensitivity.csv", index=False)
print(res.round(4).T.to_string())
