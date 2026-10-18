# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Availability

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- Internet access (to download datasets)

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd plant-root-architecture

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

```bash
# Step 1: Ingest root phenotypes and soil nutrients (separate downloads)
python code/ingestion.py   # Handles PlantPheno and open soil dataset; falls back to merged dataset if needed

# Step 2: Preprocess (filter, log‑transform, z‑score, missing‑data handling, covariate imputation)
python code/preprocessing.py

# Step 3: Fit models and evaluate (species‑stratified CV)
python code/modeling.py

# Step 4: Visualize and compile the final report
python code/visualization.py
```

### Expected Outputs
- Clean dataset: `data/processed/merged_dataset.parquet`  
- Metrics JSON: `artifacts/metrics.json` (includes power analysis, merge success rate, and all SC booleans)  
- Partial dependence PNGs: `artifacts/reports/plots/*.png` (total ≤ 100 MB)  
- Final PDF report: `artifacts/reports/final_report.pdf` (contains the mandatory associational statement; causal wording checked)  

## Contract Validation

```bash
pytest tests/contract/test_schemas.py
```

All tests should pass. Failure indicates schema mismatches or missing artifacts.

## Troubleshooting
- **RootPheno or soil dataset unavailable** – The pipeline will abort with a clear error logged in `artifacts/logs/fallback.log`. Ensure at least one of the verified URLs is reachable.  
- **MemoryError** – Reduce dataset size by limiting to the top 5 species: `python code/preprocessing.py --max-species 5`.  
- **Schema test failures** – Ensure the three schema files exist under `contracts/` and that the dataset columns match the schema (nullability for `phosphorus`/`nitrogen` is allowed).  

---



