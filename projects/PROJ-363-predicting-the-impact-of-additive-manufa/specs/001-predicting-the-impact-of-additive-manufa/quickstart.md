# Quickstart: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## Prerequisites
-   Python 3.11+
-   `pip`
-   Access to GitHub Actions (for CI) or local environment.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Step 1: Download and Preprocess Data
This step downloads the verified dataset, imputes missing values, and normalizes features.
```bash
python download_data.py
python preprocess.py
```
*Output*: `data/processed/cleaned_data.csv`

### Step 2: Train Models
Trains Gradient Boosting and MLP models with 5-fold CV.
```bash
python train_models.py
```
*Output*: `models/artifacts/`, `results/reports/metrics.json`

### Step 3: Explainability & Analysis
Generates SHAP plots and statistical significance tables.
```bash
python analyze_explainability.py
```
*Output*: `results/plots/shap_summary.png`, `results/reports/significance_table.csv`

### Step 4: Run Tests
```bash
pytest tests/
```

## Troubleshooting

-   **Memory Error**: If OOM occurs, reduce the dataset sample size in `preprocess.py` (e.g., `df = df.sample(n=50000)`).
-   **Missing Columns**: Check `data/raw/` for the column names. If they differ from the spec, update the mapping in `preprocess.py`.
-   **Runtime > 6h**: Reduce the number of bootstrap permutations in `analyze_explainability.py` from 100 to 50.
-   **Material Mismatch**: If the dataset is not 316L, the script will halt. Verify the dataset source.