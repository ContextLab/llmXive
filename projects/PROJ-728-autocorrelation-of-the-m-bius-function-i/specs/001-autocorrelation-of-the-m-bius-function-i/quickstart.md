# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- At least **500 MB** free disk space
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
2. **Window sampling** – creates 20 stratified windows per L.  
3. **Autocorrelation** – computes all lags.  
4. **Permutation test** – 1 000 block‑permutations per window.  
5. **Sensitivity analysis** – zero‑density ±5 % / ±10 %.  
6. **Multiple‑comparison correction** – BH FDR.  
7. **Uniformity validation** – KS test.  
8. **Visualization** – heatmaps saved as PNGs.  
9. **CSV/JSON output** – written to `data/processed/`.

### Expected Outputs
| Path | Description |
|------|-------------|
| `data/raw/mobius_array.npy` | Deterministic Möbius sequence (int8). |
| `data/processed/autocorrelation_stats.csv` | Table of all statistics (see `contracts/mobius_stats.schema.yaml`). |
| `data/processed/null_distributions.parquet` | Full permutation null values (optional). |
| `data/processed/uniformity_test.json` | KS test result for p‑value uniformity. |
| `outputs/figures/heatmap_L1000.png` | Heatmap for L = 10³. |
| `outputs/figures/heatmap_L10000.png` | Heatmap for L = 10⁴. |
| `outputs/figures/heatmap_L100000.png` | Heatmap for L = 10⁵. |

## Running Individual Stages

- **Generate Möbius array only**  
  ```bash
  python code/sieve.py --output data/raw/mobius_array.npy
  ```

- **Compute autocorrelations only** (requires the Möbius array)  
  ```bash
  python code/autocorrelation.py --array data/raw/mobius_array.npy --out data/processed/autocorrelation_stats.csv
  ```

- **Run permutation test only** (needs the CSV from the previous step)  
  ```bash
  python code/permutation.py --stats data/processed/autocorrelation_stats.csv
  ```

- **Create visualisations only**  
  ```bash
  python code/viz.py --stats data/processed/autocorrelation_stats.csv --outdir outputs/figures/
  ```

## Verification Steps

1. **Check Möbius array values**  
   ```bash
   python - <<'PY'
   import numpy as np, sys
   arr = np.load('data/raw/mobius_array.npy')
   print('Unique values:', np.unique(arr))
   PY
   ```
   Expected output: `Unique values: [-1  0  1]`.

2. **Run unit tests**  
   ```bash
   pytest tests/unit/
   ```

3. **Run integration test** (full pipeline sanity check, uses a reduced N=10⁶ for speed)  
   ```bash
   pytest tests/integration/test_pipeline.py
   ```

4. **Inspect a specific CSV row** (example for interval start 123456, L=10000, lag=57)  
   ```bash
   pandas -c "import pandas as pd; df=pd.read_csv('data/processed/autocorrelation_stats.csv'); print(df[(df.interval_start==123456)&(df.interval_length==10000)&(df.lag==57)])"
   ```

## Troubleshooting

- **MemoryError** – Ensure `mobius_array.npy` is stored as `int8`. If you inadvertently saved as default `int64`, delete the file and rerun the sieve.  
- **Timeout** – The full pipeline is designed to finish within 4 h on the free runner. If it exceeds 5 h, the script automatically reduces the number of windows per L from 20 to 10 and retries.  
- **p‑value reported as 0.0** – The implementation adds 1 to the numerator and denominator, so the smallest possible p‑value is `1/1001 ≈ 0.001`.  
- **Missing PNGs** – Verify that `matplotlib` backend is not set to a non‑interactive one that suppresses file saving (`Agg` is forced in `viz.py`).  

## Reproducibility Checklist
- [x] Fixed random seed (`seed=20231017`) used everywhere.  
- [x] All dependencies pinned in `requirements.txt`.  
- [x] Checksums for `mobius_array.npy` recorded in `state/projects/PROJ-728-autocorrelation-of-the-mobius-function-i.yaml`.  
- [x] Scripts are deterministic; running `main.py` twice on a fresh runner yields identical CSV and PNG files (verified by `md5sum`).  

---
