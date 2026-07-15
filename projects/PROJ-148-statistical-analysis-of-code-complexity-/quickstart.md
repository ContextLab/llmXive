# Quickstart Guide

This guide provides the commands to run the full analysis pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Run the Pipeline

The pipeline consists of several stages. Execute them in order:

1. **Data Download and Extraction**
 ```bash
 python code/data/download_gh.py --output data/raw
 python code/data/extract_commits.py --input data/raw --output data/commits
 python code/data/extract_metrics.py --input data/commits --output data/metrics.csv
 python code/data/label_bug_fixes.py --input data/metrics.csv --output data/labeled.csv
 python code/data/validate_bug_labels.py --input data/labeled.csv
 python code/data/preprocess.py --input data/labeled.csv --output data/preprocessed.csv --ground-truth data/labeled.csv --min-precision 0.85
 python code/data/split_dataset.py --input data/preprocessed.csv --output data/split
 ```

2. **Modeling and Evaluation**
 ```bash
 python code/modeling/train.py --data-dir data/split --model-dir data/model --seed 42
 python code/modeling/correct_pvalues.py --input data/model/raw_pvalues.csv --output data/model/corrected_pvalues.csv
 python code/modeling/pdp.py --model-dir data/model --output-dir figures/pdp
 python code/report/generate_report.py --model-dir data/model --output reports/analysis_report.html
 ```

3. **Testing and Validation**
 ```bash
 pytest tests/
 ```

## Output Artifacts

- `data/model/corrected_pvalues.csv`: Benjamini-Hochberg corrected p-values.
- `data/model/thresholds.csv`: Practical threshold values for developers.
- `figures/pdp/`: Partial dependence plots for top 3 metrics.
- `reports/analysis_report.html`: Final research report.

## Notes

- Ensure all data files are present in the `data/` directory before running the modeling stage.
- The `correct_pvalues.py` script must be run after `train.py` to generate the corrected p-values file.
- If any step fails, check the logs for detailed error messages.