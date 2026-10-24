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
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install exact dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Load & Verify Data (streaming)**
   ```bash
   python code/data/preprocess.py
   ```
   - Streams the verified datasets from Hugging Face, computes SHA‑256 checksums, parses SMILES, and writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv`.  
   - If the valid‑molecule retention rate falls below 95 %, the script attempts canonicalization, logs a warning, and writes the largest valid subset, continuing with a `retention_warning` flag in `results/metrics.json`.  
   - If no `permeability` column is found, the script halts after this step with an informative message and **automatically creates a GitHub issue** requesting a suitable open dataset (see Phase 0).  

2. **Cross‑Validation Training & Evaluation** *(only runs when a true permeability target is present or an approved surrogate is used)*
   ```bash
   # This runs the k‑fold CV, the hold‑out test, power analysis, bias check, and writes results/metrics.json
   python code/analysis/train.py --config config.yaml
   ```
   - Handles stratified CV, early stopping, power analysis, bias check, and records `sufficient: false` if under‑powered.  

3. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP plots for the Random Forest (excluding any surrogate target) and GNNExplainer visualizations for the GNN.  
   - Outputs are stored in `results/interpretability/`.  

4. **Full End‑to‑End Run (optional)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables (or a warning if retention < 95 %).  
- `data/processed/` contains **5 CV split files** (`train_fold_0.parquet`, `test_fold_0.parquet`, …) and a **[deferred] hold‑out** (`holdout_test.parquet`), each with matching CSV versions.
- `results/metrics.json` – RMSE, MAE, R² (mean ± SD across folds) for GNN and RF; paired test result; normality test outcome; power‑analysis summary; **interpretability overlap** metric; **bias_check** fields.  
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.  
- Model checkpoints: `code/models/gnn.pt`, `code/models/rf.pkl`.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.  

## What Happens When No Permeability Data Is Available?
The preprocessing script will stop after the retention guard and **automatically file a GitHub issue** titled “Request open permeability dataset for PROJ‑422”. No modeling or downstream analysis will be performed until such a dataset is added, preserving scientific rigor.  

---


