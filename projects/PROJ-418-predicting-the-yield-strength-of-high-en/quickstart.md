# Quickstart Guide: Predicting HEA Yield Strength

This guide provides a step-by-step walkthrough to execute the full research pipeline for predicting the yield strength of High-Entropy Alloys (HEAs) using compositional descriptors.

## Prerequisites

- Python 3.9+
- `pip` package manager
- Access to the verified dataset URL (configured in `code/utils/config.py` or via environment variables)

## 1. Installation

Clone the repository and install dependencies:

```bash
# Navigate to project root
cd PROJ-418-predicting-the-yield-strength-of-high-en

# Install dependencies
pip install -r requirements.txt
```

## 2. Verify Data Source Configuration

Before running the pipeline, ensure the verified dataset URL is configured. The pipeline will fail immediately if the URL is missing to prevent accidental use of unverified data.

Check `code/utils/config.py` or set the environment variable:
```bash
export HEA_DATASET_URL="your_verified_url_here"
```

## 3. Execute the Full Pipeline

The entire research workflow is orchestrated by the `profiler.py` script, which runs the data acquisition, model training, and statistical validation stages sequentially.

```bash
# Run the full pipeline
python code/profiler.py
```

**What this command does:**
1. **Data Acquisition (US1):** Downloads the HEA dataset, filters for single-phase room-temperature alloys, calculates descriptors (δ, Δχ, VEC, etc.), and saves `data/processed/hea_descriptors.csv`.
2. **Model Training (US2):** Splits data, trains Linear Regression, Random Forest, and Gradient Boosting models with 5-fold CV, and saves `output/metrics.json`.
3. **Statistical Validation (US3):** Performs power analysis, VIF diagnostics, permutation testing, bootstrap resampling, and sensitivity analysis, generating `output/report.md`.

*Note: The pipeline respects the runtime limit of 3 hours for training (T022) and skips heavy statistical tests if sample size is insufficient (T030).*

## 4. Review Results

Upon successful completion, the following artifacts will be available:

- **Processed Data:** `data/processed/hea_descriptors.csv`
- **Data Status:** `output/data_status.json` (includes sample count and power status)
- **Model Metrics:** `output/metrics.json` (R², MAE, RMSE for all models)
- **Statistical Report:** `output/report.md` (includes disclaimers and validation results)
- **Validation Artifacts:**
 - `output/power_analysis.json`
 - `output/vif_results.json`
 - `output/permutation_results.json`
 - `output/bootstrap_results.json`
 - `output/sensitivity_results.json`

## 5. Validate Execution

To ensure the pipeline ran correctly and all expected outputs were generated, run the validation script:

```bash
python code/validate_quickstart.py
```

This script checks for the existence of all required output files and verifies that the report contains mandatory disclaimers.

## Troubleshooting

- **Missing Dataset URL:** If you see `DATA_SOURCE_MISSING`, verify your `code/utils/config.py` or environment variables.
- **Low Power Warning:** If the dataset count is < 50, statistical tests (permutation, bootstrap) will be skipped automatically. Check `output/data_status.json` for the count.
- **Runtime Errors:** Check `output/logs/pipeline.log` for detailed error traces.