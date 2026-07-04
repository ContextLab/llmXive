# Quickstart Guide: Reproducibility Validation

This guide validates the end-to-end reproducibility of the research pipeline.

## Prerequisites

- Python 3.11+
- All dependencies installed: `pip install -r code/requirements.txt`

## Execution

To run the full validation pipeline:

```bash
cd code/
python validate_quickstart.py
```

## Expected Outputs

The pipeline should generate the following files in their respective directories:

- `data/raw/survey_data.csv`: Raw survey data (synthetic or downloaded)
- `data/processed/cleaned_data.csv`: Cleaned dataset with no missing values
- `data/processed/engineered_data.csv`: Dataset with derived features
- `results/model_results.yaml`: Logistic regression and mediation results
- `results/validity_metrics.yaml`: Reliability and validity statistics
- `modeling_log.yaml`: Comprehensive log of modeling decisions
- `results/report.pdf`: Final research report
- `figures/roc_curve.png`: ROC curve visualization

## Validation Steps

1. **Data Generation**: Creates synthetic data if real data is unavailable
2. **Data Download**: Attempts to fetch real data from World Bank/FAO APIs
3. **Data Cleaning**: Handles missing values and normalizes categorical codes
4. **Feature Engineering**: Creates engagement scores and adoption indicators
5. **Model Analysis**: Fits logistic regression, calculates VIF, performs mediation analysis
6. **Report Generation**: Produces PDF report with all results
7. **Finalization**: Saves summary and updates modeling log

## Troubleshooting

- If data download fails, the pipeline automatically falls back to synthetic data
- Check `modeling_log.yaml` for detailed error messages
- Ensure all required columns exist in the source data
- Verify that `config.py` paths are correctly configured