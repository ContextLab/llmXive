# Quickstart: Predicting Bacterial Antibiotic Resistance (Real‑Data Pipeline)

This guide walks a new contributor through running the full analysis on the GitHub Actions free‑tier runner (or locally on a comparable Linux machine).

## Prerequisites
- Python 3.11
- Git
- `venv` or Conda (recommended)
- Internet access (required for downloading real genomes and AST data)

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
All pipeline stages are invoked via the `src/pipeline` modules. The orchestrator `run_all.py` runs the full workflow in order.

| Step | Command | Description |
|------|---------|-------------|
| **0 – Data Acquisition** | `python -m src.pipeline.download_data` | Downloads real *E. coli* and *S. aureus* assemblies and AST phenotypes from NCBI Pathogen Genome Browser, extracts ARG presence via CARD API, and writes raw FASTA files and phenotype parquet. If the required number of isolates cannot be obtained, the script logs a warning and aborts. |
| **0‑b – Power Check** | `python -m src.pipeline.power_check` | Calculates required N (≈ 1 400 for effect size = 0.1, 80 % power, α = 0.05). |
| **0‑c – Power Gate** | `python -m src.pipeline.power_gate` | Skips modeling for any species‑antibiotic pair with `observed_n < required_n`; logs a warning and records insufficiency in the final report. |
| **1 – Baseline Feature Matrix** | `python -m src.pipeline.extract_baseline` | Builds `arg_matrix.csv` from the real CARD results. |
| **2 – Extended Feature Construction** | `python -m src.pipeline.extract_extended` | Merges SNP counts (via `snippy` + `snp-sites`), binned MGE distances (via `mob-suite` and `isfinder`), and confounder encodings; filters isolates with < 90 % “coverage”. |
| **3 – Inner‑CV Feature Selection & Hyper‑parameter Tuning** | `python -m src.pipeline.feature_selection` | Variance‑threshold → optional chi‑square → optional PCA → grid search with early‑stopping, all inside each inner 5‑fold CV fold. |
| **4 – Outer‑Loop Model Training & Evaluation** | `python -m src.pipeline.train_model` | 5‑fold stratified CV trains XGBoost and Random Forest classifiers (baseline & integrated) using hyper‑parameters from inner CV; stores per‑fold AUC, Precision, Recall, F1. |
| **5 – Paired‑Outcome Significance Test (Wilcoxon)** | `python -m src.pipeline.stats_validation --wilcoxon` | Performs a **two‑sided Wilcoxon signed‑rank test** on paired predicted probabilities (baseline vs. integrated) for each outer‑fold test set; outputs `wilcoxon_results.csv`. |
| **6 – Mann‑Whitney & FDR** | `python -m src.pipeline.stats_validation --mw-test` | Runs Mann‑Whitney U on SNP/MGE feature distributions, applies Benjamini‑Hochberg FDR, generates `mannwhitney_results.csv`. |
| **7 – Phylogeny‑aware Permutation** | `python -m src.pipeline.stats_validation --perm-test` | Runs `pyseer` permutation test, outputs `permutation_results.csv`. |
| **8 – Comparative Report & Threshold Sweep** | `python -m src.pipeline.report --thresholds 0.3 0.5 0.7` | Generates `report.pdf` and `metrics.json` (populated with overall deltas, threshold analysis, power analysis, and explicit abort flags if data were insufficient). |
| **9 – Contract Validation** | `pytest -q tests/contract` | Checks `metrics.json` against `contracts/metrics.schema.yaml`. Validates FR‑018 and SC‑003. |
| **10 – Feasibility Monitoring** | `python -m src.pipeline.monitor_feasibility` | Records wall‑clock time and peak RAM for each phase; fails if > 6 h or > 7 GB, satisfying FR‑018 and SC‑003. |
| **11 – Edge‑Case Logging** | Integrated in each script | Logs any power‑insufficiency warnings, class‑imbalance checks, confounder sparsity, and download failures (FR‑008, FR‑009, FR‑010). |

## Expected Outputs (all under `data/reports/`)
- `baseline_metrics.csv`
- `integrated_metrics.csv`
- `wilcoxon_results.csv`
- `mannwhitney_results.csv`
- `permutation_results.csv`
- `report.pdf`
- `metrics.json` (conforms to `contracts/metrics.schema.yaml`)
- `checksums.txt` (SHA‑256 checksums for all generated raw files)

## Re‑running / Updating
- To change the isolate limit or random seed, edit `src/pipeline/config.py` (`MAX_ISOLATES`, `RANDOM_SEED`).  
- To add a new antibiotic, ensure the download step creates a balanced split; otherwise the pipeline will skip it and log a warning.  

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).

**Important:** If the required real dataset cannot be obtained, the pipeline aborts early and no downstream results are produced. When a suitable open dataset becomes available, re‑run the pipeline without code changes.

---


