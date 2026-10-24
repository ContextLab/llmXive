# Quickstart: Predicting Molecular Halide Binding Affinities

## Prerequisites
- Python 3.11 or newer  
- `git` and internet access (for dataset download)  
- Adequate RAM (GitHub Actions runner provides this automatically)

## Installation
```bash
# Clone the repository (or navigate to the project directory)
cd projects/PROJ-446-predicting-molecular-halide-binding-affi

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline
Each step depends on the previous one. All scripts write to `data/processed/`. All ingestion steps handle expected network/scrape failures defensively and log warnings rather than exiting non‑zero.

### Step 1: Data Ingestion
```bash
python code/01_data_ingestion.py
```
*Creates* `data/processed/halide_binding_data.csv` and `data/processed/independent_eval.csv`.  
If real NIST/PubChem data are insufficient, the script automatically falls back to simulated data (FR‑011) and also creates the independent evaluation set. In Simulated mode each host carries a single halide measurement.

### Step 2: Feature Engineering
```bash
python code/02_feature_engineering.py
```
Adds RDKit descriptors, ECFP‑like fingerprints, and standardized columns to the CSV.  
The unit test `tests/test_feature_engineering.py` (located in the top‑level `tests/` directory) imports the module via `sys.path.append('code')` and verifies that all required descriptor columns are present and correctly typed.

### Step 3: Model Training
```bash
python code/03_model_training.py
```
Trains Random Forest and Gradient Boosting models with host‑molecule `RepeatedGroupKFold`.  
Outputs `data/processed/model_runs.json`.

### Step 4: Model Output Schema Validation
```bash
python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml
```
Ensures the model output conforms to the contract (Task T009).

### Step 5: Feature Analysis
```bash
python code/04_feature_analysis.py
```
Performs bootstrap stability analysis and the physical plausibility check on the top feature (`charge_density`). In Simulated mode the check result is annotated “trivially satisfied by construction (simulated data)”.  
Outputs `data/processed/feature_analysis.json`.

### Step 6: Partial Dependence Plots
```bash
python code/06_partial_dependence.py
```
Generates PDPs for the two most stable features and saves PNGs under `data/processed/figures/`.

### Step 7: Statistical Reporting
```bash
python code/05_statistical_reporting.py
```
Generates bootstrap confidence intervals, under‑power warnings, and the final `report.md`.  
Also creates a machine‑readable `output_summary.json` that conforms to `contracts/output.schema.yaml`.

### Step 8: Independent Evaluation on Hold‑Out Set
```bash
python code/07_independent_evaluation.py
```
Runs **after** statistical reporting. Loads `independent_eval.csv`, makes predictions with the trained models, and **appends** an R²/RMSE section for this **feature‑independent** target set to the existing `report.md` (it does not regenerate the report).

### Step 9: Citation Verification
The Reference‑Validator Agent automatically checks all URLs listed in `research.md`. No manual command is required; the CI pipeline runs this step after the statistical reporting stage.

## Verification Checklist
1. `data/processed/halide_binding_data.csv` exists and validates against `contracts/dataset.schema.yaml`.  
2. `data/processed/independent_eval.csv` exists and validates against `contracts/dataset.schema.yaml`.  
3. `data/processed/model_runs.json` validates against `contracts/model_output.schema.yaml`.  
4. `data/processed/feature_analysis.json` contains `feature_name`, `cv`, and `is_stable`.  
5. `data/processed/figures/` contains at least two PNGs (`pdp_*.png`).  
6. `data/processed/report.md` includes:
   - Dataset summary (real vs simulated flag).  
   - Per‑halide performance tables **or** abort notice.  
   - Feature‑stability ranking.  
   - Partial dependence plots.  
   - Associational disclaimer.  
   - Appended independent‑evaluation metrics (feature‑independent target).  
7. `data/processed/output_summary.json` conforms to `contracts/output.schema.yaml`.

## Troubleshooting
- **MemoryError**: Reduce the number of sampled SMILES (edit `MAX_HOSTS` in `01_data_ingestion.py`).  
- **No data found**: Expected when the scrape fails; the script logs a warning and proceeds with simulated data (exit code 0).  
- **RDKit import errors**: Install via `conda` (`conda install -c rdkit rdkit`) or use the `rdkit-pypi` wheel.  
