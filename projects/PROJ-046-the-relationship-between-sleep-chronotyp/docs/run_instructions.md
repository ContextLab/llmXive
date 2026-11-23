# Detailed Run Instructions

This document provides detailed instructions for running the pipeline, including error handling and configuration.

## Prerequisites Checklist

- [ ] R 4.3+ installed
- [ ] Python 3.8+ installed
- [ ] Raw data file placed in `data/raw/chronotype_data.csv`
- [ ] Project dependencies initialized (`renv` active)

## Step-by-Step Execution

### Step 1: Data Ingestion (`code/01_ingest.R`)

**Purpose**: Loads raw CSV, validates columns, handles missing `acute_sleepiness`.

**Command**:
```bash
Rscript code/01_ingest.R
```

**Expected Output**:
- `data/processed/cleaned_data.csv`
- `data/derived/ingest_exclusion_count.json`
- `logs/ingest_exclusions.log`

**Failure Mode**: If required columns are missing, the script will abort with a clear error message.

### Step 2: Chronotype Classification (`code/02_classify.R`)

**Purpose**: Assigns "morning", "intermediate", or "evening" labels based on MEQ scores.

**Command**:
```bash
Rscript code/02_classify.R
```

**Expected Output**:
- `data/derived/classified_data.csv`
- `logs/classify_exclusions.log`

**Logic**:
- MEQ >= 59: Morning
- MEQ <= 41: Evening
- Else: Intermediate
- Rows with NA/Out-of-range MFQ are excluded.

### Step 3: Aggregate Exclusions (`code/02.5_aggregate_exclusions.R`)

**Purpose**: Calculates total exclusion rate. Aborts if > 20%.

**Command**:
```bash
Rscript code/02.5_aggregate_exclusions.R
```

**Expected Output**:
- `data/derived/exclusions.log`
- `data/derived/exclusion_counts.json`

**Critical Check**: If `Total Excluded / Original Rows > 0.20`, the pipeline terminates.

### Step 4: Reliability Analysis (`code/02.6_reliability.R`)

**Purpose**: Computes Cronbach's Alpha for MFQ subscales.

**Command**:
```bash
Rscript code/02.6_reliability.R
```

**Expected Output**:
- `data/derived/reliability_metrics.csv`

### Step 5: ANCOVA Analysis (`code/03_analysis.R`)

**Purpose**: Runs ANCOVA for each subscale, calculates effect sizes, checks VIF.

**Command**:
```bash
Rscript code/03_analysis.R
```

**Expected Output**:
- `data/derived/ancova_results.csv`
- `data/derived/effect_sizes.csv`

**Critical Check**: If any Variance Inflation Factor (VIF) > 2, the pipeline aborts and logs to `logs/vif_error.flag`.

### Step 6: Report Generation (`code/04_render_report.py`)

**Purpose**: Renders the R Markdown report using generated data.

**Command**:
```bash
python3 code/04_render_report.py
```

**Expected Output**:
- `reports/chronotype_moral_analysis.html`

### Step 7: Report Validation (`code/05_validate_report.py`)

**Purpose**: Verifies the report contains all required sections.

**Command**:
```bash
python3 code/05_validate_report.py
```

**Expected Output**:
- Exit code 0 if valid, non-zero if missing sections.

## Configuration

- **Paths**: Defined in `code/00_config.R`.
- **Logging**: Configured in `code/utils_logging.R`.
- **R Environment**: Managed by `renv` (see `renv.lock`).

## Troubleshooting Guide

| Issue | Solution |
|-------|----------|
| `Error in library(...): there is no package called '...'` | Run `python3 code/00_setup_r_env.py` to install missing R packages. |
| `ABORT: Exclusion rate > 20%` | Review `data/raw/` for data quality; ensure columns are correctly named. |
| `ABORT: VIF > 2` | Check collinearity of covariates (PSQI, age, sex, acute_sleepiness). |
| `Rmarkdown render failed` | Ensure `rmarkdown` package is installed and `pandoc` is available. |
| `File not found: data/raw/...` | Verify your raw data file is in the correct location with the correct name. |
