# Quickstart: 001-molecular-reactivity

## Prerequisites

- Python 3.10+
- 7 GB RAM available
- 14 GB disk space
- Git

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-442-predicting-molecular-reactivity-using-ma
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
    *Note: `requirements.txt` pins versions for `rdkit`, `xgboost`, `pandas`, `scikit-learn`, `pyarrow`.*

## Running the Pipeline

The pipeline is orchestrated by `src/main.py`. It performs the following steps in order:
1.  **Download**: Fetches the USPTO dataset.
2.  **Filter**: Applies reaction templates to extract SN1, SN2, and Diels-Alder reactions.
3.  **Feature Extract**: Converts SMILES to numerical features.
4.  **Train**: Runs 5-fold cross-validation with XGBoost.
5.  **Evaluate**: Computes Spearman correlations and permutation test p-values.

### Step 1: Download and Filter Data

```bash
python src/data/ingestion.py --output data/processed/filtered_reactions.parquet
```
- **Input**: Raw USPTO parquet (downloaded automatically if missing).
- **Output**: `data/processed/filtered_reactions.parquet`.
- **Logs**: `logs/ingestion.log` (contains counts of filtered/excluded reactions).

### Step 2: Feature Extraction

```bash
python src/data/preprocessing.py --input data/processed/filtered_reactions.parquet --output data/processed/features.parquet
```
- **Input**: Filtered reactions.
- **Output**: `data/processed/features.parquet` (with molecular descriptors).
- **Logs**: `logs/preprocessing.log` (contains warnings for malformed SMILES).

### Step 3: Train and Evaluate

```bash
python src/modeling/train.py --config src/modeling/config.yaml
```
- **Input**: Features and config.
- **Output**:
  - `data/models/` (saved XGBoost models).
  - `data/results/cv_results.csv` (Spearman ρ, p-values per fold).
  - `data/results/permutation_test.csv` (p-value for overall significance).
- **Logs**: `logs/training.log` (contains runtime and memory usage).

### Step 4: Generate Report

```bash
python src/modeling/evaluate.py --input data/results/cv_results.csv --output reports/final_report.md
```
- **Output**: `reports/final_report.md` containing the ranked list of reaction classes and statistical significance.

## Verification

To verify the pipeline:
1.  Check that `data/processed/features.parquet` contains only SN1, SN2, and Diels-Alder reactions.
2.  Ensure `reports/final_report.md` shows a p-value < 0.01 for the permutation test.
3.  Confirm that the total runtime (from `logs/training.log`) is < 30 minutes.

## Troubleshooting

- **Memory Error**: If the process crashes due to OOM, reduce the `BATCH_SIZE` in `src/modeling/config.yaml` from [deferred] to [deferred].
- **SMILES Parsing Errors**: Check `logs/preprocessing.log` for the specific SMILES strings that failed. These are excluded from the dataset.
- **Low Sample Size**: If a class has < 1,000 samples, a warning will be logged, and that class will be excluded from the final report.
