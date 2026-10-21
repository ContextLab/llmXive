# Quickstart: Predicting Bacterial Antibiotic Resistance (Synthetic Study)

This guide walks a new contributor through running the full synthetic analysis end‑to‑end on the GitHub Actions free‑tier runner (or locally on a comparable Linux machine).

## Prerequisites
- Python 3.11
- Git
- `venv` or Conda (recommended)
- Internet access (only to fetch the repository; no external data download required)

## Setup
```bash
# 1️⃣ Clone the repository
git clone https://github.com/your-org/predicting-bacterial-antibiotic-resistance.git
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
| **0‑a – Synthetic Data Generation** | `python -m src.pipeline.generate_synthetic` | Generates a comparable number of synthetic FASTA assemblies for *E. coli* and *S. aureus*, along with phenotype labels and confounder metadata; writes checksums to `data/checksums.txt`. |
| **0‑b – Power Check** | `python -m src.pipeline.power_check` | Calculates required sample size for effect size = 0.1; logs a warning if observed N < required but **continues**. |
| **0‑c – Power Gate** | `python -m src.pipeline.power_gate` | Skips modeling for any species‑antibiotic pair whose observed isolate count is below the required N; records the insufficiency in the final report. |
| **1 – Baseline Feature Matrix** | `python -m src.pipeline.extract_baseline` | Builds `arg_matrix.csv`. |
| **2 – Extended Features (incl. Confounders)** | `python -m src.pipeline.extract_extended` | Generates SNP counts (via `pysam`) and simulated MGE distance features (pure‑Python), **adds confounder columns** (geography, collection_date, sequencing_platform), and scales to `selected_features.npy`. |
| **3 – Inner‑CV Feature Selection & Hyper‑parameter Tuning** | `python -m src.pipeline.feature_selection` | Variance‑threshold → (optional) chi‑square ranking **only on training folds** → optional PCA (≤ 100 PCs) → grid search with early‑stopping; all inside the inner CV loop to prevent leakage. |
| **4 – Outer‑fold Model Training** | `python -m src.pipeline.train_model` | 5‑fold stratified CV XGBoost for baseline and integrated models; outputs `baseline_metrics.csv` and `integrated_metrics.csv`. |
| **5 – Paired‑Fold Significance** | `python -m src.pipeline.stats_validation --paired-test` | Paired **t‑test** on per‑fold metric deltas; creates `paired_test_results.csv`. |
| **6 – Mann‑Whitney & FDR** | `python -m src.pipeline.stats_validation --mw-test` | Runs Mann‑Whitney U on outer‑fold held‑out sets only; produces `mannwhitney_results.csv`. |
| **7 – Phylogeny‑aware Permutation** | `python -m src.pipeline.stats_validation --perm-test` | Runs `pyseer` permutation; produces `permutation_results.csv`. |
| **8 – Sensitivity & Power Analysis** | `python -m src.pipeline.report --thresholds 0.3 0.5 0.7` | Generates `report.pdf` and `metrics.json` (populated with **overall_metrics**, **per_fold_metrics**, **threshold_analysis**, **power_analysis**). |
| **9 – Contract Validation** | `pytest -q tests/contract` | Checks `metrics.json` against `contracts/metrics.schema.yaml`. |

## Expected Outputs (all under `data/reports/`)
- `baseline_metrics.csv`
- `integrated_metrics.csv`
- `paired_test_results.csv`
- `mannwhitney_results.csv`
- `permutation_results.csv`
- `report.pdf`
- `metrics.json`
- `checksums.txt`

## Re‑running / Updating
- To change the isolate limit or random seed, edit `src/pipeline/config.py` (`MAX_ISOLATES`, `RANDOM_SEED`).  
- To add a new antibiotic, ensure the synthetic phenotype generator creates a balanced (≈ equal) split; otherwise the pipeline will skip it and log a warning.  

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).
