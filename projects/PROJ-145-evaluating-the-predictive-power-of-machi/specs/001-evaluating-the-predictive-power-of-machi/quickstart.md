# Quickstart: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal with `pip`

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `datasets`, and `pytest`.*

## Running the Pipeline

The pipeline is executed via a series of scripts in the `code/` directory.

### Step 1: Data Ingestion
Download and filter the HEA data.
```bash
python code/data_ingestion.py
```
*Output*: `data/processed/heas_train.csv`, `data/processed/holdout_known.csv`

### Step 2: Descriptor Calculation
Calculate compositional descriptors for all datasets.
```bash
python code/descriptor_calc.py
```
*Output*: Updated CSVs with descriptor columns.

### Step 3: Model Training
Train Random Forest and Gradient Boosting models with 5-fold CV.
```bash
python code/model_training.py
```
*Output*: `data/models/rf_model.pkl`, `data/models/gb_model.pkl`

### Step 4: Generate & Evaluate Novel Candidates
Generate "True Novel" candidates and evaluate uncertainty.
```bash
python code/evaluation.py
```
*Output*: `data/processed/true_novel.csv`, `data/processed/metrics_summary.csv`

### Step 5: Run Tests
Verify the pipeline correctness.
```bash
pytest tests/
```

## Expected Outputs

- **Interpolation Performance**: $R^2$ and MAE for the training set (5-fold CV).
- **Extrapolation Performance**: $R^2$ and MAE for the "Hold-out Known" set.
- **Uncertainty Metrics**: Variance and distance-from-hull for "True Novel" candidates.
- **Final Report**: A summary of accuracy degradation and uncertainty correlation.

## Troubleshooting

- **API Timeouts**: The `data_ingestion.py` script includes exponential backoff. If it fails after 3 retries, it logs a "partial failure" and continues.
- **Numerical Errors**: If you see `divide by zero` errors, ensure the `utils.py` clamping logic is active (default threshold $1e-6$).
- **Memory Issues**: The pipeline is designed for < 7 GB RAM. If you encounter OOM, reduce the `n_estimators` in `model_training.py` or sample a smaller subset of the data.
