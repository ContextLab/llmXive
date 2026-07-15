# Quickstart Guide

This guide describes how to run the full research pipeline for the Statistical Analysis of Code Complexity project.

## Prerequisites

- Python 3.11+
- Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Preparation

1. **Download Data**: Fetch Java projects from GHTorrent.
 ```bash
 python code/data/download_gh.py --output data/raw/gh_projects
 ```
2. **Extract Metrics**: Compute complexity metrics using Lizard.
 ```bash
 python code/data/extract_metrics.py --input data/raw/gh_projects --output data/processed/metrics.csv
 ```
3. **Label Bug Fixes**: Identify bug-fix commits.
 ```bash
 python code/data/label_bug_fixes.py --input data/processed/metrics.csv --output data/processed/labeled_metrics.csv
 ```
4. **Preprocess**: Clean and transform data.
 ```bash
 python code/data/preprocess.py --input data/processed/labeled_metrics.csv --output data/processed/preprocessed_data.csv
 ```
5. **Split Dataset**: Create train/test splits.
 ```bash
 python code/data/split_dataset.py --input data/processed/preprocessed_data.csv --output data/splits/
 ```

## Modeling & Evaluation

6. **Train Models**: Run the full training pipeline (Primary & Alternative models, evaluation, p-value correction, thresholds).
 ```bash
 python code/modeling/train.py \
 --train data/splits/train.csv \
 --test data/splits/test.csv \
 --output data/model/
 ```

## Reporting

7. **Generate Report**: Create the final research report.
 ```bash
 python code/report/generate_report.py --input data/model/ --output reports/final_report.html
 ```

## Testing

Run the full test suite:
```bash
python code/run_tests.py
```

## Notes

- All paths are relative to the project root.
- Ensure `data/` directory exists or is created by the scripts.
- The `train.py` script orchestrates the modeling phase and produces `data/model/corrected_pvalues.csv` and `data/model/thresholds.csv`.
