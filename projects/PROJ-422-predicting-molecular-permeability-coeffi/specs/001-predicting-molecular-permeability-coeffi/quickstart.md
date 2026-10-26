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

1. **Verify & Download Data**
   ```bash
   python code/data/download.py
   ```
   - Streams the verified datasets from Hugging Face, checks SHA‑256 checksums, and writes raw files under `data/raw/`.  
   - The script **first searches for an experimental `permeability` column**; if none is found, it **searches for an approved surrogate column** (e.g., `simulated_permeability`, `logS`).  
   - **Surrogate Independence Check**: compute Pearson correlation between the surrogate and every standard descriptor; accept the surrogate only when max |r| < 0.5.  
   - If **no target column** (experimental nor surrogate) is present, the script prints a clear error, **creates a GitHub issue** titled “Request open permeability dataset for PROJ‑422”, and exits with status 1. No downstream steps are executed.

2. **Preprocess**
   ```bash
   python code/data/preprocess.py
   ```
   - Parses SMILES with `rdkit.Chem.MolFromSmiles`; logs & drops invalid entries (FR‑011).  
   - **Retention Guard**: ensures **≥ 95 %** of molecules are valid; aborts if < 95 % valid (FR‑012).  
   - Computes MW, logP, TPSA, HBA, HBD, rotatable bonds, and one‑hot `polymer_type` (if present).  
   - Writes `data/processed/processed_data.parquet` **and** `processed_data.csv`.  
   - If a surrogate target is used, `target_type` is set to `"surrogate"` in the output files.

3. **Split – runs only if a target column is present**
   ```bash
   python code/data/split.py
   ```
   - Generates **5‑fold stratified CV** splits and a **hold‑out test set**; aborts with a clear error if the `target` column is missing, ensuring that downstream **only runs** when a valid target exists.  
   - Logs an informative message if the dataset is too small (< 50 samples) and falls back to a random split with a warning.

4. **Train Models**
   ```bash
   python code/analysis/train.py
   ```
   - Trains the GNN and Random Forest on each CV **training** fold, applies early stopping, records wall‑clock time, and writes `results/training_log.json`.  
   - **Power‑analysis gate **ensures** `achieved_power` ≥ 0.8; if not, training aborts and logs the insufficiency.  
   - Writes model checkpoints `code/models/gnn.pt` and `code/models/rf.pkl`.  
   **Returns **exit 0** on success (fixes previous T007 failure).**

5. **Evaluate & Test Significance**
   ```bash
   python code/analysis/evaluate.py
   ```
   - Computes RMSE, MAE, R² on the **hold‑out test set** (not aggregated fold means), performs the Shapiro‑Wilk normality test on per‑sample error differences, then runs the appropriate paired test (t‑test or Wilcoxon) **on those per‑sample errors**, and records the p‑value and significance flag.

6. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates **SHAP** bar charts for the Random Forest and **GNNExplainer** subgraph heatmaps for the GNN.  
   - Computes the **empirical overlap metric**: <br> • Count `overlap_top5` (number of overlapping features between GNN substructure mapping and SHAP descriptor ranking).<br> • Set `overlap_meets_threshold` **true when `overlap_top5 ≥ 3`** (per SC‑003).  
   - Stores results in `results/metrics.json`.

7. **Full End‑to‑End Run (convenience)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* sequentially executes the commands above with `set -e`, aborting early if any step returns a non‑zero exit code (e.g., when no permeability target is found, power is insufficient, or a script fails). This script now **returns** exit 0 **only** when all stages succeed (fixes previous T004).

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned **if** a target is present; otherwise the pipeline halts with a logged error.
- `data/processed/` – 5 CV split files + hold‑out test set (only when a target exists).  
- `code/models/gnn.pt`, `code/models/rf.pkl` – trained model checkpoints.  
- `results/training_log.json` – start/end timestamps, **total_hours** (must be < 6 h), **planned_sample_size**, **achieved_power**, **sufficient** flag.  
- `results/metrics.json` – RMSE, MAE, R² for both models, statistical‑test outcome, bias‑check (including max correlation coefficient), and interpretability overlap metric (`overlap_top5`, `overlap_meets_threshold`).  
- `results/interpretability/` – PNG/HTML visualizations for SHAP and GNNExplainer.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden packages are assumed.

## What Happens When No Permeability Data Is Available?
`code/data/download.py` will stop after checksum verification, log the absence of a `permeability` column, and **automatically file a GitHub issue** titled “Request open permeability dataset for PROJ‑422”. The pipeline will **not** proceed to preprocessing, splitting, or modeling until a suitable dataset is added, preserving scientific rigor.  

---



