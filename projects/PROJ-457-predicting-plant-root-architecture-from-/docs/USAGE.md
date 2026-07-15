# Usage Guide: Predicting Plant Root Architecture from Soil Nutrient Availability

## Overview

This guide provides detailed instructions for using the root architecture prediction pipeline.

## Configuration

### Environment Setup

Create a `config.yaml` file based on `code/config.yaml.template`:

```yaml
DATA_PATH:./data
SEED: 42
LOG_LEVEL: INFO
OUTPUT_PATH:./artifacts
```

### Logging

The pipeline uses Python's logging module. Logs are written to:
- Console (stdout)
- File: `artifacts/logs/pipeline.log`

Log levels:
- DEBUG: Detailed diagnostic information
- INFO: General progress information
- WARNING: Exclusion counts, missing data warnings
- ERROR: Critical failures

## Step-by-Step Execution

### 1. Data Ingestion

Run the data ingestion pipeline:

```bash
python code/data_ingestion.py
```

This will:
- Download root phenotype data from RootReader/PlantPheno
- Fetch ISRIC soil nutrient data
- Interpolate missing nutrients using KNN
- Filter out species with n<20 and experimental data
- Merge datasets
- Save to `data/processed/merged_dataset.csv`

**Output**:
- `data/processed/merged_dataset.csv`: Cleaned, merged dataset
- `artifacts/logs/exclusion_log.json`: Exclusion counts

### 2. Preprocessing

Run preprocessing:

```bash
python code/preprocessing.py
```

This will:
- Apply log-transformation to root metrics
- Apply z-score normalization to nutrients
- Perform KNN imputation (k=5)
- Save processed data

**Output**:
- `data/processed/processed_dataset.csv`: Preprocessed dataset

### 3. Model Training

Run model training:

```bash
python code/modeling.py
```

This will:
- Perform species-stratified cross-validation
- Fit LMM with REML estimation
- Fit Random Forest baseline
- Calculate R² difference and evaluate success criteria
- Perform F-tests and p-value corrections

**Output**:
- `artifacts/models/lmm_model.pkl`: LMM model
- `artifacts/models/rf_model.pkl`: Random Forest model
- `artifacts/reports/metrics.json`: Model performance metrics

### 4. Visualization

Generate visualizations:

```bash
python code/visualization.py
```

This will:
- Generate partial dependence plots
- Create scatter plots with fit lines
- Save figures to `artifacts/plots/`

**Output**:
- `artifacts/plots/pdp_phosphorus.png`: Partial dependence for phosphorus
- `artifacts/plots/pdp_nitrogen.png`: Partial dependence for nitrogen
- `artifacts/plots/scatter_plots.png`: Scatter plots with fits

### 5. Reporting

Generate final report:

```bash
python code/reporting.py
```

This will:
- Load model results and metrics
- Calculate merge success rate
- Verify biological plausibility
- Compile final report
- Save report to `artifacts/reports/`

**Output**:
- `artifacts/reports/final_report.md`: Comprehensive report
- `artifacts/reports/metrics.json`: Final metrics including success criterion status

## Troubleshooting

### Data Fetching Failures

If data fetching fails, the pipeline will raise an exception. Check:
- Network connectivity
- Data source availability
- Configuration settings

### Memory Issues

For large datasets, the pipeline uses streaming. If you encounter memory issues:
- Reduce the sample size in configuration
- Increase available RAM
- Use a machine with more resources

### Model Training Errors

If model training fails:
- Check data preprocessing steps
- Verify feature columns exist
- Review log files for specific errors

## Output Interpretation

### Metrics File

The `metrics.json` file contains:
- `lmm_r2`: LMM R² score
- `rf_r2`: Random Forest R² score
- `r2_delta`: Difference between LMM and RF R²
- `sc002_status`: PASS/FAIL based on 5% threshold
- `merge_success_rate`: Percentage of successful merges
- `p_values`: Statistical significance values

### Exclusion Log

The `exclusion_log.json` file documents:
- Species excluded due to n<20
- Rows excluded due to experimental data
- Rows excluded due to missing nutrients

## Performance Expectations

- **Runtime**: ≤ 6 hours on standard hardware
- **Memory**: ≤ 7GB RAM
- **Output Size**: ≤ 100MB total

## Advanced Usage

### Custom Configuration

Modify `config.yaml` to:
- Change data paths
- Adjust logging levels
- Set random seeds
- Configure model parameters

### Parallel Processing

Some tasks can be run in parallel:
- Data ingestion and preprocessing
- Model training and visualization
- Unit tests

### Sensitivity Analysis

Run sensitivity analysis separately:

```bash
python code/sensitivity_analysis.py
```

This compares model coefficients against literature ranges.
