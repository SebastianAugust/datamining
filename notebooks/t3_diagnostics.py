"""
Tahap 3 langkah 6: diagnostik klaster semu untuk label K-Means final (30 menit).
a. kedekatan waktu (uji permutasi), b. drift (proporsi per bulan + ulang klaster setelah detrend),
c. artefak celah/interpolasi, d. profil klaster.
Tidak membaca machine_status. sensor.csv hanya dibaca untuk menandai sel hasil interpolasi.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import RobustScaler
from t3_common import *

N_PERM = 1000
JARAK_CELAH = 60
DETREND = "7D"

r = build(WINDOW_UTAMA)
lab_df = pd.read_csv(TABLE_DIR / "t3_labels_30m.csv", parse_dates=["mulai"])
assert (lab_df.window_idx.to_numpy() == r["idx"]).all()
sets = {"utama": lab_df["label"].to_numpy()}
if "label_sekunder" in lab_df:
    sets["sekunder"] = lab_df["label_sekunder"].to_numpy()
w, idx, starts = r["w"], r["idx"], pd.DatetimeIndex(r["starts"])
rng = np.random.default_rng(SEED)
out = []


def add(bagian, set_, uraian, nilai):
    out.append(dict(bagian=bagian, label_set=set_, uraian=uraian, nilai=nilai))


# ---------- a. kedekatan waktu ----------
adj = np.diff(idx) == 1                       # pasangan window yang benar-benar bersebelahan
for nm, lab in sets.items():
    same = lambda l: (l[:-1] == l[1:])[adj].mean()
    obs = same(lab)
    perm = np.array([same(rng.permutation(lab)) for _ in range(N_PERM)])
    add("a_waktu", nm, "proporsi pasangan bersebelahan berlabel sama (observasi)", obs)
    add("a_waktu", nm, f"rata-rata {N_PERM} permutasi", perm.mean())
    add("a_waktu", nm, "persentil 95 permutasi", np.percentile(perm, 95))
    add("a_waktu", nm, "p-value (>= observasi)", (1 + (perm >= obs).sum()) / (N_PERM + 1))
    seg = np.concatenate([[0], np.flatnonzero(~adj) + 1, [len(lab)]])           # batas per blok kontigu
    runs = []                                                                    # (label, panjang)
    for a0, a1 in zip(seg[:-1], seg[1:]):
        l = lab[a0:a1]
        b = np.concatenate([[0], np.flatnonzero(l[1:] != l[:-1]) + 1, [len(l)]])
        runs += [(l[s], e - s) for s, e in zip(b[:-1], b[1:])]
    runs = pd.DataFrame(runs, columns=["k", "n"])
    for k, g in runs.groupby("k"):
        add("a_waktu", nm, f"klaster {k}: rata-rata panjang run (window), jumlah run {len(g)}", g.n.mean())

# ---------- b. drift ----------
mon = starts.to_period("M").astype(str)
for nm, lab in sets.items():
    ct = pd.crosstab(mon, lab)
    for m_, row in ct.div(ct.sum(axis=1), axis=0).iterrows():
        for k, v in row.items():
            add("b_drift_bulan", nm, f"{m_} proporsi klaster {k} (n bulan={int(ct.loc[m_].sum())})", v)
    if nm == "utama":
        fig, ax = plt.subplots(figsize=(7, 3.5))
        (ct.div(ct.sum(axis=1), axis=0) * 100).plot.bar(stacked=True, ax=ax, color=PALET[:ct.shape[1]], rot=0)
        ax.set(ylabel="% window", xlabel="bulan", title="Proporsi klaster per bulan")
        ax.legend(title="klaster", bbox_to_anchor=(1, 1)); fig.tight_layout()
        fig.savefig(FIG_DIR / "t3_diag_monthly.png", dpi=150); plt.close(fig)

# detrend: fitur setelah log1p dikurangi median bergulir 7 hari (terpusat) per kolom
tf = r["raw"].copy()
for c in tf.columns:
    if c.endswith(tuple("__" + f for f in LOG_FEATS)):
        tf[c] = np.log1p(tf[c])
tf.index = starts
med = tf.rolling(DETREND, center=True, min_periods=1).median()
Zd = RobustScaler().fit_transform(tf - med)
pd_ = PCA(n_components=VAR_PCA, svd_solver="full", random_state=SEED).fit(Zd)
Pd = pd_.transform(Zd)
add("b_drift_detrend", "-", "komponen PCA 90% setelah detrend", pd_.n_components_)
for nm, lab in sets.items():
    k = len(set(lab))
    ld = fit_kmeans(Pd, k)
    add("b_drift_detrend", nm, f"ARI klaster detrend (K={k}) vs asli", adjusted_rand_score(lab, ld))
    add("b_drift_detrend", nm, "Silhouette klaster detrend", silhouette_score(Pd, ld))

# ---------- c. artefak celah / interpolasi ----------
df = r["df"]
raw_csv = pd.read_csv(BASE_DIR / "data" / "sensor.csv", usecols=["timestamp", *df.columns], parse_dates=["timestamp"])
raw_csv = raw_csv.set_index("timestamp").sort_index().reindex(df.index)
nan_any = df.isna().any(axis=1).to_numpy()
interp_any = (raw_csv.isna() & df.notna()).any(axis=1).to_numpy()
cs = np.concatenate([[0], np.cumsum(nan_any)])
t = np.arange(len(nan_any))
near = (cs[np.minimum(t + JARAK_CELAH + 1, len(nan_any))] - cs[np.maximum(t - JARAK_CELAH, 0)]) > 0   # ada NaN dalam +-60 menit
n_tot = r["n_total"]
f_near = near[: n_tot * w].reshape(n_tot, w).any(axis=1)[idx]
f_int = interp_any[: n_tot * w].reshape(n_tot, w).any(axis=1)[idx]
f_all = f_near | f_int
fl = {"dekat_celah_NaN_<=60mnt": f_near, "mengandung_sel_interpolasi": f_int, "salah_satu": f_all}
add("c_celah", "-", "jumlah window dipertahankan", len(idx))
for nm, lab in sets.items():
    for fn, f in fl.items():
        add("c_celah", nm, f"{fn}: keseluruhan (%)", 100 * f.mean())
        for k in sorted(set(lab)):
            add("c_celah", nm, f"{fn}: klaster {k} (%)", 100 * f[lab == k].mean())
fig, ax = plt.subplots(figsize=(6, 3.5))
lab = sets["utama"]
xs = ["keseluruhan", *[f"klaster {k}" for k in sorted(set(lab))]]
for j, (fn, f) in enumerate(fl.items()):
    vals = [100 * f.mean(), *[100 * f[lab == k].mean() for k in sorted(set(lab))]]
    ax.bar(np.arange(len(xs)) + j * 0.27, vals, 0.27, label=fn, color=PALET[j])
ax.set_xticks(np.arange(len(xs)) + 0.27); ax.set_xticklabels(xs)
ax.set(ylabel="% window", title="Window dekat celah / berisi interpolasi"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG_DIR / "t3_diag_gap.png", dpi=150); plt.close(fig)

# ---------- d. profil klaster ----------
lab = sets["utama"]; ks = sorted(set(lab))
prof = r["raw"].groupby(lab).mean().T
prof.columns = [f"klaster_{k}" for k in ks]
prof.index.name = "fitur"
prof.to_csv(TABLE_DIR / "t3_cluster_profile_features.csv")          # satuan asli, 196 fitur
zm = r["zdf"].groupby(lab).mean()
tot = ((r["zdf"] - r["zdf"].mean()) ** 2).sum()
btw = sum(((zm.loc[k] - r["zdf"].mean()) ** 2) * (lab == k).sum() for k in ks)
eta = (btw / tot).replace([np.inf], np.nan)
eta_s = pd.DataFrame({"eta2": eta}).assign(sensor=lambda d: d.index.str.split("__").str[0])
top = eta_s.groupby("sensor").eta2.max().sort_values(ascending=False).head(10)
rows = []
for s in top.index:
    for f in FEATS:
        c = f"{s}__{f}"
        rows.append(dict(sensor=s, fitur=f, eta2=eta[c], **{f"klaster_{k}": prof.loc[c, f"klaster_{k}"] for k in ks}))
tp = pd.DataFrame(rows)
tp.to_csv(TABLE_DIR / "t3_cluster_top_sensors.csv", index=False)
for s, v in top.items():
    add("d_profil", "utama", f"sensor pembeda (maks eta2 antar 4 fitur): {s}", v)
H = np.array([[zm.loc[k, f"{s}__{f}"] for k in ks] for s in top.index for f in FEATS])
lbl = [f"{s} {f}" for s in top.index for f in FEATS]
fig, ax = plt.subplots(figsize=(4 + len(ks), 11))
im = ax.imshow(np.arcsinh(H), cmap="RdBu_r", vmin=-np.arcsinh(np.abs(H).max()), vmax=np.arcsinh(np.abs(H).max()), aspect="auto")
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        ax.text(j, i, f"{H[i, j]:.2g}", ha="center", va="center", fontsize=7, color="white" if abs(np.arcsinh(H[i, j])) > 4 else "black")
ax.set_xticks(range(len(ks))); ax.set_xticklabels([f"klaster {k}" for k in ks])
ax.set_yticks(range(len(lbl))); ax.set_yticklabels(lbl, fontsize=7)
ax.set_title("Rata-rata fitur terskala per klaster\n(10 sensor paling membedakan; warna = arcsinh, angka = nilai z)", fontsize=9)
fig.colorbar(im, ax=ax, label="arcsinh(z)", shrink=0.5); fig.tight_layout()
fig.savefig(FIG_DIR / "t3_cluster_profile.png", dpi=150); plt.close(fig)

res = pd.DataFrame(out)
res.to_csv(TABLE_DIR / "t3_diagnostics.csv", index=False)
pd.set_option("display.width", 200, "display.max_colwidth", 90)
print(res[~res.bagian.isin(["b_drift_bulan"])].to_string(index=False))
print(res[res.bagian == "b_drift_bulan"].query("label_set=='utama'").to_string(index=False))
print(tp.round(3).to_string(index=False))
