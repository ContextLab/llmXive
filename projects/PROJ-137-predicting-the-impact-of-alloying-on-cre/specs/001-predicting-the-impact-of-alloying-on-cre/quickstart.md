# Quickstart: Predicting the Impact of Alloying on Creep Resistance

## 1. Prerequisites

*   Python 3.11+
*   `pip` and `venv`
*   (Optional) Materials Project API Key (for real data path)

## 2. Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins all versions to ensure reproducibility.*

## 3. Configuration

1.  **Edit `config/settings.yaml`**:
    *   Set `random_seed` (e.g., 42).
    *   (Optional) Set `materials_project_api_key` if using real data.
2.  **Verify `config/synthetic_params.yaml`**:
    *   Contains physics parameters (A, B, C, n) for synthetic data generation.

## 4. Running the Pipeline

### 4.1 Full Pipeline (Synthetic Data Path)
This is the default execution path. It generates synthetic data, trains models, and produces reports.

```bash
python src/main.py --mode synthetic
```

### 4.2 Full Pipeline (Real Data Path)
Requires a valid NIMS URL and Materials Project API key.

```bash
python src/main.py --mode real
```

### 4.3 Specific Tasks
*   **Data Generation Only**:
    ```bash
    python src/data/generate.py --output data/processed/synthetic_data.csv
    ```
*   **Model Training & Evaluation**:
    ```bash
    python src/models/train.py --input data/processed/synthetic_data.csv
    ```
*   **SHAP Analysis**:
    ```bash
    python src/models/interpret.py --model-path models/gbr_thermo.pkl
    ```

## 5. Expected Outputs

*   `data/processed/processed_dataset.csv`: Cleaned, merged dataset.
*   `models/`: Trained model artifacts (`.pkl`).
*   `docs/reports/`:
    *   `comparison_report.md`: R², RMSE, and statistical test results.
    *   `shap_summary.png`: Feature importance plot.
    *   `physics_check.log`: Validation of synthetic data physics.

## 6. Testing

Run the test suite to verify data integrity and pipeline logic:

```bash
pytest tests/ -v
```

*   `tests/contract/`: Validates CSVs against YAML schemas.
*   `tests/integration/`: Runs the full pipeline end-to-end.
*   `tests/unit/`: Tests parsing and thermodynamic calculations.

## 7. Troubleshooting

*   **API Rate Limits**: If using real data, the system automatically retries with exponential backoff. If it fails, it logs the error and excludes the entry.
*   **Memory Errors**: The pipeline is optimized for <7GB RAM. If issues persist, reduce the synthetic dataset size in `config/synthetic_params.yaml`.
*   **Physics Check Failure**: If the synthetic data does not achieve R² > 0.8, check `config/synthetic_params.yaml` for incorrect physics parameters.
