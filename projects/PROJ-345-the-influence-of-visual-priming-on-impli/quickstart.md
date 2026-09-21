# Quickstart Guide for PROJ-345

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu
 ```

3. Verify environment:
 ```bash
 python scripts/verify_env.sh
 ```

## Data Setup

The pipeline downloads data from OSF/HF automatically. No manual download required unless specified.

## Run Pipeline

Execute the full pipeline in order:

```bash
# 1. Setup Directories and State
python code/run_setup.py
python code/run_state_init.py

# 2. Ingest Data (T013)
python code/data/ingest.py

# 3. Preprocess & Derive Metrics (T014, T015a, T018a)
python code/data/preprocess.py
python code/data/calculate_ingest_metrics.py

# 4. Linkage Verification (T016)
python code/data/linkage.py

# 5. Generate Linked Trials (T017) - THIS TASK
python code/data/generate_linked_trials.py

# 6. Modeling (T021-T028)
python code/models/lmm.py
python code/models/metrics.py

# 7. Reporting (T032-T037)
python code/viz/plots.py
python code/reports/generate_report.py

# 8. Validation
python code/validation/validate_quickstart.py
```

## Verification

After running, check `data/processed/linked_trials.csv` exists and contains the expected columns.
Check `reports/final_report.pdf` for the generated report.