# Quickstart: Gut Microbiome and Cognitive Decline Analysis

## Prerequisites
- Python 3.11+  
- Git  
- ≤ 7 GB free RAM  
- **Data Access**: The AGP and HRS parquet files are publicly available via HuggingFace (no authentication required).  

## Setup

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-189-investigating-the-correlation-between-gu

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Download (automated)

The first script fetches the raw files, verifies their SHA‑256 checksums, and records the hashes in the project state file.

```bash
python code/01_data_ingestion.py
```

- **AGP** → `data/raw/agp.parquet`  
- **HRS** → `data/raw/hrs.parquet`  
- **BMI supplement** → `data/raw/bmi.csv`  

If any checksum mismatches, the script aborts with a clear error.

## Run the Full Analysis

```bash
# 4. Preprocess, merge, and create the analysis dataset
python code/02_preprocessing.py

# 5. Correlation analysis (Spearman + BH FDR)
python code/03_correlation_analysis.py

# 6. Predictive modeling with permutation testing
python code/04_predictive_modeling.py

# 7. Sensitivity analysis over rarefaction depths
python code/05_sensitivity_analysis.py
```

Each script writes its output to `data/processed/` or `data/results/`. The final markdown summary can be inspected with:

```bash
cat data/results/summary.md
```

## Verification

```bash
# Run contract tests – will fail if any output does not match the schema
pytest tests/contract/
```

All tests should pass (`0 passed, 0 failed`). The CI runner enforces this step automatically.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Fatal Coverage Gap** (`overlap < 500`) | Datasets do not share enough IDs. | The pipeline aborts with a clear message. Obtain a linked microbiome‑cognition dataset and update `spec.md`. |
| **MemoryError** | Dataset larger than RAM budget. | Reduce taxa (`MAX_TAXA=200`) in `02_preprocessing.py` or lower permutation count (`PERMUTATIONS=500`) in `04_predictive_modeling.py`. |
| **Merge yields < 500 rows** | Low overlap after age filter. | Verify column names; the pipeline will stop as required by FR‑001. |
| **pytest failures** | Output does not conform to `results.schema.yaml`. | Re‑run the offending script; check logs for schema‑validation errors. |

---
