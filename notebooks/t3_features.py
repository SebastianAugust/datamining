"""
Tahap 3 langkah 2: 4 fitur x 49 sensor per window (30 menit, tau 0,20),
log1p (std, dstd), RobustScaler, PCA 90%.
"""
import numpy as np
import pandas as pd
from t3_common import *

r = build(WINDOW_UTAMA)
pca = r["pca"]
var = pd.DataFrame(dict(komponen=np.arange(1, len(pca.explained_variance_ratio_) + 1),
                        varians=pca.explained_variance_ratio_,
                        kumulatif=np.cumsum(pca.explained_variance_ratio_)))
var.to_csv(TABLE_DIR / "t3_pca_variance.csv", index=False)

feat = r["raw"].copy()
feat.insert(0, "mulai", r["starts"])
feat.to_csv(BASE_DIR / "data" / "t3_features_30m.csv", index=False)   # tidak di-commit (.gitignore)

print(f"Window dipertahankan : {len(r['idx'])} dari {r['n_total']}")
print(f"Fitur                : {r['raw'].shape[1]}")
print(f"Komponen PCA (90%)   : {r['ncomp']}  (kumulatif {var.kumulatif.iloc[-1]:.4f})")
print("Varians per komponen :", var.varians.round(4).tolist()[:5])
