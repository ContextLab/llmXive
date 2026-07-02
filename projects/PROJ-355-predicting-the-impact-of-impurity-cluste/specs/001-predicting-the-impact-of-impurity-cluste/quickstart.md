# Quickstart: Impurity Clustering Segregation Project

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI) or local Linux environment.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-355-predicting-the-impact-of-impurity-cluste
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `pymatgen`, `scikit-learn`, `ase`, `statsmodels`.*

## Running the Pipeline

### 1. Data Download & Preparation
Download bulk configurations and generate GB structures.
```bash
python code/data/download.py --source oqmd --limit 100
python code/data/gb_builder.py --config data/raw/bulk_configs.json --output data/processed/gb_structures.json
```

### 2. Compute Descriptors & Energies
Calculate clustering metrics and segregation energies.
```bash
python code/data/descriptors.py --input data/processed/gb_structures.json --output data/processed/descriptors.csv
python code/data/simulate_energy.py --input data/processed/gb_structures.json --output data/processed/energies.csv
```
*Note: If simulation is too slow, this step uses a surrogate model for the CI run.*

### 3. Train & Evaluate Model
Train the regression model and perform sensitivity analysis.
```bash
python code/modeling/train.py --input data/processed/final_dataset.parquet --output results/metrics.json
python code/modeling/evaluate.py --input results/metrics.json --output results/sensitivity_report.json
```

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```
Expected output:
- All unit tests pass (descriptor logic).
- Integration tests confirm data flow from download to metrics.
- Collinearity check (VIF) is performed and logged.

## Output Artifacts

- `results/metrics.json`: Contains R², RMSE, p-values, and VIF scores.
- `results/sensitivity_report.json`: Contains RMSE variance across threshold sweeps.
- `data/processed/final_dataset.parquet`: The merged dataset used for training.
