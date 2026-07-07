# Quickstart: Evaluating CBNRM vs State-Led Management

## Overview

This project analyzes the association between Community-Based Natural Resource Management (CBNRM) and land-use change in developing countries. The pipeline ingests data from FAO FRA and World Bank sources, harmonizes them, runs a fixed-effects regression, and generates visualizations.

**Critical Note**: This pipeline uses verified datasets (FAO FRA, World Bank) that contain all required variables. The pipeline will only halt if the specific mapping logic fails (e.g., invalid country codes), not due to missing data sources.

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-016-evaluating-the-effectiveness-of-communit
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Analysis

### Step 1: Data Ingestion & Cleaning
This step downloads data from verified sources, merges them, and handles missing values.

```bash
python code/data/download.py
python code/data/clean.py
python code/data/classify.py
```

*   **Output**: `data/processed/panel_data_v1.csv` (or error log if mapping fails).
*   **Note**: The script will log the "Coverage Rate" (SC-001) and handle missing secondary variables gracefully (FR-007).

### Step 2: Regression Analysis
Runs the fixed-effects panel regression, robustness checks, and sensitivity analysis.

```bash
python code/analysis/regression.py
```

*   **Output**: `data/processed/regression_results.csv`, `data/processed/robustness_results.csv`
*   **Log**: Console output includes the "Associational" disclaimer, F-test results, Benjamini-Hochberg correction status, and sensitivity analysis results (SC-005).

### Step 3: Visualization
Generates residual scatter plots and coefficient plots.

```bash
python code/analysis/visualization.py
```

*   **Output**: `docs/output/residuals.png`, `docs/output/coefficients.png`

## Testing

Run the test suite to verify data cleaning and regression logic:

```bash
pytest code/tests/
```

*   **Key Test**: `test_regression_synthetic` verifies the model recovers known coefficients from synthetic data (US-2).

## Troubleshooting

- **Mapping Error**: If you see "Mapping Error: Invalid Country Code", check the ISO codes in the source data.
- **API 503 Errors**: The script automatically retries with exponential backoff. If it fails after 3 retries, check your internet connection.
- **Missing Data**: If the script excludes a row, check the log for "Primary Variable Missing" or "Secondary Variable Missing". The script will continue unless the primary variables are missing for the majority of the dataset.
- **Memory Errors**: If you encounter memory errors, ensure you are not running other heavy applications. The script is optimized for < 7GB RAM.

## Output Interpretation

- **Coefficients**: Look for the `regime_type` coefficient. A negative value suggests CBNRM is associated with lower land-use change (better outcomes).
- **P-values**: Values < 0.05 indicate statistical significance (Constitution Principle VII).
- **Disclaimer**: All results are **associational**. Causality cannot be inferred due to the observational nature of the study.
- **Coverage Rate**: Check the log for the "Merge Coverage Rate" metric (SC-001).
- **Sensitivity**: Check the log for the "Sensitivity Analysis" result (SC-005) to see how robust the CBNRM effect is to GDP controls.