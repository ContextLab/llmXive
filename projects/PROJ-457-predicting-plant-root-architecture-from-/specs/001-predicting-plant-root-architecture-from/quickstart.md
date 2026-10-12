# Quickstart: Predicting Plant Root Architecture from Soil Nutrient Availability

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- Internet access (to download datasets)

## Installation

```bash
# 1. Clone the repository
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
# Step 1: Ingest data (attempt ISRIC merge; fallback to merged dataset)
python code/ingestion.py

# Step 2: Preprocess (filter, log‑transform, z‑score, missing‑data handling)
python code/preprocessing.py

# Step 3: Fit models and evaluate (species‑stratified CV)
python code/modeling.py

# Step 4: Visualize and compile the final report
python code/visualization.py
```

### Expected Outputs
- Clean dataset: `data/processed/merged_dataset.parquet`  
- Metrics JSON: `artifacts/metrics.json` (includes power analysis and SC‑001 value)  
- Partial dependence PNGs: `artifacts/reports/plots/*.png` (total ≤ 100 MB)  
- Final PDF report: `artifacts/reports/final_report.pdf` (contains associational statement; causal wording checked)

## Contract Validation

```bash
pytest tests/contract/test_schemas.py
```

All tests should pass. Failures indicate schema mismatches or missing artifacts.

## Troubleshooting
- **ISRIC unavailable** – The pipeline logs “ISRIC unavailable” and proceeds with the first verified merged dataset. See `artifacts/logs/deviation.log` for details.  
- **MemoryError** – Reduce dataset size by limiting to the top 5 species: `python code/preprocessing.py --max-species 5`.  
- **Schema test failures** – Ensure the three schema files exist under `contracts/` and that the dataset columns match the schema (nullability for `phosphorus`/`nitrogen` is allowed).

---

