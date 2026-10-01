"""
ANALISIS PEMBANDING (terpisah dari pipeline).
Persentase data kosong per sensor per machine_status. TIDAK dipakai untuk keputusan cleaning
dan TIDAK di-import oleh script lain. Satu-satunya tempat machine_status dibaca.

Cara pakai:  python notebooks/compare_missing_vs_status.py
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TABLE_DIR = BASE_DIR / "outputs" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(BASE_DIR / "data" / "sensor.csv")
sensors = [c for c in df.columns if c.startswith('sensor_')]

pct = df[sensors].isna().groupby(df['machine_status']).mean().mul(100).round(3)
out = pct.T.rename_axis('sensor').reset_index()
out.columns.name = None
out = out.rename(columns={s: f'pct_kosong_{s}' for s in pct.index})
out['keterangan'] = "Analisis pembanding. Tidak dipakai untuk keputusan cleaning."
out.to_csv(TABLE_DIR / "missing_vs_status_comparison.csv", index=False)
print(df['machine_status'].value_counts().to_string())
print(out.sort_values(out.columns[1], ascending=False).head(10).to_string(index=False))
