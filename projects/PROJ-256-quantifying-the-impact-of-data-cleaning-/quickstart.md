# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Setup
```bash
pip install -r requirements.txt
```

## Run the Pipeline
The pipeline executes the following steps in order:

1. Ensure data exists
2. Run baseline analysis
3. Save cleaned datasets
4. Re-analyze cleaned variants
5. Run comparison
6. **Run Permutation Null FPR Estimation (T032)**
7. Generate visualizations and reports

```bash
python code/t011_ensure_data.py
python code/t012_run_baseline_analysis.py
python code/t022_save_cleaned_datasets.py
python code/t023_reanalyze_cleaned_variants.py
python code/t027_run_comparison.py
python code/t032_permutation_null_fpr.py
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
python code/t041_generate_final_report.py
```

## Validate Artifacts
```bash
python code/run_quickstart_validation.py
```