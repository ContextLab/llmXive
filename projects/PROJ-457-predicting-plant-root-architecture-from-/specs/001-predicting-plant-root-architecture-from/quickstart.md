# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Availability

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- Internet access (to download datasets)

## Installation

```bash
# 1. Clone the repo (or navigate to the project root if already present)
git clone https://github.com/your-org/plant-root-architecture.git
cd plant-root-architecture

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

```bash
# Step 1: Ingest and (attempt) merge data
python code/ingestion.py

# Step 2: Preprocess (filter, transform, impute)
python code/preprocessing.py

# Step 3: Fit models and evaluate
python code/modeling.py

# Step 4: Visualize and compile the report
python code/visualization.py
```

- **Outputs**  
  - Clean dataset: `data/processed/merged_dataset.parquet`  
  - Metrics JSON: `artifacts/metrics.json`  
  - Plots (PNG): `artifacts/reports/plots/*.png` (total ≤ 100 MB)  
  - Final PDF report: `artifacts/reports/final_report.pdf`

## Contract Validation

```bash
pytest tests/contract/test_schemas.py
```

All tests should pass; failures indicate schema mismatches or missing artifacts.

## Troubleshooting
- **Missing soil data** – The pipeline logs “ISRIC unavailable” and proceeds with root‑only analysis. Check `artifacts/logs/deviation.log` for details.  
- **MemoryError** – Reduce dataset size by limiting to the top 5 species (`python code/preprocessing.py --max-species 5`).  
- **Schema test failures** – Ensure the schema files exist under `contracts/` and that the dataset columns match the schema (nullability for `phosphorus`/`nitrogen` is allowed).

---
