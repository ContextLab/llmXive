# Quickstart Guide: Predicting Crystal Structures from Molecular Fingerprints

## Prerequisites
- Python 3.11+
- Git
- A HuggingFace account (for dataset access)

## Setup
1. Clone the repository.
2. Navigate to the project directory:
 ```bash
 cd projects/PROJ-030-predicting-crystal-structures-from-molec
 ```
3. Create a virtual environment and activate it:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
4. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
5. Set up environment variables (create `.env` from `.env.example`):
 ```bash
 cp code/.env.example code/.env
 # Edit code/.env and add your HF_TOKEN
 ```

## Running the Pipeline
The full end-to-end pipeline (Task T030) verifies SC-004 (6-hour limit) and generates all required artifacts.

**Run the full pipeline:**
```bash
python code/execution/run_full_pipeline.py
```

This script will:
1. Execute the ingestion pipeline (Download -> Parse -> Fingerprint -> Build).
2. Group rare space groups.
3. Perform scaffold splitting.
4. Train models (RF, GB, Ridge).
5. Calculate baselines.
6. Evaluate models.
7. Perform interpretability analysis.
8. Generate the final metrics and reports.
9. Log the total execution time to `data/results/pipeline_timing.log`.

**Expected Output:**
- `data/processed/crystal_dataset.csv`
- `data/processed/grouped_dataset.csv`
- `data/processed/split_indices.json`
- `data/models/*.pkl`
- `data/results/model_metrics.json`
- `data/results/pipeline_timing.log` (Contains the duration and SC-004 status)

## Verification
After running, check `data/results/pipeline_timing.log` to ensure the `status` field is "PASS" (duration < 6 hours).

## Testing
Run unit tests:
```bash
python -m pytest tests/unit/ -v
```

Run integration tests (if available):
```bash
python -m pytest tests/integration/ -v
```
