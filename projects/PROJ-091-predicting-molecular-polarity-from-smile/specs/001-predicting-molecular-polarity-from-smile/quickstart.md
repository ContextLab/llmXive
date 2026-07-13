# Quickstart: Predicting Molecular Polarity from SMILES Strings with Machine Learning

## Prerequisites

- Python 3.10+
- A minimal number of CPU cores, 6GB+ RAM (GitHub Actions Free Tier compatible)
- Git

## Installation

1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-091-predicting-molecular-polarity-from-smile
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for `rdkit`, `lightgbm`, `pandas`, `numpy`, `scikit-learn`, `shap`, `statsmodels`.*

## Data Preparation

The pipeline automatically downloads the QM9 dataset from the verified HuggingFace source.

1. **Download Data**
   ```bash
   python code/data/download.py
   ```
   - This script fetches the Parquet file to `data/raw/qm9_full.parquet`.
   - It calculates and stores the SHA256 checksum in `state/` for verification.

2. **Generate Features**
   ```bash
   python code/data/preprocess.py
   ```
   - Reads `data/raw/qm9_full.parquet`.
   - Computes numerous 2D descriptors using RDKit.
   - Saves the feature matrix to `data/processed/raw_descriptors.parquet`.
   - **Time Estimate**: ~30-45 minutes for full dataset on 2 vCPU.

3. **Feature Selection (VIF & Target Check)**
   ```bash
   python code/data/feature_selection.py
   ```
   - Filters descriptors based on Target Correlation ($|r|>0.90$) and VIF (>5.0).
   - Saves the final feature matrix to `data/processed/final_features.parquet`.

## Model Training

1. **Run Training Pipeline**
   ```bash
   python code/models/train.py
   ```
   - Performs k-fold cross-validation (Random Split, no stratification).
   - Trains the final LightGBM model.
   - Saves the model to `artifacts/model.pkl`.
   - Outputs metrics to `artifacts/metrics.json`.

2. **Evaluate & Explain**
   ```bash
   python code/models/evaluate.py
   python code/models/explain.py
   ```
   - Generates test set predictions.
   - Runs SHAP analysis.
   - Performs **Bootstrap Stability Analysis** (multiple iterations) to validate feature robustness.
   - Saves results to `artifacts/predictions.csv`, `artifacts/stability_report.json`.

## Verification

To ensure the pipeline meets the **Constitution Check** requirements:

1. **Check Memory Usage**: The scripts include a `memory_monitor` that logs peak usage. Ensure it stays within a manageable memory footprint.
   ```bash
   grep "Peak Memory" logs/memory.log
   ```
2. **Verify Reproducibility**: Re-run the entire pipeline. The `metrics.json` values should match (within floating point tolerance) if seeds are pinned.
3. **Validate Contracts**:
   ```bash
   # Ensure contracts are linked for the test runner
   # The contracts live in specs/.../contracts and are symlinked to tests/contract
   ln -s ../../specs/001-predict-molecular-polarity-from-smile/contracts tests/contract
   
   pytest tests/contract/
   ```
   - Validates that outputs match the schemas defined in `specs/001-predict-molecular-polarity/contracts/`.
4. **Verify 2D-Only Constraint**:
   ```bash
   pytest tests/unit/test_no_3d_conformers.py
   ```
   - Ensures no 3D conformer generation logic is executed.

## Expected Outputs

- `artifacts/metrics.json`: Contains R², RMSE, MAE.
- `artifacts/model.pkl`: The trained LightGBM model.
- `artifacts/stability_report.json`: Top features and their bootstrap stability frequency.
- `logs/errors.log`: Any skipped molecules or parsing errors.

## Troubleshooting

- **Memory Error**: If `MemoryError` occurs, reduce the batch size in `code/data/preprocess.py` or use a smaller sample of QM9.
- **RDKit Import Error**: Ensure `rdkit` is installed correctly. On Linux, `conda install -c conda-forge rdkit` is often more reliable than pip.
- **Dataset Download Failed**: Verify internet access and the URL in `code/data/download.py`. The URL is hardcoded to the verified HuggingFace source.
- **VIF Timeout**: If VIF calculation is too slow on the full dataset, the script automatically switches to a sufficiently large sample for VIF estimation, then applies the filter to the full set.