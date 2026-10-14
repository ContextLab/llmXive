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

1. **Download & Verify Raw Data**
   ```bash
   python code/data/download.py
   ```
   - Downloads all verified datasets into `data/raw/`.  
   - Computes SHA256 checksums; aborts on mismatch.

2. **Preprocess**
   ```bash
   python code/data/preprocess.py
   ```
   - Parses SMILES, builds graphs, computes RDKit descriptors, performs retention & bias checks.  
   - Outputs `data/processed/processed_data.parquet`.

3. **Train / Evaluate**
   ```bash
   # Train all models and evaluate in one command
   python code/analysis/train.py --config config.yaml
   ```
   - Handles train/validation split, early stopping, and writes `results/metrics.json`.  
   - If the dataset is larger than available RAM, the script automatically streams.

4. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP plots for the Random Forest and GNNExplainer visualizations for the GNN.  
   - Outputs are stored in `results/interpretability/`.

5. **Full End‑to‑End Run (optional)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* simply chains the three commands above and exits with a non‑zero code if any step fails.

## Expected Outputs
- `data/processed/processed_data.parquet` – cleaned feature table.  
- `results/metrics.json` – RMSE, MAE, R² for GNN, RF, RF‑ablation; paired t‑test p‑value; Cohen’s d; bias‑check flag.  
- `results/interpretability/` – PNG/HTML files for SHAP bar charts and GNNExplainer substructure heatmaps.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.

---
