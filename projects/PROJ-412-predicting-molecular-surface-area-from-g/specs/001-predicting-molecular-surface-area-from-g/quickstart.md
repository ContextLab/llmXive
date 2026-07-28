# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM available
- Internet access (for dataset download)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-412-predicting-molecular-surface-area-from-g
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    # Install CPU-only PyTorch and Torch Geometric
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install torch-geometric==2.5.3
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `rdkit`, `pandas`, `scikit-learn`, `datasets`.*

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
Generates 2D graphs and 3D SASA labels.
```bash
python code/main.py --stage preprocess
```
- **Output**: `data/processed/paired_dataset.parquet`
- **Logs**: `logs/preprocess.log` (includes invalid SMILES count, conformer failure rate).

### 2. Model Training
Trains GCN model.
```bash
python code/main.py --stage train
```
- **Output**: `models/gcn_model.pt`
- **Logs**: `logs/train.log` (loss curves, early stopping info).

### 3. Evaluation & Sensitivity Analysis
Compares models and runs threshold sweeps.
```bash
python code/main.py --stage evaluate
```
- **Output**: `data/results/metrics.json`, `data/results/sensitivity_analysis.csv`
- **Logs**: `logs/evaluate.log` (t-test/wilcoxon results, p-values).

### 4. Full Run
Runs the entire pipeline end-to-end.
```bash
python code/main.py --stage full
```

## Verification

To verify the pipeline ran correctly:
1.  Check `data/processed/paired_dataset.parquet` exists and has no `NaN` in the `sasa` column.
2.  Check `data/results/metrics.json` contains `p_value` and `statistic`.
3.  Verify `logs/preprocess.log` shows conformer failure rate < 10% (or a failure report generated).

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in `config.py` or enable `--streaming` flag.
- **Conformer Failure**: Increase `--max-attempts` in `config.py`. If >10% fail, check input SMILES quality.
- **Import Error**: Ensure `torch` and `torch-geometric` versions match (see `requirements.txt`).
