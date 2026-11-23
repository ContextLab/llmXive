# Quickstart Guide: Chronotype & Moral Judgement Pipeline

## 1. Quick Setup
Ensure you have R 4.3+ and Python 3.9+ installed.

```bash
# Clone the repo
git clone <repo-url>
cd projects/PROJ-046-the-relationship-between-sleep-chronotyp

# Initialize R environment (installs dependencies)
python code/00_setup_r_env.py
```

## 2. Prepare Data
Place your raw merged dataset in `data/raw/merged_data.csv`.
**Required Columns**: `MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`.

## 3. Run the Pipeline
Execute the following commands in order:

```bash
# 1. Ingest and Clean
Rscript code/01_ingest.R

# 2. Classify Chronotypes
Rscript code/02_classify.R

# 3. Check Exclusion Rates (Aborts if > 20%)
Rscript code/02.5_aggregate_exclusions.R

# 4. Reliability Check
Rscript code/02.6_reliability.R

# 5. Run ANCOVA
Rscript code/03_analysis.R

# 6. Generate Report
python code/04_render_report.py

# 7. Validate Report
python code/05_validate_report.py
```

## 4. View Results
Open `reports/chronotype_moral_analysis.html` in your browser to view the full analysis.
Check `data/derived/ancova_results.csv` for statistical tables.

## 5. Validation
To ensure your environment is ready:
```bash
python code/06_validate_quickstart.py
```
This script checks for R installation, `renv` setup, directory structure, and logging infrastructure.
