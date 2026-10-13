# Quickstart: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Prerequisites
- Python 3.10 or newer
- Git
- Internet access (to download FEMNIST from Hugging Face)

## Setup

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-044-evaluating-the-effectiveness-of-differen

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

### 1️⃣ Download the FEMNIST dataset (stream → static parquet)
```bash
python code/data/download.py --dataset femnist
# → creates data/raw/femnist.parquet and data/checksums.json
```

### 2️⃣ Verify checksum (optional but recommended)
```bash
python code/data/verify_checksum.py data/raw/femnist.parquet data/checksums.json
```

### 3️⃣ Generate client partitions (5 seeds, three α values)
```bash
python code/data/partition.py \
    --seed-list 42,43,44,45,46 \
    --alphas 0.1,0.5,1.0 \
    --clients 100
# Output: data/partitions/partition_femnist_{seed}_{alpha}.json
```

### 4️⃣ Run the full experiment sweep (DP & non‑DP)
```bash
python code/main.py sweep \
    --dataset femnist \
    --alphas 0.1,0.5,1.0 \
    --epsilons 0.1,0.5,1.0,5.0,inf \
    --seeds 42,43,44,45,46
```
- **What happens**: `main.py` invokes the orchestrator (`T018c`).  
- **Outputs**: `results/raw_logs.csv`, plus intermediate per‑seed logs.

### 5️⃣ Post‑processing & Filtering
```bash
python code/analysis/filter.py \
    --input results/raw_logs.csv \
    --random-guess-threshold 0.01613
# Produces results/filtered_data.csv and results/filtered_time.csv
```

### 6️⃣ Statistical Analysis
```bash
python code/analysis/stats.py \
    --input results/filtered_data.csv \
    --output results/final_stats.csv
```
- Performs paired t‑tests, LMM, and Bonferroni correction.  

### 7️⃣ Plotting
```bash
python code/analysis/plots.py \
    --stats results/final_stats.csv \
    --output-dir figures/
```
- Generates `figures/minority_vs_global_overlay.png` and `figures/sensitivity_alpha.png`.

### 8️⃣ Final Summary & Validation Report
```bash
python code/analysis/aggregate.py \
    --stats results/final_stats.csv \
    --plots figures/ \
    --output-dir results/
```
- Creates `results/summary.csv`, `results/validation_report.md`, and `results/p_values_by_seed.json`.

## Expected Directory Layout after a Successful Run
```text
data/
├── raw/
│   └── femnist.parquet
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
| **MemoryError** during download | Streaming chunk size too large | Reduce `--batch-size` in `download.py` (default 1000). |
| **Timeout / `is_time_limited=True`** | Too many rounds for the 6 h budget | The orchestrator automatically caps rounds at the deterministic `max_rounds`; you can manually lower `--max-rounds` if you prefer a shorter run. |
| **Missing `shakespeare` error** | Attempted to use an excluded dataset | The partitioner raises `ValueError: "Shakespeare excluded per plan.md Gap Analysis"`; choose `"femnist"` instead. |
| **Paired‑test warning: < 3 valid seeds** | One or more seeds failed repeatedly | Inspect `results/validation_report.md`; the orchestrator retries up to 3 times per seed. Re‑run the sweep with a different seed list if needed. |

## Reproducibility Checklist
- All random seeds are logged in `results/raw_logs.csv`.  
- The exact FEMNIST parquet URL is hard‑coded in `download.py`.  
- SHA‑256 checksum of the raw file is stored in `data/checksums.json`.  
- No GPU is required; the same commands run on a fresh GitHub Actions runner and reproduce identical results.

**Note on ε representation**: In `results/raw_logs.csv` the non‑DP baseline uses the literal string `"inf"` for the `epsilon` field, which is allowed by the results schema.

Enjoy your analysis!  

---

