# Quick Start Guide: Chronotype and Moral Judgement Analysis Pipeline

This guide provides instructions for setting up and running the automated science pipeline for analyzing the relationship between sleep chronotype and moral judgement.

## Prerequisites

- R version 4.3 or higher
- Python 3.9+ (for pipeline orchestration scripts)
- Git
- Sufficient disk space (~2GB for dependencies and derived data)

## Setup

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-046-the-relationship-between-sleep-chronotyp
 ```

2. **Initialize R environment**:
 ```bash
 Rscript code/00_setup_r_env.R
 ```
 This will install required R packages (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`, `emmeans`) and initialize `renv`.

3. **Set up data directories**:
 ```bash
 Rscript code/setup_data_structure.R
 ```
 This creates `data/raw/`, `data/processed/`, `data/derived/`, and `logs/` directories.

4. **Prepare your data**:
 - Place your merged CSV file at `data/raw/study_data.csv`.
 - **Required columns**: `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `acute_sleepiness`, `age`, `sex`.
 - Ensure no required columns are missing (see Troubleshooting below).
 - See `data/raw/README_DATA_NEEDED.md` for detailed data requirements.

## Running the Pipeline

Execute the pipeline in order:

```bash
# 1. Capture original row count
Rscript code/00.5_capture_original_count.R

# 2. Ingest and clean data
Rscript code/01_ingest.R

# 3. Classify chronotypes
Rscript code/02_classify.R

# 4. Final exclusion check (Hard Gate)
Rscript code/02.5_final_exclusion_check.R

# 5. Run ANCOVA analysis
Rscript code/03_analysis.R

# 6. Generate report
Rscript code/04_render_report.R

# 7. Validate report
Rscript code/05_validate_report.R
```

Alternatively, run all steps sequentially:
```bash
./run_all_steps.sh
```

## Output Artifacts

- `data/processed/cleaned_data.csv`: Cleaned dataset after ingestion
- `data/derived/classified_data.csv`: Dataset with chronotype labels
- `data/derived/ancova_results.csv`: ANCOVA results with effect sizes
- `data/derived/sensitivity_sweep.csv`: Sensitivity analysis results
- `reports/chronotype_moral_analysis.html`: Final analysis report
- `logs/`: Log files for exclusions and warnings

## Troubleshooting

The pipeline includes several hard-gate abort conditions. Below are the specific scenarios that will cause the pipeline to stop, along with how to fix them.

### 1. Missing Required Columns in Input Data

**Error Message**: `ABORT: Missing required columns in input data. Required: [list of columns]. Found: [list of columns].`

**Cause**: The input file `data/raw/study_data.csv` is missing one or more of the required columns defined in FR-001.

**Fix**:
- Verify the column names in your CSV file match exactly: `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `acute_sleepiness`, `age`, `sex`.
- Check for typos, extra spaces, or case sensitivity issues.
- Ensure the file is a valid CSV (comma-separated, proper quoting).
- If you are using a template, fill in all required columns.

### 2. Excessive Data Exclusion Rate (>20%)

**Error Message**: `ABORT: Exclusion rate (XX%) exceeds 20% threshold. Review data quality or collection methods.`

**Cause**: More than 20% of rows were excluded due to invalid MEQ scores or out-of-range MFQ scores (as defined in FR-006). This check is performed in `code/02.5_final_exclusion_check.R`.

**Fix**:
- Inspect `logs/classify_exclusions.log` to see which rows were excluded and why.
- Check your data collection process for systematic errors (e.g., survey skip logic, data entry mistakes).
- Verify that MEQ scores are within the valid range (typically 1-64) and MFQ subscale scores are within expected bounds.
- If the high exclusion rate is due to a specific data quality issue, clean the raw data and re-run the pipeline.
- **Note**: Rows excluded for missing `acute_sleepiness` are NOT counted towards this 20% threshold.

### 3. Missing Input File

**Error Message**: `ABORT: Input file data/raw/study_data.csv not found.`

**Cause**: The pipeline cannot find the required input data file.

**Fix**:
- Ensure `data/raw/study_data.csv` exists in the correct location.
- Check file permissions.
- If you are running in a test environment, ensure you have provided a valid test file or are running with the appropriate test flag (if applicable for specific scripts).

### 4. Low Group Balance Alert

**Warning Message**: `WARNING: Intermediate chronotype group exceeds 70% of sample. Consider recruiting more extreme-type participants.`

**Cause**: The proportion of participants classified as "intermediate" is >70%, which may reduce statistical power for detecting differences between morning and evening types.

**Fix**:
- This is a warning, not a hard abort. The pipeline will continue.
- Review your recruitment strategy to ensure a more balanced distribution of chronotypes.
- The final report will include this alert in the limitations section.

### 5. High Variance Inflation Factor (VIF > 2)

**Warning Message**: `WARNING: VIF > 2 detected for predictor(s). Results may be unreliable due to multicollinearity.`

**Cause**: One or more predictors in the ANCOVA model have a Variance Inflation Factor greater than 2, indicating potential multicollinearity.

**Fix**:
- This is a warning, not a hard abort. The pipeline will continue but mark results as potentially unreliable.
- Examine `data/derived/vif_flag.csv` and `logs/vif_warnings.log` for details.
- Consider removing or combining highly correlated predictors in future studies.
- The final report will include a note about this limitation.

### 6. R or Python Environment Issues

**Error Message**: `Error: R version < 4.3 required` or `ModuleNotFoundError: No module named '...'`

**Cause**: Missing or incompatible runtime environments.

**Fix**:
- Ensure R version is 4.3 or higher (`R --version`).
- Re-run `code/00_setup_r_env.R` to reinstall R packages.
- Ensure Python 3.9+ is installed and active.
- Install missing Python dependencies: `pip install -r requirements.txt`.

### 7. Test Mode vs. Production Mode

**Error Message**: `ABORT: This script requires --mode=test flag.` or `ABORT: Output path validation failed.`

**Cause**: Scripts designed for testing (e.g., `code/06_benchmark_accuracy.R`) are being run without the required `--mode=test` flag, or output paths are incorrect.

**Fix**:
- Add `--mode=test` to the command line when running test-specific scripts.
- Verify that output paths are within `data/derived/` for test scripts.
- Do not run test scripts in production mode.

## Getting Help

- Check the `logs/` directory for detailed error messages and exclusion logs.
- Review `docs/README.md` for additional context.
- Refer to `data/raw/README_DATA_NEEDED.md` for data requirements.
- Consult the project's issue tracker for known problems.