# Quickstart: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Prerequisites

-   Python 3.11+
-   `pip` (Python package installer)
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-177-investigating-the-validity-of-the-equipa
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `pytest`.*

## Running the Pipeline

### 1. Generate Synthetic Test Data & Ground Truth
Since no verified real dataset is available, run the synthetic generator to create ground-truth data for validation.
```bash
python -m src.ingestion.generate_synthetic --seed 42 --output data/synthetic/raw.parquet --ground-truth artifacts/ground_truth.json
```
*This creates a dataset with known "thermal" and "non-thermal" regimes and outputs `artifacts/ground_truth.json` containing manual calculation values for SC-001 validation.*

**Required Artifact**: `artifacts/test_params.json` must be present with the following content:
```json
{
  "maxwell_boltzmann": {
    "mean": 1.0,
    "scale": 0.1
  },
  "pareto": {
    "shape": 2.0
  }
}
```

### 2. Ingest and Compute Energy
Process the data to calculate energy components.
```bash
python -m src.ingestion.sync_data --input data/synthetic/raw.parquet --output data/processed/energy_samples.parquet
python -m src.ingestion.energy_calc --input data/processed/energy_samples.parquet --output data/processed/energy_calculated.parquet
```

### 3. Run Statistical Analysis
Perform KS and Chi-squared tests.
```bash
python -m src.analysis.hypothesis_test --input data/processed/energy_calculated.parquet --output results/statistical_results.json
```

### 4. Run Sensitivity and Regression
```bash
python -m src.analysis.sensitivity --input results/statistical_results.json --output results/sensitivity_report.json
python -m src.analysis.regression --input data/processed/energy_calculated.parquet --output results/regression_results.json
```

### 5. Run Tests
Verify the implementation against the contract.
```bash
pytest tests/ -v
```

## Expected Outputs

-   `results/statistical_results.json`: P-values and rejection flags.
-   `results/sensitivity_report.json`: Robustness of conclusions across thresholds.
-   `results/regression_results.json`: Slopes and significance of deviation drivers.
-   `artifacts/ground_truth.json`: Ground truth parameters for validation (SC-001).
-   `artifacts/test_params.json`: Configuration for synthetic data generation (Maxwell-Boltzmann mean=1.0, scale=0.1; Pareto shape=2.0).

## Troubleshooting

-   **Missing Data**: If the script fails to find `data/synthetic/raw.parquet`, ensure you ran the `generate_synthetic` step.
-   **Memory Errors**: If processing real data (if added later) fails, enable streaming in `sync_data.py` by setting `streaming=True` in the loader config.
-   **Test Failures**: Ensure `artifacts/ground_truth.json` and `artifacts/test_params.json` exist and match the expected schema.
