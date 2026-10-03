# Quickstart Guide

## Prerequisites

- Python 3.10+
- pip
- git

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

1. **Download Data** (T005):
 ```bash
 python code/data/download.py
 ```

2. **Preprocess Data** (T006a, T006b):
 ```bash
 python code/data/preprocess.py
 ```

3. **Train Deep Ensemble** (T013):
 ```bash
 python code/models/deep_ensemble.py
 ```

4. **Train MC Dropout** (T014):
 ```bash
 python code/models/mc_dropout.py
 ```

5. **Train Sparse GP** (T015b, T015c):
 ```bash
 python code/models/sparse_gp.py
 ```

6. **Run Inference and Calculate Metrics** (T016a, T016b):
 ```bash
 python code/main.py
 ```

## Output Artifacts

After successful execution, the following artifacts will be generated:

- `data/raw/oqmd.parquet`: Raw dataset
- `data/processed/features_train_20pca.csv`: Training features (PCA reduced)
- `data/processed/features_val_20pca.csv`: Validation features (PCA reduced)
- `data/processed/features_test_20pca.csv`: Test features (PCA reduced)
- `results/models/ensemble/`: Trained ensemble models
- `results/models/mc_dropout/`: Trained MC Dropout model
- `results/models/sparse_gp_model.pt`: Trained Sparse GP model
- `results/uq_predictions_mc_dropout.csv`: MC Dropout predictions
- `results/calibration_report.csv`: Calibration metrics
- `results/reliability_diagrams/`: Reliability diagrams

## Troubleshooting

If you encounter errors:

1. Ensure all dependencies are installed: `pip install -r code/requirements.txt`
2. Check that data files exist in `data/raw/` and `data/processed/`
3. Verify configuration in `code/config.yaml`
4. Check logs in `logs/` directory for detailed error messages