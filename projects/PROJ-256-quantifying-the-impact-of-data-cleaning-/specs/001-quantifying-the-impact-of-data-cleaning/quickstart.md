# Quickstart: Running the Data‑Cleaning Impact Pipeline

## Prerequisites
- Python 3.11 installed (the CI runner provides it).
- Git 2.40+ and internet access to download the open datasets.
- No GPU required.

## Step‑by‑Step

```bash
# 1️⃣ Clone the repository
git clone
cd quantify-cleaning-impact

# 2️⃣ Create a virtual environment and install dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins all versions as listed in plan.md

# 3️⃣ Run the full pipeline (this will download data, run analyses, and produce artefacts)
python -m code.main
```

### What `code.main` does
| Stage | Output file(s) | Brief description |
|-------|----------------|-------------------|
| Data download & checksum | `data/raw/*`, `state/projects/…yaml` | Retrieves verified datasets, records SHA‑256. |
| Metadata generation | `data/processed/dataset_metadata.json` | Stores outcome column, size, missingness. |
| Baseline analysis | `data/processed/baseline_metrics.json`, `data/processed/analysis_results.json` | t‑tests / regressions on raw data. |
| Cleaning variants | `data/processed/cleaned_metrics.json`, `data/processed/null_fpr_metrics.json` | All outlier‑removal, imputation, recoding combos. |
| Bootstrap CI | `data/processed/bootstrap_metrics.json` | 1000 resamples per variant. |
| Permutation FPR | `data/processed/null_fpr_metrics.json` (adds FPR) | Outcome permuted **after** cleaning; outcome excluded from cleaning. |
| Multiple‑comparison correction | `data/processed/cleaned_metrics.json` (adds `adjusted_p_value`) | Holm‑Bonferroni per dataset. |
| Sensitivity analysis | `data/processed/sensitivity_metrics.json` | Factorial (cleaning × missingness) stratification. |
| Power analysis | `power_analysis.txt` | Wilcoxon‑based per‑dataset power checks. |
| Hypothesis testing | `data/processed/hypothesis_test_results.json` | Wilcoxon on Δ‑metrics. |
| Final report & figures | `data/processed/comparison_report.json`, `output/figures/*.png` | Forest plot, CI heatmap, summary table. |
| Validation | Console output `All schemas validated ✅` | Runs `code/validation.py` against contracts. |

### Running a Subset (for debugging)
```bash
# Only download data
python -m code.data_loader

# Run baseline only
python -m code.analysis --stage baseline

# Run cleaning + bootstrap for a single dataset (example)
python -m code.main --dataset-id wine_quality --stage cleaning_bootstrap
```

### Re‑producibility Tips
- All random seeds are defined in `code/config.py`. Changing the seed requires a full pipeline rerun to maintain hash consistency.
- The pipeline logs every major step to `logs/pipeline.log`.

### Expected Runtime
- Full run on the GitHub Actions free tier: **≈ 4 h 30 m**.
- Memory peak: **≈ 5.5 GB** (during permutation FPR for the largest dataset).

If the job exceeds the 6‑hour limit, the CI will automatically cancel; you can resume by re‑running the workflow (the pipeline is checkpointed after each stage).

---

