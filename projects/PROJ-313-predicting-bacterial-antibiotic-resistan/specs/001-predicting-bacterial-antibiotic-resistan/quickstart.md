# Quickstart: Predicting Bacterial Antibiotic Resistance (Real‑Data First, Synthetic Fallback)

This guide walks a new contributor through running the full analysis on the GitHub Actions free‑tier runner (or locally on a comparable Linux machine).

## Prerequisites
- Python 3.11
- Git
- `venv` or Conda (recommended)
- Internet access (required for real data download from NCBI/CARD; no external data download needed for the synthetic fallback)

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
| **0‑a – Real Data Download** | `python -m src.pipeline.download_real` | Attempts to fetch *E. coli* and *S. aureus* FASTA assemblies and AST phenotypes from NCBI Pathogen Browser and CARD. Uses **Bio.Entrez** to query the NCBI Assembly database for accession numbers matching the target species and antibiotics, then downloads the corresponding FASTA files and associated BioSample AST fields. If any download fails, the script logs the error and **automatically falls back** to the synthetic generator (Phase 0‑a). |
| **0‑a‑b – Synthetic Fallback** | `python -m src.pipeline.generate_synthetic` | Generates deterministic synthetic FASTA assemblies, phenotype parquet, and confounder tables; writes checksums to `data/checksums.txt`. **Only used for pipeline sanity‑checking; results are not used for the primary scientific claim.** |
| **0‑b – Power Check** | `python -m src.pipeline.power_check` | Calculates required N (≈ 1 400 for effect size = 0.1, 80 % power, α = 0.05). If power < 0.8 the pipeline **aborts** downstream modeling (Phase 0‑c) and records a clear warning in the final report. |
| **0‑c – Power Gate** | `python -m src.pipeline.power_gate` | Skips modeling for any species‑antibiotic pair whose `observed_n < required_n`; logs a warning and records insufficiency in the final report. |
| **1 – Baseline Feature Matrix** | `python -m src.pipeline.extract_baseline` | Builds `arg_matrix.csv` using the CARD JSON API (real data) or the bundled static CARD subset (synthetic fallback). |
| **2 – Extended Feature Construction** | `python -m src.pipeline.extract_extended` | Generates SNP counts **via `snippy` followed by `snp-sites`** on real assemblies, computes genomic distances from each ARG to the nearest transposon (via ISfinder) or plasmid (via MOB‑suite), adds confounder columns (one‑hot geography & platform, ordinal year), and filters isolates with < 90 % core‑genome coverage. When synthetic fallback is active, placeholder numeric features are generated but flagged as demo‑only. |
| **3 – Inner‑CV Feature Selection & Hyper‑parameter Tuning** | `python -m src.pipeline.feature_selection` | Variance‑threshold filtering → optional chi‑square ranking → optional PCA → grid search with early‑stopping. All steps occur within each **inner 5‑fold CV** fold to prevent leakage (addresses methodology‑79af9d6b). |
| **4 – Outer‑Loop Model Training & Evaluation** | `python -m src.pipeline.train_model` | 5‑fold stratified CV trains XGBoost and Random Forest classifiers (baseline & integrated) using hyper‑parameters from inner CV. Stores per‑fold metrics. |
| **5 – Paired‑Outcome Significance Test** | `python -m src.pipeline.stats_validation --wilcoxon` | Performs a **two‑sided Wilcoxon signed‑rank test** on paired predicted probabilities (baseline vs. integrated) for each outer fold, producing `paired_test_results.csv`. |
| **6 – Mann‑Whitney & FDR** | `python -m src.pipeline.stats_validation --mw-test` | Runs Mann‑Whitney U on outer‑fold held‑out sets, applies Benjamini‑Hochberg FDR, generates `mannwhitney_results.csv`. |
| **7 – Phylogeny‑aware Permutation** | `python -m src.pipeline.stats_validation --perm-test` | Runs `pyseer` permutation test, outputs `permutation_results.csv`. |
| **8 – Comparative Report & Threshold Sweep** | `python -m src.pipeline.report --thresholds 0.3 0.5 0.7` | Generates `report.pdf` and `metrics.json` (populated with overall deltas, threshold analysis, power analysis, and edge‑case warnings). |
| **9 – Contract Validation** | `pytest -q tests/contract` | Checks `metrics.json` against `contracts/metrics.schema.yaml`. This step validates FR‑018 (computational feasibility) and SC‑003. |
| **10 – Feasibility Monitoring** | `python -m src.pipeline.monitor_feasibility` | Records wall‑clock time and peak RAM for each phase; fails the run if limits (≤ 6 h, ≤ 7 GB) are exceeded, thereby satisfying FR‑018 and SC‑003. |
| **11 – Edge‑Case Logging** | Integrated in each script | Logs any download/API failures, low‑coverage isolates, class‑imbalance warnings, and power insufficiencies (FR‑008, FR‑009, FR‑010). |

## Expected Outputs (all under `data/reports/`)
- `baseline_metrics.csv`
- `integrated_metrics.csv`
- `paired_test_results.csv`
- `mannwhitney_results.csv`
- `permutation_results.csv`
- `report.pdf` – includes a clear “Demo‑only” flag if synthetic data were used.  
- `metrics.json` – conforms to `contracts/metrics.schema.yaml`.  
- `checksums.txt` – SHA‑256 checksums for all generated raw files.  

## Re‑running / Updating
- To change the isolate limit or random seed, edit `src/pipeline/config.py` (`MAX_ISOLATES`, `RANDOM_SEED`).  
- To add a new antibiotic, ensure the synthetic phenotype generator creates a balanced split; otherwise the pipeline will skip it and log a warning.  

All random processes use seeds defined in `src/utils/random_seeds.py` to guarantee reproducibility (Constitution I).

**Important:** When real data are successfully downloaded, all downstream steps use the authentic assemblies and AST phenotypes, providing results that directly address the research question. If the fallback is used, the final report clearly labels the results as “demo‑only” and notes the associated scientific limitation.

---



