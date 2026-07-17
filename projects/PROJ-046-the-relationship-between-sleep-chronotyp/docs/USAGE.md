# Usage Guide: Automated Research Pipeline

## Introduction
This guide details the usage of the `code/` scripts for researchers and data scientists.

## Script Reference

### `code/00_setup_r_env.py`
**Purpose**: Initializes the R environment and installs dependencies.
**Usage**: `python code/00_setup_r_env.py`
**Dependencies**: `utils_renv.py`

### `code/01_ingest.R`
**Purpose**: Loads raw CSV, validates columns, handles missing `acute_sleepiness`, and saves cleaned data.
**Input**: `data/raw/merged_data.csv`
**Output**: `data/processed/cleaned_data.csv`
**Fail Condition**: Missing required columns (ABORT).

### `code/02_classify.R`
**Purpose**: Assigns chronotype labels based on MEQ thresholds.
**Logic**:
- `MEQ >= 59`: "morning"
- `MEQ <= 41`: "evening"
- Else: "intermediate"
**Fail Condition**: Out-of-range MFQ scores or missing MEQ (excluded and logged).

### `code/02.5_aggregate_exclusions.R`
**Purpose**: Aggregates exclusion counts from ingestion and classification.
**Logic**: Calculates total exclusion rate.
**Fail Condition**: Exclusion rate > 20% (ABORT).

### `code/02.6_reliability.R`
**Purpose**: Calculates Cronbach's alpha for MFQ subscales.
**Output**: `data/derived/reliability_metrics.csv`

### `code/03_analysis.R`
**Purpose**: Runs ANCOVA models for each MFQ subscale.
**Model**: `MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`
**Controls**:
- Bonferroni correction (α = 0.01).
- VIF Check: Aborts if any VIF > 2.
**Output**: `data/derived/ancova_results.csv`, `data/derived/effect_sizes.csv`

### `code/04_render_report.py`
**Purpose**: Renders the RMarkdown report using processed data.
**Input**: `data/derived/`, `code/04_report.Rmd`
**Output**: `reports/chronotype_moral_analysis.html`
**Dependencies**: `utils_logging.py`, `00_config.R` (via R subprocess)

### `code/05_validate_report.py`
**Purpose**: Validates the generated report for required sections.
**Output**: Console summary of validation status.

## Configuration
Environment variables for paths can be set in `code/00_config.R` or via shell environment:
- `PROJECT_ROOT`: Root of the project.
- `DATA_RAW`: Path to raw data.
- `LOG_DIR`: Path to logs.

## Logging
All scripts write to `logs/`.
- `logs/ingest_exclusions.log`
- `logs/classify_exclusions.log`
- `logs/vif_warnings.log` (if applicable)
- `logs/pipeline.log` (general info)

## Error Handling
- **ABORT**: The pipeline stops immediately on critical errors (missing columns, high exclusion rate, high VIF).
- **LOG**: Non-critical exclusions are logged but processing continues.
- **WARN**: Warnings (e.g., VIF < 2 but > 1.5) are logged but do not stop execution (unless VIF > 2).
