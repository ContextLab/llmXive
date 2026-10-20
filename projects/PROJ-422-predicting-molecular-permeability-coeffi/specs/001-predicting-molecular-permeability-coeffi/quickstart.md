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
   - Streams the verified datasets directly from Hugging Face, computes SHA‑256 checksums on the fly, parses SMILES, and writes `data/processed/processed_data.parquet`.  
   - Logs a warning and **exits with a non‑zero code after the file is written** if the valid‑molecule retention rate falls below 95 %; the file is still present for inspection.  
   - If no `permeability` column is found, the script stops after this step with an informative message (see research plan).

2. **Train / Evaluate** *(only runs when a true permeability target is present)*
   ```bash
   # Train all models and evaluate in one command
   python code/analysis/train.py --config config.yaml
   ```
   - Handles train/validation split, early stopping, a priori power analysis, and writes `results/metrics.json`.  
   - If the required target column is missing, the script will terminate gracefully after reporting the limitation.

3. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP plots for the Random Forest and GNNExplainer visualizations for the GNN.  
   - Outputs are stored in `results/interpretability/`.

4. **Full End‑to‑End Run (optional)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` – cleaned feature table (or a warning if retention < 95 %).  
- `results/metrics.json` – RMSE, MAE, R² for GNN, RF, RF‑ablation; paired test result; normality test outcome; power‑analysis summary; bias‑check flag.  
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.
