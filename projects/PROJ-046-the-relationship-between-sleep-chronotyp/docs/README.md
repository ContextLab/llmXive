# Sleep Chronotype and Moral Judgement Study

## Overview
This project implements an automated research pipeline to analyze the relationship between sleep chronotype (measured by MEQ and MFQ) and moral judgement (measured by MFQ subscales). The pipeline handles data ingestion, classification, ANCOVA analysis with multiplicity control, and reproducible reporting.

## Prerequisites

### Software
- **R**: Version 4.3 or higher
- **Python**: Version 3.8+ (for pipeline orchestration scripts)
- **Git**: For version control

### System Requirements
- **CPU**: 2 cores minimum
- **RAM**: 7 GB minimum
- **GPU**: Not required (CPU-only execution)
- **Disk**: ~14 GB free space for data and intermediate files

### R Packages
The project uses `renv` for dependency management. Required packages include:
- `tidyverse`
- `lme4`
- `car`
- `effectsize`
- `pwr`
- `rmarkdown`
- `knitr`
- `data.table`
- `testthat`
- `lintr`

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-046-the-relationship-between-sleep-chronotyp
 ```

2. **Initialize R environment**:
 ```bash
 Rscript code/00_setup_r_env.py
 ```
 This will:
 - Check R version (requires >= 4.3)
 - Initialize `renv`
 - Install required packages

3. **Generate `renv.lock`**:
 ```bash
 Rscript code/03_generate_renv_lock.py
 ```

4. **Set up project structure** (if not already done):
 ```bash
 python code/setup_project_structure.py
 ```

5. **Create data directories**:
 ```bash
 python code/setup_data_structure.py
 ```
 This creates:
 - `data/raw/`
 - `data/processed/`
 - `data/derived/`
 - `logs/`

## Data Preparation

### Input Data
The pipeline requires a user-provided merged dataset in CSV format placed in `data/raw/`. The dataset must contain the following columns:
- `MEQ_score`: Morningness-Eveningness Questionnaire score
- `MFQ_*`: Morality Foundation Questionnaire subscale scores (5 subscales)
- `PSQI`: Pittsburgh Sleep Quality Index
- `acute_sleepiness`: Acute sleepiness measure
- `age`: Participant age
- `sex`: Participant sex

### Data Validation
Before running the pipeline, ensure:
- The CSV file is properly formatted with headers
- All required columns are present
- No critical missing data (the pipeline will exclude rows with missing `acute_sleepiness`)

## Running the Pipeline

The pipeline executes in sequential stages. Run each script in order:

### 1. Ingestion and Cleaning
```bash
Rscript code/01_ingest.R
```
- Loads raw CSV
- Validates required columns
- Excludes rows with missing `acute_sleepiness`
- Outputs: `data/processed/cleaned_data.csv`, `data/derived/ingest_exclusion_count.json`

### 2. Chronotype Classification
```bash
Rscript code/02_classify.R
```
- Classifies participants into "morning", "intermediate", or "evening" based on MEQ scores
- Flags and excludes out-of-range MFQ scores
- Outputs: `data/derived/classified_data.csv`

### 3. Aggregate Exclusions Check
```bash
Rscript code/02.5_aggregate_exclusions.R
```
- Calculates cumulative exclusion rate
- ABORTS if exclusion rate > 20%
- Outputs: `data/derived/exclusions.log`, `data/derived/exclusion_counts.json`

### 4. Reliability Analysis
```bash
Rscript code/02.6_reliability.R
```
- Calculates Cronbach's alpha for all 5 MFQ subscales
- Outputs: `data/derived/reliability_metrics.csv`

### 5. ANCOVA Analysis
```bash
Rscript code/03_analysis.R
```
- Runs ANCOVA for each MFQ subscale: `MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`
- Applies Bonferroni correction (α = 0.01)
- Calculates Cohen's d and 95% CI
- Checks VIF (ABORTS if VIF > 2)
- Outputs: `data/derived/ancova_results.csv`, `data/derived/effect_sizes.csv`

### 6. Regression Test
```bash
Rscript code/07_regression_test.R
```
- Compares p-values against reference values
- Verifies tolerance ≤ 0.01

### 7. Report Generation
```bash
Rscript code/04_render_report.py
```
- Renders the R-Markdown report
- Includes descriptive stats, ANCOVA results, effect sizes, power analysis, and sensitivity sweep
- Outputs: `reports/chronotype_moral_analysis.html`

### 8. Report Validation
```bash
python code/05_validate_report.py
```
- Validates report structure and required sections
- Checks presence of sensitivity table with at least 3 alpha thresholds

## Output Files

### Data Files
- `data/processed/cleaned_data.csv`: Cleaned input data
- `data/derived/classified_data.csv`: Data with chronotype labels
- `data/derived/exclusion_counts.json`: Summary of excluded rows
- `data/derived/reliability_metrics.csv`: Cronbach's alpha values
- `data/derived/ancova_results.csv`: ANCOVA results with p-values
- `data/derived/effect_sizes.csv`: Cohen's d and confidence intervals
- `data/derived/sensitivity_sweep.csv`: Sensitivity analysis results

### Log Files
- `logs/ingest_exclusions.log`: Details of rows excluded during ingestion
- `logs/classify_exclusions.log`: Details of rows excluded during classification
- `logs/vif_warnings.log`: VIF warnings (if any)
- `logs/vif_error.flag`: Flag file created if VIF > 2

### Reports
- `reports/chronotype_moral_analysis.html`: Final analysis report

## Testing

### Unit Tests
Run unit tests for specific components:
```bash
Rscript -e "testthat::test_dir('tests/')"
```

### Quickstart Validation
Validate the quickstart guide:
```bash
python code/06_validate_quickstart.py
```

### CI Compatibility Check
Verify CI runner compatibility:
```bash
python code/07_verify_ci_compatibility.py
```

## Troubleshooting

### Common Issues

1. **Missing R packages**:
 Re-run `code/00_setup_r_env.py` to install missing packages.

2. **VIF > 2**:
 The pipeline will abort. Check your data for multicollinearity issues.

3. **Exclusion rate > 20%**:
 The pipeline will abort. Review your data quality and preprocessing steps.

4. **Report validation fails**:
 Ensure all required sections are present in the R-Markdown template.

### Logging
All pipeline logs are stored in the `logs/` directory. Check these files for detailed error messages and exclusion reasons.

## Project Structure

```
PROJ-046-the-relationship-between-sleep-chronotyp/
├── code/
│ ├── 00_setup_r_env.py
│ ├── 01_ingest.R
│ ├── 02_classify.R
│ ├── 02.5_aggregate_exclusions.R
│ ├── 02.6_reliability.R
│ ├── 03_analysis.R
│ ├── 04_report.Rmd
│ ├── 04_render_report.py
│ ├── 05_validate_report.py
│ ├── 05_validate_report.R
│ ├── 06_benchmark_accuracy.R
│ ├── 06_validate_quickstart.py
│ ├── 07_regression_test.R
│ ├── 07_verify_ci_compatibility.py
│ ├── analysis.py
│ ├── setup_data_structure.py
│ ├── setup_lintr_config.py
│ ├── setup_project_structure.py
│ ├── utils_logging.py
│ ├── utils_logging_test.py
│ ├── utils_renv.py
│ └── 03_generate_renv_lock.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── derived/
├── logs/
├── reports/
├── tests/
├── docs/
├── requirements.txt
├── renv.lock
└── README.md
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and validation
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Morningness-Eveningness Questionnaire (MEQ) by Horne & Östberg
- Morality Foundation Questionnaire (MFQ) by Graham et al.
- Pittsburgh Sleep Quality Index (PSQI) by Buysse et al.
