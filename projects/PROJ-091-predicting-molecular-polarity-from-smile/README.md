# Predicting Molecular Polarity from SMILES Strings with Machine Learning

This project implements an automated pipeline to predict molecular polarity (dipole moment) from 2D SMILES strings using machine learning. It leverages the QM9 dataset, generates topological descriptors using RDKit, trains a LightGBM regression model, and performs interpretability analysis using SHAP.

## Features

- **2D Descriptor Generation**: Computes >200 topological descriptors from SMILES strings without 3D conformer generation. [UNRESOLVED-CLAIM: c_88d21f12 — status=not_enough_info]
- **Machine Learning**: Trains a LightGBM regressor with hyperparameter tuning and cross-validation.
- **Interpretability**: Cluster-aware SHAP analysis and bootstrap stability testing for feature importance.
- **Reproducibility**: Hardcoded random seeds and strict 2D-only constraints.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-091-predicting-molecular-polarity
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Sources

This project uses the **QM9** dataset, which contains 134k small organic molecules with quantum mechanical properties.

- **Source**: Maxwell et al. (2016) / Zenodo
- **Download URL**: `
- **Local Path**: `data/raw/gdb9.sdf.gz` (automatically downloaded by `code/data/download_qm9.py`)

The pipeline automatically downloads and validates the dataset on first run if `data/raw/` is empty.

## Usage

### Running the Full Pipeline

Execute the main orchestration script to run the complete pipeline from data download to analysis:

```bash
python code/main.py
```

This will:
1. Download and validate QM9 data (if missing).
2. Generate 2D descriptors.
3. Split data and train the LightGBM model.
4. Perform SHAP analysis and stability checks.
5. Save all artifacts to `data/processed/`.

### Individual Steps

You can also run specific stages of the pipeline:

**Download Data**:
```bash
python code/data/download_qm9.py
```

**Preprocess Descriptors**:
```bash
python code/data/preprocess_2d.py
```

**Train Model**:
```bash
python code/models/train_lightgbm.py
```

**Run Interpretability Analysis**:
```bash
python code/models/interpret.py
```

### Configuration

Hyperparameters can be configured in `code/config.yaml`. Random seeds are hardcoded in `code/utils/config.py` for reproducibility.

## Results

Upon successful completion, analysis artifacts are saved in `data/processed/analysis/`:

- **SHAP Summary Plot**: `shap_summary.png`
- **Feature Importance Report**: `feature_importance.json`
- **Cluster Stability Report**: `stability_report.json`
- **Processed Descriptors**: `data/processed/descriptors.parquet`
- **Trained Model**: `data/processed/model.pkl`

If the stability analysis fails (Jaccard similarity < 0.7), a `stability_failed.json` file will be generated, and the process will exit with code 1.

## Testing

Run the test suite using pytest:

```bash
pytest tests/ -v
```

## Constraints & Compliance

- **2D Only**: The pipeline strictly excludes 3D conformer generation (`EmbedMolecule`, `Get3DConformer`) and TPSA/SMARTS-based descriptors.
- **Memory**: Batch processing ensures <6GB RAM usage.
- **Reproducibility**: All random seeds are fixed in code.

## License

MIT License