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

1. **Load & Verify Data (streaming)**
 ```bash
 python code/data/preprocess.py
 ```
 - Streams the verified datasets from Hugging Face, computes SHA‑256 checksums, parses SMILES, and writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv`.
 - If the valid‑molecule retention rate falls below 95 %, the script logs a warning and **exits with a non‑zero code after the files are written** (so they are available for inspection).
 - If no `permeability` column is found, the script stops after this step with an informative message and prompts the user to approve a surrogate target via the spec‑amendment workflow (see Phase 0 of the plan).

2. **Create Train/Test Split**
 ```bash
 python code/data/split.py
 ```
 - Generates `data/processed/train.parquet` and `data/processed/test.parquet` (stratified when possible) [UNRESOLVED-CLAIM: c_d8df92df — status=not_enough_info].

3. **Train GNN Model**
 ```bash
 python code/models/gnn_train_and_checkpoint.py
 ```
 - Runs the GNN training routine, producing the checkpoint file `code/models/gnn.pt` [UNRESOLVED-CLAIM: c_ac17941f — status=not_enough_info].

4. **Train & Evaluate Remaining Models**
 ```bash
 # Train all models, perform power analysis, and evaluate
 python code/analysis/train.py --config config.yaml
 ```

5. **Interpretability**
 ```bash
 python code/analysis/explain.py
 ```

6. **Full End‑to‑End Run (optional)**
 ```bash
./run_all.sh
 ```
 *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables (or a warning if retention < 95 %).
- `data/processed/train.parquet` and `data/processed/test.parquet` – train/test splits.
- `code/models/gnn.pt` – trained GNN checkpoint.
- `results/metrics.json` – RMSE, MAE, R² for GNN, RF, RF‑ablation; paired test result; normality test outcome; power‑analysis summary; bias‑check flag; **interpretability overlap** metric.
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.