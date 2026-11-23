# Quickstart: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project**: PROJ-044 | **Entry point**: `python code/main.py`

This guide reproduces the entire study on a fresh GitHub Actions runner (or locally) using only CPU resources.

## Prerequisites
- Python 3.11+  
- Git  
- Internet access (to download FEMNIST from Hugging Face)  
- No GPU required.

## Repository Layout

```text
projects/PROJ-044-evaluating-the-effectiveness-of-differen/
├── data/
│   ├── raw/
│   │   ├── femnist_train.parquet
│   │   ├── femnist_test.parquet
│   │   └── femnist.sha256
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}.json
├── results/
│   ├── raw_logs.csv
│   ├── final_stats.csv
│   ├── summary.csv
│   ├── validation_report.md
│   └── p_values_by_seed.json
├── figures/
│   ├── minority_vs_global_overlay.png
│   └── sensitivity_alpha.png
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet, checksum
│   │   ├── partition.py         # Dirichlet split, global entropy, minority flag, correlation diagnostic
│   │   └── verify_shakespeare_exclusion.py   # real verification script
│   ├── models/
│   │   └── cnn.py               # tiny ConvNet (≈ tens of thousands of parameters)
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired tests, LMM (two‑way interactions), survival analysis
│   │   └── plots.py             # overlay & sensitivity plots
│   └── main.py                  # CLI orchestrator (sweep)
├── tests/
│   ├── unit/
│   │   ├── test_partition.py
│   │   └── test_dp_utils.py
│   └── integration/
│       └── test_training_loop.py
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-044-evaluating-the-effectiveness-of-differen

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Verify environment (creates folders, checks imports)
python -c "import code, torch; print('Env OK')"
```

## Step‑by‑step Execution

### 1. Download FEMNIST (stream → parquet) and verify checksum
```bash
python code/data/download.py --dataset femnist
# → creates:
#   data/raw/femnist_train.parquet
#   data/raw/femnist_test.parquet
#   data/raw/femnist.sha256
```
The script streams via `datasets.load_dataset(..., streaming=True)`, writes static parquet files, and records a SHA‑256 checksum over the concatenated bytes of the two files. Supplying `--dataset shakespeare` raises the required `ValueError("Shakespeare excluded per plan.md Gap Analysis")`.

### 2. Verify checksum (optional)
```bash
python -c "
import hashlib, pathlib, sys
p_train = pathlib.Path('data/raw/femnist_train.parquet')
p_test  = pathlib.Path('data/raw/femnist_test.parquet')
combined = p_train.read_bytes() + p_test.read_bytes()
actual = hashlib.sha256(combined).hexdigest()
expected = pathlib.Path('data/raw/femnist.sha256').read_text().split()[0]
assert actual == expected, f'checksum mismatch: {actual} != {expected}'
print('checksum OK')
"
```

### 3. Generate client partitions
```bash
python code/data/partition.py \
    --train data/raw/femnist_train.parquet \
    --test  data/raw/femnist_test.parquet \
    --output data/partitions \
    --seeds 42 43 44 45 46 47 48 49 50 51 \
    --alphas 0.1 0.5 1.0
```
- `--seeds` and `--alphas` are space‑separated lists.  
- Minority clients are flagged as the **global bottom quartile** of label‑entropy (computed once on the full training set) and applied to all partitions.  
- SHA‑256 hashes of each JSON file are printed for reproducibility (SC‑001).  
- A Pearson correlation between entropy and α is computed and logged; any |r| > 0.3 triggers a warning in `validation_report.md`.

### 4. Run the full experiment sweep
```bash
python code/main.py sweep \
    --dataset femnist \
    --alphas 0.1,0.5,1.0 \
    --epsilons 0.1,1.0,inf \
    --seeds 42,43,44,45,46,47,48,49,50,51
```
- The orchestrator runs DP and non‑DP FedAvg on the *same* partition for each seed.  
- Early‑stop logic caps rounds when the remaining wall‑clock time would exceed the 6 h budget; such runs are marked `is_time_limited=True` and **retained** for analysis.  
- DP vs. non‑DP are compared at the **minimum number of completed rounds** between the pair (matched‑round evaluation).  
- All metrics are appended to `results/raw_logs.csv`.

### 5. Statistical Analysis
```bash
python code/analysis/stats.py \
    --input results/raw_logs.csv \
    --output results/final_stats.csv
```
- Performs Shapiro‑Wilk normality test on paired differences.  
- Runs paired t‑test if normal, otherwise Wilcoxon signed‑rank test.  
- Fits the mixed‑effects model with the **two‑way** interaction `is_minority:alpha` and random slope for ε per seed.  
- Applies Bonferroni correction across the multiple (α, ε) tests.  
- Runs a Cox survival‑analysis on `rounds_to_80` with right‑censoring for time‑limited runs.  
- Writes `results/final_stats.csv`.

### 6. Plot Generation
```bash
python code/analysis/plots.py
```
- Generates `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves).  
- Generates `figures/sensitivity_alpha.png` (accuracy & convergence speed vs. ε for each α).

### 7. Final Summary & Validation Report
```bash
python code/analysis/generate_summary.py
```
- Writes `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  
- The validation report includes:  
  * FEMNIST checksum verification.  
  * Confirmation that the only occurrence of “Shakespeare” is inside the mandated exclusion message (via `verify_shakespeare_exclusion.py`).  
  * Seed completeness and any flagged runs.  
  * Minority‑definition correlation diagnostic (Pearson r).  

## Expected Directory Layout after Successful Run
```text
data/
├── raw/
│   ├── femnist_train.parquet
│   ├── femnist_test.parquet
│   └── femnist.sha256
└── partitions/
    └── partition_femnist_42_0.1.json
results/
├── raw_logs.csv
├── final_stats.csv
├── summary.csv
├── validation_report.md
└── p_values_by_seed.json
figures/
├── minority_vs_global_overlay.png
└── sensitivity_alpha.png
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** during download | Chunk size too large for streaming | Reduce `--chunk-size` in `download.py` (default 1000). |
| **`is_time_limited=True`** for many runs | Too many communication rounds for the 6 h budget | Reduce `--max-rounds` via an optional flag in `main.py`. |
| **ValueError: Shakespeare excluded per plan.md Gap Analysis** | Attempted to load Shakespeare | Use `--dataset femnist` only; the exclusion script satisfies verification T000. |
| **Paired‑test warning: fewer than 10 seeds** | Some seeds repeatedly failed | Check `results/validation_report.md`; adjust seed list or increase retry limit. |
| **ImportError: Opacus not found** | Dependency mismatch | Ensure `requirements.txt` is installed in the active virtualenv. |

## Reproducibility Checklist
- All random seeds are logged in `results/raw_logs.csv`.  
- FEMNIST source URLs are fixed in `download.py`.  
- SHA‑256 checksum stored in `data/raw/femnist.sha256`.  
- No GPU is required; the same commands run on GitHub Actions and yield identical results.  

**Note on ε representation**: In `results/raw_logs.csv` the non‑DP baseline uses the literal string `"inf"` for the `epsilon` field, which conforms to the `results.schema.yaml` contract.

---

