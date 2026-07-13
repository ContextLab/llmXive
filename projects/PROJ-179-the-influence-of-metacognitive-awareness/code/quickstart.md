# Quickstart Guide: The Influence of Metacognitive Awareness on Reality Testing

This guide provides instructions to run the full analysis pipeline end-to-end.

## Prerequisites

1. Python 3.8+
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Execute the following commands in order:

```bash
# Phase 2: Data Download and Validation
python code/data/download.py
python code/data/validate_data.py

# Phase 3: Preprocessing
python code/data/preprocess.py

# Phase 4: Analysis (Primary Correlation)
python code/src/analysis/correlation.py

# Phase 5: Bootstrap Analysis
python code/src/analysis/bootstrap.py

# Phase 6: Regression Analysis
python code/src/analysis/regression.py

# Phase 7: Robustness Analysis
python code/src/analysis/robustness.py

# Phase 8: Report Generation
python code/src/report/generate.py
```

## Expected Outputs

After successful execution, the following files will be generated:

- `data/derived/trial_data.csv` - Preprocessed trial data
- `data/validation_report.json` - Data validation report
- `data/results/bootstrap_config.json` - Bootstrap configuration
- `data/results/primary_analysis.json` - Primary correlation results
- `data/results/regression_analysis.json` - Regression analysis results
- `data/results/robustness_analysis.json` - Modality-specific results

## Troubleshooting

If you encounter errors:
1. Ensure all prerequisites are installed
2. Check that the dataset is available (see `data/validate_data_availability.py`)
3. Verify file paths are correct relative to project root
4. Check logs for specific error messages
