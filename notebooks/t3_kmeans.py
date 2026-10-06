"""
Tahap 3 langkah 3: K-Means K=2..10 di ruang PCA 90%, pemilihan K menurut aturan tetap,
stabilitas 10 seed. Fungsi analisis dipakai juga oleh t3_sensitivity.py.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from t3_common import *


def analisis(r: dict) -> dict:
    """Aturan: kandidat (klaster min >= 1%) -> Silhouette tertinggi; elbow & DBI hanya konfirmasi."""
    m = kmeans_sweep(r["P"])
    k = pilih_k(m)
    out = dict(metrics=m, K=k, K_elbow=int(m.K.iloc[lutut(m.WCSS.values)]),
               K_dbi=int(m.loc[m.DBI.idxmin(), "K"]))
    out["K_sekunder"] = pilih_k(m, 3) if k == 2 else None
    out["lemah"] = bool(m.Silhouette.max() < SIL_LEMAH)
    out["sil_terbaik"] = float(m.Silhouette.max())
    if k is not None:
        out["labels"] = fit_kmeans(r["P"], k)
        out["stab"] = stabilitas(r["P"], k)
        if out["K_sekunder"]:
            out["labels_sekunder"] = fit_kmeans(r["P"], out["K_sekunder"])
    return out


if __name__ == "__main__":
    r = build(WINDOW_UTAMA)
    a = analisis(r)
    m = a["metrics"].copy()
    m["kandidat"] = m.frac_min >= MIN_FRAC_KLASTER
    m["terpilih"] = m.K == a["K"]
    m.to_csv(TABLE_DIR / "t3_kmeans_metrics.csv", index=False)
    a["stab"].to_csv(TABLE_DIR / "t3_kmeans_stability.csv", index=False)

    lab = pd.DataFrame(dict(mulai=r["starts"], window_idx=r["idx"], label=a["labels"]))
    if a["K_sekunder"]:
        lab["label_sekunder"] = a["labels_sekunder"]
    lab.to_csv(TABLE_DIR / "t3_labels_30m.csv", index=False)

    # Elbow
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(m.K, m.WCSS, "o-", color=PALET[0])
    ax.axvline(a["K"], ls="--", color=PALET[4], label=f"K terpilih = {a['K']}")
    ax.set(xlabel="K", ylabel="WCSS", title="Elbow (K-Means, PCA 90%, window 30 menit)")
    ax.legend(); fig.tight_layout(); fig.savefig(FIG_DIR / "t3_elbow.png", dpi=150); plt.close(fig)

    # Silhouette & DBI
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    axs[0].plot(m.K, m.Silhouette, "o-", color=PALET[0])
    axs[0].axhline(SIL_LEMAH, ls=":", color="gray", label=f"ambang lemah {SIL_LEMAH}")
    axs[0].set(xlabel="K", ylabel="Silhouette", title="Silhouette (lebih tinggi lebih baik)")
    axs[1].plot(m.K, m.DBI, "o-", color=PALET[1])
    axs[1].set(xlabel="K", ylabel="Davies-Bouldin", title="DBI (lebih rendah lebih baik)")
    for ax in axs:
        ax.axvline(a["K"], ls="--", color=PALET[4])
    axs[0].legend(); fig.tight_layout(); fig.savefig(FIG_DIR / "t3_silhouette_dbi.png", dpi=150); plt.close(fig)

    # Sebaran PCA 2D
    V2 = PCA(n_components=2, random_state=SEED).fit_transform(r["Z"])
    fig, ax = plt.subplots(figsize=(6, 5))
    for c in range(a["K"]):
        s = a["labels"] == c
        ax.scatter(V2[s, 0], V2[s, 1], s=6, alpha=.6, color=PALET[c], label=f"klaster {c} (n={s.sum()})")
    ax.set(xlabel="PC1", ylabel="PC2", title=f"K-Means K={a['K']} pada PCA 2D (visualisasi saja)")
    ax.legend(markerscale=2); fig.tight_layout(); fig.savefig(FIG_DIR / "t3_pca_scatter_kmeans.png", dpi=150); plt.close(fig)

    # Linimasa label
    fig, ax = plt.subplots(figsize=(12, 2.8))
    for c in range(a["K"]):
        s = a["labels"] == c
        ax.scatter(r["starts"][s], np.full(s.sum(), c), s=4, color=PALET[c])
    ax.set(yticks=range(a["K"]), yticklabels=[f"klaster {c}" for c in range(a["K"])],
           title="Label klaster sepanjang waktu (celah = window dibuang)")
    fig.tight_layout(); fig.savefig(FIG_DIR / "t3_cluster_timeline.png", dpi=150); plt.close(fig)

    print(m.round(4).to_string(index=False))
    print(f"\nK terpilih (aturan a-b) : {a['K']}")
    print(f"K elbow (lutut) {a['K_elbow']}, K DBI-terbaik {a['K_dbi']}")
    print(f"K sekunder (>=3)        : {a['K_sekunder']}")
    print(f"Silhouette terbaik {a['sil_terbaik']:.4f} -> struktur lemah: {a['lemah']}")
    st = a["stab"].ARI
    print(f"Stabilitas ARI rata-rata {st.mean():.4f}, min {st.min():.4f}, stabil: {st.mean() >= ARI_STABIL}")
