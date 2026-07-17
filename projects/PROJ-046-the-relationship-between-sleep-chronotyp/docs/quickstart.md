# Quick Start Guide: Chronotype-Moral Judgement Analysis

This guide provides the minimal steps to run the analysis pipeline on a fresh environment.

## 1. Environment Setup

Ensure you have **R 4.3+** and **Python 3.8+** installed.

```bash
# Verify R version
R --version

# Verify Python version
python3 --version
```

## 2. Initialize Project Dependencies

Run the setup scripts to install R packages and configure the project structure.

```bash
# Create directory structure and gitignore
python3 code/setup_project_structure.py

# Initialize R environment and install packages
python3 code/00_setup_r_env.py
python3 code/03_generate_renv_lock.py
```

## 3. Prepare Input Data

1. Obtain your raw dataset (CSV format) containing the required variables:
 `MEQ_score`, `MFQ_harm`, `MFQ_fairness`, `MFQ_purity`, `MFQ_loyalty`, `MFQ_authority`, `PSQI`, `acute_sleepiness`, `age`, `sex`.
2. Place the file as `data/raw/chronotype_data.csv`.

## 4. Execute the Pipeline

Run the following commands in sequence. Each script depends on the successful completion of the previous one.

```bash
# 1. Ingest and Clean Data
Rscript code/01_ingest.R

# 2. Classify Chronotypes
Rscript code/02_classify.R

# 3. Check Exclusion Rates
Rscript code/02.5_aggregate_exclusions.R

# 4. Calculate Reliability Metrics
Rscript code/02.6_reliability.R

# 5. Run ANCOVA Analysis
Rscript code/03_analysis.R

# 6. Render the Report
python3 code/04_render_report.py

# 7. Validate the Report
python3 code/05_validate_report.py
```

## 5. Verify Results

Upon successful completion:
- Check `reports/chronotype_moral_analysis.html` for the full analysis.
- Check `data/derived/` for CSV outputs.
- Check `logs/` for any exclusion details or warnings.

## Common Issues

- **"Rscript not found"**: Ensure R is added to your system PATH.
- **"Missing package"**: Re-run `code/00_setup_r_env.py`.
- **"Exclusion rate > 20%"**: Review your input data quality; the pipeline stops if too much data is missing.
