# Quickstart: Evaluating the Effectiveness of Differential Privacy in Federated Learning

**Project**: PROJ-044 | **Runnable entry point**: `python code/main.py`

This document is the authoritative run-book for reproducing the full study:
streaming FEMNIST download → Dirichlet client partitions → DP-FedAvg training
(with a non-DP baseline) → filtering → statistical analysis → plots → summary.

## Prerequisites
- Python 3.10 or newer
- Git
- Internet access (to download FEMNIST from Hugging Face)
- No GPU required; everything runs on CPU.

## Project Structure

The repository layout (created/verified by `code/setup_check.py`) is:

```text
projects/PROJ-044-evaluating-the-effectiveness-of-differen/
├── data/
│   ├── raw/
│   │   └── femnist.parquet               # streamed download → static parquet
│   └── partitions/
│       └── partition_femnist_{seed}_{alpha}_*.json
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── setup_check.py
│   ├── data/
│   │   ├── download.py          # streaming → parquet (materialized)
│   │   └── partition.py         # Dirichlet splitter, entropy calc, minority flag
│   ├── models/
│   │   └── cnn.py               # tiny ConvNet (≈ 30 k params)
│   ├── training/
│   │   ├── fedavg.py            # core FedAvg loop (DP optional)
│   │   └── dp_utils.py          # Opacus wrapper, Moments Accountant
│   ├── analysis/
│   │   ├── stats.py             # paired t-test, LMM, Bonferroni
│   │   └── plots.py             # overlay plot, sensitivity curves
│   └── main.py                  # CLI entry point (orchestration)
├── results/
├── figures/
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

## Dependencies

All dependencies are pinned in `requirements.txt` at the project root:
`torch` (CPU), `opacus`, `datasets`, `pandas`, `scipy`, `statsmodels`,
`pyarrow` (parquet I/O), plus `numpy`, `matplotlib`, and `pytest`.

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-044-evaluating-the-effectiveness-of-differen

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install exact dependencies
pip install -r requirements.txt

# 4. Verify the setup (dependencies importable, directories created)
python code/setup_check.py
```

## Step-by-Step Execution

### 1. Download the FEMNIST dataset (stream → static parquet)
```bash
python code/data/download.py --dataset femnist
# → creates data/raw/femnist.parquet and data/raw/femnist.sha256
```
The loader streams the dataset (`datasets.load_dataset(..., streaming=True)`)
and fails loudly on fetch errors — there is no synthetic fallback. Requesting
`--dataset shakespeare` raises
`ValueError: Shakespeare excluded per plan.md Gap Analysis`.

### 2. Verify checksum (optional but recommended)
```bash
python -c "import hashlib, pathlib; p = pathlib.Path('data/raw/femnist.parquet'); expected = pathlib.Path('data/raw/femnist.sha256').read_text().split()[0]; actual = hashlib.sha256(p.read_bytes()).hexdigest(); assert actual == expected, 'checksum mismatch'; print('checksum OK:', actual)"
```

### 3. Generate client partitions (5 seeds, three α values)
```bash
python code/data/partition.py \
    --data data/raw/femnist.parquet \
    --output data/partitions \
    --seeds 42 43 44 45 46 \
    --alphas 0.1 0.5 1.0
# Output: data/partitions/partition_femnist_{seed}_{alpha}_*.json
```
Note: `partition.py` takes space-separated `--seeds` and `--alphas` values
(not comma-separated lists) and requires `--data` pointing at the parquet
file produced in step 1.
Minority clients are flagged as the bottom [deferred] of the within-partition
empirical label-entropy distribution (in bits), independent of α.

### 4. Run the full experiment sweep (DP & non-DP)
```bash
python code/main.py sweep \
    --dataset femnist \
    --alphas 0.1,0.5,1.0 \
    --epsilons 0.1,0.5,1.0,5.0,inf \
    --seeds 42,43,44,45,46
```
- **What happens**: `main.py` invokes the orchestrator. It runs 5 seeds ×
  3 α × 5 ε (ε = ∞ is the non-DP baseline with `is_dp=False`), implements
  the deterministic time-budget round cap (`is_time_limited=True` when
  triggered), and retries failed seeds up to 3 times.
- **Outputs**: `results/raw_logs.csv` (single source of truth for all metrics).

### 5. Post-processing & Filtering
```bash
python code/analysis/stats.py \
    --input results/raw_logs.csv
# Produces results/filtered_time.csv and results/filtered_data.csv
```
Filtering removes (1) runs with `global_accuracy < 1/62 ≈ 0.01613`
(utility collapse) and (2) runs with `is_time_limited=True`. It also computes
`rounds_to_80` (first round with global accuracy ≥ 0.80) into
`results/filtered_time.csv`.

### 6. Statistical Analysis
```bash
python code/analysis/stats.py \
    --input results/filtered_data.csv \
    --output results/final_stats.csv
```
- Performs paired t-tests (DP vs. non-DP per seed), the minority-vs-majority
  LMM, and Bonferroni correction across the 15 (α, ε) tests
  (α_adj = 0.05/15 ≈ 0.0033).

### 7. Plotting
```bash
python code/analysis/plots.py
```
- Generates the accuracy-vs-ε sensitivity plot and the
  `minority_vs_global_overlay.png` overlay plot into `results/plots/`.
  (The plotting module reads `results/filtered_data.csv` by default and
  takes no CLI flags.)

### 8. Final Summary & Validation Report
```bash
python code/analysis/generate_summary.py
```
- Creates `results/summary.csv`, `results/validation_report.md`, and
  `results/p_values_by_seed.json`.

## Expected Directory Layout after a Successful Run
```text
data/
├── raw/
│   ├── femnist.parquet
│   └── femnist.sha256
└── partitions/
    └── partition_femnist_42_0.1_*.json
results/
├── raw_logs.csv
├── filtered_data.csv
├── filtered_time.csv
├── final_stats.csv
├── summary.csv
├── validation_report.md
└── p_values_by_seed.json
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **MemoryError** during download | Streaming chunk size too large | Reduce the batch size in `download.py` (default 1000). |
| **Timeout / `is_time_limited=True`** | Too many rounds for the 6 h budget | The orchestrator automatically caps rounds at the deterministic `max_rounds`; you can manually lower the round count for a shorter run. Time-limited runs are excluded from all statistical analyses. |
| **`Shakespeare excluded` error** | Attempted use of an excluded dataset | The loader/partitioner raises `ValueError: "Shakespeare excluded per plan.md Gap Analysis"`; choose `"femnist"` instead. |
| **`partition.py: error: argument --alphas`** | Comma-separated list passed | `partition.py` expects space-separated values: `--alphas 0.1 0.5 1.0` and `--seeds 42 43 44 45 46`, plus a required `--data` path. |
| **Paired-test warning: < 3 valid seeds** | One or more seeds failed repeatedly | Inspect `results/validation_report.md`; the orchestrator retries up to 3 times per seed. Re-run the sweep with a different seed list if needed. |

## Reproducibility Checklist
- All random seeds are logged in `results/raw_logs.csv`.
- The exact FEMNIST source is fixed in `download.py` (streaming HF dataset).
- SHA-256 checksum of the raw parquet is stored in `data/raw/femnist.sha256`.
- No GPU is required; the same commands run on a fresh GitHub Actions runner
  and reproduce identical results.

**Note on ε representation**: In `results/raw_logs.csv` the non-DP baseline uses
the literal string `"inf"` for the `epsilon` field, which is allowed by the
results schema.