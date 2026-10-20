# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites
* Python 3.11 or newer  
* Git  
* ~2 GB free disk space (real data)  
* Internet connection (to install Python packages and download the OpenNeuro dataset)

## 2. Installation
```bash
# Clone the repository (replace <REPO_URL> with the actual URL)
git clone <REPO_URL>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Real‑Data Mode (default)
This mode runs the full analysis on the **OpenNeuro ds001734** dataset, which satisfies FR‑001 and FR‑011.

```bash
python code/main.py --mode real
```
* The script downloads the dataset, validates required columns, applies the ≥1 year musician cutoff, performs propensity‑score matching, and proceeds through the full analysis chain.  
* If the dataset cannot be accessed or fails validation, the pipeline aborts with a clear error and falls back to synthetic verification (see below).

### 3.2 Synthetic Verification Mode (optional)
Use this mode only for debugging or to reproduce the pipeline logic without downloading the real data.

```bash
python code/main.py --mode synthetic --n-subjects 100 --seed 42
```
* Generates mock resting‑state fMRI data and behavioral variables, then runs the full analysis.

### 3.3 Individual Stage Execution (optional)
```bash
# Ingest real data (downloads OpenNeuro ds001734)
python code/data/real_ingest.py --output data/raw/

# Preprocess (filter, match, residualize if needed)
python code/data/preprocess.py --input data/raw/subjects.parquet

# Compute connectivity
python code/analysis/connectivity.py

# Run the full statistical suite
python code/analysis/stats.py
python code/analysis/correlation.py
python code/analysis/sensitivity.py
```

### 3.4 Smoke Test (quickstart verification)
```bash
python code/run_quickstart_test.py
```
The test script runs the exact commands from Sections 3.1–3.3, checks that all expected output files exist, and validates them against the JSON‑Schema contracts in `contracts/`. It exits with a success status on success.

## 4. Verify Outputs
```bash
# Run the full test suite
pytest tests/
```
* Unit tests validate individual functions.  
* Integration tests ensure end‑to‑end reproducibility.  
* Contract tests (`jsonschema.validate`) confirm that every output file conforms to its schema.

## 5. Expected Results
* `data/results/results_summary.csv` – the Single Source of Truth for downstream reporting (FR‑010).  
* `data/results/statistical_results.csv` – edge‑wise test statistics, p‑values, q‑values, effect sizes, and CIs.  
* `data/results/nbs_components.json` – NBS component summary.  
* `data/results/sensitivity_analysis.csv` – counts of significant connections at each threshold.  

All files are checksummed (see `data/logs/checksums.txt`) and version‑controlled.
