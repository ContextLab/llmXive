# Quickstart: Quantifying the Influence of Topological Defects on 2D Material Properties

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the Materials Project API (optional; synthetic fallback is available).
*   Internet access to download dependencies and datasets.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-209-quantifying-the-influence-of-topological
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

## Running the Workflow

The entire pipeline is orchestrated via `code/run_workflow.sh` (or `python code/run_workflow.py`).

```bash
# Execute the full pipeline
python code/run_workflow.py
```

### Steps Performed
1.  **Data Acquisition**:
    *   Attempts to download pristine structures from Materials Project API.
    *   Attempts to download defect dataset.
    *   If defect dataset is missing, generates synthetic data (`data/raw/synthetic_train.csv`, `data/raw/synthetic_holdout.csv`) with `data_source='synthetic'`.
    *   Calibrates noise parameters from verified DFT data.
2.  **Data Processing**:
    *   Normalizes properties.
    *   Handles missing values.
    *   Encodes features.
3.  **Modeling**:
    *   Trains Random Forest models.
    *   Performs 5-fold CV.
    *   Runs permutation testing and FDR control.
    *   Handles collinearity iteratively.
    *   Performs stratification or covariate inclusion.
4.  **Validation**:
    *   Evaluates on hold-out set.
    *   Generates `Validation_Report.json`.
5.  **Sensitivity Analysis**:
    *   Sweeps thresholds and reports FPR/FNR.

## Outputs

*   `data/processed/features.csv`: Processed feature matrix.
*   `data/processed/model_outputs.json`: Model performance metrics.
*   `data/validation/Validation_Report.json`: Validation status.
*   `code/04_sensitivity_analysis.py` output: Threshold sensitivity table.

## Troubleshooting

*   **API Failure**: If the Materials Project API is unreachable, the workflow will use the local cache or synthetic data. Check logs for `[ERROR: API access unavailable and no cache present]`.
*   **Missing Data**: If required variables are missing, entries are excluded. Check `data/processed/feature_selection_log.json` for details.
*   **Runtime Error**: Ensure the dataset fits in memory. If not, the plan includes sampling logic.