# Quickstart: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Prerequisites
- Python 3.11+
- pip
- 6GB+ RAM, 14GB+ Disk
- Internet access (for `qm9pack` data download)

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `qm9pack`, `rdkit`, `lightgbm`, `shap`, `pandas`, `numpy`, `scikit-learn`, `pytest`, `scipy`.*

## Running the Pipeline

### 1. Fetch and Preprocess Data
This step downloads QM9, generates 2D descriptors, and saves the feature matrix.
```bash
python code/main.py --step fetch_and_preprocess
```
*Output*: `data/raw/qm9_raw.parquet`, `data/processed/descriptors.parquet`.

### 2. Feature Selection
Computes VIF, performs iterative removal (with L1 fallback), and generates cluster map.
```bash
python code/main.py --step feature_selection
```
*Output*: `data/processed/vif_scores.csv`, `data/processed/cluster_map.csv`.

### 3. Train Model
Trains the LightGBM regressor with cross-validation.
```bash
python code/main.py --step train
```
*Output*: `data/processed/model.pkl`, `data/results/training_metrics.json`.

### 4. Analyze & Validate
Runs SHAP analysis (with interaction values), bootstrap stability checks (A resampling approach with multiple iterations and subsamples per iteration will be employed to assess variability, following established protocols (e.g., Efron & Tibshirani, 1993).), and contract validation.
```bash
python code/main.py --step analyze
```
*Output*: `data/results/shap_summary.png`, `data/results/stability_report.json`.

### 5. Verify Reproducibility
Checks checksums against `state/manifest.json`.
```bash
python code/main.py --step verify
```

## Testing

Run the full test suite (unit, contract, integration):
```bash
pytest tests/ -v
```

**Key Contract Tests**:
- `tests/contract/test_schema_validation.py`: Validates that `descriptors.parquet`, `vif_scores.csv`, and `cluster_map.csv` match the schema.
- `tests/unit/test_descriptors.py`: Asserts no 3D functions are called during preprocessing (mocking `EmbedMolecule`).

## Troubleshooting

- **Memory Error**: If RAM exceeds 6GB, reduce the batch size in `code/data/preprocess.py` or the bootstrap subsample size in `code/model/evaluate.py`.
- **NaN in Descriptors**: The pipeline automatically imputes with median. If >5% missing, the record is dropped. Check `logs/preprocess.log`.
- **3D Leakage**: If the unit test `test_no_3d_generation` fails, check `code/data/preprocess.py` for any accidental calls to `EmbedMolecule`.
- **VIF Fallback**: If the feature count drops below a predefined threshold, the pipeline automatically switches to L1 regularization. Check `data/processed/vif_scores.csv` for the `fallback_triggered` flag.