# Technical Architecture

## Component Overview

The pipeline follows a modular, script-based architecture designed for reproducibility and clarity.

### Core Modules (`code/`)

- **`config.py`**: Central hub for configuration loading, random seed management, and directory creation. Enforces the "Fail Loudly" principle if seeds are missing.
- **`ingest.py`**: Handles HTTP requests to download raw data. Validates schema against expected columns.
- **`clean.py`**: Implements listwise deletion for missing values. Enforces power constraints ($N \ge 30$).
- **`validity.py`**: Contains the `check_construct_validity` function to detect mathematical coupling.
- **`model.py`**: Implements statistical logic using `statsmodels` and `scipy`. Includes OLS fitting and diagnostic checks.
- **`robustness.py`**: Logic for subset selection and comparative analysis.
- **`viz.py`**: Generates matplotlib/seaborn visualizations.
- **`report_generator.py`**: Aggregates JSON results into a markdown report.

### Data Flow

1. **Ingestion**: `data/raw/` (CSV) <- `requests` <- External URL
2. **Cleaning**: `data/processed/analysis_data.csv` <- `clean.py` <- `data/raw/`
3. **Analysis**: `outputs/*.json` <- `model.py`/`robustness.py` <- `data/processed/`
4. **Visualization**: `outputs/plot.png` <- `viz.py` <- `data/processed/`
5. **Reporting**: `outputs/final_report.md` <- `report_generator.py` <- `outputs/*.json`

## Error Handling

Custom exceptions are defined in `code/exceptions.py`:
- `PowerLimitationError`: Raised when sample size is insufficient.
- `MathematicalCouplingError`: Raised when construct validity fails.
- `DataValidationError`: Raised when schema mismatches occur.

## Logging

All scripts write to `outputs/analysis.log`. Critical steps (seed application, power checks, validity failures) are logged with appropriate severity levels.

## Dependencies

- `pandas`: Data manipulation.
- `statsmodels`: Statistical modeling.
- `scipy`: Correlation and statistical tests.
- `matplotlib`/`seaborn`: Visualization.
- `pyyaml`: Configuration parsing.
