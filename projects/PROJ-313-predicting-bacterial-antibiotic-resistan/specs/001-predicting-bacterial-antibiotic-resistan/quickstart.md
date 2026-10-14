# Quickstart: Predicting Bacterial Antibiotic Resistance

This guide walks a new contributor through running the full analysis end‑to‑end on the GitHub Actions free‑tier runner (or locally on a comparable Linux machine).

## Prerequisites
- Python 3.11
- Git
- Conda or `venv` (recommended)
- Internet access (to download NCBI Pathogen Detection parquet files and query CARD)

## Setup
```bash
# 1️⃣ Clone the repository
git clone 
cd predicting-bacterial-antibiotic-resistance

# 2️⃣ Create a clean environment
python -m venv .venv
source .venv/bin/activate

# 3️⃣ Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution
All pipeline stages are invoked via the `src/pipeline/run_all.py` orchestrator.

| Step | Command | Description |
|------|---------|-------------|
| **0 – Data download & verification** | `python -m src.pipeline.download` | Downloads NCBI Pathogen Detection parquet files, verifies checksums, queries CARD for ARGs, filters low‑quality isolates, and writes `sample_sizes.csv`. |
| **1 – Baseline feature matrix** | `python -m src.pipeline.extract_baseline` | Builds `arg_matrix.csv`. |
| **2 – Extended features** | `python -m src.pipeline.extract_extended` | Calls `snippy` + `snp-sites` (excluding SNPs overlapping ARG loci), runs MOB‑suite & ISfinder, produces SNP and MGE CSVs, then merges & scales the raw extended feature matrix. |
| **2a – Feature selection** | `python -m src.pipeline.feature_selection` | Applies variance‑threshold filter, selects top 500 chi‑square features, optionally reduces to ≤ 100 PCs via PCA; outputs the dimension‑reduced matrix `selected_features.npy`. |
| **3 – Baseline hyper‑parameter tuning** | `python -m src.pipeline.hyperparameter_tuning baseline` | Grid search CV (max_depth, learning_rate, n_estimators, reg_lambda, reg_alpha) with early stopping; picks best hyper‑parameters for the ARG‑only model. |
| **4 – Baseline model training** | `python -m src.pipeline.train_baseline` | 5‑fold stratified CV XGBoost using the tuned hyper‑parameters; outputs `baseline_metrics.csv`. |
| **5 – Integrated hyper‑parameter tuning** | `python -m src.pipeline.hyperparameter_tuning integrated` | Same grid search and CV scheme on the full (selected) feature set. |
| **6 – Integrated model training** | `python -m src.pipeline.train_integrated` | Same CV using tuned hyper‑parameters; outputs `integrated_metrics.csv`. |
| **7 – Paired‑fold significance** | `python -m src.pipeline.stats_validation --paired-test` | Wilcoxon signed‑rank test on per‑fold metric deltas; generates `paired_test_results.csv`. |
| **8 – Mann‑Whitney & FDR** | `python -m src.pipeline.stats_validation --mw-test` | Generates `mannwhitney_results.csv`. |
| **9 – Phylogeny‑aware permutation** | `python -m src.pipeline.stats_validation --perm-test` | Generates `permutation_results.csv`. |
| **10 – Sensitivity & Power analysis** | `python -m src.pipeline.report --thresholds 0.3 0.5 0.7` | Produces `report.pdf` and `metrics.json`. |
| **11 – Contract validation** | `pytest -q tests/contract` | Checks `metrics.json` against `contracts/metrics.schema.yaml`. |

## Expected Outputs
- `data/reports/baseline_metrics.csv`
- `data/reports/integrated_metrics.csv`
- `data/reports/paired_test_results.csv`
- `data/reports/mannwhitney_results.csv`
- `data/reports/permutation_results.csv`
- `data/reports/report.pdf`
- `data/reports/metrics.json` (validated against contract)

## Re‑running / Updating
- To change the isolate limit, edit `src/pipeline/config.py` (`MAX_ISOLATES = 1000`).
- To add a new antibiotic, ensure it meets the 50/50 threshold; otherwise the pipeline will automatically skip it and log a warning.

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).