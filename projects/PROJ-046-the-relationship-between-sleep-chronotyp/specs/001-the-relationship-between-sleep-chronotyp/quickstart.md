# Quickstart: The Relationship Between Sleep Chronotype and Moral Judgement

## Prerequisites

- R 4.3 or higher
- RStudio (optional but recommended)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-046-the-relationship-between-sleep-chronotyp
   ```

2. **Install dependencies**:
   ```bash
   Rscript -e "install.packages('renv')"
   Rscript -e "renv::restore()"
   ```

## Data Preparation

The pipeline requires a CSV file with the following columns:
`participant_id`, `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `acute_sleepiness`, `age`, `sex`.

**Note**: No verified public dataset contains all these columns. You must provide your own data file (`data/raw/study_data.csv`) for scientific analysis.
- **For Testing**: Use `data/benchmark/synthetic_benchmark.csv` to verify the classification logic (SC-001) only.
- **For Analysis**: Place your real data in `data/raw/study_data.csv`. If this file is missing, the statistical analysis step will be skipped.

## Running the Analysis

1. **Ingest and Classify**:
   ```bash
   Rscript code/01_ingest_classify.R --input data/raw/study_data.csv --output data/processed/cleaned_data.csv
   ```
   - If the input file is missing or >20% of rows are unusable, the script will abort with an error.

2. **Run MANCOVA/ANCOVA and Generate Report**:
   ```bash
   Rscript code/02_mancova_ancova.R --input data/processed/cleaned_data.csv --output data/processed/analysis_results.json
   Rscript code/03_report_render.R --input data/processed/analysis_results.json --output reports/analysis_report.html
   ```
   - If `cleaned_data.csv` is missing, these steps will be skipped, and the report will indicate "No Data".

3. **Run Linting (T031)**:
   ```bash
   Rscript code/04_lint_check.R
   ```
   - Generates `reports/lint_report.txt`.

4. **View Results**:
   Open `reports/analysis_report.html` in your browser.

## Validation

- **Classification Check**: Run `Rscript tests/test-classification.R` against `data/benchmark/synthetic_benchmark.csv`. Verify accuracy ≥ 95%.
- **Statistical Check**: Compare ANCOVA p-values with a reference R script (provided in `tests/`).
- **Linting**: Check `reports/lint_report.txt` for errors.
- **Quickstart Validation (T032)**: Ensure all steps above execute without manual intervention.

## Troubleshooting

- **Missing Columns**: Ensure your CSV has all required columns.
- **Missing Values**: Rows with missing `MEQ_score` or `acute_sleepiness` will be excluded. Check logs for warnings.
- **Power Limitations**: If sample size < 159, the report will flag low power and provide a sensitivity analysis for effect size.
- **Data Missing**: If `data/raw/study_data.csv` is missing, the analysis will not run. This is expected behavior to prevent fabricated results.
