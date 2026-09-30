# Quickstart Guide: Neural Correlates of Predictive Error Signals

This guide describes how to run the full pipeline for project **PROJ-500-neural-correlates-of-predictive-error-si**.

## Prerequisites

- Python 3.11+
- `pip` and `virtualenv`

## Setup

1. **Clone and Setup Environment**
 ```bash
 cd code
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Initialize Project Structure (if not already done)**
 ```bash
 python scripts/create_project_structure.py
 python scripts/init_git.py
 python scripts/generate_project_state.py
 ```

## Running the Pipeline

The pipeline consists of sequential stages. Run them in order to generate the final `aligned_data.csv`.

### Step 1: Data Ingestion (T014)
Downloads and streams raw EEG data.
```bash
python src/data/ingest.py
```
*Output*: `data/interim_raw_chunks/`, `data/streaming_log.json`

### Step 2: Preprocessing (T015, T016, T017)
Filters, applies ICA, and epochs data.
```bash
python src/data/preprocess.py
```
*Output*: `data/epochs/`, `data/power_report.csv`

### Step 3: Alignment (T020, T021, T022, T022b)
Calculates MMN, bins accuracy, and performs lagged alignment.
```bash
python src/data/align.py
```
*Output*: `data/accuracy_blocks.csv`, `data/interim_lagged_mmns.csv`

### Step 4: Finalization (T023, T024)
Filters data based on power analysis and merges into the final aligned dataset.
```bash
python src/data/finalize.py
```
*Output*: `data/aligned_data.csv`

### Step 5: Modeling (T027, T028, T029)
Fits the LME model and runs permutation tests.
```bash
python src/analysis/model.py
```
*Output*: `analysis/results/model_output.json`, `analysis/results/permutation_stability_log.json`

## Verification

Verify the final output exists and matches the schema:
```bash
python -m pytest tests/contract/test_schemas.py -v
```

## Notes

- Ensure `DATA_DIR` environment variable is set if not using the default `data/` folder.
- For large datasets, ensure sufficient disk space and RAM (see `requirements.txt` for memory profiling tools).
- The `ANALYSIS_MODE` environment variable can be set to `error_signal` or `stimulus_driven` to control filtering logic in T023/T024.