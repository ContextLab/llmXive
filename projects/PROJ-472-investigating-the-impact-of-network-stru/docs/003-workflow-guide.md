# Workflow Guide

This guide outlines the step-by-step workflow for executing the research pipeline, from data acquisition to final reporting.

## Phase 1: Setup and Data Acquisition

1. **Initialize Environment**
 - Ensure Python 3.11 is installed.
 - Install dependencies: `pip install -r code/requirements.txt`.
 - Configure environment variables in `.env` (if applicable).

2. **Download Data**
 - Execute `code/data/download.py` to fetch dMRI data from OpenNeuro ds003813.
 - Verify data integrity using checksums.

3. **Preprocess Data**
 - Run `code/data/preprocess_dMRI.py` to generate adjacency matrices.
 - Ensure the HCP-MMP1.0 parcellation is correctly applied.

4. **Simulate EEG**
 - Execute `code/data/simulate_EEG.py` to generate synthetic resting-state EEG.
 - Verify the output files in `data/processed/`.

5. **Quality Control**
 - Run `code/data/quality_control.py` to filter out low-quality subjects.
 - Check `data/results/qc_report.json` for excluded subjects.

## Phase 2: Analysis

1. **Store Processed Data**
 - Run `code/data/store.py` to persist connectomes and EEG data.

2. **Compute Network Metrics**
 - Execute `code/analysis/metrics.py` to calculate degree, clustering, and rich-club coefficients.

3. **Detect Avalanches**
 - Run `code/analysis/avalanches.py` to identify neural avalanches.
 - Verify avalanche size distributions.

4. **Fit Power-Law Models**
 - Execute `code/analysis/fitting.py` to fit models and determine exponents.

5. **Statistical Analysis**
 - Run `code/analysis/stats.py` for correlation and robustness testing.
 - Review VIF diagnostics for collinearity.

6. **Sensitivity Analysis**
 - Execute `code/analysis/sensitivity.py` to test threshold robustness.

## Phase 3: Reporting

1. **Export Metrics**
 - Run `code/analysis/export_metrics.py` to generate the master metrics CSV.

2. **Generate Final Report**
 - Execute `code/analysis/report.py` to produce the associational report.
 - Output: `data/results/correlation_report.csv`.

## Troubleshooting

- **Data Loading Errors**: Check that `data/raw/` contains the expected files.
- **Simulation Failures**: Verify `code/config.py` parameters and Wilson-Cowan settings.
- **Permutation Test Timeouts**: Ensure sufficient CPU resources; consider reducing shuffles for debugging.

## Running Tests

Execute the test suite to verify implementation:

```bash
pytest tests/ -v
```

Specific tests:
- `tests/test_metrics.py`: Validates network metric calculations.
- `tests/test_avalanches.py`: Validates avalanche detection logic.
- `tests/test_stats.py`: Validates statistical analysis with mock data.
