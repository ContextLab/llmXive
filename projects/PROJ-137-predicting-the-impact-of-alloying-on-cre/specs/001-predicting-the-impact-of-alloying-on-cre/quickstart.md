# Quickstart: Predicting the Impact of Alloying on Creep Resistance via Public Data

## Prerequisites

*   Python 3.11+
*   A Materials Project API Key (optional; synthetic data will be used if unavailable).
*   Git

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `pymatgen`, `scikit-learn`, `shap`, `pandas`, `numpy`, `requests`, and `jsonschema`.*

## Running the Pipeline

The pipeline is designed to run end-to-end. It will automatically attempt to fetch data from NIMS/Materials Project. If these fail or the data schema is invalid, it will generate a synthetic dataset.

### Option 1: Full Pipeline (Recommended)
```bash
cd code
python main.py
```
This script performs:
1.  **Data Download**: Attempts to fetch NIMS data and Materials Project thermodynamics.
2.  **Preprocessing**: Parses compositions to Atomic%, calculates descriptors.
3.  **Strict Intersection**: Drops rows missing thermo data from ALL models.
4.  **Training**: Runs Nested CV for Thermodynamic, Linear, and Polynomial models.
5.  **Evaluation**: Computes statistical tests and generates SHAP plots.
6.  **Output**: Saves `results/` containing `metrics.csv`, `shap_summary.png`, and `report.txt`.

### Option 2: Synthetic Mode (For Testing/CI)
To force synthetic data generation (useful if API keys are missing or for CI validation):
```bash
cd code
python main.py --synthetic
```

### Option 3: Individual Steps
*   **Download & Preprocess**:
    ```bash
    python data/download.py && python data/preprocess.py
    ```
*   **Train & Evaluate**:
    ```bash
    python models/train.py && python models/evaluate.py
    ```

## Expected Outputs

After a successful run, the following files will be generated in the `data/` and `results/` directories:

*   `data/processed/alloy_features.csv`: The cleaned, feature-engineered dataset.
*   `results/metrics.csv`: R² and RMSE for all three models, plus statistical test results.
*   `results/shap_summary.png`: Feature importance plot.
*   `results/report.txt`: Human-readable summary of findings.

## Troubleshooting

*   **Materials Project API Error**: If you see "Rate Limit Exceeded", the script will automatically retry with exponential backoff. If it fails after 3 retries, the entry is dropped from **ALL models** to ensure strict intersection.
*   **Missing Dependencies**: Ensure you activated the virtual environment. Run `pip install -r code/requirements.txt` again.
*   **No Data**: If the NIMS URL is unreachable and `--synthetic` is not used, the script will generate a synthetic dataset automatically as per FR-008.
*   **Schema Validation Error**: If synthetic data fails validation against `dataset.schema.yaml`, the pipeline will abort and report the specific validation error.