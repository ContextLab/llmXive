# Quickstart: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Prerequisites
- **Python** ≥ 3.11  
- **RAM** ≥ 8 GB (minimum 7 GB for CI)  
- **Disk** ≥ 15 GB free (raw EEG can be large)  
- **Dependencies** listed in `requirements.txt`

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-712-predicting-individual-pain-sensitivity-f

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup
1. **Obtain the dataset**  
   The pipeline expects a folder `data/raw/` containing the **OpenNeuro ds003542** accession, which provides:
   - Resting‑state EEG recordings (e.g., `.fif` or `.edf` files)  
   - `heat_pain_thresholds.csv` with columns `participant_id,heat_pain_threshold[,age,gender]`  
   The dataset can be downloaded programmatically:
   ```bash
   python -c "import datasets; datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')"
   ```
   **Important:** If the downloaded CSV does not contain a `heat_pain_threshold` column, the script will exit with the message:  
   ```
   Dataset lacks verified pain threshold labels in provided verified sources.
   ```
2. **Verify integrity**  
   ```bash
   python code/utils.py --verify-checksums
   ```

## Pre‑Run Validation
Run the citation‑validation guard (required by Constitution II):
```bash
bash scripts/pre-run-validation.sh
```
If the script returns a non‑zero exit code, fix the cited references before proceeding.

## Running the Full Pipeline
```bash
python code/main.py
```
The orchestrator will:
1. Preprocess EEG (streamed via `DataChunk`) and write `data/processed/feature_matrix.csv`.  
2. Perform a **pilot construct‑validity analysis** on a 20‑participant subset; abort if no feature shows |r| ≥ 0.20.  
3. Train Elastic Net with nested CV, perform the global permutation test, and write `artifacts/model_results.json`.  
4. Compute diagnostics, permutation‑importance FDR, VIF (including the flagged VIF = 33 predictor), and sensitivity sweeps (logistic regression for binary outcomes); results saved in `artifacts/diagnostics.csv` and `artifacts/sensitivity_report.md`.  
5. Record SHA‑256 hashes of all artifacts in the project state file.

## Running Individual Steps (optional)
```bash
# Only preprocessing
python code/main.py --step preprocess

# Only modeling (requires preprocessed features)
python code/main.py --step model

# Only diagnostics (requires model results)
python code/main.py --step diagnostics
```

## Testing
```bash
pytest -q
```
- **Unit tests** verify each module’s core functions (e.g., `extract_microstate_features` returns a multi‑column DataFrame containing the extracted microstate features).  
- **Integration tests** run the full preprocessing on a small participant subset and check that `data/processed/feature_matrix.csv` exists, has multiple feature columns plus covariates, and contains no NaNs.  

## Output Interpretation
| File | Description |
|------|-------------|
| `artifacts/model_results.json` | Pearson r, empirical p‑value, MAE, 95 % CI, runtime. |
| `artifacts/diagnostics.csv` | Coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags (including VIF = 33). |
| `artifacts/sensitivity_report.md` | Tables & plots for binary classification AUC/accuracy across median‑split thresholds and regularization sweep. |
| `figures/` | PDF/PNG versions of key plots (correlation scatter, importance bar, VIF histogram, ROC curves). |

## Troubleshooting
- **MemoryError** – Ensure `data/raw/` files are not being fully loaded; the pipeline streams data in `DataChunk` batches automatically.  
- **ConvergenceWarning** – The script will automatically increase `max_iter` (Edge Case 2). If convergence still fails, the run aborts with an explicit error.  
- **Blocked status** – Verify that the OpenNeuro ds003542 dataset containing `heat_pain_threshold` has been placed in `data/raw/`. No placeholder data should be used.  



---
