# Quickstart: Predicting Crystal Structures from Molecular Fingerprints

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal (local or GitHub Actions)

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd projects/PROJ-030-predicting-crystal-structures-from-molec
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: This installs `rdkit`, `openbabel`, `pycifrw`, `scikit-learn`, `shap`, `pandas`, `numpy`, and `datasets` (HuggingFace). The `datasets` library is a hard dependency for the primary data flow.*

4.  **Install System Dependencies (if needed)**
    - `Open Babel` and `pycifrw` may require system libraries.
    - Ubuntu/Debian: `sudo apt-get install libopenbabel-dev libopenbabel-utils`
    - macOS: `brew install open-babel`

## Running the Pipeline

The pipeline is designed to run end-to-end on the GitHub Actions free-tier.

### 1. Download and Ingest Data
This step loads the pre-filtered organic subset of the COD from HuggingFace and generates fingerprints.
```bash
python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet
python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet
```
*Expected Output*: `data/processed/crystal_molecules.parquet` containing SMILES, fingerprints, and lattice data.

### 2. Split Data (Scaffold-Based)
```bash
python code/modeling/split.py --input data/processed/crystal_molecules.parquet --output_dir data/splits
```
*Expected Output*: `train.parquet` and `test.parquet` with zero scaffold overlap.

### 3. Train Models
```bash
python code/modeling/train.py --train data/splits/train.parquet --test data/splits/test.parquet --output data/results/model_metrics.json
```
*Expected Output*: `data/results/model_metrics.json` containing Accuracy, F1, R², MAE, Top-K Accuracy, and baseline comparisons.

### 4. Analyze Feature Importance
```bash
python code/analysis/interpret.py --model_path data/results/model_metrics.json --data data/splits/train.parquet --output data/results/feature_importance.csv
```
*Expected Output*: `data/results/feature_importance.csv` listing top bits and substructures.

## Verification

To verify the pipeline works on a small scale:
```bash
python -m pytest tests/unit/test_ingestion.py -v
python -m pytest tests/integration/test_full_pipeline.py --sample-size 100
```

## Troubleshooting

- **MemoryError**: If the process crashes with `MemoryError`, the dataset is too large for the runner. The script automatically retries with a smaller sample size (see `code/config.py`).
- **Open Babel Not Found**: Ensure `openbabel` is installed on the system and `openbabel` is in your `PATH`.
- **CIF Parsing Errors**: Files with malformed crystallographic data are skipped and logged in `logs/ingestion_errors.log`.
- **HF Mirror Unavailable**: If the HuggingFace mirror is inaccessible, the pipeline will fail. No raw download fallback is implemented.