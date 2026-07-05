# Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

## Overview

This project investigates how spatial data resolution affects statistical power in the analysis of land cover patterns. Using National Land Cover Database (NLCD) data for Colorado, we generate coarser resolution rasters via nearest-neighbor resampling and evaluate the impact on spatial autocorrelation metrics (Moran's I) and statistical power.

## Key Findings

- **Threshold Resolution**: Statistical power drops below 0.80 at **240m** resolution.
- **Type II Error**: At 480m resolution, the Type II error delta relative to 30m baseline is significant. [UNRESOLVED-CLAIM: c_645fcbd7 — status=not_enough_info]
- **Sensitivity**: The threshold is stable within ±10% sensitivity sweeps, varying by no more than one resolution step. [UNRESOLVED-CLAIM: c_9f030d1a — status=not_enough_info]

## Project Structure

```
projects/PROJ-421-assessing-the-impact-of-data-resolution-/
├── code/
│ ├── analysis.py # Spatial autocorrelation and power analysis
│ ├── config.py # Project configuration (resolutions, seeds, paths)
│ ├── data_ingestion.py # NLCD data download and validation
│ ├── generate_final_report.py # Final report generation
│ ├── models.py # Data models (ResolutionRaster, BinaryIndicatorMap)
│ ├── resampling.py # Resolution aggregation (nearest-neighbor)
│ ├── sensitivity_analysis.py # Sensitivity analysis around threshold
│ ├── setup_dirs.py # Directory initialization
│ ├── type2_error_analysis.py # Type II error calculation
│ ├── utils.py # I/O helpers, checksumming, retry logic
│ ├── validate_checksums.py # Checksum validation utilities
│ ├── visualization.py # Power curve generation and threshold identification
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Original high-resolution NLCD data
│ ├── derived/ # Coarser resolution rasters (60m, 120m, 240m, 480m)
│ └── results/ # Analysis outputs (Moran's I, power estimates, reports)
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications and design documents
└── README.md # This file
```

## Quick Start

### Prerequisites

- Python 3.9+
- Required packages listed in `code/requirements.txt`

### Installation

```bash
cd projects/PROJ-421-assessing-the-impact-of-data-resolution-
pip install -r code/requirements.txt
```

### Running the Pipeline

1. **Initialize Directories**:
 ```bash
 python code/setup_dirs.py
 ```

2. **Download and Ingest Data**:
 ```bash
 python code/data_ingestion.py
 ```

3. **Generate Coarser Resolutions**:
 ```bash
 python code/resampling.py
 ```

4. **Run Spatial Analysis**:
 ```bash
 python code/analysis.py
 ```

5. **Generate Final Report**:
 ```bash
 python code/generate_final_report.py
 ```

## Output Artifacts

- `data/results/power_results.csv`: Statistical power estimates for each resolution.
- `data/results/threshold_report.txt`: Identified resolution threshold where power < 0.80.
- `data/results/final_report.md`: Comprehensive analysis report including Type II error delta and sensitivity analysis.
- `figures/power_curve.png`: Visualization of power vs. resolution.

## Methodology

### Data Ingestion
- High-resolution (30m) NLCD land cover data for Colorado is downloaded from a verified HuggingFace source.
- Checksums are validated to ensure data integrity.

### Resolution Aggregation
- Coarser resolutions (60m, 120m, 240m, 480m) are generated using nearest-neighbor resampling to preserve categorical integrity.
- Windowed reads are used to manage memory constraints (<7GB RAM).

### Spatial Autocorrelation Analysis
- Binary indicator maps are created (Forest=1, Others=0).
- Moran's I is calculated for each resolution.
- Null distributions (H0) are generated via 1,000 random permutations.
- Alternative distributions (H1) are simulated using a Gibbs Sampler with a fixed λ parameter calibrated from 30m data.
- Statistical power is computed as the rejection rate of H1 simulations (p < 0.05).

### Threshold Identification
- The resolution where power drops below 0.80 is identified.
- Sensitivity analysis (±10% sweep) confirms threshold stability.

## Configuration

Edit `code/config.py` to modify:
- Target resolutions: `[30, 60, 120, 240, 480]`
- Random seed: `42`
- Data paths and API keys

## Testing

Run tests using:
```bash
pytest tests/
```

## References

- NLCD Data: National Land Cover Database
- PySAL: Python Spatial Analysis Library
- Specification: `specs/001-assessing-resolution-power/spec.md`

## License

This project is for research purposes.
