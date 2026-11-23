# Quick Start Guide: Assessing Dataset Imbalance Effects on Materials Property Predictions

This guide provides step-by-step instructions to execute the full pipeline, from data ingestion to final analysis, for project **PROJ-756**.

## Prerequisites

1. **Python Version**: Ensure you have Python 3.11 installed.
2. **Dependencies**: Install all required packages listed in `code/requirements.txt`.

```bash
cd code
pip install -r requirements.txt
cd..
```

3. **API Keys** (Optional):
 - **Materials Project**: Set the environment variable `MP_API_KEY` if you intend to include Materials Project data. If unset or invalid, the pipeline will automatically fallback to OQMD/AFLOW data only.
 - **OQMD**: No key required for the public REST API endpoints used.

## Directory Structure

The project follows this structure:

```text
.
├── code/ # Python source modules
├── data/ # Raw and processed data
│ ├── raw/ # Downloaded parquet files (oqmd.parquet, mp.parquet, etc.)
│ └── processed/ # Computed descriptors and derived datasets
├── results/ # Analysis outputs (reports, plots, logs)
├── logs/ # API error logs and execution traces
├── contracts/ # Schema definitions for validation
├── docs/ # Documentation (this file)
└── README.md # Project overview
```

## Execution Steps

### Step 1: Initialize Project Structure (Optional)
If the directory structure does not exist, run the setup script:

```bash
python code/main.py --setup-only
```

*Note: If T001 and T001b are complete, this is typically handled automatically.*

### Step 2: Run the Full Pipeline
Execute the entire pipeline from data ingestion to SHAP analysis.

**Standard Run (Includes Materials Project if available):**
```bash
python code/main.py --full-pipeline --include-mp --streaming
```

**Fallback Run (OQMD/AFLOW only, if MP is unavailable):**
```bash
python code/main.py --full-pipeline --fallback-mode --streaming
```

**Arguments:**
- `--full-pipeline`: Runs ingestion, descriptors, imbalance analysis, training, resampling, evaluation, and SHAP analysis.
- `--include-mp`: Attempts to fetch Materials Project data. If the API is unavailable, it logs a warning and proceeds with available data.
- `--fallback-mode`: Explicitly skips MP data fetch and uses only OQMD/AFLOW.
- `--streaming`: Processes large datasets in chunks to stay within memory limits (required for full dataset runs).

### Step 3: Monitor Execution
The pipeline will output progress to the console. Detailed logs are written to:
- `logs/api_errors.log`: JSON lines of any API fetch errors.
- `results/validation_log_mp.txt` or `results/validation_log_fallback.txt`: Final execution summary including runtime and exit code.

## Expected Output Files

Upon successful completion, the following artifacts will be generated in the `results/` and `data/` directories:

### Data Artifacts
- `data/raw/oqmd.parquet`: Raw OQMD dataset.
- `data/raw/mp.parquet` (if available): Raw Materials Project dataset.
- `data/processed/descriptors.parquet`: Computed Magpie compositional descriptors.
- `data/processed/descriptor_schema.json`: Schema definition for descriptors (required for T036).
- `data/synthetic/ground_truth.parquet`: Synthetic dataset with known physics-inspired weights (T036).

### Analysis Reports
- `results/target_imbalance_scores.csv`: Gini coefficients for target properties (T008a).
- `results/compositional_imbalance_score.csv`: Gini coefficients for cluster assignments (T008b).
- `results/baseline_report.csv`: Baseline model performance (MAE, RMSE, R²) on skewed data (T016).
- `results/performance_degradation.csv`: Performance difference on minority subsets (T027).
- `results/statistical_test_results.csv`: Paired t-test/Wilcoxon results (T029).
- `results/correlation_analysis.csv`: Correlation between imbalance scores and performance degradation (T030, T031).
- `results/comparison_report.csv`: Comprehensive comparison of skewed vs. balanced models (T032).
- `results/minority_threshold_justification.md`: Documentation of minority subset thresholds (T026).

### SHAP Analysis Outputs
- `results/shap_analysis/shap_skewed.npy`: SHAP values for skewed models.
- `results/shap_analysis/shap_balanced.npy`: SHAP values for balanced models.
- `results/shap_analysis/rank_shift.csv`: Feature rank shifts between models (T038).
- `results/shap_analysis/shap_validation.json`: Validation summary against synthetic ground truth (T039).
- `results/shap_analysis/rank_shift_plot.png`: Visualization of rank shifts (T040).
- `results/shap_analysis/feature_importance_bar.png`: Feature importance comparison (T040).
- `results/shap_analysis/shap_report.md`: Final SHAP analysis report (T041).

### Logs and Validation
- `results/resampling_log.json`: Log of resampling events, synthetic data percentages, and CV values (T051).
- `results/power_analysis.json`: Minimum seed count required for statistical power (T028).
- `logs/api_errors.log`: API error trace (if any).

## Troubleshooting

- **Data Fetch Errors**: If the pipeline fails to download data, check `logs/api_errors.log` for specific error codes. The pipeline is designed to "fail loudly" on persistent OQMD/AFLOW errors (T049).
- **Missing MP Data**: If `MP_API_KEY` is missing, the pipeline will log a warning and proceed with OQMD/AFLOW only. This is expected behavior in fallback mode.
- **Memory Issues**: Ensure the `--streaming` flag is used for full dataset runs. If memory errors persist, reduce the dataset size by filtering properties or samples in the configuration (not yet exposed via CLI).
- **Validation Errors**: If `ValidationException` is raised, check `results/resampling_log.json` to see if the Combined CV exceeded 0.30 or synthetic data exceeded 30% (T023, T051).

## Next Steps

After generating the results:
1. Review `results/shap_analysis/shap_report.md` for feature importance insights.
2. Analyze `results/correlation_analysis.csv` to understand the relationship between dataset imbalance and model performance.
3. Validate the pipeline outputs against the schemas in `contracts/`.

For detailed API documentation, refer to the docstrings in the `code/` modules.