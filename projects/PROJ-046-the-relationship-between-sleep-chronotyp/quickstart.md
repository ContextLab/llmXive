# Quickstart Guide: Sleep Chronotype and Moral Judgement Analysis

This guide provides instructions for setting up the environment, preparing data, and running the analysis pipeline for the study on the relationship between sleep chronotype and moral judgement.

## Prerequisites

- **R Version**: 4.3 or higher
- **Python**: 3.8+ (for pipeline orchestration scripts)
- **Git**: For version control
- **Internet Connection**: Required for initial package installation

## 1. Setup Environment

### 1.1 Clone the Repository
```bash
git clone <repository-url>
cd PROJ-046-the-relationship-between-sleep-chronotyp
```

### 1.2 Initialize R Environment
The project uses `renv` for package management.
```bash
# Run the setup script to initialize renv and install dependencies
python code/00_setup_r_env.py
```
*This will check your R version, initialize `renv`, and install the required packages (`tidyverse`, `lme4`, `emmeans`, etc.).*

### 1.3 Verify Setup
Ensure all directories and configurations are in place:
```bash
python code/06_validate_quickstart.py
```

## 2. Data Preparation

### 2.1 Required Data Structure
The pipeline requires a single merged CSV file located at `data/raw/study_data.csv`.

**Required Columns:**
- `MEQ_score`: Morningness-Eveningness Questionnaire total score (numeric)
- `MFQ_care`: Moral Foundations Questionnaire - Care subscale (numeric)
- `MFQ_fairness`: MFQ - Fairness subscale (numeric)
- `MFQ_loyalty`: MFQ - Loyalty subscale (numeric)
- `MFQ_authority`: MFQ - Authority subscale (numeric)
- `MFQ_sanctity`: MFQ - Sanctity subscale (numeric)
- `PSQI`: Pittsburgh Sleep Quality Index score (numeric)
- `age`: Participant age (numeric)
- `sex`: Participant sex (character)
- `acute_sleepiness`: Acute sleepiness rating (numeric)

**Note:** No public dataset currently contains all these variables. You must provide this file manually or via a custom merge of your survey data. See `data/raw/README_DATA_NEEDED.md` for details.

### 2.2 Place Your Data
1. Ensure your data is saved as a CSV file.
2. Place the file at: `data/raw/study_data.csv`
3. Ensure the file uses UTF-8 encoding and comma delimiters.

## 3. Running the Pipeline

The pipeline executes sequentially through ingestion, classification, analysis, and reporting.

### 3.1 Full Pipeline Execution
```bash
# Run the complete analysis pipeline
python code/00_config.py && \
python code/01_ingest.py && \
python code/02_classify.py && \
python code/02.5_final_exclusion_check.py && \
python code/03_analysis.py && \
python code/04_report.py && \
python code/05_validate_report.py
```

*Alternatively, use the convenience script if available:*
```bash
./run_pipeline.sh
```

### 3.2 Generating the Report
The final report is generated as an HTML file:
```bash
python code/04_render_report.py
```
Output: `reports/chronotype_moral_analysis.html`

## 4. Troubleshooting

This section addresses common failure modes and abort conditions.

### 4.1 Missing Columns (Abort Condition)
**Symptom:** The pipeline stops immediately with an error message: `ABORT: Missing required columns in input data.`

**Cause:** The input file `data/raw/study_data.csv` is missing one or more of the required columns listed in Section 2.1.

**Fix:**
1. Open your source data file.
2. Verify that all 10 required columns are present and spelled exactly as listed.
3. Ensure there are no hidden characters or encoding issues in the header row.
4. Resave the file as a clean CSV and place it in `data/raw/study_data.csv`.

### 4.2 High Exclusion Rate (>20%) (Abort Condition)
**Symptom:** The pipeline stops at the `02.5_final_exclusion_check` step with an error: `ABORT: Exclusion rate exceeds 20% threshold.`

**Cause:** More than 20% of the original rows were excluded due to invalid `MEQ_score` or out-of-range `MFQ` scores.

**Fix:**
1. Check `logs/classify_exclusions.log` to see which rows were excluded and why.
2. Review your data collection process to ensure valid responses were recorded.
3. If the high exclusion rate is due to data quality issues (e.g., many `NA` values in `MEQ_score`), you must clean the source data before re-running.
4. If the exclusion rate is legitimate (e.g., strict inclusion criteria), you may need to collect more data to reach a sufficient sample size. **Do not** modify the threshold in the code to bypass this check; the 20% limit is a hard gate for data quality assurance.

### 4.3 Missing Data File
**Symptom:** `FileNotFoundError: data/raw/study_data.csv`

**Cause:** The required input file has not been placed in the `data/raw/` directory.

**Fix:**
1. Ensure your merged dataset is saved as `study_data.csv`.
2. Copy the file to the `data/raw/` directory.
3. Verify file permissions allow reading.

### 4.4 VIF Warnings (Non-Blocking)
**Symptom:** Warning messages in `logs/vif_warnings.log` indicating Variance Inflation Factors (VIF) > 2.

**Cause:** High multicollinearity between predictors (e.g., age and acute_sleepiness).

**Fix:**
1. The pipeline will **not** abort but will mark the results as "Invalid" in `data/derived/vif_flag.csv`.
2. Review the `reports/vif_visualization.png` to identify correlated predictors.
3. Consider removing or combining highly correlated variables for the final model if publication is the goal.

### 4.5 R/Package Errors
**Symptom:** Errors related to missing R packages or version mismatches.

**Fix:**
1. Re-run the setup script: `python code/00_setup_r_env.py`
2. Ensure `renv` is active: `R -e "renv::activate()"`
3. Check `renv.lock` to ensure all packages are listed.

## 5. Verification and Testing

### 5.1 Run Unit Tests
```bash
python -m pytest tests/ -v
```

### 5.2 Run All Tests (Including Pipeline Smoke Tests)
```bash
./run_all_tests.sh
```
*This script runs unit tests, the benchmark accuracy test (T014), and renders the report using test data.*

## 6. Output Files

After a successful run, check the following directories:

- `data/processed/`: Cleaned data (`cleaned_data.csv`)
- `data/derived/`: Classified data, ANCOVA results, effect sizes, reliability metrics
- `logs/`: Execution logs and exclusion logs
- `reports/`: Final HTML report, VIF visualization, lint reports

## 7. Support

If you encounter issues not covered here, please refer to the project documentation in `docs/README.md` or contact the research team.