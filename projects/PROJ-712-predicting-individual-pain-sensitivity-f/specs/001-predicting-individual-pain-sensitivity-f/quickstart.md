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
   The pipeline expects a folder `data/raw/` containing the **OpenNeuro ds003542** dataset, which provides:  
   - Resting‑state EEG recordings (e.g., `.fif` files)  
   - `heat_pain_thresholds.csv` with columns `participant_id,heat_pain_threshold[,age,gender]`  

   Download programmatically:
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
A non‑zero exit code indicates missing or mismatched citations; fix them before proceeding.

## Running the Full Pipeline
```bash
python code/main.py
```
The orchestrator will:
1. **Create required directories** (`scripts/create_dirs.sh`).  
2. **Run integration test** (`pytest tests/integration/test_structure.py`) to confirm directory creation.  
3. **Preprocess EEG** (streamed via `DataChunk`) and write `data/processed/feature_matrix.csv`.  
4. **Pilot construct‑validity** on a 20‑participant subset, logs a warning if no feature reaches |r| ≥ 0.20 but does **not abort**.  
5. **Train Elastic Net** with nested CV, perform the global permutation test, and write `artifacts/model_results.json`.  
6. **Compute diagnostics** (permutation importance, FDR, VIF, sensitivity sweep); results saved in `artifacts/diagnostics.csv` and `artifacts/sensitivity_report.md`.  
7. **Record SHA‑256 hashes** of all artifacts in `artifacts/manifest.json`.  
8. **Log runtime** in `artifacts/runtime_log.json`.  

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
- **Unit tests** verify core functions (e.g., `extract_microstate_features`).  
- **Integration tests** run the full preprocessing on a small subset and check that `data/processed/feature_matrix.csv` exists, has the correct columns, and contains no NaNs.  

## Output Interpretation
| File | Description |
|------|-------------|
| `artifacts/model_results.json` | Pearson r, empirical p‑value, MAE, 95 % CI, runtime. |
| `artifacts/diagnostics.csv` | Coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags (including the verified VIF = 33 flag). |
| `artifacts/sensitivity_report.md` | Tables & plots for binary classification AUC/accuracy across median‑split thresholds and regularization sweep. |
| `figures/` | PDF/PNG versions of key plots (correlation scatter, importance bar, VIF histogram, ROC curves). |

## Troubleshooting
- **MemoryError** – The pipeline streams data via `DataChunk`; ensure you are not forcing a full preload.  
- **ConvergenceWarning** – The script will automatically increase `max_iter` (Edge Case 2). If convergence still fails, the run aborts with an explicit error.  
- **Blocked status** – Verify that the OpenNeuro ds003542 dataset containing `heat_pain_threshold` is present in `data/raw/`. No placeholder data should be used.  

---

