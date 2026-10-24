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
   - If the valid‑molecule retention rate falls below 95 %, the script logs a warning and **exits with a non‑zero code after the files are written** (so they are available for inspection).  
   - If no `permeability` column is found, the script stops after this step with an informative message and prompts the user to approve a surrogate target via the spec‑amendment workflow (see Phase 0 of the plan).  

2. **Train & Evaluate** *(only runs when a true permeability target is present or an approved surrogate is used)*
   ```bash
   # Train all models, perform power analysis, and evaluate
   python code/analysis/train.py --config config.yaml
   ```
   - Handles train/validation split, early stopping, power analysis, and writes `results/metrics.json`.  
   - If the required target column is missing and no surrogate is approved, the script terminates gracefully after reporting the limitation.

3. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP plots for the Random Forest (and ablation) and GNNExplainer visualizations for the GNN.  
   - Outputs are stored in `results/interpretability/`.

4. **Full End‑to‑End Run (optional)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables (or a warning if retention < 95 %).  
- `results/metrics.json` – RMSE, MAE, R² for GNN, RF, RF‑ablation; paired test result; normality test outcome; power‑analysis summary; bias‑check flag; **interpretability overlap** metric.  
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.

## What Happens When No Permeability Data Is Available?
The pipeline will stop after the preprocessing step and emit a clear message indicating that **FR‑001 cannot be satisfied with the current open datasets**. At that point, a spec‑amendment request can be submitted (see Phase 0) to permit a surrogate target. Until such an amendment is approved, no modeling or downstream analysis will be performed, preserving scientific rigor.  

---
