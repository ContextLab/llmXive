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
│   │   └── femnist.parquet               # streamed download → static parquet
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}.json
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet, checksum
│   │   └── partition.py         # Dirichlet split, entropy, minority flag
│   ├── models/
│   │   └── cnn.py               # tiny ConvNet (≈ 30 k params)
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired t‑test, LMM, Bonferroni
│   │   └── plots.py             # overlay & sensitivity plots
│   └── main.py                  # CLI orchestrator (sweep)
├── results/
├── figures/
├── tests/
│   ├── unit/
│   └── integration/
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
python code/setup_check.py
```

## Step‑by‑Step Execution

### 1. Download FEMNIST (stream → parquet)
```bash
python code/data/download.py --dataset femnist
# → creates data/raw/femnist.parquet and data/raw/femnist.sha256
```
The script streams via `datasets.load_dataset(..., streaming=True)`, writes a static parquet file, and records a SHA‑256 checksum. Supplying `--dataset shakespeare` raises the required `ValueError`.

### 2. Verify checksum (optional)
```bash
python -c "
import hashlib, pathlib;
p = pathlib.Path('data/raw/femnist.parquet');
expected = pathlib.Path('data/raw/femnist.sha256').read_text().split()[0];
actual = hashlib.sha256(p.read_bytes()).hexdigest();
assert actual == expected, 'checksum mismatch';
print('checksum OK:', actual)
"
```

### 3. Generate client partitions
```bash
python code/data/partition.py \
    --data data/raw/femnist.parquet \
    --output data/partitions \
    --seeds 42 43 44 45 46 \
    --alphas 0.1 0.5 1.0
# Output files: data/partitions/partition_femnist_{seed}_{alpha}.json
```
- `--seeds` and `--alphas` are space‑separated lists.  
- Minority clients are flagged as the bottom 30 % of label‑entropy **within each partition**.

### 4. Run the full experiment sweep
```bash
python code/main.py sweep \
    --dataset femnist \
    --alphas 0.1,0.5,1.0 \
    --epsilons 0.1,0.5,1.0,5.0,inf \
    --seeds 42,43,44,45,46
```
- The orchestrator runs DP and non‑DP FedAvg on the *same* partition for each seed.  
- Early‑stop logic caps rounds when the remaining wall‑clock time would exceed the 6 h budget; such runs are marked `is_time_limited=True` and excluded from analysis.  
- All metrics are appended to `results/raw_logs.csv`.

### 5. Post‑processing & Filtering
```bash
python code/analysis/stats.py \
    --input results/raw_logs.csv \
    --filter-utility-collapse \
    --filter-time-limit
# Produces results/filtered_data.csv and results/filtered_time.csv
```
- Removes runs with `global_accuracy < 1/62 ≈ 0.01613`.  
- Removes runs flagged `is_time_limited=True`.

### 6. Statistical Analysis
```bash
python code/analysis/stats.py \
    --input results/filtered_data.csv \
    --output results/final_stats.csv
```
- Performs paired t‑tests (DP vs. non‑DP) and the minority‑vs‑majority mixed‑effects model.  
- Applies Bonferroni correction across the 15 (α, ε) tests.  

### 7. Plot Generation
```bash
python code/analysis/plots.py
```
- Generates `figures/minority_vs_global_overlay.png` (minority vs. global accuracy curves).  
- Generates `figures/sensitivity_alpha.png` (accuracy vs. ε for each α).

### 8. Final Summary & Validation Report
```bash
python code/analysis/generate_summary.py
```
- Writes `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.  

## Expected Directory Layout after Successful Run
```text
data/
├── raw/
│   ├── femnist.parquet
│   └── femnist.sha256
└── partitions/
    └── partition_femnist_42_0.1.json
results/
├── raw_logs.csv
├── filtered_data.csv
├── filtered_time.csv
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
| **`is_time_limited=True`** for many runs | Too many communication rounds for the 6 h budget | Reduce `max_rounds` manually via `--max-rounds` flag (optional). |
| **`ValueError: Shakespeare excluded per plan.md Gap Analysis`** | Attempted to load Shakespeare | Use `--dataset femnist` only; the exclusion message satisfies verification T000. |
| **Paired‑test warning: fewer than 5 seeds** | One or more seeds repeatedly failed | Check `results/validation_report.md`; adjust seed list or increase retry limit. |
| **ImportError: Opacus not found** | Dependency mismatch | Ensure `requirements.txt` is installed in the active virtualenv. |

## Reproducibility Checklist
- All random seeds are logged in `results/raw_logs.csv`.  
- FEMNIST source URL is fixed in `download.py`.  
- SHA‑256 checksum stored in `data/raw/femnist.sha256`.  
- No GPU is required; the same commands run on GitHub Actions and yield identical results.

**Note on ε representation**: In `results/raw_logs.csv` the non‑DP baseline uses the literal string `"inf"` for the `epsilon` field, which conforms to the `results.schema.yaml` contract.

---
