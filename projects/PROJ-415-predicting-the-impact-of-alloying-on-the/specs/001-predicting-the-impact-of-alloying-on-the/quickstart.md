# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites
- Python 3.11+
- Git
- (Optional) Conda or venv for environment management
- **API Access**: Ensure you have an API key for Materials Project (if used) or network access to NIST mirrors.

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Preparation
*Note: This project requires **real** data from NIST or Materials Project. Synthetic data is not supported.*

1.  **Fetch Data**: Run the acquisition script to download the verified dataset.
    ```bash
    python code/data/acquisition.py
    ```
    This will fetch data from the verified NIST/Materials Project source and save it to `data/raw/`. If the fetch fails, the script will exit with an error.
2.  **Verify**: Ensure `data/raw/diffusion_data.csv` exists and is checksummed.

## Running the Pipeline

Execute the full pipeline (Acquisition -> Ingestion -> Feature Engineering -> Training -> Validation):

```bash
python code/main.py
```

This will:
1.  Acquire data from verified sources.
2.  Ingest and filter data (FCC, Self-diffusion).
3.  Compute `size_mismatch` using Metallic Radii.
4.  Train RF, GB, and Linear models (with Host Metal fixed effects).
5.  Perform threshold sensitivity analysis and Power Analysis.
6.  Save results to `models/` and `reports/`.

## Running Tests

Run the unit and integration tests:

```bash
pytest tests/ -v
```

To check contract validation:

```bash
pytest tests/contract/test_schema.py -v
```

## Expected Outputs
- `models/final_rf.pkl`: Trained Random Forest model.
- `models/final_gb.pkl`: Trained Gradient Boosting model.
- `models/linear_coef.json`: Linear regression coefficients and p-values.
- `reports/validation_report.json`: Full statistical validation report (including Power Analysis).
- `data/curated/features.csv`: Final dataset with engineered features.