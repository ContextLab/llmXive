# Quickstart Guide

## Overview

This guide walks you through setting up and running the full pipeline for investigating the influence of network topology on spontaneous brain activity patterns.

## Prerequisites

- Python 3.9+
- pip
- ~14 GB disk space for data
- ~7 GB RAM for processing

## Step 1: Environment Setup

1. **Clone the repository** (if applicable)
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Step 2: Directory Structure

Run the setup script to create the required directories:
```bash
python code/setup_directory_structure.py
```

This creates:
- `data/raw/` - For raw HCP data
- `data/processed/` - For processed metrics
- `data/logs/` - For execution logs
- `contracts/` - For schema files

## Step 3: Fetch Data

The pipeline uses real HCP data from OpenNeuro. Data is fetched programmatically at runtime by the loader modules.

**Note**: The first run will download the data. Ensure you have sufficient disk space (~14 GB).

To manually verify data availability:
```bash
python code/preprocess/loader.py --verify
```

## Step 4: Run the Pipeline

Execute the main pipeline:
```bash
python code/main.py
```

This will:
1. Load raw HCP data
2. Preprocess structural and functional data
3. Compute graph metrics (structural)
4. Extract dynamic states (functional)
5. Perform correlation analysis
6. Run sensitivity analyses
7. Generate logs and intermediate outputs

**Expected runtime**: 30-60 minutes depending on cohort size and hardware.

## Step 5: Generate Final Report

After the pipeline completes, generate the final report:
```bash
python code/reports/generate_report.py
```

This produces:
- `data/processed/final_report.json` - Comprehensive results
- `data/processed/sensitivity_comparison.csv` - Window length sensitivity
- `data/processed/structural_density_sensitivity.csv` - Density sensitivity
- `data/processed/tractography_sensitivity_metrics.csv` - Tractography noise analysis
- `data/processed/tractography_correlation_sensitivity.csv` - Correlation sensitivity to tractography confidence

## Step 6: Validate Report

Validate the report against the schema:
```bash
python code/reports/validate_report.py
```

Check for associational language compliance:
```bash
python code/reports/audit_associational_language.py
```

## Step 7: Run Tests (Optional)

Run the test suite to verify correctness:
```bash
pytest tests/
```

Key tests:
- LOO independence constraint (`tests/unit/test_functional.py::test_loo_independence`)
- Normality testing (`tests/unit/test_correlation.py::test_normality_check`)
- FDR correction (`tests/unit/test_correlation.py::test_benjamini_hochberg`)
- Tractography thresholding (`tests/unit/test_tractography.py`)

## Output Files

### Processed Data
- `data/processed/structural_metrics.csv` - Graph metrics per subject
- `data/processed/dynamic_metrics.csv` - Dynamic state metrics per subject
- `data/processed/correlation_results.csv` - Structure-function correlations
- `data/processed/completeness_report.json` - Data completeness summary
- `data/processed/loo_centroids_all_subjects.npz` - LOO centroids

### Logs
- `data/logs/exclusion_log.json` - Excluded subjects and reasons
- `data/logs/execution_log.json` - Pipeline execution details

### Reports
- `data/processed/final_report.json` - Final comprehensive report
- `data/processed/sensitivity_comparison.csv` - Window length sensitivity
- `data/processed/structural_density_sensitivity.csv` - Density sensitivity
- `data/processed/tractography_sensitivity_metrics.csv` - Tractography noise metrics
- `data/processed/tractography_correlation_sensitivity.csv` - Correlation sensitivity

## Troubleshooting

### Data Fetching Errors
- Ensure internet connection is available
- Check that OpenNeuro is accessible
- Verify disk space is sufficient

### Memory Errors
- Reduce cohort size or use chunked processing
- Ensure `code/utils/cpu_optimization.py` is being used
- Close other memory-intensive applications

### Convergence Failures
- Check `data/logs/exclusion_log.json` for excluded subjects
- Verify data quality in `data/raw/`
- Adjust `DENSITY_THRESHOLD` if too strict

### Tractography Sensitivity
- If findings vanish at high confidence thresholds, see `final_report.json` for explicit warnings about potential tractography artifacts

## Next Steps

- Review `final_report.json` for key findings
- Examine sensitivity analyses for robustness
- Validate "associational" language compliance
- Share results with the research team

## Support

For issues, refer to:
- Project documentation in `docs/`
- Code comments in `code/`
- Test examples in `tests/`
