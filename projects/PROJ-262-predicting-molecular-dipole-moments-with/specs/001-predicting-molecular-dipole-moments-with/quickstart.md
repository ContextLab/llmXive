# Quickstart: Predicting Molecular Dipole Moments with Graph Neural Networks

## Prerequisites

- Python 3.11+
- 2 CPU cores minimum
- 8GB RAM minimum
- 10GB disk space for data + checkpoints

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd projects/PROJ-262-predicting-molecular-dipole-moments-with
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

### 2. Download and Verify Data

```bash
python code/data/download_qm9.py
# Output: data/raw/qm9.parquet with checksum verification
```

### 3. Run Full Pipeline

```bash
# Extract features
python code/data/preprocess_3d.py
python code/data/extract_2d_descriptors.py

# Train models (5 seeds each)
python code/training/train_gnn.py --seeds 42,123,456,789,101112
python code/training/train_rf.py --seeds 42,123,456,789,101112

# Evaluate and analyze
python code/training/evaluate.py
python code/attribution/permutation_importance.py
python code/attribution/saliency_mapping.py
python code/analysis/statistical_tests.py
```

### 4. View Results

```bash
cat results/metrics.csv
cat results/significance.csv
ls results/figures/
```

## Expected Output

### Directory Structure After Completion

```
data/
├── raw/
│   └── qm9.parquet              # ~500MB, checksummed
├── processed/
│   ├── features_3d.parquet      # ~100MB
│   ├── features_2d.parquet      # ~50MB
│   └── molecules_10k.parquet    # ~30MB
└── checkpoints/
    ├── model_seed_42.pt         # GNN checkpoint
    ├── model_seed_123.pt
    ├── ...
    ├── rf_seed_42.pkl           # RF checkpoint
    └── ...

results/
├── metrics.csv                  # MAE, RMSE for all seeds
├── attributions.json            # Feature importance rankings
├── significance.csv             # Paired t-test results
└── figures/
    ├── importance_barplot.png
    ├── molecule_saliency_001.png
    └── rmse_distribution.png
```

### Sample Output (metrics.csv)

```csv
metric_name,model_type,seed,value,std_error
MAE,schnet,42,0.142,0.008
MAE,schnet,123,0.138,0.007
MAE,schnet,456,0.145,0.009
MAE,schnet,789,0.141,0.008
MAE,schnet,101112,0.143,0.008
MAE,random_forest,42,0.187,0.011
MAE,random_forest,123,0.182,0.010
MAE,random_forest,456,0.191,0.012
MAE,random_forest,789,0.185,0.010
MAE,random_forest,101112,0.189,0.011
```

### Sample Output (significance.csv)

```csv
test_statistic,p_value,significant,comparison
t=4.23,p=0.0023,TRUE,schnet_vs_rf_mae
t=3.87,p=0.0051,TRUE,schnet_vs_rf_rmse
```

## Troubleshooting

### Dataset Download Fails

```bash
# Try alternative verified source
python code/data/download_qm9.py --source https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet
```

### Memory Error During Training

```bash
# Reduce batch size
python code/training/train_gnn.py --batch-size 32
```

### Timeout (>6h Runtime)

```bash
# Reduce seeds for quick test
python code/training/train_gnn.py --seeds 42
python code/training/train_rf.py --seeds 42
```

## Verification Commands

```bash
# Verify data integrity
python -c "import hashlib; f=open('data/raw/qm9.parquet','rb'); print(hashlib.sha256(f.read()).hexdigest())"

# Verify 10k subset
python -c "import pandas as pd; df=pd.read_parquet('data/processed/molecules_10k.parquet'); print(f'Molecules: {len(df)}')"

# Verify no NaN values
python -c "import pandas as pd; df=pd.read_parquet('data/processed/features_3d.parquet'); print(f'NaN count: {df.isna().sum().sum()}')"

# Verify schema compliance
pytest tests/contract/
```

## Next Steps

1. Review `research.md` for methodology details
2. Check `data-model.md` for schema definitions
3. Run `pytest tests/contract/` to verify data integrity
4. Examine `results/figures/` for attribution visualizations
5. Read `plan.md` for full implementation roadmap
