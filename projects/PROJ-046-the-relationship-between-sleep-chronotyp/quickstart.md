# Quickstart Guide: Sleep Chronotype and Moral Judgement Analysis

## Overview

This project implements an automated pipeline to analyze the relationship between sleep chronotype (measured by MEQ and MFQ) and moral judgement (measured by MFQ subscales). The pipeline performs data ingestion, chronotype classification, ANCOVA analysis with multiplicity control, and generates a reproducible report.

## Dependencies

### System Requirements
- Python 3.8+
- R 4.3+
- R packages: `tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`

### Installation

1. **Install Python dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Initialize R environment**:
 ```bash
 Rscript code/00_setup_r_env.py
 ```
 This will check for R 4.3+ and initialize `renv` with the required packages.

3. **Generate `renv.lock`**:
 ```bash
 Rscript code/03_generate_renv_lock.py
 ```

## Data Source Note

**IMPORTANT**: This pipeline requires a **user-provided merged CSV file** containing the following columns:
- `MEQ_score`: Total score from the Morning-Evening Questionnaire
- `MFQ_*`: Individual items or subscale scores from the Munich ChronoType Questionnaire
- `PSQI`: Pittsburgh Sleep Quality Index score
- `acute_sleepiness`: Acute sleepiness measure (must be non-missing)
- `age`: Participant age
- `sex`: Participant sex

The pipeline will **ABORT immediately** if any required column is missing. No synthetic data generation is permitted for primary analysis. Users must provide their own real dataset in `data/raw/`.

## Setup

1. **Create data directories**:
 ```bash
 python code/setup_data_structure.py
 ```
 This creates:
 - `data/raw/` - Raw input data (never modified)
 - `data/processed/` - Cleaned and intermediate data
 - `data/derived/` - Final analysis outputs
 - `logs/` - Pipeline execution logs

2. **Configure linting**:
 ```bash
 python code/setup_lintr_config.py
 ```

3. **Verify project structure**:
 ```bash
 python code/06_validate_quickstart.py
 ```

## Run

Execute the pipeline in order:

1. **Ingest and clean data**:
 ```bash
 Rscript code/01_ingest.R
 ```
 Output: `data/processed/cleaned_data.csv`

2. **Classify chronotypes**:
 ```bash
 Rscript code/02_classify.R
 ```
 Output: `data/derived/classified_data.csv`

3. **Calculate reliability metrics**:
 ```bash
 Rscript code/02.6_reliability.R
 Rscript code/02.7_meq_reliability.R
 ```
 Output: `data/derived/reliability_metrics.csv`, `data/derived/meq_reliability.csv`

4. **Run ANCOVA analysis**:
 ```bash
 Rscript code/03_analysis.R
 ```
 Output: `data/derived/ancova_results.csv`, `data/derived/effect_sizes.csv`

5. **Generate report**:
 ```bash
 Rscript code/04_report.Rmd
 ```
 Output: `reports/chronotype_moral_analysis.html`

6. **Validate report**:
 ```bash
 python code/05_validate_report.py
 ```

## Output Files

After successful execution, the following files will be generated:

| File | Description |
|------|-------------|
| `data/processed/cleaned_data.csv` | Cleaned dataset with exclusions logged |
| `data/derived/classified_data.csv` | Dataset with chronotype labels |
| `data/derived/reliability_metrics.csv` | Cronbach's alpha for MFQ subscales |
| `data/derived/meq_reliability.csv` | MEQ internal consistency report |
| `data/derived/ancova_results.csv` | ANCOVA results with Bonferroni correction |
| `data/derived/effect_sizes.csv` | Cohen's d and confidence intervals |
| `data/derived/sensitivity_sweep.csv` | Sensitivity analysis results |
| `reports/chronotype_moral_analysis.html` | Final analysis report |
| `logs/ingest_exclusions.log` | Log of excluded rows during ingestion |
| `logs/classify_exclusions.log` | Log of excluded rows during classification |

## Troubleshooting

- **Missing columns**: Ensure your input CSV has all required columns. The pipeline will abort with a clear error message if any are missing.
- **High exclusion rate**: If >20% of rows are excluded, the pipeline will abort. Check your data quality.
- **R package errors**: Re-run `code/00_setup_r_env.py` to ensure all packages are installed.
- **VIF warnings**: If Variance Inflation Factors > 2, the pipeline will flag results as potentially unreliable but continue execution.

## Limitations

This is an observational study. No causal inferences can be drawn from the results. The pipeline assumes the input data is representative and of high quality.
