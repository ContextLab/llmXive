# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- Git

## Installation

1.  Clone the repository and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Extraction

Download, merge, and filter data from Materials Project and NIST MDR:

```bash
python code/cli/download_cli.py --extract
```

This command:
- Queries the Materials Project API and NIST MDR.
- Merges and deduplicates the data.
- Filters for monolithic aluminum alloys with complete data and independent Poisson's ratio measurements.
- Normalizes units and composition.
- Saves the cleaned dataset to `data/processed/alloys_clean.parquet`.

### 2. Model Training & Evaluation

Train the Random Forest model and evaluate performance:

```bash
python code/modeling.py
```

This script:
- Applies Isometric Log-Ratio (ILR) transformation to the atomic fractions of Cu, Mg, Si, Zn, and Mn.
- Performs 5-fold cross-validation.
- Trains the final model on [deferred] of the data.
- Evaluates on the held-out [deferred] test set.
- Saves metrics to `data/processed/model_metrics.json`.

### 3. Analysis & Diagnostics

Generate feature importance rankings and collinearity diagnostics:

```bash
python code/analysis.py
```

This script:
- Extracts feature importance scores using Permutation Importance and SHAP values in ILR space.
- Computes VIF for raw predictors (diagnostic only).
- Outputs results to `data/processed/analysis_results.json`.

### 4. Verifying Results

To ensure reproducibility, run the following test suite:

```bash
pytest tests/
```

This validates:
- Schema compliance of all output files.
- Correctness of ILR transformation.
- Consistency of model metrics.
- Verification of associational framing in results.

## Troubleshooting

- **No data found**: If the pipeline halts with "No valid entries found", check the source APIs for availability or update the query parameters.
- **VIF > 5**: If collinearity is flagged, note that this is expected for compositional data and confirms the need for ILR transformation.
- **High MAE**: If test MAE is high relative to the target standard deviation, the model may not be capturing the underlying physics. Consider feature engineering or alternative models in future iterations.
