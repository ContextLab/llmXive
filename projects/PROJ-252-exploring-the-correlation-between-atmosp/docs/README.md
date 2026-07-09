# Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Project Overview

This project investigates the potential correlation between atmospheric pressure anomalies and earthquake precursors. It implements a rigorous scientific pipeline for data acquisition, preprocessing, statistical analysis, and robustness validation.

## Current Status: Pilot / Methodology Validation

**This is a pilot study focused on methodology validation.** The full-scale global analysis described in the original design has been scoped down due to data availability constraints (see Deviations below).

## Key Limitations and Deviations

The following scope reductions have been formally documented in `docs/deviations.md` and implemented in the pipeline:

- **FR-001: Global Data Download Blocked**: Verified global NOAA NCEP/NCAR pressure data sources are unavailable programmatically. The pipeline falls back to a verified test dataset (2018 Alaska subset, N=12 earthquakes) for methodology validation. [UNRESOLVED-CLAIM: c_906e90cf — status=not_enough_info]
- **FR-011: Climate Index Deferment**: ENSO and PDO climate indices are not currently stratified due to lack of verified programmatic sources. Control windows are matched by date only.
- **Scope**: Analysis is limited to the 2018 Alaska test subset (M≥4.0, depth≤70km) with N=12 events. [UNRESOLVED-CLAIM: c_b135df70 — status=not_enough_info]

See `docs/deviations.md` for the complete list of deviations and their verification logic.

## Repository Structure

```
.
├── code/ # Python implementation
│ ├── analysis.py # Statistical tests (KS, permutation, FDR)
│ ├── config.py # Configuration management
│ ├── download.py # Data acquisition and validation
│ ├── preprocess.py # Data cleaning and feature engineering
│ ├── generate_master_dataset.py
│ ├── generate_pilot_report.py
│ ├── generate_robustness_report.py
│ └── utils/
│ └── logging.py
├── data/
│ ├── raw/ # Downloaded raw data (immutable)
│ ├── interim/ # Intermediate processed data
│ └── processed/ # Analysis-ready datasets
├── tests/ # Test suite
├── docs/
│ ├── deviations.md # Formal deviation records
│ ├── pilot_report.md # Final pilot findings
│ └── quickstart.md # Execution guide
├── requirements.txt # Python dependencies
└── README.md
```

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Run the Pipeline**:
 ```bash
 # Download and preprocess data
 python code/download.py
 python code/preprocess.py

 # Generate master dataset
 python code/generate_master_dataset.py

 # Run statistical analysis
 python code/analysis.py

 # Generate reports
 python code/generate_robustness_report.py
 python code/generate_pilot_report.py
 ```

3. **Run Tests**:
 ```bash
 pytest tests/ -v
 ```

## Output Artifacts

- `data/processed/master_dataset.csv`: Paired earthquake and pressure anomaly data
- `data/processed/statistical_results.json`: KS test and permutation test results
- `data/processed/robustness_report.json`: Sensitivity analysis across subsets
- `docs/pilot_report.md`: Final pilot findings and limitations

## Deviation Records

All scope reductions and their verification logic are documented in `docs/deviations.md`. This includes:
- Absence of global NOAA NCEP/NCAR sources (FR-001)
- Deferral of climate index stratification (FR-011)
- Verification of fallback to test data only

## Contributing

This is a research project. All changes must adhere to the scientific method and maintain reproducibility.

## License

See LICENSE file for details.
