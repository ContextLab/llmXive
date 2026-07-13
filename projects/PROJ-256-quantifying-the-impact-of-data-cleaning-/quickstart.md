# Quickstart Guide for Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites

- Python 3.11+
- pip and virtual environment

## Setup

1. Clone the repository
2. Create and activate virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\\.venv\\Scripts\\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Run the Full Pipeline

Execute the main pipeline script:
```bash
python code/main.py
```

This will:
1. Ensure dataset availability
2. Run baseline analysis (T012)
3. Record baseline metrics (T013)
4. Apply cleaning strategies (T017-T022)
5. Re-analyze cleaned variants (T023)
6. Run comparison analysis (T027)
7. Perform sensitivity analysis (T029-T031)
8. Estimate FPR via permutation tests (T032)
9. Run threshold sweep (T033)
10. Generate visualizations (T034-T035)
11. Generate reports (T036-T041)
12. Verify checksums (T048)

## Individual Task Execution

You can also run individual tasks:

```bash
# Download and prepare data
python code/t011_ensure_data.py

# Run baseline analysis
python code/t012_run_baseline_analysis.py

# Record baseline metrics
python code/t013_record_baseline_metrics.py

# Apply cleaning strategies
python code/t022_save_cleaned_datasets.py

# Re-analyze cleaned variants
python code/t023_reanalyze_cleaned_variants.py

# Run comparison
python code/t027_run_comparison.py

# Permutation null FPR estimation (T032)
python code/t032_permutation_null_fpr.py

# Generate forest plot
python code/t034_generate_forest_plot.py

# Generate CI heatmap
python code/t035_generate_ci_heatmap.py

# Generate final report
python code/t041_generate_final_report.py
```

## Expected Outputs

After running the full pipeline, you should see:

- `data/processed/baseline_metrics.json` - Baseline statistical metrics
- `data/processed/cleaned_metrics.json` - Metrics after cleaning
- `data/processed/null_fpr_metrics.json` - False positive rate estimates from permutation tests
- `figures/` - Visualization outputs (forest plot, heatmap)
- `reports/` - Final analysis reports

## Validation

To validate the pipeline execution:
```bash
python code/run_quickstart_validation.py
```

This script checks that all required artifacts are present and valid.