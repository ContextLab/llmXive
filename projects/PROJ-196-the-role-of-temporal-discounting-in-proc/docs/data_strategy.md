# Data Strategy

## Overview

This document outlines the data acquisition and processing strategy for the
"Role of Temporal Discounting in Procrastination" project.

## Data Sources

### Synthetic Data Generation (Current Phase)

For the initial methodological validation phase, the project uses a
Data Generating Process (DGP) to create synthetic datasets that mimic
the expected distribution of real experimental data.

The DGP parameters are defined in `code/ingestion.py` and include:
- Discount rate parameters (k_mean, k_sd)
- Procrastination scale parameters
- Working memory task parameters
- Demographic distributions

### Real Data Integration (Future)

When real data becomes available, the pipeline will be extended to:
1. Load raw data from CSV/ARFF files in `data/raw/`
2. Validate column names and data types
3. Apply the same harmonization logic as synthetic data

## Fail-Loud Policy

The data loading implementation follows a strict "Fail Loud" policy:

1. **No Silent Fallbacks**: If a real data source fails to load, the system
 raises a specific `FileNotFoundError` with the message:
 "Data source not found: {path}"

2. **No Synthetic Fallback**: The loader will NOT fall back to generating
 synthetic data if the real source is unavailable. This ensures that:
 - All results are traceable to a real data source
 - Failed runs are immediately visible and fixable
 - There is no risk of accidentally reporting synthetic results as real

3. **Explicit Error Messages**: When data loading fails, the error message
 clearly indicates:
 - The path that was attempted
 - The specific reason for failure (file not found, permission denied, etc.)

## Implementation Details

The fail-loud behavior is implemented in `code/ingestion.py`:

```python
def load_real_data(path: str) -> pd.DataFrame:
 if not os.path.exists(path):
 raise FileNotFoundError(f"Data source not found: {path}")
 return pd.read_csv(path)
```

Any `try/except` blocks that previously allowed silent fallback to synthetic
data have been removed. If the data loading fails, the script terminates
with a clear error, allowing the execution stage to detect and report the issue.

## Reproducibility

To ensure reproducibility:
- All DGP parameters are logged to `data/processed/dgp_params.log`
- A SHA-256 hash of the parameters is stored in `data/processed/data_source_flag.json`
- The random seed is explicitly set and logged
- All generated files are checksummed and recorded in the state file