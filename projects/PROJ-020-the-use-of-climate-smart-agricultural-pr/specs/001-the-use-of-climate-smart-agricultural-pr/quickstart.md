# Quickstart Guide: Climate-Smart Agricultural Practices Analysis

This guide provides step-by-step instructions to reproduce the full analysis pipeline from raw data download to final visualization and robustness reporting.

## Prerequisites

- Python 3.12.0
- Access to the required data sources (LSMS, FAOSTAT, NASA POWER)
- Sufficient disk space (~15GB for raw data, ~5GB for processed data)
- CPU-only execution environment (no GPU required)

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment and install dependencies:

```bash
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
pip install -r code/requirements.txt
```

## Configuration

Set the target countries and years in `code/utils/config.py` or via environment variables:

- `TARGET_COUNTRIES`: "Kenya,India,Vietnam"
- `TARGET_YEARS`: "2015,2016,2017,2018,2019,2020"

Ensure the configuration file `specs/001-csa-food-security/config.yaml` exists with appropriate settings.

## Execution Pipeline

The full analysis pipeline is executed via the following wrapper scripts. Run them in order:

### Step 1: Data Ingestion

Download raw data from LSMS, FAOSTAT, and NASA POWER, then clean and merge into a single dataset.

```bash
python code/ingestion.py
```

This script:
- Downloads raw data for target countries and years
- Cleans and merges data sources
- Applies stratified sampling if necessary
- Outputs `data/processed/merged_sample.parquet` and `data/processed/ipw_weights.parquet`

### Step 2: Preprocessing (Optional)

If additional preprocessing is required beyond the ingestion step:

```bash
python code/preprocessing.py
```

### Step 3: Statistical Modeling

Fit Fixed-Effects Regression models and perform mediation analysis.

```bash
python code/modeling.py
```

This script:
- Constructs the CSA Index
- Runs Fixed-Effects Regression (OLS with Country Dummies)
- Performs mediation analysis
- Applies multiple hypothesis correction (Bonferroni)
- Outputs `data/processed/model_results.json` and `data/processed/model_diagnostics.json`

### Step 4: Robustness Checks

Perform leave-one-country-out cross-validation and bootstrap resampling.

```bash
python code/analysis/robustness.py --data data/processed/merged_sample.parquet --formula "hdds ~ csa_index + digital_access + finance_access + (digital_access * finance_access)"
```

This script:
- Runs leave-one-country-out cross-validation
- Performs bootstrap resampling (default: 1000 iterations)
- Outputs `data/processed/robustness_results.json` and `data/processed/loco_stability_report.json`

### Step 5: Visualization

Generate scatter plots, coefficient plots, regional maps, and distribution plots.

```bash
python code/viz.py
```

This script:
- Creates scatter plots (CSA Index vs. Food Security)
- Generates coefficient plots with confidence intervals
- Produces regional maps of CSA adoption
- Outputs plots to `output/plots/` and `output/maps/`

### Step 6: Reproducibility Verification

Validate the full pipeline reproducibility by checking checksums, artifact existence, and log consistency.

```bash
python code/verify_reproducibility.py
```

This script:
- Verifies checksums of all output files
- Checks existence of declared deliverables
- Validates log consistency
- Outputs `data/reproducibility_report.json`

## Expected Deliverables

After running the full pipeline, the following files should exist:

- `data/processed/merged_sample.parquet` - Cleaned, merged, and sampled dataset
- `data/processed/ipw_weights.parquet` - Inverse probability weighting factors
- `data/processed/model_results.json` - Model coefficients, p-values, and diagnostics
- `data/processed/robustness_results.json` - Robustness check results
- `data/processed/loco_stability_report.json` - Leave-one-country-out stability metrics
- `output/plots/scatter_plot.png` - Scatter plot of CSA Index vs. Food Security
- `output/plots/coefficients_plot.png` - Coefficient plot with confidence intervals
- `output/maps/csa_adoption_map.png` - Regional map of CSA adoption
- `data/reproducibility_report.json` - Reproducibility verification report

## Troubleshooting

### Missing Data

If data download fails, ensure network connectivity and check that the target countries and years are valid. The script will log errors and skip unavailable datasets.

### Memory Issues

If the pipeline runs out of memory, reduce the sample size in `code/utils/config.py` by adjusting `MAX_RAM_GB` or enabling stratified sampling with a smaller target.

### Model Convergence

If the model fails to converge, check for collinearity using the VIF diagnostics in `data/processed/model_diagnostics.json`. Remove or combine highly correlated predictors if necessary.

### CLI Argument Errors

Ensure all required arguments are provided when running scripts. For example, `robustness.py` requires `--data` to specify the input dataset.

## Notes

- All findings are framed as **associational** relationships, not causal effects.
- The Fixed-Effects Regression approach is used instead of Mixed-Effects due to the small number of countries (N=3). [UNRESOLVED-CLAIM: c_8f19ca86 — status=not_enough_info]
- The CSA Index includes digital and finance access as per the specification, with equal weighting (0.2 each) as the default. [UNRESOLVED-CLAIM: c_ad11e13c — status=not_enough_info]
- Bonferroni correction is applied for multiple hypothesis testing.

For more details, refer to the design documents in `specs/001-csa-food-security/`.