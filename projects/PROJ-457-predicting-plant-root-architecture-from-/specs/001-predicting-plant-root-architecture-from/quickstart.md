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

## Configuration Template

A `config.yaml.template` file will be generated in `code/` by the scaffolding step (Task T001). Edit this file to set any optional parameters (e.g., logging level, maximum species to process). The pipeline reads `code/config.yaml` at runtime.

## Running the Full Pipeline

```bash
# Step 1: Ingest datasets (PlantPheno + attempt RootReader & ISRIC; fallback to MergedDataset)
python code/ingestion.py   # Handles download, verification, and initial merge

# Step 2: Preprocess (filter, log‑transform, z‑score, missing‑data handling, covariate imputation)
python code/preprocessing.py

# Step 3: Fit models and evaluate (species‑stratified CV)
python code/modeling.py

# Step 4: Visualize and compile the final report
python code/visualization.py
```

### Expected Outputs
- Clean dataset: `data/processed/merged_dataset.parquet`  
- Metrics JSON: `artifacts/metrics.json` (contains power analysis, merge success rate, all SC booleans)  
- Partial dependence PNGs: `artifacts/reports/plots/*.png` (total ≤ 100 MB)  
- Final PDF report: `artifacts/reports/final_report.pdf` (contains the mandatory associational statement; causal‑language lint passed)  
- Model results JSON: `artifacts/model_results.json` (validated against `contracts/model_results.schema.yaml`)  
- Final report JSON: `artifacts/final_report.json` (validated against `contracts/output.schema.yaml`)  
- Configuration template: `code/config.yaml.template`

## Contract Validation

```bash
pytest tests/contract/test_schemas.py
```

All tests should pass. Failure indicates a mismatch between generated artifacts and the JSON‑Schema contracts.

## Troubleshooting
- **Dataset download failure** – The pipeline will abort and write details to `artifacts/logs/ingestion.log`. Verify that at least one of the verified URLs in the “Dataset Strategy” table is reachable.  
- **MemoryError** – Reduce the number of species processed by adding `--max-species N` to `preprocessing.py`.  
- **Schema test failures** – Ensure the three schema files exist under `contracts/` and that column names/types in `merged_dataset.parquet` match the schema (nullability for `phosphorus`/`nitrogen` is allowed).

---


