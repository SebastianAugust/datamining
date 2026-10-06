"""
Tahap 3: fungsi bersama (windowing, fitur, praproses, pemilihan K).
TIDAK membaca machine_status. Input satu-satunya: data/cleaned_sensor_v2.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import RobustScaler

BASE_DIR = Path(__file__).resolve().parent.parent
CLEANED = BASE_DIR / "data" / "cleaned_sensor_v2.csv"
TABLE_DIR = BASE_DIR / "outputs" / "tables"
FIG_DIR = BASE_DIR / "outputs" / "figures"
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Parameter yang ditetapkan sebelum melihat hasil
ANCHOR = pd.Timestamp("2018-04-01 00:00")
WINDOW_UTAMA = 30
WINDOW_SENSITIVITAS = (15, 60)
TAU = 0.20
SEED = 42
VAR_PCA = 0.90
K_RANGE = range(2, 11)
MIN_FRAC_KLASTER = 0.01
SIL_LEMAH = 0.25
ARI_STABIL = 0.80
FEATS = ["mean", "std", "slope", "dstd"]
LOG_FEATS = ("std", "dstd")
PALET = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442", "#000000",
         "#999999", "#8C564B"]


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CLEANED, parse_dates=["timestamp"]).set_index("timestamp")
    assert df.index[0] == ANCHOR, "grid tidak mulai dari jangkar"
    assert (df.index.to_series().diff().dropna() == pd.Timedelta("1min")).all()
    assert not any(c in df.columns for c in ("machine_status", "Unnamed: 0"))
    return df


def to_windows(df: pd.DataFrame, w: int):
    """Array (n_window, w, n_sensor); baris sisa yang tidak membentuk window penuh tidak dipakai."""
    n = len(df) // w
    return df.to_numpy()[: n * w].reshape(n, w, df.shape[1]), n


def keep_mask(x: np.ndarray, tau: float) -> np.ndarray:
    """True jika TIDAK ada sensor dengan NaN > tau di window itu (tau=0,2 -> tepat 20% masih lolos)."""
    w = x.shape[1]
    return ~(np.isnan(x).sum(axis=1) > tau * w + 1e-9).any(axis=1)


def compute_features(x: np.ndarray) -> np.ndarray:
    """4 fitur per sensor dari nilai tersedia: (n, 4, n_sensor) urutan FEATS."""
    w = x.shape[1]
    m = ~np.isnan(x)
    cnt = m.sum(axis=1)
    mean = np.where(m, x, 0).sum(axis=1) / cnt
    dev = np.where(m, x - mean[:, None, :], 0)
    std = np.sqrt((dev ** 2).sum(axis=1) / cnt)
    t = np.arange(w, dtype=float)[None, :, None]
    tc = np.where(m, t - (t * m).sum(axis=1, keepdims=True) / cnt[:, None, :], 0)
    slope = (tc * dev).sum(axis=1) / (tc ** 2).sum(axis=1)       # satuan per menit
    d = np.diff(x, axis=1)                                      # NaN jika salah satu menit kosong
    dm = ~np.isnan(d)
    dcnt = dm.sum(axis=1)
    dmean = np.where(dm, d, 0).sum(axis=1) / dcnt
    dstd = np.sqrt((np.where(dm, d - dmean[:, None, :], 0) ** 2).sum(axis=1) / dcnt)
    return np.stack([mean, std, slope, dstd], axis=1)


def build(w: int, tau: float = TAU, df: pd.DataFrame | None = None) -> dict:
    """Windowing + fitur + praproses + PCA 90%. Mengembalikan semua yang dibutuhkan skrip lain."""
    if df is None:
        df = load_clean()
    x, n = to_windows(df, w)
    keep = keep_mask(x, tau)
    idx = np.flatnonzero(keep)
    f = compute_features(x[idx])                                 # (n_keep, 4, S)
    sensors = list(df.columns)
    cols = [f"{s}__{ft}" for s in sensors for ft in FEATS]
    raw = pd.DataFrame(f.transpose(0, 2, 1).reshape(len(idx), -1), columns=cols)
    out = preprocess(raw)
    out.update(w=w, tau=tau, n_total=n, idx=idx, keep=keep, sensors=sensors, raw=raw,
               starts=ANCHOR + pd.to_timedelta(idx * w, unit="min"), df=df)
    return out


def preprocess(raw: pd.DataFrame) -> dict:
    """log1p (std, dstd) -> RobustScaler -> PCA 90%."""
    tf = raw.copy()
    for c in tf.columns:
        if c.endswith(tuple("__" + f for f in LOG_FEATS)):
            tf[c] = np.log1p(tf[c])
    Z = RobustScaler().fit_transform(tf)
    pca = PCA(n_components=VAR_PCA, svd_solver="full", random_state=SEED).fit(Z)
    return dict(Z=Z, pca=pca, P=pca.transform(Z), ncomp=pca.n_components_,
                zdf=pd.DataFrame(Z, columns=raw.columns))


def kmeans_sweep(P: np.ndarray) -> pd.DataFrame:
    n = len(P)
    ss = 10000 if n > 20000 else None
    rows = []
    for k in K_RANGE:
        km = KMeans(k, n_init=10, random_state=SEED).fit(P)
        sizes = np.bincount(km.labels_, minlength=k)
        rows.append(dict(K=k, WCSS=km.inertia_,
                         Silhouette=silhouette_score(P, km.labels_, sample_size=ss, random_state=SEED),
                         DBI=davies_bouldin_score(P, km.labels_),
                         ukuran_min=int(sizes.min()), frac_min=sizes.min() / n))
    return pd.DataFrame(rows)


def pilih_k(m: pd.DataFrame, k_min: int = 2):
    """Aturan a-b: kandidat = klaster terkecil >= 1%, lalu Silhouette tertinggi. None jika tak ada."""
    c = m[(m.frac_min >= MIN_FRAC_KLASTER) & (m.K >= k_min)]
    return None if c.empty else int(c.loc[c.Silhouette.idxmax(), "K"])


def lutut(y: np.ndarray) -> int:
    """Indeks lutut: titik dengan jarak terjauh dari garis lurus ujung-ke-ujung (kurva dinormalisasi)."""
    y = np.asarray(y, float)
    x = np.linspace(0, 1, len(y))
    yn = (y - y.min()) / (y.max() - y.min())
    d = np.abs((yn[-1] - yn[0]) * x - (x[-1] - x[0]) * (yn - yn[0]) + x[-1] * yn[0] - yn[-1] * x[0])
    return int(np.argmax(d))


def fit_kmeans(P: np.ndarray, k: int, seed: int = SEED) -> np.ndarray:
    return KMeans(k, n_init=10, random_state=seed).fit_predict(P)


def stabilitas(P: np.ndarray, k: int, seeds=range(10)) -> pd.DataFrame:
    labs = {s: fit_kmeans(P, k, s) for s in seeds}
    ss = list(labs)
    return pd.DataFrame([dict(seed_a=a, seed_b=b, ARI=adjusted_rand_score(labs[a], labs[b]))
                         for i, a in enumerate(ss) for b in ss[i + 1:]])


def label_per_menit(res: dict, labels: np.ndarray) -> np.ndarray:
    """Label window dipetakan ke tiap menit di dalam window (menit lain = NaN)."""
    a = np.full((res["n_total"], res["w"]), np.nan)
    a[res["idx"]] = np.asarray(labels, float)[:, None]
    return a.ravel()
