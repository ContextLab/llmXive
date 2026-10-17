# Quickstart: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Prerequisites
- Python 3.11 or newer
- At least **7 GB RAM** and **14 GB free disk**
- No GPU required (CPU‑only)

## Installation

```bash
# 1. Clone the repository
git clone <repo_url>
cd PROJ-551-asymptotic-behavior-of-random-matrix-eig

# 2. Install dependencies
pip install -r code/requirements.txt
```

## Running the Analyses

### 1. Single‑run sanity check (T002)
```bash
python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
```
*Expected*: A JSON report in `data/processed/single_run_results.json` containing one `SimulationRun` and ten `EigenvalueResult` entries. The top eigenvalue should exceed `2.05` (outlier) when `theta > 1`.

### 2. Full parameter sweep
```bash
python code/analysis/threshold_sweep.py --grid theta
```
*Output*: `data/processed/mc_results.csv`.

### 3. Sparsity sensitivity
```bash
python code/analysis/sensitivity_analysis.py
```
*Output*: `data/processed/sensitivity_results.parquet`.

### 4. Finite‑size analysis
```bash
python code/analysis/finite_size.py
```
*Output*: `data/processed/finite_size_results.parquet`.

## Verifying Results

### Schema validation
```bash
pytest tests/contract/test_schemas.py
```

### Reproducibility check
```bash
pytest tests/integration/test_t001.py
```