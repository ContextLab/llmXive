# Quickstart Guide

## Prerequisites
- Python 3.10+
- pip

## Installation
```bash
pip install -r code/requirements.txt
```

## Running the Pipeline
The pipeline consists of several stages. Run them in order:

1. **Download Data** (T005):
 ```bash
 python code/data/download.py
 ```

2. **Preprocess Data** (T006a):
 ```bash
 python code/data/preprocess.py
 ```

3. **Train Models** (T012, T013b, T014, T015):
 ```bash
 python code/models/baseline_nn.py
 python code/models/deep_ensemble.py
 python code/models/mc_dropout.py
 python code/models/sparse_gp.py
 ```

4. **Run UQ Inference** (T016a):
 ```bash
 python code/models/run_single_seed.py --seed 42
 python code/models/run_single_seed.py --seed 43
 python code/models/run_single_seed.py --seed 44
 ```

5. **Compute Calibration Metrics** (T024):
 ```bash
 python code/uq/compute_calibration_report.py
 ```

6. **Screening Analysis** (T028):
 ```bash
 python code/uq/screening.py
 ```

7. **Main Orchestrator** (T016b):
 ```bash
 python code/main.py
 ```

## Expected Outputs
After running the full pipeline, you should find:
- `data/raw/oqmd.parquet` - Raw dataset
- `data/processed/raw_train.csv`, `raw_val.csv`, `raw_test.csv` - Stratified splits with `target_bin`
- `data/processed/features_train_20pca.csv`, etc. - PCA-transformed features
- `results/` - Model checkpoints, predictions, and metrics