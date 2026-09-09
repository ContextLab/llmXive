# Quick Start Guide

This guide validates the end-to-end pipeline for predicting molecular polarity from SMILES strings on a small batch of data.

## Prerequisites

- Python 3.9+
- pip
- A working internet connection (to download QM9 data if not present)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Validation Steps

The following steps validate the full pipeline on a small subset of the QM9 dataset.

### Step 1: Verify Environment

Ensure all dependencies are installed:
```bash
python -c "import rdkit; import lightgbm; import pandas; import numpy; import shap; import yaml; import pytest; print('All dependencies installed.')"
```

### Step 2: Run Small Batch Pipeline

Execute the pipeline with a small batch size to verify functionality without consuming excessive resources:

```bash
python code/main.py --batch-size 100 --skip-training
```

**Expected Outputs:**
- `data/raw/qm9_smiles.csv` (if not present, will be downloaded)
- `data/processed/descriptors.parquet` (contains 2D descriptors for the batch)
- `data/processed/correlation_matrix.csv`
- `logs/app.log` (contains pipeline execution logs)

**Validation Checks:**
1. Check that `data/processed/descriptors.parquet` exists and has the expected columns:
 ```bash
 python -c "import pandas as pd; df = pd.read_parquet('data/processed/descriptors.parquet'); print(f'Shape: {df.shape}'); print(f'Columns: {list(df.columns)}'); assert 'smiles' in df.columns; assert 'target' in df.columns"
 ```
2. Verify no 3D descriptors are present:
 ```bash
 python -c "import pandas as pd; df = pd.read_parquet('data/processed/descriptors.parquet'); assert not any('TPSA' in col for col in df.columns), 'TPSA found in output'; print('No 3D/TPSA descriptors found.')"
 ```
3. Check log file for successful completion:
 ```bash
 grep "Pipeline completed successfully" logs/app.log
 ```

### Step 3: Verify Data Loading

Validate that the data loader correctly processes SMILES strings:
```bash
python code/data/loader.py --input data/raw/qm9_smiles.csv --batch-size 10
```

**Expected Output:**
- Console output showing processed batches
- No errors related to SMILES validation

### Step 4: Verify Descriptor Computation

Ensure descriptors are computed correctly for a small set:
```bash
python code/data/preprocess_2d.py --input data/raw/qm9_smiles.csv --output data/processed/test_descriptors.parquet --batch-size 50
```

**Expected Output:**
- `data/processed/test_descriptors.parquet` with computed descriptors
- Console output showing descriptor computation progress

### Step 5: Verify Logging Configuration

Check that logging is configured correctly:
```bash
python -c "from utils.logging_config import setup_logging; setup_logging(); import logging; logger = logging.getLogger('test'); logger.info('Test log message'); print('Logging configuration verified.')"
```

## Troubleshooting

### Missing Dependencies
If you encounter import errors, ensure all dependencies are installed:
```bash
pip install -r code/requirements.txt --force-reinstall
```

### Data Download Failures
If the QM9 data download fails, check your internet connection and try again. The script will validate checksums automatically.

### Memory Issues
If you encounter memory issues, reduce the `--batch-size` parameter in the commands above.

## Next Steps

After successful validation:
1. Run the full pipeline without `--skip-training` to train the model.
2. Review the generated reports in `data/processed/analysis/`.
3. Customize hyperparameters in `code/config.yaml` for production runs.

## Notes

- This quick start guide is designed for validation purposes only.
- For production runs, refer to the full documentation in `README.md`.
- All data artifacts are stored in the `data/` directory as per project structure.
