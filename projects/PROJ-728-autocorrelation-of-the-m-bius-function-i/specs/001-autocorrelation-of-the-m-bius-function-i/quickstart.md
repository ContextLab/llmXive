# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python 3.11 or newer  
- `git` (to clone the repository)  
- At least **500 MB** free disk space  
- Internet connection (to download Python packages)

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

3. **Install pinned dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following stages in order:

| Stage | Description | Output |
|-------|-------------|--------|
| **Sieve** | Generates `data/raw/mobius_array.npy`. | `mobius_array.npy` |
| **Window sampling** | 50 non‑overlapping windows per L (seed = 20231017). | Implicit (recorded in CSV). |
| **Autocorrelation** | Computes all lags ≤ L/2 via FFT for each window. | `autocorrelation_stats.csv` (partial). |
| **Permutation + Sensitivity** | 5,000 full random‑sign permutations per window; inline ±5 %/±10 % zero‑density analysis. | Completed rows in CSV. |
| **Multiple‑comparison correction** | Benjamini‑Hochberg FDR (α = 0.05). | `adjusted_p_value` column. |
| **Uniformity validation** | KS test against Uniform[0,1]. | `uniformity_test.json`. |
| **Visualization** | Heatmaps saved as PNGs with a correct zero line at 0 and confidence‑band overlay. | `outputs/figures/heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`. |
| **Output consolidation** | Final CSV, JSON, PNGs, checksums. | All artefacts listed below. |

### Expected Outputs

| Path | Description |
|------|-------------|
| `data/raw/mobius_array.npy` | Deterministic Möbius sequence (int8). |
| `data/processed/autocorrelation_stats.csv` | Table of all statistics (see `contracts/mobius_stats.schema.yaml`). |
| `data/processed/uniformity_test.json` | KS test result for p‑value uniformity. |
| `outputs/figures/heatmap_L1000.png` | Heatmap for **L = 10³** (zero line at 0, confidence bands). |
| `outputs/figures/heatmap_L10000.png` | Heatmap for **L = 10⁴**. |
| `outputs/figures/heatmap_L100000.png` | Heatmap for **L = 10⁵**. |

## Running Individual Stages

- **Generate Möbius array only**  
  ```bash
  python code/sieve.py --output data/raw/mobius_array.npy
  ```

- **Compute autocorrelations only** (requires the array)  
  ```bash
  python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv
  ```

- **Run permutation + sensitivity only** (needs the CSV from the previous step)  
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
   print('Shape:', arr.shape)
   PY
   ```
   Expected: `Unique values: [-1  0  1]` and `Shape: (10000000,)`.

2. **Run unit tests**  
   ```bash
   pytest tests/unit/ -v
   ```

3. **Run integration test** (uses a reduced N=10⁶ for speed)  
   ```bash
   pytest tests/integration/test_pipeline.py -v
   ```

4. **Inspect a specific CSV row** (example for interval start = 1, L = 1000, lag = 1)  
   ```bash
   python - <<'PY'
   import pandas as pd
   df = pd.read_csv('data/processed/autocorrelation_stats.csv')
   row = df[(df['interval_start']==1) & (df['interval_length']==1000) & (df['lag']==1)]
   print(row)
   PY
   ```

5. **Check heatmap resolution**  
   ```bash
   python - <<'PY'
   from PIL import Image
   img = Image.open('outputs/figures/heatmap_L10000.png')
   print(f'Resolution: {img.size[0]}x{img.size[1]} px')
   print('Format:', img.format)
   PY
   ```
   Expected: Resolution ≥ 1200 × 1200 px, Format = PNG.

## Troubleshooting

- **MemoryError** – Ensure `mobius_array.npy` is saved as `int8`. Delete and rerun `sieve.py` if needed.  
- **Timeout** – The full pipeline is designed to finish within a few hours. If it exceeds **4 h**, `main.py` automatically reduces the number of windows per L (from 50 to 30) and, if still exceeding **5 h**, reduces to 20 windows and drops permutation count to 2,000. This staged fallback is logged.  
- **p‑value reported as 0.0** – The implementation adds 1 to numerator and denominator, so the smallest possible value is a very small positive number (observed under a large number of permutations).  
- **Missing PNGs or zero line at wrong height** – `viz.py` now contains `plt.axhline(y=0, ...)` guaranteeing the zero line is drawn at autocorrelation = 0. Ensure `matplotlib.use('Agg')` is set before any plotting.  
- **CSV shows all zeros in a window** – This is expected for rare pathological windows; `sensitivity_flag` will be `"not_applicable"` and the row will contain `nan` for autocorrelation.  

## Reproducibility Checklist
- [x] Fixed random seed (`seed=20231017`) used everywhere.  
- [x] All dependencies pinned in `requirements.txt`.  
- [x] Checksums for `mobius_array.npy` recorded in the project state file.  
- [x] Scripts are deterministic; running `main.py` twice on a fresh runner yields identical CSV and PNG files (verified by `md5sum`).  

## Expected Runtime (on GitHub Actions free tier)

- **Sieve**: ~0.2 s  
- **Autocorrelation (FFT)**: [deferred] total  
- **Permutation + Sensitivity**: ~4.5 h (vectorised NumPy + FFT) with 50 windows per L and 5,000 permutations.  
- **Visualization**: [deferred]  
- **Total**: ~5 h < 6 h limit  

---



