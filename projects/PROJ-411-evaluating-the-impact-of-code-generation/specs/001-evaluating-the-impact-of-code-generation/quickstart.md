# Quickstart: Evaluating the Impact of Code Generation on Code Review Burden

This guide walks you through reproducing the full analysis on a fresh GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11
- Internet access (to download the three HuggingFace parquet files)
- `git` (to clone the repository)

## Step‑by‑Step

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/PROJ-411-evaluating-the-impact-of-code-generation.git
   cd PROJ-411-evaluating-the-impact-of-code-generation
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Download and verify raw data**
   ```bash
   python code/download_data.py
   # Verifies SHA‑256 checksums; outputs data/raw/combined_prs.parquet
   ```

4. **Classify provenance**
   ```bash
   python code/classify_provenance.py \
       --input data/raw/combined_prs.parquet \
       --output data/processed/processed_prs.csv
   ```

5. **Compute metrics & apply primary filters**
   ```bash
   python code/compute_metrics.py \
       --input data/processed/processed_prs.csv \
       --output data/processed/filtered_prs.csv
   # Uses `first_comment_timestamp` when available to compute `review_active_seconds`;
   # falls back to `review_duration_seconds` if the timestamp is missing.
   ```

6. **Run outlier removal (default IQR = 1.5)**
   ```bash
   python code/sensitivity.py --mode outlier --iqr 1.5
   ```

7. **Statistical analysis**
   ```bash
   python code/statistical_analysis.py \
       --input data/processed/filtered_prs.csv \
       --results data/results/stats_summary.csv
   ```

8. **Validation (manual sample)**
   ```bash
   python code/validation.py \
       --input data/processed/filtered_prs.csv \
       --report data/results/validation_report.md
   ```

9. **Full sensitivity sweep**
   ```bash
   python code/sensitivity.py --mode full
   ```

10. **Generate the final report**
    ```bash
    python code/report.py \
        --stats data/results/stats_summary.csv \
        --validation data/results/validation_report.md \
        --output report.md
    ```

11. **Inspect results**
    - `report.md` contains all tables, figures (saved under `data/results/figures/`), and the required null‑result or robustness statements.
    - `data/results/stats_summary.csv` conforms to `contracts/statistical_results.schema.yaml`.
    - `data/processed/processed_prs.csv` conforms to `contracts/processed_prs.schema.yaml`.

All scripts log progress to `logs/` and abort cleanly if CPU/RAM limits are exceeded (SC‑005). The entire pipeline completes in < 5 h on the free‑tier runner.  
