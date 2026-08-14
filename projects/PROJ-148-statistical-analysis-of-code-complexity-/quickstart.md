# Quickstart Guide

This guide provides the commands to run the full statistical analysis pipeline for code complexity and bug prediction.

## Prerequisites

- Python 3.11+
- Installed dependencies (see `requirements.txt`)

## Setup

1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Pipeline

The data pipeline consists of several steps. Ensure you have the necessary data sources available.

### 1. Download Projects
Download Java projects from GHTorrent.
```bash
python code/data/download_gh.py --output-dir data/raw --project-count 10
```

### 2. Extract Commits
Extract commit metadata from the downloaded archives.
```bash
python code/data/extract_commits.py --input-dir data/raw --output data/commits.csv
```

### 3. Extract Metrics
Compute complexity metrics using lizard.
```bash
python code/data/extract_metrics.py --input data/raw --output data/metrics.csv
```

### 4. Label Bug Fixes
Label code units as bug-fix or non-bug-fix.
```bash
python code/data/label_bug_fixes.py --input data/commits.csv --metrics data/metrics.csv --output data/labeled_data.csv
```

### 5. Validate Bug Labels
Validate the reliability of bug labels.
```bash
python code/data/validate_bug_labels.py --input data/labeled_data.csv
```

### 6. Preprocess Data
Clean and preprocess the data.
```bash
python code/data/preprocess.py --input data/labeled_data.csv --output data/preprocessed_data.csv
```

### 7. Split Dataset
Perform a project-level stratified train/test split.
```bash
python code/data/split_dataset.py --input data/preprocessed_data.csv --output-dir data/splits
```

## Modeling Pipeline

### 1. Train Models
Train the primary (L1 Logistic Regression) and alternative (Random Forest) models.
```bash
python code/modeling/train.py --data-dir data/splits --model-dir data/model
```

### 2. Evaluate Models
Evaluate model performance on the test set.
```bash
python code/modeling/evaluate.py --data-dir data/splits --model-path data/model/primary.pkl --output-dir data/evaluation
```

### 3. Correct P-values
Apply Benjamini-Hochberg correction to p-values.
```bash
python code/modeling/correct_pvalues.py --input data/evaluation/pvalues.csv --output data/model/corrected_pvalues.csv
```

### 4. Generate Partial Dependence Plots
Generate PDPs for the top 3 metrics.
```bash
python code/modeling/pdp.py --data-dir data/splits --model-path data/model/primary.pkl --output-dir data/figures
```

### 5. Generate Thresholds
Derive practical threshold values for bug probability.
```bash
python code/modeling/generate_thresholds.py --input data/evaluation/predictions.csv --output data/model/thresholds.csv
```

### 6. Generate Report
Assemble the final research report.
```bash
python code/report/generate_report.py --metrics data/evaluation/metrics.json --importance data/model/importance.json --output reports/final_report.html
```

## Running the Full Pipeline

To run the entire pipeline from data download to report generation, execute the following commands in order:

```bash
# Data Pipeline
python code/data/download_gh.py --output-dir data/raw --project-count 10
python code/data/extract_commits.py --input-dir data/raw --output data/commits.csv
python code/data/extract_metrics.py --input data/raw --output data/metrics.csv
python code/data/label_bug_fixes.py --input data/commits.csv --metrics data/metrics.csv --output data/labeled_data.csv
python code/data/validate_bug_labels.py --input data/labeled_data.csv
python code/data/preprocess.py --input data/labeled_data.csv --output data/preprocessed_data.csv
python code/data/split_dataset.py --input data/preprocessed_data.csv --output-dir data/splits

# Modeling Pipeline
python code/modeling/train.py --data-dir data/splits --model-dir data/model
python code/modeling/evaluate.py --data-dir data/splits --model-path data/model/primary.pkl --output-dir data/evaluation
python code/modeling/correct_pvalues.py --input data/evaluation/pvalues.csv --output data/model/corrected_pvalues.csv
python code/modeling/pdp.py --data-dir data/splits --model-path data/model/primary.pkl --output-dir data/figures
python code/modeling/generate_thresholds.py --input data/evaluation/predictions.csv --output data/model/thresholds.csv
python code/report/generate_report.py --metrics data/evaluation/metrics.json --importance data/model/importance.json --output reports/final_report.html
```

## Notes

- Ensure all input directories and files exist before running the corresponding scripts.
- The pipeline expects specific directory structures and file names as defined in the script arguments.
- For detailed usage of each script, use the `--help` flag.
- The `--seed` argument can be used to ensure reproducibility across runs.