# Quickstart: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Prerequisites
- Python 3.11 or newer
- At least **7 GB RAM** and **14 GB free disk** on the CI runner or local machine
- No GPU required (CPU‑only)

## Installation

```bash
# 1. Clone the repository
git clone <repo_url>
cd PROJ-551-asymptotic-behavior-of-random-matrix-eig

# 2. Create and activate a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

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

### 1. Single‑run sanity check (T002)
```bash
python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
```
*Expected*: A JSON report in `data/processed/single_run_results.json` containing one `SimulationRun` and ten `EigenvalueResult` entries. The top eigenvalue should exceed `2.05` (outlier) when `theta > 1`, because outlier detection uses the **theoretical edge 2.0 [UNRESOLVED-CLAIM: c_7ed104bc — status=not_enough_info] plus tolerance 0.05** (not an empirical bulk estimate).

### 2. Full parameter sweep (T004, T005)
```bash
python -m code.analysis.threshold_sweep --grid theta
```
*Output*: `data/processed/mc_results.csv`.

### 3. Sparsity sensitivity (T008)
```bash
python -m code.analysis.sensitivity_analysis
```
*Output*: `data/processed/sensitivity_results.parquet`.

### 4. Finite‑size analysis (T011)
```bash
python -m code.analysis.finite_size
```
*Output*: `data/processed/finite_size_results.parquet` showing how bulk edge and outlier probability vary with \(N\).

## Verifying Results

### Schema validation
```bash
pytest tests/contract/test_schemas.py
```
All tests must pass (exit code 0). This ensures every JSON/Parquet file conforms to the contracts.

### Reproducibility check (T001)
```bash
pytest tests/integration/test_t001.py
```
The test re‑runs a single configuration and asserts that the top eigenvalue matches the stored reference within `1e-6`.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| **MemoryError** | `N` too large for available RAM | Reduce `--N` to ≤ 1500 or enable streaming mode (`--stream`). |
| **ARPACK did not converge** | `tol` too strict or maxiter insufficient | Increase `--maxiter` (default 1000) or relax `--tol` (default 1e-10). |
| **Schema validation fails** | Output file corrupted or missing required fields | Re‑run the failing phase; ensure the corresponding schema file exists under `contracts/`. |
| **Test T001 fails** | Seed mismatch or nondeterministic RNG usage | Verify that all random calls use the same `numpy.random.default_rng(seed)` instance. |