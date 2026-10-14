# Quickstart: Quantifying the Impact of Data Cleaning

The quickstart shows how to run the full analysis on a fresh GitHub Actions runner.

## Prerequisites
* Python 3.11 (provided by the CI runner)
* `pip install -r requirements.txt` (see `requirements.txt` at the repository root)

## Step‑by‑Step Guide

1. **Clone the repository**  
   (GitHub Actions does this automatically.)

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Download and verify raw datasets**  
   ```bash
   python -m src.data_loader download_all
   ```
   This script:
   * Pulls each dataset from the verified URLs (see `research.md`) or from OpenML.
   * Computes SHA‑256 checksums and writes `data/hashes.json`.
   * Writes `data/processed/dataset_metadata.json` with outcome column name, sample size, missingness proportion, and checksum.
   * Aborts with a non‑zero exit code if any download fails or checksum mismatches.

4. **Run the full pipeline**  
   ```bash
   python -m src.main run_all
   ```
   `src.main` orchestrates the phases defined in `plan.md`:
   * Baseline analysis → `baseline_metrics.json`
   * Cleaning variants (outlier, imputation, recoding) → `cleaned_metrics.json`
   * Permutation FPR & synthetic benchmarks → `null_fpr_metrics.json`
   * Bootstrap variance → `bootstrap_metrics.json`
   * Sensitivity ANOVA (with assumption checks) → `sensitivity_metrics.json`
   * Wilcoxon hypothesis test (raw p‑values) → `hypothesis_test_results.json`
   * Comparison report & figures → `comparison_report.json`, `output/figures/*.png`
   * Power‑analysis generation → `power_analysis.txt`
   * Citation‑validation → runs the reference‑validator script.

5. **Validate contracts** (optional but recommended)  
   ```bash
   pytest -m contract
   ```
   The test suite loads each schema from `contracts/` and validates the corresponding JSON artefact, including the newly added `bootstrap_metrics.json`, `sensitivity_metrics.json`, and `hypothesis_test_results.json`.

6. **Inspect results**  
   * Open `data/processed/comparison_report.json` for aggregated numbers.  
   * View visualisations in `output/figures/`.  
   * Review `power_analysis.txt` for the a‑priori justification.  

All random seeds are fixed (`numpy.random.seed(42)`, `random_state=42`), guaranteeing reproducibility (Constitution Principle I).

## Debugging / Sub‑setting
For faster debugging you can limit the dataset list via the environment variable `DATASET_SUBSET` (comma‑separated dataset IDs). The pipeline respects the subset while still performing all phases.

---

