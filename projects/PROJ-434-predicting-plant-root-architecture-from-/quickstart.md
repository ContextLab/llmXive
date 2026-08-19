# Quickstart Guide: Predicting Plant Root Architecture from Soil Nutrient Profiles

This guide provides step-by-step instructions to set up the environment, run the data ingestion pipeline, train predictive models, and generate the final sensitivity analysis report.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- ~15GB disk space (for temporary raster processing and outputs)
- Internet connection (to download SoilGrids and trait data)

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Directory Structure

Ensure the following directory structure exists. If not, run the setup script:

```bash
python code/setup_directories.py
```

Expected structure:
```
code/
data/
 raw/
 processed/
 logs/
tests/
artifacts/
figures/
```

## 3. Data Ingestion (User Story 1)

This step extracts soil nutrient data (N, P, K, pH) at specific coordinates and merges it with root trait measurements.

Run the full ingestion pipeline:

```bash
python code/ingestion/merge.py
```

**Outputs**:
- `data/processed/merged_dataset.csv`: Unified dataset with soil and trait data.
- `data/processed/excluded_species_summary.csv`: Summary of species filtered out (<10 observations).
- `data/logs/species_exclusions.log`: Detailed log of excluded species.
- `data/logs/record_exclusions.log`: Log of individual rows excluded due to missing soil data or invalid values.

**Validation**:
The pipeline will automatically validate data quality. If the match proportion (valid rows / total rows) is below 0.90, the process will halt and log an error to `data/logs/validation_error.log`.

## 4. Model Training and Validation (User Story 2)

Train Random Forest models to predict root architecture traits (Max Depth, Root Biomass) using soil nutrients and species information.

Run the training script:

```bash
python code/modeling/train.py
```

**Outputs**:
- `artifacts/model_metrics.json`: Cross-validation metrics (R², RMSE) for both Soil-Only and Soil+Species models.
- `artifacts/permutation_distributions.json`: Distribution of R² scores from permutation tests.
- `artifacts/sc002_status.json`: Pass/Fail status for Constitution Principle 002 (Significant Gain from Species).
- `figures/feature_importance.png`: Bar chart of feature importance scores.
- `artifacts/feature_importance.csv`: Raw feature importance scores with p-values.

**Note**: This script performs Stratified 5-Fold CV and Leave-One-Species-Out (LOSO) validation.

## 5. Sensitivity Analysis (User Story 3)

Analyze the robustness of feature importance rankings across different p-value thresholds.

Run the sensitivity analysis script:

```bash
python code/modeling/sensitivity.py
```

**Outputs**:
- `artifacts/sensitivity_report.md`: Final report detailing threshold stability and justification for significance levels.
- `artifacts/feature_importance.csv`: Updated with p-values (if not already present).

## 6. Verification

To verify the entire pipeline end-to-end:

```bash
# Check that all required output files exist
ls data/processed/merged_dataset.csv
ls artifacts/model_metrics.json
ls figures/feature_importance.png
ls artifacts/sensitivity_report.md
```

## Troubleshooting

- **Missing Data**: Ensure your internet connection is active. The pipeline downloads SoilGrids data and trait datasets on the first run.
- **Validation Errors**: If the pipeline halts with a `DataQualityError`, check `data/logs/validation_error.log` for the specific reason (e.g., low match proportion).
- **Memory Issues**: If processing large rasters fails, ensure you have sufficient RAM. The pipeline streams data where possible but may require ~7GB for full processing.

## License

This project is part of the llmXive automated science pipeline. See the repository root for license details.
