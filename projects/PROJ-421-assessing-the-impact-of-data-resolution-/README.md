# Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

This project investigates how spatial data resolution affects statistical power in detecting spatial autocorrelation, using publicly available land cover datasets (NLCD).

## Prerequisites

- Python 3.9+
- `pip install -r code/requirements.txt`

## Quick Start

### 1. Setup Directories
```bash
python -m code.setup_dirs
```

### 2. Validate Data Sources
```bash
python -m code.reference_validator --input data/ --config code/config.py
```

### 3. Ingest Data
Downloads the high-resolution (30m) NLCD data for Colorado.
```bash
python -m code.data_ingestion
```

### 4. Generate Coarser Resolutions
Creates aggregated rasters at 60m, 120m, 240m, and 480m using nearest-neighbor resampling.
```bash
python -m code.resampling --input data/raw/nlcd_30m_colorado.tif --factors 2,4,8,16 --output data/derived/
```

### 5. Run Calibration (Phase 0)
Estimates the spatial lag parameter ($\lambda$) from the 30m data.
```bash
python -m code.calibration --input data/raw/nlcd_30m_colorado.tif --output data/results/calibration_lambda.json
```

### 6. Run Full Analysis (US2)
Computes Moran's I, generates null/alternative distributions, and calculates statistical power.
```bash
python -m code.analysis --input-dir data/derived/ --lambda-file data/results/calibration_lambda.json --output data/results/results.csv
```

### 7. Generate Reports (US3)
Creates the power curve visualization and threshold report.
```bash
python -m code.visualization --input data/results/results.csv --output data/results/
python -m code.generate_sensitivity_report --input data/results/results.csv --output data/results/sensitivity_report.md
python -m code.generate_final_report --input data/results/results.csv --output data/results/final_report.md
```

## CLI Usage Examples

### Resampling with Custom Factors
```bash
python -m code.resampling --input data/raw/nlcd_30m_colorado.tif --factors 2,3,4 --output data/derived_custom/
```

### Analysis with Specific Seed
```bash
python -m code.analysis --input-dir data/derived/ --lambda-file data/results/calibration_lambda.json --seed 42 --output data/results/results.csv
```

### Sensitivity Sweep
```bash
python -m code.sensitivity_analysis --input data/results/results.csv --output data/results/sensitivity_report.md --sweep-factors 1.8,2.2
```

## Project Structure

```
.
├── code/
│ ├── analysis.py # Moran's I, power calculation, simulation
│ ├── calibration.py # Lambda estimation
│ ├── config.py # Project configuration
│ ├── data_ingestion.py # Data download and validation
│ ├── resampling.py # Resolution aggregation
│ ├── visualization.py # Power curve generation
│ ├── utils.py # IO helpers, logging, retry logic
│ └──...
├── data/
│ ├── raw/ # Original downloaded data
│ ├── derived/ # Aggregated rasters
│ └── results/ # Analysis outputs, reports
├── tests/
│ ├── test_analysis.py
│ ├── test_resampling.py
│ └──...
├── README.md
└── requirements.txt
```

## Validation

Run the quickstart validator to ensure all components are functional:
```bash
python -m code.quickstart_validator
```

## License

This project is for research purposes using public domain data (NLCD).