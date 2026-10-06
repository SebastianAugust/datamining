"""
ANALISIS TAMBAHAN PASCA-HASIL: pembanding machine_status untuk label varian A dan B (t3x_labels_30m.csv).
Skrip mandiri (tidak meng-import skrip lain), dijalankan setelah label tersimpan, tanpa tuning ulang.
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
win = pd.DataFrame(dict(idx=np.arange(n), mayoritas=[pd.Series(r).value_counts().idxmax() for r in S],
                        abnormal_min1=[np.isin(r, ["BROKEN", "RECOVERING"]).any() for r in S]))
lab = pd.read_csv(T / "t3x_labels_30m.csv")
d = lab.merge(win, left_on="window_idx", right_on="idx")
assert len(d) == len(lab)

rows = []
cols = [c for c in lab.columns if c in ("label_A", "label_B")]
fig, axs = plt.subplots(1, len(cols), figsize=(4.8 * len(cols), 3.6), squeeze=False)
for ax, col in zip(axs[0], cols):
    ct = pd.crosstab(d[col], d.mayoritas).reindex(columns=STATUS, fill_value=0)
    any_ = pd.crosstab(d[col], d.abnormal_min1).reindex(columns=[False, True], fill_value=0)
    for k, r_ in ct.iterrows():
        rows.append(dict(varian=col[-1], bagian="silang", klaster=k, **{s: int(r_[s]) for s in STATUS},
                         abnormal_min1=int(any_.loc[k, True]), total=int(r_.sum())))
    rows.append(dict(varian=col[-1], bagian="ringkasan", klaster="semua", purity=ct.max(axis=1).sum() / ct.values.sum(),
                     purity_baseline=ct.sum().max() / ct.values.sum(),
                     ARI=adjusted_rand_score(d.mayoritas, d[col]), NMI=normalized_mutual_info_score(d.mayoritas, d[col]),
                     ARI_abnormal_min1=adjusted_rand_score(d.abnormal_min1, d[col]),
                     NMI_abnormal_min1=normalized_mutual_info_score(d.abnormal_min1, d[col])))
    pct = ct.div(ct.sum(axis=1), axis=0) * 100
    ax.imshow(pct.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    for i in range(ct.shape[0]):
        for j in range(3):
            ax.text(j, i, f"{ct.values[i, j]}\n({pct.values[i, j]:.1f}%)", ha="center", va="center", fontsize=8,
                    color="white" if pct.values[i, j] > 60 else "black")
    ax.set_xticks(range(3)); ax.set_xticklabels(STATUS)
    ax.set_yticks(range(ct.shape[0])); ax.set_yticklabels([f"klaster {k}" for k in ct.index])
    ax.set_title(f"Varian {col[-1]}", fontsize=9)
fig.suptitle("[Analisis tambahan pasca-hasil] Klaster x status mayoritas (BROKEN 7 menit: jangan dibaca)", fontsize=9)
fig.tight_layout(); fig.savefig(F / "t3x_cluster_vs_status.png", dpi=150); plt.close(fig)
res = pd.DataFrame(rows)
res.to_csv(T / "t3x_cluster_vs_status.csv", index=False)
pd.set_option("display.width", 220)
print(res.round(4).to_string(index=False))
