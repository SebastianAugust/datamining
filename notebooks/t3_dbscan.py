"""
Tahap 3 langkah 4: DBSCAN sebagai pembanding (ruang PCA 90% yang sama).
eps = lutut kurva k-distance (k = min_samples, titik itu sendiri dihitung seperti pada definisi
inti DBSCAN). Lutut = titik terjauh dari garis ujung-ke-ujung (t3_common.lutut).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from t3_common import *

r = build(WINDOW_UTAMA)
P = r["P"]
km = pd.read_csv(TABLE_DIR / "t3_labels_30m.csv")["label"].to_numpy()
ms_list = sorted({5, 10, 2 * r["ncomp"]})

rows = []
fig, axs = plt.subplots(1, len(ms_list), figsize=(4.5 * len(ms_list), 3.8), squeeze=False)
for ax, ms in zip(axs[0], ms_list):
    kd = np.sort(NearestNeighbors(n_neighbors=ms).fit(P).kneighbors(P)[0][:, -1])
    i = lutut(kd)
    eps = float(kd[i])
    ax.plot(kd, color=PALET[0]); ax.axhline(eps, ls="--", color=PALET[4], label=f"eps = {eps:.3g}")
    ax.set(xlabel="titik (urut)", ylabel=f"jarak ke tetangga ke-{ms}", title=f"k-distance, min_samples={ms}")
    ax.legend()
    lab = DBSCAN(eps=eps, min_samples=ms).fit_predict(P)
    nz = lab != -1
    ncl = len(set(lab[nz]))
    sil = dbi = np.nan
    if ncl >= 2:
        sil = silhouette_score(P[nz], lab[nz]); dbi = davies_bouldin_score(P[nz], lab[nz])
    rows.append(dict(min_samples=ms, eps=eps, n_klaster=ncl, persen_noise=round(100 * (~nz).mean(), 2),
                     silhouette_tanpa_noise=sil, dbi_tanpa_noise=dbi,
                     ukuran_klaster=str(sorted(np.bincount(lab[nz]).tolist(), reverse=True)[:10]) if ncl else "",
                     ARI_vs_kmeans_noise_sbg_label=adjusted_rand_score(km, lab),
                     ARI_vs_kmeans_tanpa_noise=adjusted_rand_score(km[nz], lab[nz]) if ncl >= 1 and nz.sum() > 1 else np.nan))
fig.tight_layout(); fig.savefig(FIG_DIR / "t3_kdistance.png", dpi=150); plt.close(fig)

res = pd.DataFrame(rows)
res.to_csv(TABLE_DIR / "t3_dbscan_results.csv", index=False)
print(res.round(4).to_string(index=False))
