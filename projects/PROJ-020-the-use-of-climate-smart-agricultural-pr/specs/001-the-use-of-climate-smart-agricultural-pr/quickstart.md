# Quickstart Guide: Climate-Smart Agriculture Analysis Pipeline

This guide provides instructions for setting up and running the full analysis pipeline
for the study: **"The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods"**.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- At least 8GB RAM available (7GB limit enforced by config)
- Internet connection for data download

## 1. Project Setup

### Clone and Install Dependencies

```bash
# Ensure you are in the project root
cd PROJ-020-the-use-of-climate-smart-agricultural-pr

# Install dependencies
pip install -r code/requirements.txt
```

### Verify Environment Setup

```bash
# Run setup scripts to create directory structure
python code/data/setup_directories.py

# Configure environment variables (optional, defaults to Kenya, India, Vietnam)
export TARGET_COUNTRIES="KEN,IND,VNM"
export TARGET_YEARS="2015,2016,2017,2018,2019,2020"
export MAX_RAM_GB=7
```

## 2. Data Ingestion Pipeline (User Story 1)

This stage downloads raw data from LSMS, NASA POWER, and FAOSTAT, then cleans, merges, and samples the data.

```bash
# Run the full data pipeline
python code/main.py --stage download_clean
```

**Outputs:**
- `data/raw/`: Raw downloaded files (JSON, CSV)
- `data/processed/merged_sample.parquet`: Final analysis-ready dataset
- `state/checksums.json`: Data integrity checksums
- `state/provenance.json`: Mapping of derived variables to source IDs

**Expected Results:**
- Dataset with ≥ 5,000 households per country
- ≤ 7GB RAM usage during processing
- No missing values in key predictors (after imputation)

## 3. Statistical Modeling (User Story 2)

Fit Mixed-Effects Regression models to quantify relationships between CSA adoption and food security.

```bash
# Run the modeling pipeline
python code/main.py --stage model_analysis
```

**Outputs:**
- `data/processed/model_results.json`: Standardized coefficients, p-values, VIF scores
- `data/processed/robustness_results.json`: Bootstrap and leave-one-region-out results
- `state/model_state.json`: Checkpoint state for timeout recovery

**Key Features:**
- Benjamini-Hochberg FDR correction for multiple hypotheses
- Mediation analysis for digital and finance access
- Interaction terms for moderation effects
- Robustness checks with variance reporting

## 4. Visualization and Reporting (User Story 3)

Generate publication-quality plots and robustness reports.

```bash
# Run the visualization pipeline
python code/main.py --stage viz_report
```

**Outputs:**
- `figures/scatter_csa_food_security.png`: CSA Index vs. Food Security
- `figures/coefficient_plot.png`: Standardized coefficients with confidence intervals
- `figures/regional_map.png`: Spatial distribution of CSA adoption
- `figures/distribution_plots.png`: Variable distributions
- `data/processed/robustness_report.md`: Detailed robustness analysis

## 5. Running Individual Components

For development and debugging, you can run individual modules:

```bash
# Download specific data sources
python code/data/download.py --source lsms --country KEN --year 2020
python code/data/download.py --source nasa_power --lat 0.5 --lon 37.0 --start 2020-01-01 --end 2020-12-31
python code/data/download.py --source faostat --indicator "Crop Production Index"

# Clean and merge data
python code/data/clean.py --input data/raw --output data/processed

# Calculate CSA index
python code/data/features.py --input data/processed/merged_sample.parquet

# Run diagnostics
python code/analysis/diagnostics.py --input data/processed/merged_sample.parquet

# Fit model
python code/analysis/model.py --input data/processed/merged_sample.parquet

# Generate plots
python code/viz/plots.py --input data/processed/model_results.json
```

## 6. Testing

Run the test suite to verify pipeline integrity:

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v # Unit tests
pytest tests/integration/ -v # Integration tests
pytest tests/contract/ -v # Contract tests
```

## 7. Troubleshooting

### Common Issues

**Issue: "Missing data for country X"**
- LSMS surveys are not available for all years. The pipeline automatically skips missing years and logs warnings.

**Issue: "VIF > 5.0 for predictor Y"**
- This indicates multicollinearity. The pipeline flags these predictors but does not auto-exclude them. Review the collinearity report.

**Issue: "Model fitting timeout"**
- The pipeline attempts a reduced-batch retry. Check `state/model_state.json` for recovery points.

**Issue: "Memory limit exceeded"**
- Ensure `MAX_RAM_GB` is set correctly. The pipeline enforces this limit and may downcast data types.

### Logs

All pipeline logs are written to `state/logs/` with timestamps:
- `download_YYYYMMDD_HHMMSS.log`
- `clean_YYYYMMDD_HHMMSS.log`
- `model_YYYYMMDD_HHMMSS.log`
- `viz_YYYYMMDD_HHMMSS.log`

## 8. Reproducibility

To ensure reproducibility:
1. Use the pinned dependencies in `code/requirements.txt`
2. Set the same `TARGET_COUNTRIES` and `TARGET_YEARS` environment variables
3. Use the same random seed (default: 42) for sampling and bootstrapping
4. Verify data checksums in `state/checksums.json`

## 9. Next Steps

After running the pipeline:
1. Review the robustness report in `data/processed/robustness_report.md`
2. Examine the visualization outputs in `figures/`
3. Validate findings against the user stories in `specs/001-csa-food-security/spec.md`
4. Prepare results for publication or stakeholder review

## Support

For issues or questions, refer to:
- `specs/001-csa-food-security/plan.md` for project requirements
- `specs/001-csa-food-security/data-model.md` for data schema
- `code/README.md` for detailed module documentation