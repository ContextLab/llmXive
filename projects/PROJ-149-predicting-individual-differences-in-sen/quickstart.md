# Quickstart Guide

## Prerequisites
- Python 3.8+
- Install dependencies: `pip install -r code/requirements.txt`

## Execution Order
Run the following commands in order:

1. **Download Data (T007)**
 ```bash
 python code/01_download_data.py
 ```

2. **Feasibility Check (T008a)**
 ```bash
 python code/00_feasibility_check_join.py
 ```

3. **Preprocess EEG (T010a/b/c)**
 ```bash
 python code/02_preprocess_eeg.py
 ```

4. **Extract Behavioral Metrics (T013)**
 ```bash
 python code/04_extract_behavioral_metrics.py
 ```

5. **Extract Features (T012)**
 ```bash
 python code/03_extract_features.py
 ```

6. **Validate Features (T035a)**
 ```bash
 pytest tests/contract/test_feature_schema.py
 ```

## Output Artifacts
- `data/processed/features_clr.csv`
- `data/interim/behavioral_metrics.csv`
- `data/interim/exclusion_log.csv`

## Notes
- Ensure `config.yaml` is configured with `overlap_seconds` before running T012.
- If any step fails, check the logs in `data/interim/`.