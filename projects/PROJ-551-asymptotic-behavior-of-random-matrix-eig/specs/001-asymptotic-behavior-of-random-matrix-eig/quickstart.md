# Quickstart: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Prerequisites
- Python 3.11+, `git`, ~7 GB RAM, ~14 GB disk. CPU-only; no GPU needed.

## Installation
```bash
git clone <repo-url>
cd PROJ-551-asymptotic-behavior-of-random-matrix-eig
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

`code/requirements.txt` pins `numpy`, `scipy`, `pandas`, `pyarrow`, `pydantic`, `matplotlib`, `jsonschema` (exact versions in the file).

## Running the Analyses

### 1. Single run (FR-001–FR-004) — produces verifiable artifacts
```bash
python -m code.main --mode single --N 1000 --theta 2.5 --k 1 --pattern diagonal --seed 42
```
**Expected stdout** (evidence of artifacts):
```
[artifact] data/processed/single_run_results.json  sha256=<64-hex>
[artifact] data/processed/convergence_report.json  sha256=<64-hex>
[checksum] data/checksums.yaml updated (matrix sha256=<64-hex>)
top_eigenvalue=2.901642355091  (reference value for seed 42, N=1000, theta=2.5, k=1, diagonal)
```
Verify the files exist and match the contracts:
```bash
pytest tests/contract/test_schemas.py -v   # all tests PASSED, none SKIPPED
```

### 2. Full parameter sweep (FR-005)
```bash
python -m code.main --mode sweep --N 2000 --theta-min 0.5 --theta-max 3.0 --theta-step 0.1 \
    --k 1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000
```
Output: `data/processed/sweep_runs.parquet`. Repetitions are auto‑capped to fit the ≤6 h budget; the achieved count is recorded in `total_runs`.

### 3. Sparsity sensitivity (FR-006)
```bash
python -m code.main --mode sensitivity --N 1500 --theta 1.5 --k 2 --pattern random-sparse \
    --densities 0.05 0.1 0.2 0.3 0.4 0.5 --iterations 500 --seed-start 5000
```
Output: `data/processed/sensitivity_results.parquet`.

### 4. Finite-size analysis
```bash
python -m code.main --mode finite-size --Ns 500 1000 1500 2000 --theta 1.5 --k 1 \
    --pattern diagonal --iterations 500 --seed-start 8000
```
Output: `data/processed/finite_size_results.parquet`.

### 5. Aggregation and threshold fit (FR-007)
```bash
python -m code.main --mode aggregate     # writes data/processed/aggregated_thresholds.json, exit 0
python -m code.main --mode fit           # writes data/processed/threshold_fit.json, exit 0
```
Both must exit 0 and print their artifact paths + checksums. A non‑convergent sigmoid fit is recorded with `fit_status: "failed"` rather than crashing.

## Verifying Results
```bash
pytest tests/contract/ -v        # per-file schema validation; FAILS on missing files
pytest tests/integration/ -v     # reproducibility: top eigenvalue within 1e-6 of reference
```

### Visual inspection
```python
import pandas as pd, matplotlib.pyplot as plt
df = pd.read_json("data/processed/aggregated_thresholds.json")
for pat in df["pattern_type"].unique():
    sub = df[(df["pattern_type"] == pat) & (df["k"] == 1)]
    plt.plot(sub["theta"], sub["outlier_probability"], label=pat)
plt.axvline(x=1.0, color="red", linestyle="--", label="Theoretical theta_c")
plt.xlabel("Perturbation norm theta"); plt.ylabel("Outlier probability"); plt.legend(); plt.show()
```

## Troubleshooting
| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| Contract test FAILS (not skips) | Artifact file missing or schema‑invalid | Re‑run the producing CLI mode; read the write‑time validation error printed by `artifacts.py`. |
| `aggregate`/`fit` exits non‑zero | Missing/empty input Parquet | Run the sweep mode first; the repaired scripts raise a clear message naming the missing input. |
| ARPACK did not converge | tol/maxiter too strict | Increase `--maxiter` or relax `--tol`. |
| Reproducibility test fails | Seed mismatch or nondeterministic RNG | Ensure all random draws use the single `default_rng(seed)` instance. |

---


