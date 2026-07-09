# Quickstart: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## Prerequisites
- Python 3.10+
- Git
- Access to GitHub Actions (for CI) or a local Linux environment with 7GB+ RAM.

## 1. Clone and Setup

```bash
git clone <repo-url>
cd projects/PROJ-351-predicting-the-solubility-of-pharmaceuti
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Run the Pipeline

The `main.py` script orchestrates the full pipeline: download, clean, train, evaluate, and visualize.

```bash
# Run full pipeline
python code/main.py

# Run individual steps (optional)
python code/data/download_esol.py
python code/data/preprocess.py
python code/training/train_baseline.py
python code/training/train_gnn.py
python code/evaluation/statistical_test.py
python code/evaluation/interpretability.py
```

## 3. Verify Results

Check the `results/` directory for:
- `metrics.json`: Contains RMSE, R², p-value, and power.
- `interpretability/`: Contains PNG heatmaps for 5 molecules.

```bash
cat results/metrics.json
ls -lh results/interpretability/
```

## 4. Reproducibility Check

To ensure reproducibility, run the pipeline again. The results should be identical (within floating point tolerance) due to pinned random seeds.

```bash
# Clear previous results (optional)
rm -rf models/* results/*

# Re-run
python code/main.py

# Compare checksums (if implemented in CI)
sha256sum results/metrics.json
```

## 5. Troubleshooting

- **RDKit Errors**: Ensure `rdkit` is installed correctly. Check `data/logs/exclusion.log` for invalid SMILES.
- **CUDA Errors**: If you see "CUDA not available", ensure you installed the CPU-only version of PyTorch and PyTorch Geometric.
- **Timeout**: If the job exceeds 6 hours, check the GNN training logs. The early stopping mechanism should have triggered. If not, reduce `max_epochs` in `code/models/gnn_mpnn.py`.
