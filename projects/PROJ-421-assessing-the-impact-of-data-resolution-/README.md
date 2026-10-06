# Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

This project analyzes how spatial data resolution affects the statistical power to detect spatial autocorrelation using publicly available land cover data (NLCD).

## Project Structure

```
.
├── code/
│ ├── data_ingestion.py # Download high-resolution NLCD data
│ ├── resampling.py # Generate coarser resolution rasters
│ ├── calibration.py # Estimate spatial lag parameter (lambda)
│ ├── analysis.py # Moran's I, null/alternative simulation, power calculation
│ ├── visualization.py # Generate power curves and threshold reports
│ ├── utils.py # Shared utilities (logging, I/O, validation)
│ ├── config.py # Configuration (resolutions, seeds, paths)
│ └──...
├── data/
│ ├── raw/ # Original downloaded data
│ ├── derived/ # Processed rasters (resampled, binary)
│ └── results/ # Analysis outputs (CSV, reports)
├── tests/ # Unit and integration tests
└── README.md
```

## Prerequisites

- Python 3.9+
- Required packages listed in `code/requirements.txt`

Install dependencies:
```bash
pip install -r code/requirements.txt
```

## Quick Start: Full Pipeline

Run the entire analysis pipeline from data ingestion to final report:

```bash
# 1. Ingest high-resolution NLCD data (Colorado subset)
python -m code.data_ingestion --output data/raw/nlcd_30m.tif

# 2. Generate coarser resolution rasters (60m, 120m, 240m, 480m)
python -m code.resampling --input data/raw/nlcd_30m.tif --factors 2,4,8,16 --output data/derived

# 3. Create binary indicator map (Forest=1, Others=0)
python -m code.analysis --action create_binary --input data/raw/nlcd_30m.tif --output data/derived/nlcd_30m_binary.tif

# 4. Calibrate spatial lag parameter (lambda)
python -m code.calibration --input data/derived/nlcd_30m_binary.tif --output data/results/calibration_lambda.json

# 5. Run full analysis (Moran's I, null/alternative simulation, power calculation)
python -m code.analysis --action full_analysis --input data/derived --results data/results/results.csv

# 6. Generate power curve and threshold report
python -m code.visualization --input data/results/results.csv --output data/results/threshold_report.txt

# 7. Generate final report
python -m code.generate_final_report --input data/results/results.csv --output data/results/final_report.md
```

Alternatively, run the main pipeline script:
```bash
python -m code.main --full-sweep
```

## Individual Components

### Data Ingestion

Download NLCD 30m data for Colorado:
```bash
python -m code.data_ingestion --output data/raw/nlcd_30m.tif
```

### Resampling

Generate coarser resolution rasters using nearest-neighbor resampling:
```bash
python -m code.resampling --input data/raw/nlcd_30m.tif --factors 2,4,8,16 --output data/derived
```
Output files: `nlcd_co_res_60m.tif`, `nlcd_co_res_120m.tif`, etc.

### Calibration

Estimate the spatial lag parameter ($\lambda$) from the binary map:
```bash
python -m code.calibration --input data/derived/nlcd_30m_binary.tif --output data/results/calibration_lambda.json
```

### Analysis

Run Moran's I, generate null distributions, simulate alternative hypotheses, and calculate statistical power:
```bash
python -m code.analysis --action full_analysis --input data/derived --results data/results/results.csv
```

### Visualization

Generate power-vs-resolution curve and identify threshold where power < 0.80:
```bash
python -m code.visualization --input data/results/results.csv --output data/results/threshold_report.txt
```

### Final Report

Generate the comprehensive final report:
```bash
python -m code.generate_final_report --input data/results/results.csv --output data/results/final_report.md
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test modules:
```bash
pytest tests/test_resampling.py
pytest tests/test_analysis.py
```

## Configuration

Edit `code/config.py` to modify:
- Target resolutions (default: 30, 60, 120, 240, 480)
- Random seeds (default: 42)
- File paths
- Data source URLs

## Output Files

- `data/derived/nlcd_30m_binary.tif`: Binary indicator map
- `data/results/calibration_lambda.json`: Estimated spatial lag parameter
- `data/results/results.csv`: Moran's I, p-values, power estimates per resolution
- `data/results/threshold_report.txt`: Resolution where power < 0.80
- `data/results/final_report.md`: Comprehensive analysis report

## Citation

If you use this code or its results, please cite the NLCD data source and acknowledge the project's methodology.