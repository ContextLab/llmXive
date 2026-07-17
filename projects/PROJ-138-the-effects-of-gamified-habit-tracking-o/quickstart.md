# Quick Start Guide

This guide provides step-by-step instructions to execute the full analysis pipeline for "The Effects of Gamified Habit Tracking on Long-Term Behavioral Change."

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Access to the project root directory

## Step 1: Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

## Step 2: Verify Project Structure

Ensure the required directories exist. If not, run the setup script:

```bash
python code/setup_project_structure.py
```

This creates:
- `data/raw/`, `data/processed/`, `data/consent/`
- `code/data/`, `code/analysis/`, `code/reports/`, `code/utils/`, `code/tests/`

## Step 3: Generate Synthetic Data & Consent

If you do not have real longitudinal data, the pipeline will generate a synthetic dataset.

### Consent Verification

The pipeline requires a consent record in `data/consent/`.
- For **real data**: Place your IRB-approved consent documentation here.
- For **synthetic data**: The pipeline automatically generates `data/consent/synthetic_consent_record.json` confirming the data is synthetic and approved for research.

To generate synthetic data explicitly:

```bash
python code/data/synthetic_generator.py
```

This creates `data/raw/synthetic_data.csv` with N=100 users (70% gamified, 30% non-gamified). [UNRESOLVED-CLAIM: c_c440ea01 — status=not_enough_info]

## Step 4: Run the Full Pipeline

Execute the main analysis script:

```bash
python code/scripts/run_quickstart_validation.py
```

Alternatively, run individual stages:

### 4.1 Data Ingestion & Validation
```bash
python code/data/ingestion.py
```
- Loads data (real or synthetic)
- Validates schema against `contracts/dataset.schema.yaml`
- Checks consent status
- Ensures group sizes (≥30 non-gamified)

### 4.2 Data Aggregation
```bash
python code/data/aggregation.py
```
- Converts daily logs to weekly bins
- Calculates `weekly_adherence_flag`

### 4.3 Merging Datasets
```bash
python code/data/merge.py
```
- Produces `data/processed/merged_data.csv`

### 4.4 Statistical Modeling
```bash
python code/analysis/modeling.py
```
- Calculates VIF and handles collinearity
- Fits mixed-effects logistic regression
- Applies Benjamini-Hochberg FDR correction

### 4.5 Survival Analysis
```bash
python code/analysis/survival.py
```
- Counts dropout events
- Runs Kaplan-Meier and Cox models (if events ≥ 10)

### 4.6 Robustness Checks
```bash
python code/analysis/robustness.py
```
- Performs bootstrapping for confidence intervals

### 4.7 Report Generation
```bash
python code/reports/generate_report.py
```
- Generates `data/reports/final_analysis.html`

## Step 5: Verify Outputs

Check that the following artifacts exist:
- `data/processed/merged_data.csv`
- `data/reports/final_analysis.html`
- `state.yaml` (updated with artifact hashes)

## Step 6: Run Tests (Optional)

Execute the test suite to validate logic:

```bash
pytest code/tests/ -v
```

## Troubleshooting

- **Missing Consent**: Ensure `data/consent/` exists. The synthetic generator will create a consent record if needed.
- **Group Imbalance**: If the non-gamified group has < 30 users, the pipeline will halt with a "Group Imbalance" error.
- **Low Dropout Events**: If survival events < 10 per group, the survival analysis will generate a descriptive report and halt.
- **Memory Errors**: The robustness module uses chunked processing; if issues persist, reduce bootstrap iterations in `code/utils/config.py`.

## Next Steps

After successful execution, review the generated `final_analysis.html` for visualizations, model coefficients, and sensitivity analysis results.
