# Quickstart: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

## Prerequisites
- GitHub Actions runner (or local Linux environment) with **Python 3.11**.
- Internet access to download the verified SRA parquet files.
- No GPU required.

## Setup

```bash
# Clone the repository (assumed already present in the CI workspace)
git checkout 001-predict-plant-defense

# Create a virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes pandas, scikit-learn, datasets, rpy2, etc.
```

## Execution Steps

```bash
# 0️⃣ Data‑availability guard (fails fast if metabolomics missing)
python -m code.acquire   # downloads SRA parquet, validates checksum

# 1️⃣ Pre‑process 16S reads (optional DADA2; skipped if only ASV table is provided)
python -m code.curate   # produces asv_table.csv

# 2️⃣ Integration (will abort here if metabolomics data absent)
python -m code.integrate   # produces merged_dataset.csv, runs missing‑data assessment

# 3️⃣ Core modeling (only runs if integration succeeded)
python -m code.model       # performs CV, reports R², saves figures

# 4️⃣ Permutation test (reduced to 200 permutations for compute feasibility)
python -m code.permutation   # generates p‑value file (parallelised)

# 5️⃣ Sensitivity analysis (sweeps PCA variance thresholds AND RF hyper‑parameters)
python -m code.sensitivity   # saves table of R² across configurations

# 6️⃣ Power analysis (post‑hoc)
python -m code.power         # computes effect‑size‑based power and writes summary

# 7️⃣ Summary report
python -m code.report        # aggregates all results into `results/summary.md`
```

## Expected Outputs
- `data/processed/merged_dataset.csv` (validated against contract)  
- `results/cv_metrics.json`  
- `results/permutation_pvalue.txt`  
- `results/sensitivity_table.csv`  
- `results/power_summary.txt`  
- Figures under `figures/` (`regression_*.png`, `feature_importance.png`, `sensitivity.png`, `species_performance.png`)  

If the metabolomics data are missing, step 2 will terminate with:

```
Error: missing metabolomics data – cannot proceed.
```

This satisfies **FR‑008** and **SC‑005**.

## Re‑running with a New Dataset
To substitute a different open metabolomics or 16S dataset, add its download URL to `code/acquire.py`, ensure it is listed in the verified datasets block, and rerun the pipeline. No code changes are required beyond the URL.

---

