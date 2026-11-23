# Quickstart: Machine Learning Prediction of Glass Transition Temperature from Composition

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a Linux environment (GitHub Actions runner or local Linux/WSL).

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-120-machine-learning-prediction-of-glass-tra
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
    *Note: `requirements.txt` pins versions of `pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `requests`, `shap`, and `pytest`.*

## Data Acquisition

The pipeline attempts to download the dataset automatically from the verified Zenodo source.

1.  **Run the download script**:
    ```bash
    python code/download_data.py
    ```
    *   This script fetches the dataset from **Zenodo DOI: 10.17188/1271234**.
    *   If the dataset is not found or is inaccessible, the script will exit with an error: `Error: Verified dataset (Zenodo 10.17188/1271234) not accessible.`
    *   If successful, it saves the raw CSV to `data/raw/glass_data.csv` and records the checksum.

## Execution

Run the full pipeline end-to-end:

```bash
python code/featurize.py
python code/train.py
python code/evaluate.py
python code/interpret.py
```

### Step-by-Step Breakdown

1.  **Featurization**:
    ```bash
    python code/featurize.py
    ```
    - Parses formulas, calculates descriptors, and performs **Stoichiometric Conversion** for the baseline.
    - Outputs: `data/processed/featurized_data.csv`.

2.  **Training**:
    ```bash
    python code/train.py
    ```
    - Splits data (fixed seed).
    - Trains Random Forest, Gradient Boosting, and Linear Baseline.
    - Outputs: `artifacts/model_performance.json`.

3.  **Evaluation**:
    ```bash
    python code/evaluate.py
    ```
    - Computes metrics.
    - If N >= 50: Performs paired t-test on residuals.
    - If N < 50: Performs Bootstrap resampling for confidence intervals.
    - Outputs: `artifacts/evaluation_report.txt` (generated programmatically from `model_performance.json`).

4.  **Interpretation**:
    ```bash
    python code/interpret.py
    ```
    - Generates **SHAP** feature importance rankings.
    - Outputs: `artifacts/feature_importance.json`.

## Testing

Run the test suite to verify data hygiene and model logic:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Error: "Verified dataset not accessible"**: The pipeline requires the Zenodo dataset. Check network connectivity or verify the DOI.
- **Domain Mismatch Error**: The dataset composition distribution is outside the valid range (e.g., too little SiO2). This prevents invalid comparisons.
- **Memory Error**: If the dataset is too large, the pipeline will automatically sample. If sampling is insufficient, reduce the `max_depth` in `code/train.py`.
- **Formula Parsing Error**: Invalid chemical formulas in the raw data are logged and excluded. Check `data/raw/excluded_rows.log`.

## Output Artifacts

- `data/processed/featurized_data.csv`: The dataset used for modeling.
- `artifacts/model_performance.json`: Metrics for all models.
- `artifacts/evaluation_report.txt`: Statistical significance results (generated from JSON).
- `artifacts/feature_importance.json`: Ranked features (SHAP).

## Report Generation Constraint

**Important**: The final paper/report generation script **must** parse `artifacts/model_performance.json` programmatically to extract all statistics. Manual transcription of numbers from the console or intermediate files is prohibited to ensure compliance with Constitution Principle IV (Single Source of Truth).