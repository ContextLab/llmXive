# Quickstart: 001-gene-regulation

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended for CI compatibility).
- **Memory**: 7 GB RAM minimum.
- **Disk**: 14 GB free space.
- **Network**: Access to `ftp.ncbi.nlm.nih.gov`.

## Installation

1. **Clone the repository** and navigate to the project root.  
2. **Create a virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *All packages are pinned to CPU‑only wheels.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### 1. Fetch and Preprocess Data
Downloads, verifies, filters, normalizes, and harmonizes gene IDs ([deferred] intersection). Datasets that fail verification (e.g., GSE40677) are automatically excluded.
```bash
python code/main.py --stage preprocess \
    --accessions GSE30047,GSE51148,GSE59991,GSE66904
```
*Output*: `data/processed/feature_space.csv`, intermediate TPM files in `data/processed/`.

### 2. Train and Evaluate Model
Runs leave‑one‑dataset‑out CV with intra‑fold batch correction, stability selection, and global permutation baseline.
```bash
python code/main.py --stage train \
    --seed 42 \
    --n_estimators 200 \
    --bootstrap 1000
```
*Output*: `results/model_metrics.json`, `results/confusion_matrix.png`.

### 3. Generate Embeddings (Unsupervised Validation)
Runs UMAP on the batch‑corrected test set of each LODO fold.
```bash
python code/main.py --stage embed --algorithm umap
```
*Output*: `results/embedding_coords.csv`, `results/umap_plot.png`.

### 4. Full Run
Executes all steps sequentially.
```bash
python code/main.py --full-run
```

## Verification

1. Inspect `results/model_metrics.json` for cross‑dataset accuracy, post‑hoc power, MDES, and stability scores.  
2. Open `results/umap_plot.png` – at least three stress clusters should have Silhouette > 0.4.  
3. Run the test suite:
   ```bash
   pytest tests/ -v
   ```

## Troubleshooting

- **Feature Space Insufficient**: Occurs if the [deferred] gene intersection yields < 1500 genes. Check `data/processed/feature_space.csv` for the actual count.
- **Data Unavailable**: One of the GEO accessions could not be fetched or failed organism/stress verification. Review `logs/exclusion.log`.  
- **Underpowered**: Post‑hoc power < 0.8; see `results/model_metrics.json` for MDES and power estimates.  
- **Confounding Detected**: If a dataset contains only a single stress type or is highly confounded, it is excluded automatically; see the exclusion log.  
- **Memory Error**: Reduce `--n_estimators` or the top‑k gene count in `config.py`.

All steps are fully reproducible on a fresh GitHub Actions runner; random seeds are pinned in `code/config.py`, and the project state file `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` is updated after each major artifact.