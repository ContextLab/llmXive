# Data Model: Robustness of Statistical Tests to Data Contamination

## Overview

This document defines the data structures, file formats, and schemas used in the simulation study. It ensures that the `contracts/` schemas accurately reflect the data flow from raw download to final analysis.

## Key Entities

### 1. Raw Dataset
The original data downloaded from the verified UCI sources.
- **Format**: CSV.
- **Content**: Numeric features and target variables.
- **Transformation**: No modification; stored in `data/raw/`.

### 2. ContaminationProfile
A configuration object defining the contamination parameters for a specific run.
- **Fields**:
  - `type`: "gaussian" | "adversarial"
  - `rate`: float (0.0 to 1.0)
  - `threshold`: float (0.01, 0.05, 0.1)
  - `seed`: int
  - `outlier_sigma`: float (multiplier for standard deviation in adversarial mode)

### 3. SimulationResult
The primary output record for each iteration of the simulation.
- **Fields**:
  - `dataset_name`: string
  - `contamination_type`: string
  - `contamination_rate`: float
  - `contamination_threshold`: float
  - `method`: "standard" | "trimmed" | "winsorized"
  - `iteration`: int
  - `n_samples`: int
  - `effect_size`: float (0.0 for Type I error tests)
  - `test_statistic`: float
  - `p_value`: float
  - `p_value_corrected`: float (Bonferroni)
  - `null_rejected`: bool
  - `power_or_error`: float (1.0 if rejected under null, 0.0 otherwise; or 1.0 if rejected under alternative)

## File Structure

```text
data/
├── raw/
│   ├── uci_har_test.csv          # Raw download
│   └── wine_quality_red.csv      # Raw download
├── processed/
│   ├── contaminated_uci_har_5pct.csv
│   └── ...
└── results/
    └── simulation_results.csv    # Aggregated results (approximately tens of thousands of rows)
```

## Data Flow

1. **Validation**: `validate_citations.py` runs to ensure all dataset URLs are verified (Constitution Principle II).
2. **Download**: `download_datasets.py` fetches raw files to `data/raw/`.
3. **Checksum**: `checksum_artifacts.py` generates SHA256 hashes for raw files and updates `state/` manifest (Constitution Principle V).
4. **Contamination**: `generate_contamination.py` reads raw, applies `ContaminationProfile`, writes to `processed/`.
5. **Simulation**: `run_simulation.py` reads `processed/`, runs **a sufficient number of iterations per condition**, appends `SimulationResult` rows to `results/simulation_results.csv`.
6. **Analysis**: `plot_results.py` reads `results/simulation_results.csv` to generate visualizations.
7. **Final Hash**: `checksum_artifacts.py` runs again on processed data and results to update `state/` manifest.