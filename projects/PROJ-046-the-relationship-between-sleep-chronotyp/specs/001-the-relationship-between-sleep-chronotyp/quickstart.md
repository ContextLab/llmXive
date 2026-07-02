# Quickstart: The Relationship Between Sleep Chronotype and Moral Judgement

## Prerequisites
- R 4.3+
- Git

## Installation

1.  **Clone and Enter**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-046-the-relationship-between-sleep-chronotyp
    ```

2.  **Setup R Environment**:
    ```bash
    Rscript -e 'install.packages("renv")'
    Rscript -e 'renv::restore()'
    ```

3.  **Prepare Data**:
    The pipeline requires a **single, pre-merged** CSV file containing all required columns:
    `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `acute_sleepiness`, `age`, `sex`.
    Place this file in `data/raw/merged_data.csv`.
    *Note: No simulation mode is available. The pipeline will abort if required columns are missing.*

## Running the Analysis

Execute the full pipeline:
```bash
Rscript code/01_ingest.R
Rscript code/02_classify.R
Rscript code/03_analysis.R
Rscript code/04_report.Rmd
```

## Verifying Results

1.  **Check Output Files**:
    - `data/processed/classified_data.csv`
    - `reports/chronotype_moral_analysis.html` (or PDF)
2.  **Run Validation Scripts**:
    - `Rscript code/05_validate_report.R` (Verifies report content per SC-003)
    - `Rscript code/06_benchmark_accuracy.R` (Verifies classification accuracy per SC-001)
    - `Rscript code/07_regression_test.R` (Verifies p-value accuracy per SC-002)

## Troubleshooting
- **Missing Columns**: If the script fails on `acute_sleepiness` or other required columns, ensure your input CSV contains all required fields. The pipeline will not simulate missing data.
- **High Exclusion Rate**: If >20% of rows are unusable, the pipeline will abort. Review your data quality.
- **Memory Errors**: Not expected on standard data; if occurring, reduce the sample size.