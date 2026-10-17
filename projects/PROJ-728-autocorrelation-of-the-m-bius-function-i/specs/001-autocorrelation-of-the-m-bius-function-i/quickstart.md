# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites

- Python 3.11 or newer
- `git` (to clone the repository)
- At least **500 MB** free disk space
- Internet connection (to fetch Python packages)

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-org/autocorr-mobius.git
   cd autocorr-mobius
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install exact dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   `requirements.txt` pins versions (e.g., `numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.9.0`, `pytest==8.2.2`).

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following stages in order:

1. **Sieve** – generates `data/raw/mobius_array.npy`.  
2. **Window sampling** – creates 20 stratified windows per L (seed=20231017).  
3. **Autocorrelation** – computes all lags h ≤ L/2.  
4. **Permutation test** – 1,000 block‑permutations per window (inline with sensitivity analysis).  
5. **Multiple‑comparison correction** – Benjamini‑Hochberg FDR at α=0.05.  
6. **Uniformity validation** – Kolmogorov‑Smirnov test.  
7. **Visualization** – heatmaps saved as PNGs.  
8. **CSV/JSON output** – written to `data/processed/`.

### Expected Outputs

| Path | Description |
|------|-------------|
| `data/raw/mobius_array.npy` | Deterministic Möbius sequence (int8). |
| `data/processed/autocorrelation_stats.csv` | Table of all statistics (see `contracts/mobius_stats.schema.yaml`). |
| `data/processed/uniformity_test.json` | KS test result for p‑value uniformity. |
| `outputs/figures/heatmap_L1000.png` | Heatmap for L = 10³. |
| `outputs/figures/heatmap_L10000.png` | Heatmap for L = 10⁴. |
| `outputs/figures/heatmap_L100000.png` | Heatmap for L = 10⁵. |

## Running Individual Stages

- **Generate Möbius array only**  
  ```bash
  python code/sieve.py --output data/raw/mobius_array.npy
  ```

- **Compute autocorrelations only** (requires the Möbius array)  
  ```bash
  python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv
  ```

- **Run permutation test and sensitivity analysis only** (needs the CSV from the previous step)  
  ```bash
  python code/permutation.py --stats data/processed/autocorrelation_stats.csv --array data/raw/mobius_array.npy
  ```

- **Create visualisations only**  
  ```bash
  python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/
  ```

## Verification Steps

1. **Check Möbius array values**  
   ```bash
   python - <<'PY'
   import numpy as np
   arr = np.load('data/raw/mobius_array.npy')
   print('Unique values:', np.unique(arr))
   print('Array shape:', arr.shape)
   PY
   ```
   Expected output: `Unique values: [-1  0  1]` and `Array shape: (10000000,)`.

2. **Run unit tests**  
   ```bash
   pytest tests/unit/ -v
   ```

3. **Run integration test** (full pipeline sanity check, uses a reduced N=10⁶ for speed)  
   ```bash
   pytest tests/integration/test_pipeline.py -v
   ```

4. **Inspect a specific CSV row** (example for interval start 1000, L=10000, lag=57)  
   ```bash
   python - <<'PY'
   import pandas as pd
   df = pd.read_csv('data/processed/autocorrelation_stats.csv')
   row = df[(df['interval_start']==1000) & (df['interval_length']==10000) & (df['lag']==57)]
   print(row)
   PY
   ```

5. **Check heatmap file properties**  
   ```bash
   python - <<'PY'
   from PIL import Image
   img = Image.open('outputs/figures/heatmap_L10000.png')
   print(f'Resolution: {img.size[0]}x{img.size[1]} px')
   print(f'Format: {img.format}')
   PY
   ```
   Expected: Resolution ≥ 1200x1200 px, Format PNG.

## Troubleshooting

- **MemoryError** – Ensure `mobius_array.npy` is stored as `int8`. If you inadvertently saved as default `int64`, delete the file and rerun the sieve.  
- **Timeout** – The full pipeline is designed to finish within 3 h on the free runner. If it exceeds 5 h, the script automatically reduces the number of windows per L from 20 to 10 and retries.  
- **p‑value reported as 0.0** – The implementation adds 1 to the numerator and denominator, so the smallest possible p‑value is `1/1001 ≈ 0.001`.  
- **Missing PNGs** – Verify that `matplotlib` backend is set to `Agg` (non‑interactive) in `viz.py`: `matplotlib.use('Agg')` before any plotting.  
- **CSV shows all zeros in a window** – This is expected for some windows; the `sensitivity_flag` will be `"not_applicable"` for such rows.

## Reproducibility Checklist

- [x] Fixed random seed (`seed=20231017`) used everywhere.  
- [x] All dependencies pinned in `requirements.txt`.  
- [x] Checksums for `mobius_array.npy` recorded in the project state file.  
- [x] Scripts are deterministic; running `main.py` twice on a fresh runner yields identical CSV and PNG files (verified by `md5sum`).  

## Expected Runtime

- **Sieve**: ~0.2 s
- **Autocorrelation**: ~1.5 min
- **Permutation + Sensitivity (inline)**: ~2.5 h
- **Visualization**: ~5 min
- **Total**: ~2.75 h (well under the 6 h GitHub Actions limit)

---
