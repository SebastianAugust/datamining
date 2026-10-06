"""
ANALISIS TAMBAHAN PASCA-HASIL (di luar spesifikasi awal). Varian ini dipilih SETELAH melihat hasil
utama (PCA 1 komponen), sehingga tidak boleh menggantikan hasil utama (t3_*).
Pipeline sama persis (window 30 mnt, tau 0,20, 196 fitur, log1p, PCA 90%, K-Means K=2..10,
aturan K dan stabilitas yang sama), kecuali langkah penskalaan:
  A: winsorizing tiap fitur (setelah log1p) di persentil 1 dan 99, lalu RobustScaler
  B: QuantileTransformer(output_distribution="normal") sebagai pengganti RobustScaler
Tidak membaca machine_status. Tidak mengubah skrip/output t3_.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import QuantileTransformer, RobustScaler
from t3_common import *
from t3_kmeans import analisis

TAG = "[Analisis tambahan pasca-hasil]"
DETREND = "7D"


def transform(tf: pd.DataFrame, varian: str) -> np.ndarray:
    """tf = fitur setelah log1p (std, dstd)."""
    if varian == "A":
        lo, hi = tf.quantile(0.01), tf.quantile(0.99)
        return RobustScaler().fit_transform(tf.clip(lo, hi, axis=1))
    return QuantileTransformer(output_distribution="normal", n_quantiles=min(1000, len(tf)),
                               random_state=SEED).fit_transform(tf)


def pca90(Z):
    p = PCA(n_components=VAR_PCA, svd_solver="full", random_state=SEED).fit(Z)
    return p, p.transform(Z)


r = build(WINDOW_UTAMA)                       # hanya untuk window, fitur mentah, dan waktu
starts = pd.DatetimeIndex(r["starts"])
main = pd.read_csv(TABLE_DIR / "t3_labels_30m.csv", parse_dates=["mulai"])
assert (main.window_idx.to_numpy() == r["idx"]).all()
tf = r["raw"].copy()
for c in tf.columns:
    if c.endswith(tuple("__" + f for f in LOG_FEATS)):
        tf[c] = np.log1p(tf[c])
med = tf.set_axis(starts).rolling(DETREND, center=True, min_periods=1).median().to_numpy()
mon = starts.to_period("M").astype(str)

summ, topf, monthly, labels = [], [], [], pd.DataFrame(dict(mulai=r["starts"], window_idx=r["idx"]))
fig, axs = plt.subplots(2, 2, figsize=(11, 7))
fig2, axt = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
for row, v in enumerate("AB"):
    Z = transform(tf, v)
    pca, P = pca90(Z)
    r_v = dict(P=P)
    a = analisis(r_v)
    k = a["K"]
    m = a["metrics"].copy()
    m["kandidat"] = m.frac_min >= MIN_FRAC_KLASTER
    m["terpilih"] = m.K == k
    m.to_csv(TABLE_DIR / f"t3x_varian{v}_kmeans_metrics.csv", index=False)
    a["stab"].assign(varian=v).to_csv(TABLE_DIR / f"t3x_varian{v}_stability.csv", index=False)
    lab = a["labels"]
    labels[f"label_{v}"] = lab
    if a["K_sekunder"]:
        labels[f"label_{v}_sekunder"] = a["labels_sekunder"]
    # 10 fitur dengan kontribusi varians terbesar (varians kolom terskala / total)
    var = Z.var(axis=0)
    sh = pd.Series(var / var.sum(), index=r["raw"].columns).sort_values(ascending=False)
    for i, (c, s) in enumerate(sh.head(10).items(), 1):
        topf.append(dict(varian=v, peringkat=i, fitur=c, kontribusi_varians=s))
    # proporsi klaster per bulan
    ct = pd.crosstab(mon, lab)
    for mo, rw in ct.div(ct.sum(axis=1), axis=0).iterrows():
        for kk, val in rw.items():
            monthly.append(dict(varian=v, bulan=mo, klaster=kk, proporsi=val, n_window_bulan=int(ct.loc[mo].sum())))
    # detrend (fitur setelah log1p dikurangi median bergulir 7 hari), lalu transformasi varian yang sama
    pdt, Pd = pca90(transform(pd.DataFrame(tf.to_numpy() - med, columns=tf.columns), v))
    ld = fit_kmeans(Pd, k)
    ari_main = adjusted_rand_score(main.label, lab)
    st = a["stab"].ARI
    summ.append(dict(varian=v, komponen_pca=pca.n_components_, varians_pc1=pca.explained_variance_ratio_[0],
                     varians_kumulatif=pca.explained_variance_ratio_.sum(), K_terpilih=k,
                     K_elbow=a["K_elbow"], K_dbi_terbaik=a["K_dbi"], K_sekunder=a["K_sekunder"],
                     silhouette_terpilih=m.set_index("K").Silhouette[k], dbi_terpilih=m.set_index("K").DBI[k],
                     ukuran_klaster=str(sorted(np.bincount(lab).tolist(), reverse=True)),
                     ukuran_min_persen=round(100 * m.set_index("K").frac_min[k], 2),
                     silhouette_terbaik=a["sil_terbaik"], struktur_lemah=a["lemah"],
                     ARI_stab_rata2=st.mean(), ARI_stab_min=st.min(), stabil=bool(st.mean() >= ARI_STABIL),
                     ARI_vs_label_utama=ari_main, komponen_pca_detrend=pdt.n_components_,
                     ARI_detrend_vs_varian=adjusted_rand_score(lab, ld)))
    # gambar
    axs[row, 0].plot(m.K, m.Silhouette, "o-", color=PALET[0]); axs[row, 0].axvline(k, ls="--", color=PALET[4])
    axs[row, 0].axhline(SIL_LEMAH, ls=":", color="gray")
    axs[row, 0].set(title=f"Varian {v}: Silhouette (K terpilih = {k})", xlabel="K")
    axs[row, 1].plot(m.K, m.DBI, "o-", color=PALET[1]); axs[row, 1].axvline(k, ls="--", color=PALET[4])
    axs[row, 1].set(title=f"Varian {v}: Davies-Bouldin", xlabel="K")
    for c in range(k):
        s = lab == c
        axt[row].scatter(starts[s], np.full(s.sum(), c), s=4, color=PALET[c])
    axt[row].set(yticks=range(k), yticklabels=[f"klaster {c}" for c in range(k)], title=f"Varian {v}: label sepanjang waktu")
fig.suptitle(f"{TAG} Silhouette dan DBI, window 30 menit", fontsize=10); fig.tight_layout()
fig.savefig(FIG_DIR / "t3x_silhouette_dbi.png", dpi=150)
fig2.suptitle(f"{TAG} Label klaster sepanjang waktu", fontsize=10); fig2.tight_layout()
fig2.savefig(FIG_DIR / "t3x_cluster_timeline.png", dpi=150)

pd.DataFrame(summ).to_csv(TABLE_DIR / "t3x_variants_summary.csv", index=False)
pd.DataFrame(topf).to_csv(TABLE_DIR / "t3x_top_features.csv", index=False)
pd.DataFrame(monthly).to_csv(TABLE_DIR / "t3x_monthly.csv", index=False)
labels.to_csv(TABLE_DIR / "t3x_labels_30m.csv", index=False)
pd.set_option("display.width", 220)
print(pd.DataFrame(summ).round(4).T.to_string())
print(pd.DataFrame(topf).round(3).to_string(index=False))
for v in "AB":
    print(pd.read_csv(TABLE_DIR / f"t3x_varian{v}_kmeans_metrics.csv").round(4).to_string(index=False))
