"""
Tahap 3 langkah 7: pembanding machine_status (SATU-SATUNYA skrip Tahap 3 yang membaca kolom ini).
Berdiri sendiri: tidak meng-import skrip lain dan tidak di-import siapa pun. Dijalankan SETELAH label
K-Means final tersimpan; hasilnya tidak dipakai untuk tuning apa pun.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

BASE = Path(__file__).resolve().parent.parent
T, F = BASE / "outputs" / "tables", BASE / "outputs" / "figures"
ANCHOR, W = pd.Timestamp("2018-04-01 00:00"), 30
STATUS = ["NORMAL", "RECOVERING", "BROKEN"]

st = pd.read_csv(BASE / "data" / "sensor.csv", usecols=["timestamp", "machine_status"], parse_dates=["timestamp"])
st = st.drop_duplicates("timestamp").set_index("timestamp").sort_index().reindex(
    pd.date_range(ANCHOR, "2018-08-31 23:59", freq="min"))["machine_status"]
n = len(st) // W
S = st.to_numpy()[: n * W].reshape(n, W)
maj = np.array([pd.Series(r).value_counts().idxmax() for r in S])        # status mayoritas per window
abn = np.array([np.isin(r, ["BROKEN", "RECOVERING"]).any() for r in S])  # >= 1 menit BROKEN/RECOVERING
win = pd.DataFrame(dict(idx=np.arange(n), mayoritas=maj, abnormal_min1=abn))

lab = pd.read_csv(T / "t3_labels_30m.csv")
d = lab.merge(win, left_on="window_idx", right_on="idx")
assert len(d) == len(lab)

rows = []
sets = {"utama": "label"} | ({"sekunder": "label_sekunder"} if "label_sekunder" in lab else {})
fig, axs = plt.subplots(1, len(sets), figsize=(4.5 * len(sets), 3.6), squeeze=False)
for ax, (nm, col) in zip(axs[0], sets.items()):
    ct = pd.crosstab(d[col], d.mayoritas).reindex(columns=STATUS, fill_value=0)
    ct_any = pd.crosstab(d[col], d.abnormal_min1).reindex(columns=[False, True], fill_value=0)
    purity = ct.max(axis=1).sum() / ct.values.sum()
    ari, nmi = adjusted_rand_score(d.mayoritas, d[col]), normalized_mutual_info_score(d.mayoritas, d[col])
    base_purity = ct.sum().max() / ct.values.sum()
    for k, r_ in ct.iterrows():
        rows.append(dict(label_set=nm, bagian="silang_klaster_x_status_mayoritas", klaster=k,
                         **{s: int(r_[s]) for s in STATUS},
                         abnormal_min1=int(ct_any.loc[k, True]), total=int(r_.sum())))
    rows += [dict(label_set=nm, bagian="ringkasan", klaster="semua", purity=purity,
                  purity_baseline_semua_ke_status_terbanyak=base_purity, ARI=ari, NMI=nmi,
                  ARI_abnormal_min1=adjusted_rand_score(d.abnormal_min1, d[col]),
                  NMI_abnormal_min1=normalized_mutual_info_score(d.abnormal_min1, d[col]))]
    pct = ct.div(ct.sum(axis=1), axis=0) * 100
    im = ax.imshow(pct.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i in range(ct.shape[0]):
        for j in range(3):
            ax.text(j, i, f"{ct.values[i, j]}\n({pct.values[i, j]:.1f}%)", ha="center", va="center", fontsize=8,
                    color="white" if pct.values[i, j] > 60 else "black")
    ax.set_xticks(range(3)); ax.set_xticklabels(STATUS)
    ax.set_yticks(range(ct.shape[0])); ax.set_yticklabels([f"klaster {k}" for k in ct.index])
    ax.set_title(f"Klaster ({nm}) x status mayoritas\nBROKEN hanya 7 menit: jangan dibaca", fontsize=9)
fig.tight_layout(); fig.savefig(F / "t3_cluster_vs_status.png", dpi=150); plt.close(fig)

# window yang dibuang di langkah 1
dr = pd.read_csv(T / "t3_windows_dropped.csv")
dd = win.merge(dr[["window_idx"]], left_on="idx", right_on="window_idx")
cnt = dd.mayoritas.value_counts().reindex(STATUS, fill_value=0)
rows.append(dict(label_set="-", bagian="window_dibuang_status_mayoritas", klaster="dibuang", total=len(dd),
                 **{s: int(cnt[s]) for s in STATUS}, abnormal_min1=int(dd.abnormal_min1.sum())))
kept = win[~win.idx.isin(dr.window_idx)]
ck = kept.mayoritas.value_counts().reindex(STATUS, fill_value=0)
rows.append(dict(label_set="-", bagian="window_dipertahankan_status_mayoritas", klaster="dipertahankan",
                 total=len(kept), **{s: int(ck[s]) for s in STATUS}, abnormal_min1=int(kept.abnormal_min1.sum())))
menit_dr = np.concatenate([S[i] for i in dd.idx])
rows.append(dict(label_set="-", bagian="window_dibuang_status_per_menit", klaster="dibuang", total=len(menit_dr),
                 **{s: int((menit_dr == s).sum()) for s in STATUS}))

res = pd.DataFrame(rows)
res.to_csv(T / "t3_cluster_vs_status.csv", index=False)
pd.set_option("display.width", 220)
print(res.round(4).to_string(index=False))
