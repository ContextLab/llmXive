# Quickstart: Quantifying the Impact of Data Cleaning

## Prerequisites
- Python 3.11 (installed on the runner or locally).  
- Git (to clone the repository).  
- Internet access (to download OpenML datasets).

## Step‑by‑Step Guide

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/quantify-cleaning-impact.git
   cd quantify-cleaning-impact
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the full pipeline**
   ```bash
   python -m src.main
   ```
   The script will:
   - Download and checksum the multiple datasets (`data/raw/`).
   - Generate `dataset_metadata.json`.
   - Perform baseline analyses.
   - Apply all cleaning variants (outlier thresholds, imputation, recoding).
   - Run assumption checks and robust fall‑backs.
   - Execute a sufficient number of bootstrap iterations.
   - Compute delta metrics and sensitivity analyses.
   - Produce `power_analysis.txt`, figures, and `comparison_report.json`.

4. **Validate artefacts**
   ```bash
   pytest -q tests/contract
   ```
   All contract tests must pass. The citation‑validation script will also run automatically at the end of the pipeline; its log appears in `logs/citation_validation.log`.

5. **Inspect results**
   - JSON artefacts are under `data/processed/`.  
   - Figures are under `output/figures/`.  
   - The aggregated report can be opened with any JSON viewer or loaded into a notebook for further exploration.

## Re‑Running with Custom Settings
- To change the number of bootstrap iterations, edit `src/config.py`:
  ```python
  BOOTSTRAP_ITERATIONS = 2000   # any positive integer
  ```
- To use a different random seed, modify `RANDOM_SEED` in the same file.

## Expected Runtime
On the GitHub Actions free tier (2 CPU cores, ≈ 7 GB RAM) the full pipeline completes in **[deferred]**. Memory usage stays below **5 GB** thanks to streaming for the largest dataset.

---

