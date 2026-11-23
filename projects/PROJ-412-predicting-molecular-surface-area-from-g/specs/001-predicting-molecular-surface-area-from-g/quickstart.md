# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites
- Python 3.11+
- Git
- 14 GB Disk Space (for dataset caching)
- 7 GB+ RAM

## 1. Clone and Setup
```bash
git clone <repo-url>
cd projects/PROJ-412-predicting-molecular-surface-area-from-g
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Data Ingestion
Run the ingestion script to download and process the ZINC15 dataset.
```bash
python code/data/ingest.py --source zinc15 --output data/processed/molecules.parquet
```
*This script will:*
- Stream data from HuggingFace.
- Validate SMILES.
- Generate 3D conformers and surface area labels.
- Exclude invalid molecules.
- Save checksums to `data/checksums.json`.

## 3. Split Data
```bash
python code/data/split.py --input data/processed/molecules.parquet --output data/processed/splits/
```
*This script ensures the KS test p-value > 0.05 for molecular weight distributions.*

## 4. Train Models
```bash
# Train GCN
python code/train.py --model gcn --config code/config.py

# Train Baseline
python code/train.py --model baseline --config code/config.py
```
*Training runs on CPU. Max 50 epochs with early stopping.*

## 5. Evaluate & Analyze
```bash
# Evaluate both models
python code/eval.py --models artifacts/gcn_model.pt artifacts/baseline_model.pt --test data/processed/splits/test.parquet

# Sensitivity Analysis
python code/sensitivity.py --results artifacts/results.json --thresholds 0.01 0.05 0.1
```

## 6. Verify Results
Check `artifacts/final_report.json` for:
- MAE, RMSE, R² for both models.
- Paired t-test p-value and Cohen's d.
- Sensitivity analysis with corrected p-values.
