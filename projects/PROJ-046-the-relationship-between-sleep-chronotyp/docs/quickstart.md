# Quickstart Guide: Chronotype and Moral Judgement Analysis Pipeline

## Overview
This pipeline analyzes the relationship between sleep chronotype (MEQ) and moral judgement (MFQ), controlling for sleep quality (PSQI) and acute sleepiness. It produces a reproducible RMarkdown report with ANCOVA results, effect sizes, and sensitivity analyses.

## Prerequisites
- **R Version**: 4.3 or higher
- **Operating System**: Linux, macOS, or Windows (WSL recommended for CI compatibility)
- **Disk Space**: Minimum 500MB free space
- **RAM**: Minimum 2GB available
- **Python**: 3.8+ (for pipeline orchestration scripts)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd PROJ-046-the-relationship-between-sleep-chronotyp
```

### 2. Initialize R Environment
Run the setup script to install dependencies and initialize `renv`:
```bash
python code/00_setup_r_env.py
```
This will:
- Check R version (must be >= 4.3)
- Initialize `renv`
- Install required packages (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`, `emmeans`)

### 3. Prepare Data
**CRITICAL**: The pipeline requires a user-provided merged CSV file. No synthetic data is permitted for primary analysis.

1. Ensure your data file is located at: `data/raw/study_data.csv`
2. The file **MUST** contain the following columns:
 - `MEQ_score` (numeric)
 - `MFQ_care` (numeric)
 - `MFQ_fairness` (numeric)
 - `MFQ_loyalty` (numeric)
 - `MFQ_authority` (numeric)
 - `MFQ_sanctity` (numeric)
 - `PSQI` (numeric)
 - `age` (numeric)
 - `sex` (character)
 - `acute_sleepiness` (numeric)

If you do not have this file, see `data/raw/README_DATA_NEEDED.md` for instructions on data acquisition.

## Running the Pipeline

### Full Pipeline Execution
To run the entire analysis pipeline from ingestion to report generation:
```bash
python code/run_pipeline.py
```

### Individual Steps
You can also run specific steps independently:

1. **Ingest and Clean Data**:
 ```bash
 python code/01_ingest.py
 ```
 Output: `data/processed/cleaned_data.csv`

2. **Classify Chronotypes**:
 ```bash
 python code/02_classify.py
 ```
 Output: `data/derived/classified_data.csv`

3. **Run ANCOVA Analysis**:
 ```bash
 python code/03_analysis.py
 ```
 Output: `data/derived/ancova_results.csv`, `data/derived/effect_sizes.csv`

4. **Generate Report**:
 ```bash
 python code/04_render_report.py
 ```
 Output: `reports/chronotype_moral_analysis.html`

5. **Validate Report**:
 ```bash
 python code/05_validate_report.py
 ```

## Troubleshooting

This section details common abort conditions and how to resolve them.

### 1. Missing Required Columns (Abort in T011)
**Error Message**: `ABORT: Missing required columns. Found: [list]. Missing: [list].`

**Cause**: The input file `data/raw/study_data.csv` is missing one or more required columns listed in the Prerequisites section.

**Resolution**:
- Verify your CSV file contains all required columns: `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `age`, `sex`, `acute_sleepiness`.
- Check for typos in column names (case-sensitive).
- Ensure no hidden characters or encoding issues (save as UTF-8 CSV).
- If columns are missing, you must provide a valid dataset. See `data/raw/README_DATA_NEEDED.md` for data acquisition guidance.

### 2. High Exclusion Rate (Abort in T012.5)
**Error Message**: `ABORT: Exclusion rate (XX.X%) exceeds threshold (20.0%). Data quality too low for analysis.`

**Cause**: More than 20% of rows were excluded due to invalid MEQ scores or out-of-range MFQ values.

**Resolution**:
- Review `logs/classify_exclusions.log` to identify the specific reasons for exclusions.
- Check your data collection method for systematic errors (e.g., survey logic failures, data entry errors).
- If exclusions are due to `NA` values, ensure data collection captured all required fields.
- If the dataset is too small or noisy, consider recruiting more participants or revising the data collection protocol.
- **Do not** artificially manipulate data to bypass this check.

### 3. Missing Data File (Abort in T011)
**Error Message**: `ABORT: Input file 'data/raw/study_data.csv' not found.`

**Cause**: The required input file does not exist at the expected path.

**Resolution**:
- Ensure `data/raw/study_data.csv` exists in the project root.
- If you have not yet acquired data, follow the instructions in `data/raw/README_DATA_NEEDED.md`.
- Do not attempt to run the pipeline without valid input data.

### 4. VIF Warning (Non-Blocking)
**Warning Message**: `WARNING: VIF > 2 detected for predictor [name] in model [subscale]. Results may be unreliable.`

**Cause**: High multicollinearity between predictors (Variance Inflation Factor > 2).

**Resolution**:
- This is a **warning**, not an abort. The pipeline will continue but mark results as "Invalid" in `data/derived/vif_flag.csv`.
- Review `reports/vif_visualization.png` to identify collinear predictors.
- Consider removing or combining correlated predictors if publication is the goal.
- The final report will include a note about this limitation.

### 5. R Environment Issues
**Error Message**: `R version X.Y.Z is installed. Required: >= 4.3.0` or `renv not initialized.`

**Cause**: R version is too old or `renv` environment is not set up.

**Resolution**:
- Update R to version 4.3 or higher.
- Re-run `python code/00_setup_r_env.py` to initialize `renv`.
- Ensure `renv` packages are installed: `Rscript -e 'renv::restore()'`

### 6. CI Runner Compatibility
**Error Message**: `CI Check Failed: RAM usage exceeds limit` or `CPU cores insufficient.`

**Cause**: The runner does not meet minimum resource requirements.

**Resolution**:
- Ensure at least 2GB RAM and 2 CPU cores are available.
- If running on a free-tier CI, check resource limits and consider upgrading or optimizing data processing (e.g., streaming large datasets).
- Refer to `.github/workflows/ci.yml` for configuration details.

## Running Tests

To execute all verification tests:
```bash
bash run_all_tests.sh
```

This runs:
- Unit tests (`tests/test-*.R`)
- Benchmark accuracy test (`code/06_benchmark_accuracy.R --mode=test`)
- Report validation (`code/04_report.Rmd` render check)

## Output Files

After successful execution, you will find:
- **`data/processed/cleaned_data.csv`**: Ingested and filtered dataset.
- **`data/derived/classified_data.csv`**: Dataset with chronotype labels.
- **`data/derived/ancova_results.csv`**: ANCOVA results with p-values and effect sizes.
- **`data/derived/sensitivity_sweep.csv`**: Sensitivity analysis across alpha thresholds.
- **`reports/chronotype_moral_analysis.html`**: Final analysis report.
- **`reports/vif_visualization.png`**: VIF diagnostic plot.

## Support

For issues not covered here, check the logs in `logs/` or refer to the full documentation in `docs/`.