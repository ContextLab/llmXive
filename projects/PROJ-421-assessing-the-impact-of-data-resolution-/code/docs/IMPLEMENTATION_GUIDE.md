# Implementation Guide: Assessing the Impact of Data Resolution on Statistical Power

## Overview
This project implements a pipeline to analyze how data resolution affects statistical power in spatial datasets, specifically focusing on land cover data from the National Land Cover Database (NLCD).

## Project Structure
```
projects/PROJ-421-assessing-the-impact-of-data-resolution-/
├── code/
│ ├── analysis.py # Spatial autocorrelation and power analysis
│ ├── calibration.py # Lambda parameter estimation
│ ├── config.py # Configuration (resolutions, seeds, paths)
│ ├── data_ingestion.py # NLCD data download and validation
│ ├── models.py # Data models (ResolutionRaster, BinaryIndicatorMap)
│ ├── resampling.py # Resolution aggregation with nearest-neighbor
│ ├── utils.py # Utilities (I/O, logging, checksums)
│ ├── visualization.py # Power curve generation and threshold identification
│ ├── generate_final_report.py
│ ├── sensitivity_analysis.py
│ └── type2_error_analysis.py
├── data/
│ ├── raw/ # Downloaded NLCD data
│ ├── derived/ # Coarser resolution rasters
│ └── results/ # Analysis outputs (CSV, reports)
├── tests/
│ └── unit/ # Unit tests for core modules
└── docs/
 └── IMPLEMENTATION_GUIDE.md
```

## Key Components

### 1. Data Ingestion (data_ingestion.py)
- Downloads NLCD 30m data for Colorado from HuggingFace
- Validates checksums and metadata
- Implements retry logic with exponential backoff

### 2. Resolution Aggregation (resampling.py)
- Generates coarser resolution rasters (60m, 120m, 240m, 480m)
- Uses nearest-neighbor resampling to preserve categorical values
- Implements chunked processing to stay within 7GB RAM limit

### 3. Spatial Analysis (analysis.py)
- Creates binary indicator maps (Forest vs. Others)
- Calculates Moran's I statistics
- Generates null distributions (1,000 permutations)
- Simulates alternative distributions using Gibbs Sampler
- Computes statistical power

### 4. Visualization (visualization.py)
- Generates power-vs-resolution curves
- Identifies threshold where power < 0.80
- Performs sensitivity analysis (±10% sweep)

## Execution Flow

1. **Setup**: Run `python code/setup_dirs.py` to create directory structure
2. **Calibration**: Run `python code/calibration.py` to estimate λ parameter
3. **Data Ingestion**: Run `python code/data_ingestion.py` to download NLCD data
4. **Resampling**: Run `python code/resampling.py` to generate coarser rasters
5. **Analysis**: Run `python code/analysis.py` to compute statistics and power
6. **Visualization**: Run `python code/visualization.py` to generate plots and reports
7. **Final Report**: Run `python code/generate_final_report.py` to create final report

## Configuration
Edit `code/config.py` to modify:
- Resolution factors: [2, 4, 8, 16] (corresponding to 60m, 120m, 240m, 480m)
- Random seed: 42
- HuggingFace URL for NLCD data
- Output paths

## Dependencies
Install requirements:
```bash
pip install -r code/requirements.txt
```

## Testing
Run unit tests:
```bash
pytest tests/unit/
```

## Output Files
- `data/results/calibration_lambda.json`: Estimated λ parameter
- `data/results/power_results.csv`: Moran's I, p-values, power estimates
- `data/results/threshold_report.txt`: Resolution threshold where power < 0.80
- `data/results/final_report.md`: Comprehensive analysis report
- `data/results/sensitivity_report.txt`: Sensitivity analysis results

## Notes
- All random operations use seed=42 for reproducibility
- p-value = 0.05 is treated as significant but flagged
- Chunked processing ensures memory usage stays within 7GB limit
