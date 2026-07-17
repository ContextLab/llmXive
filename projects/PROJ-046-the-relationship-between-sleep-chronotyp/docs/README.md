# The Relationship Between Sleep Chronotype and Moral Judgement

## Project Overview

This project investigates the relationship between sleep chronotype (measured by MEQ and MFQ) and moral judgement (measured by MFQ subscales), controlling for sleep quality (PSQI) and acute sleepiness.

## Data Source Note

**CRITICAL**: This pipeline requires a **user-provided merged CSV file** containing the raw questionnaire data.

- The pipeline **does not** generate or download synthetic data for primary analysis.
- The input file must be placed at `data/raw/merged_questionnaire_data.csv`.
- The script `code/01_ingest.R` will **ABORT immediately** if the required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`) are missing from the input file.
- Do not attempt to run the pipeline with fabricated or placeholder data; such data will be rejected by the validation steps.

## Setup Instructions

1. **R Environment**: Ensure R 4.3+ is installed.
2. **Dependencies**: Run `Rscript code/00_setup_r_env.py` to initialize `renv` and install required packages (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`).
3. **Directory Structure**: Run `Rscript code/setup_data_structure.py` to create necessary directories (`data/raw/`, `data/processed/`, `data/derived/`, `logs/`).

## Running the Pipeline

Execute the following scripts in order:

1. **Ingestion & Cleaning**:
 ```bash
 Rscript code/01_ingest.R
 ```
 *Input*: `data/raw/merged_questionnaire_data.csv`
 *Output*: `data/processed/cleaned_data.csv`

2. **Chronotype Classification**:
 ```bash
 Rscript code/02_classify.R
 ```
 *Input*: `data/processed/cleaned_data.csv`
 *Output*: `data/derived/classified_data.csv`

3. **Reliability Analysis**:
 ```bash
 Rscript code/02.6_reliability.R
 Rscript code/02.7_meq_reliability.R
 ```
 *Output*: `data/derived/reliability_metrics.csv`, `data/derived/meq_reliability.csv`

4. **ANCOVA Analysis**:
 ```bash
 Rscript code/03_analysis.R
 ```
 *Input*: `data/derived/classified_data.csv`
 *Output*: `data/derived/ancova_results.csv`, `data/derived/effect_sizes.csv`

5. **Report Generation**:
 ```bash
 Rscript code/04_render_report.py
 ```
 *Output*: `reports/chronotype_moral_analysis.html`

## Validation

- Run `Rscript code/05_validate_report.R` to verify report structure.
- Run `Rscript code/06_validate_quickstart.py` to validate quickstart instructions.
- Run `Rscript code/07_verify_ci_compatibility.py` to check resource constraints.

## License

Open source (MIT).
