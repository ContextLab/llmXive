# Quick Start Guide

This guide provides a minimal set of commands to run the full pipeline on the ESOL dataset.

## Step 1: Environment Setup

```bash
pip install -r requirements.txt
python code/setup_environment.py
```

## Step 2: Data Pipeline

Run the data download, preprocessing, and splitting scripts sequentially:

```bash
python code/data/download_esol.py
python code/data/preprocess.py
python code/data/split.py
```

## Step 3: Model Training

Train the baseline and GNN models:

```bash
# Set seeds for reproducibility
python code/training/set_seeds.py

# Train Random Forest
python code/training/train_baseline.py

# Train GNN (MPNN)
python code/training/train_gnn.py
```

## Step 4: Analysis

Generate the final report and visualizations:

```bash
python code/evaluation/compare_models.py
python code/evaluation/statistical_test.py
python code/evaluation/interpretability.py
python code/evaluation/report_generator.py
```

## Expected Outputs

After completion, verify the following files exist:

- `data/raw/esol.csv`
- `data/processed/processed_data.json`
- `models/baseline_rf.pkl`
- `models/gnn_mpnn.pt`
- `results/baseline_metrics.json`
- `results/gnn_metrics.json`
- `results/final_report.json`
- `results/feature_importance_*.png`

## Troubleshooting

- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
- **Data Download Failures**: Check internet connection and verify the MoleculeNet/HuggingFace endpoint is accessible.
- **CUDA Errors**: This project is CPU-only. If you see CUDA errors, ensure `torch` is installed in CPU mode and no GPU flags are set in the code.
