# Quickstart: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- At least **7 GB RAM** and **14 GB free disk** on the CI runner or local machine
- No GPU required (CPU‑only)

## Installation

```bash
# 1. Clone the repository
git clone 
cd PROJ-551-asymptotic-behavior-of-random-matrix-eig

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install exact dependencies
pip install -r code/requirements.txt
```

`code/requirements.txt` pins:
```
numpy==1.26.*
scipy==1.12.*
pandas==2.2.*
pyarrow==15.*
pydantic==2.*
matplotlib==3.8.*
tqdm==4.66.*
jsonschema==4.22.*
```

## Running the Analyses

### 1. Single‑run sanity check (FR‑001 – FR‑004)
```bash
python -m src.cli run \
    --mode single \
    --N 1000 \
    --theta 2.5 \
    --k 1 \
    --pattern diagonal \
    --seed 42
```
*Expected*: A JSON report in `data/processed/run_<run_id>.json` containing one `SimulationRun` and ten `EigenvalueResult` entries. The top eigenvalue should exceed `2.05` (outlier) when `theta > 1`, because outlier detection uses the **theoretical edge 2.0 plus tolerance 0.05** (not an empirical bulk estimate).

### 2. Full parameter sweep (FR‑005)
```bash
python -m src.cli sweep \
    --N 2000 \
    --theta-grid 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2.0 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8 2.9 3.0 \
    --k 1 2 5 \
    --patterns diagonal block-sparse random-sparse \
    --iterations 500 \
    --seed-start 1000
```
*Output*: `data/processed/sweep_results.parquet` (validated against `aggregated_threshold.schema.yaml`). Runtime ≈ a few hours on the CI runner.

### 3. Sparsity sensitivity (FR‑006)
```bash
python -m src.cli sensitivity \
    --N 1500 \
    --theta 1.5 \
    --k 2 \
    --pattern random-sparse \
    --densities 0.05 0.1 0.2 0.3 0.4 0.5 \
    --iterations 500 \
    --seed-start 5000
```
*Output*: `data/processed/sensitivity_results.parquet`.

### 4. Finite‑size analysis (new phase)
```bash
python -m src.cli finite_size \
    --Ns 500 1000 1500 2000 \
    --theta 1.5 \
    --k 1 \
    --pattern diagonal \
    --iterations 500 \
    --seed-start 8000
```
*Output*: `data/processed/finite_size_results.parquet` showing how bulk edge and outlier probability vary with \(N\).

## Verifying Results

### Schema validation
```bash
pytest tests/contract/test_schemas.py
```
All tests must pass (exit code 0). This ensures every JSON/Parquet file conforms to the contracts.

### Reproducibility check (T001)
```bash
pytest tests/integration/test_t001.py
```
The test re‑runs a single configuration and asserts that the top eigenvalue matches the stored reference within `1e-6`.

### Visual inspection
```python
import pandas as pd
import matplotlib.pyplot as plt

# Example: outlier probability vs. theta for each pattern
df = pd.read_parquet("data/processed/sweep_results.parquet")
for pat in df["pattern_type"].unique():
    sub = df[df["pattern_type"] == pat]
    plt.plot(sub["theta"], sub["outlier_probability"], label=pat)
plt.axvline(x=1.0, color="red", linestyle="--", label="Theoretical θ_c")
plt.xlabel("Perturbation norm θ")
plt.ylabel("Outlier probability")
plt.legend()
plt.show()
```
The plot should display a sigmoid‑like rise near the theoretical threshold (θ ≈ the predicted critical point)..

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **MemoryError** | `N` too large for available RAM | Reduce `--N` to ≤ 1500 or enable streaming mode (`--stream`). |
| **ARPACK did not converge** | `tol` too strict or maxiter insufficient | Increase `--maxiter` (default 1000) or relax `--tol` (default 1e‑10). |
| **Schema validation fails** | Output file corrupted or missing required fields | Re‑run the failing phase; ensure the corresponding schema file exists under `contracts/`. |
| **Test T001 fails** | Seed mismatch or nondeterministic RNG usage | Verify that all random calls use the same `numpy.random.default_rng(seed)` instance. |

---


