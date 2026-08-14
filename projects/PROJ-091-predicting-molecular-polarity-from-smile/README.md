# Predicting Molecular Polarity from SMILES Strings with Machine Learning

This project implements a machine learning pipeline to predict molecular polarity (dipole moment) from SMILES strings using 2D topological descriptors. It adheres to strict constraints: **no 3D conformer generation**, **no TPSA/SMARTS features**, and **deterministic NaN handling**.

## Project Structure

```
.
├── code/
│ ├── data/ # Data loading, preprocessing, and descriptor generation
│ ├── models/ # Model training, evaluation, and interpretation
│ ├── utils/ # Configuration, logging, and validation utilities
│ ├── main.py # Orchestration script for the full pipeline
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw QM9 dataset (downloaded)
│ └── processed/ # Processed features, splits, and model artifacts
├── tests/ # Unit, integration, and contract tests
├── logs/ # Application logs
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- pip (Python package installer)
- ~6GB RAM (for full dataset processing)
- ~14GB disk space (for raw and processed data)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify installation**:
 ```bash
 python -c "import rdkit; import lightgbm; import pandas; print('Dependencies OK')"
 ```

## Usage

### Quick Start (Full Pipeline)

Run the entire pipeline from data download to analysis artifacts:

```bash
cd code
python main.py
```

This will:
1. Download and validate the QM9 dataset
2. Compute 2D descriptors and filter high-correlation features
3. Split data into train/test sets
4. Train a LightGBM model with hyperparameter tuning
5. Evaluate model performance (R², RMSE)
6. Generate SHAP analysis and stability reports
7. Save all artifacts to `data/processed/`

### Step-by-Step Execution

#### 1. Download Data
```bash
python code/data/download_qm9.py
```
- Fetches QM9 from verified URL
- Validates SMILES format and file checksum
- Output: `data/raw/qm9_smiles.csv`

#### 2. Preprocess Descriptors
```bash
python code/data/preprocess_2d.py
```
- Computes 2D topological descriptors (RDKit)
- Filters features with |r| > 0.85 correlation to target
- Handles NaNs (drop >5% missing, impute with median otherwise)
- Output: `data/processed/descriptors.parquet`

#### 3. Split Data
```bash
python code/data/split_data.py
```
- Random train/test split (no target stratification)
- Output: `data/processed/splits.csv`

#### 4. Train Model
```bash
python code/models/train_lightgbm.py
```
- 5-fold cross-validation for hyperparameter tuning
- Trains final model on full training set
- Outputs: `data/processed/model.pkl`, `code/config.yaml` (updated params)

#### 5. Evaluate Model
```bash
python code/models/evaluate.py
```
- Computes R², RMSE vs. null model (R²=0)
- Output: `data/processed/evaluation.json`

#### 6. Interpret Model (SHAP Analysis)
```bash
python code/models/interpret.py
```
- Cluster-aware SHAP analysis
- Bootstrap stability analysis (Jaccard similarity)
- Outputs: `data/processed/analysis/shap_summary.png`, `data/processed/analysis/stability_report.json`

### Running Tests

```bash
cd code
pytest../tests/ -v
```

Specific test categories:
- **Contract Tests**: `tests/contract/` (schema validation)
- **Unit Tests**: `tests/unit/` (3D exclusion, NaN handling, SHAP stability)
- **Integration Tests**: `tests/integration/` (full pipeline)

## Configuration

- **Hyperparameters**: Loaded from `code/config.yaml` (see `utils/config.py`)
- **Random Seeds**: Hardcoded in `utils/config.py` for reproducibility
- **Logging**: Configured via `utils/logging_config.py` (JSON format, `logs/app.log`)

## Data Constraints

- **2D-Only**: No 3D conformer generation (`EmbedMolecule`, `Get3DConformer` excluded)
- **No TPSA/SMARTS**: Topological descriptors only (RDKit `Descriptors` module)
- **NaN Handling**: Deterministic logic (drop >5% missing, impute with median otherwise)
- **Memory**: Batch processing ensures <6GB RAM usage

## Output Artifacts

| File | Description |
|------|-------------|
| `data/raw/qm9_smiles.csv` | Raw QM9 dataset with SMILES and dipole moments |
| `data/processed/descriptors.parquet` | 2D descriptor matrix (filtered) |
| `data/processed/splits.csv` | Train/test split indices |
| `data/processed/model.pkl` | Trained LightGBM model |
| `data/processed/evaluation.json` | Model performance metrics |
| `data/processed/analysis/shap_summary.png` | SHAP summary plot |
| `data/processed/analysis/stability_report.json` | Bootstrap stability analysis |

## Troubleshooting

- **Missing Dependencies**: Ensure `requirements.txt` is installed in the active virtual environment.
- **Memory Errors**: The pipeline processes data in batches; reduce `batch_size` in `code/data/preprocess_2d.py` if needed.
- **3D Function Calls**: The pipeline enforces 2D-only constraints via `utils/validators.py`; check logs for violations.
- **Data Download Failures**: Verify internet connectivity and checksum validation in `code/data/download_qm9.py`.

## License

[Insert License Here]

## Contributors

[List of Contributors]