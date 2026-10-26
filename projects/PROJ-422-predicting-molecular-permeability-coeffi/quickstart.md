# Quickstart: Molecular Permeability GNN Pipeline

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to download Hugging Face datasets)

## Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-422-predicting-molecular-permeability-coeffi

# Create and activate a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Download Raw Data**
 ```bash
 python code/data/download.py
 ```
 - Streams the verified dataset (or falls back to the local sample) and writes
 `data/raw/permeability_data.csv` together with a SHA‑256 manifest
 `data/raw/checksums.json`.

2. **Load & Verify Data (streaming)**
 ```bash
 python code/data/preprocess.py
 ```
 - Parses SMILES, computes descriptors, builds molecular‑graph JSON, and writes
 both `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv`.

3. **Create Train/Test Split**
 ```bash
 python code/data/split.py
 ```
 - Generates `data/processed/train.parquet`, `train.csv`, `test.parquet`,
 and `test.csv` (stratified when possible).

4. **Train GNN Model**
 ```bash
 python code/models/gnn_train_and_checkpoint.py
 ```
 - Runs the GNN training routine, producing the checkpoint file
 `code/models/gnn.pt`.

5. **Train & Evaluate Remaining Models**
 ```bash
 # Train all models, perform power analysis, and evaluate
 python code/analysis/train.py --config config.yaml
 ```

6. **Interpretability**
 ```bash
 python code/analysis/explain.py
 ```

7. **Full End‑to‑End Run (optional)**
 ```bash
./run_all.sh
 ```
 *`run_all.sh`* simply chains the commands above and exits with a non‑zero code
 if any step fails.

## Expected Outputs
- `data/raw/permeability_data.csv` and `data/raw/checksums.json` – raw dataset and its checksum.
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables.
- `data/processed/train.parquet` and `train.csv`, `test.parquet` and `test.csv` – train/test splits.
- `code/models/gnn.pt` – trained GNN checkpoint.
- `results/metrics.json` – RMSE, MAE, R² for GNN and RF; paired test result; statistical‑test outcome;
 power‑analysis summary; **interpretability overlap** metric.
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure
 heatmaps.