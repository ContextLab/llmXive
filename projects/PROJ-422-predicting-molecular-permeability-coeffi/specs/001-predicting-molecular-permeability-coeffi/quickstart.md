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
   - The script **first searches for an experimental `permeability` column**; if none is found, it **searches for an approved surrogate column** (e.g., `simulated_permeability`, `logS`, `solubility`).  
   - If a surrogate is found, the pipeline records `target_type: "surrogate"` in the metadata and proceeds.  
   - If **no target column** (experimental nor surrogate) is present, the script prints a clear error, creates a GitHub issue titled “Request open permeability dataset for PROJ‑422”, and exits with status 1. No downstream steps are executed.

2. **Preprocess**
   ```bash
   python code/data/preprocess.py
   ```
   - Parses SMILES with `rdkit.Chem.MolFromSmiles`; logs & drops invalid entries (FR‑011).  
   - **Retention Guard**: ensures ≥ 95 % of molecules are valid; if not, attempts canonicalization and aborts if still below threshold.  
   - Computes MW, logP, TPSA, HBA, HBD, rotatable bonds, and one‑hot `polymer_type` (if present).  
   - Writes `data/processed/processed_data.parquet` **and** `processed_data.csv`.  
   - If a surrogate target is used, `target_type` is set to `"surrogate"` in the output files.

3. **(Optional) Split – runs only if a target column is present**
   ```bash
   python code/data/split.py
   ```
   - Generates 5‑fold stratified CV splits and a hold‑out test set, each as Parquet and CSV.  
   - The script aborts with a clear error if the `target` column is missing, ensuring that downstream steps are never run on an invalid dataset.

4. **Train Models**
   ```bash
   python code/analysis/train.py
   ```
   - Trains the GNN and Random Forest on each CV fold, applies early stopping, records wall‑clock time, and writes `results/training_log.json`.  
   - **Power‑analysis gate**: if the achieved power is < 0.8 the script aborts and logs `sufficient: false`.

5. **Evaluate & Test Significance**
   ```bash
   python code/analysis/evaluate.py
   ```
   - Computes RMSE, MAE, R² for both models on the **hold‑out test set**, performs the Shapiro‑Wilk normality test on per‑sample error differences, then runs the appropriate paired test (t‑test or Wilcoxon) **on those per‑sample errors**, and records the p‑value and significance flag.

6. **Interpretability**
   ```bash
   python code/analysis/explain.py
   ```
   - Generates SHAP bar charts for the Random Forest and GNNExplainer substructure heatmaps for the GNN.  
   - Computes the **deterministic overlap metric** using a pre‑defined SMARTS‑to‑descriptor lookup table and a permutation‑test (10 000 shuffles) to obtain a p‑value; results are stored in `results/metrics.json`.

7. **Full End‑to‑End Run (convenience)**
   ```bash
   ./run_all.sh
   ```
   *`run_all.sh`* sequentially executes the commands above with `set -e`, aborting early if any step returns a non‑zero exit code (e.g., when no permeability target is found, power is insufficient, or a script fails).  

## Expected Outputs
- `data/processed/processed_data.parquet` and `processed_data.csv` – cleaned feature tables (or a graceful halt if target missing).  
- `data/processed/` – 5 CV split files + hold‑out test set (only when a target exists).  
- `code/models/gnn.pt`, `code/models/rf.pkl` – trained model checkpoints.  
- `results/training_log.json` – start/end timestamps, total_hours, power‑analysis fields for each model; training aborts if `sufficient` is false.  
- `results/metrics.json` – RMSE, MAE, R² for both models, statistical‑test outcome, bias‑check (including any dropped descriptors), and interpretability overlap metric (including permutation p‑value).  
- `results/interpretability/` – PNG/HTML visualizations for SHAP and GNNExplainer.  

## Reproducibility Tips
- Random seeds are fixed (`seed=42`) inside the code base.  
- All dataset URLs are hard‑coded; rerunning the pipeline will fetch identical data.  
- The CI runner uses the same `requirements.txt`; no hidden dependencies.  

## What Happens When No Permeability Data Is Available?
`code/data/download.py` will stop after checksum verification, log the absence of a `permeability` column, and **automatically file a GitHub issue** titled “Request open permeability dataset for PROJ‑422”. The pipeline will **not** proceed to preprocessing, splitting, or modeling until a suitable dataset is added, preserving scientific rigor.  

---



