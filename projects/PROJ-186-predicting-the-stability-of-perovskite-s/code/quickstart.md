# Quickstart Guide

This guide outlines the steps to run the full pipeline end-to-end.
Ensure you are in the project root directory.

## Prerequisites
- Python 3.11+
- Virtual environment activated (`.venv/bin/activate`)
- Dependencies installed (`pip install -r requirements.txt`)

## Execution Steps

1. **Data Ingestion & Descriptor Generation**
 ```bash
 python code/data/download.py
 python code/data/descriptors.py
 ```

2. **Data Preprocessing**
 ```bash
 python code/data/preprocess.py
 ```
 *This step generates `data/processed/features.csv`.*

3. **Model Training**
 ```bash
 python code/models/train.py
 ```

4. **Virtual Screening**
 ```bash
 python code/data/generate_library.py
 python code/models/predict.py
 python code/models/screening_full.py
 python code/models/generate_candidates_report.py
 ```

5. **Visualization**
 ```bash
 python code/viz/plot.py
 ```

6. **Validation**
 ```bash
 python code/quickstart_validate.py
 ```

## Expected Artifacts
- `data/processed/features.csv`
- `results/model.pkl`
- `results/metrics.json`
- `results/screening_candidates.md`
- `figures/predicted-vs-true.png`
- `figures/feature-importance.png`

## Troubleshooting
- If `ModuleNotFoundError` occurs, ensure dependencies are installed.
- If `FileNotFoundError` occurs for `raw_features.csv`, ensure `download.py` and `descriptors.py` ran successfully.
- Check `logs/pipeline.log` for detailed error messages and exclusion reasons.
