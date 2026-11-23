# Quick Start Guide

This guide provides step-by-step instructions for running the full pipeline to quantify the impact of data artifacts on planetary nebula morphology measurements.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for reproducibility tracking)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd PROJ-319-quantifying-the-impact-of-data-artifacts
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Full Pipeline

The simplest way to run the entire analysis is:

```bash
python code/main.py --run-all
```

This will:
1. Generate synthetic planetary nebulae (50 images by default)
2. Inject noise and saturation artifacts
3. Calculate ellipticity and asymmetry metrics
4. Perform statistical regression analysis
5. Derive calibration functions
6. Validate results and generate reports

Expected outputs in `data/processed/`:
- `noise_sweep_data.csv`: Raw noise sweep measurements
- `noise_stats.csv`: Statistical analysis of noise bias
- `saturation_sweep.csv`: Raw saturation sweep measurements
- `saturation_stats.csv`: Statistical analysis of saturation bias
- `aggregated_bias.csv`: Merged bias data
- `calibration_functions.json`: Derived correction models
- `run_manifest.json`: Reproducibility metadata

## Step-by-Step Execution

If you prefer to run each stage individually:

### 1. Generate Synthetic Data

```bash
python code/main.py --mode generate --n-images 50 --output data/synthetic
```

This creates:
- `data/synthetic/synth_*.fits`: Synthetic nebula images
- `data/synthetic/gt_metadata.json`: Ground truth parameters

### 2. Inject Artifacts and Measure Metrics

```bash
python code/main.py --mode process --input data/synthetic --output data/processed
```

This runs both US1 (noise) and US2 (saturation) sweeps.

### 3. Calibrate (Derive Correction Functions)

```bash
python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json
```

This fits regression models and outputs `calibration_functions.json`.

### 4. Validate

```bash
python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv
```

### 5. Verify Pipeline State

```bash
python code/main.py --mode verify --output logs/verification.log
```

## Individual Script Execution

You can also run analysis scripts directly:

### Noise Sweep Statistics
```bash
python code/analysis/statistical_tests.py
```
Outputs: `data/processed/noise_stats.csv`

### Saturation Sweep Statistics
```bash
python code/analysis/statistics.py
```
Outputs: `data/processed/saturation_stats.csv`

### Fit Calibration Models
```bash
python code/analysis/regression.py
```
Outputs: `data/processed/calibration_functions.json`

### Power Analysis
```bash
python code/analysis/power_analysis.py
```
Outputs: `data/validation/power_analysis_report.md`

## Expected Outputs

After successful execution, verify these files exist:

| File | Description |
|------|-------------|
| `data/synthetic/gt_metadata.json` | Ground truth for synthetic images |
| `data/processed/noise_sweep_data.csv` | Raw noise bias measurements |
| `data/processed/noise_stats.csv` | Noise regression results |
| `data/processed/saturation_sweep.csv` | Raw saturation bias measurements |
| `data/processed/saturation_stats.csv` | Saturation regression results |
| `data/processed/aggregated_bias.csv` | Merged bias dataset |
| `data/processed/calibration_functions.json` | Final correction models |
| `data/processed/run_manifest.json` | Reproducibility metadata |
| `data/validation/power_analysis_report.md` | Statistical power analysis |
| `docs/reports/001-final-bias-analysis.md` | Final research report |

## Troubleshooting

- **Missing `get_project_root`**: Ensure `code/config.py` is in the Python path. Run from project root.
- **Missing ground truth**: Ensure `T006` (synthetic generation) completed successfully.
- **CUDA errors**: This project is CPU-only. If you see CUDA errors, check for accidental GPU imports.

## Reproducibility

Every run generates a manifest (`data/processed/run_manifest.json`) containing:
- Git commit hash
- Environment variables
- Artifact parameters
- Timestamp

To reproduce a specific run, use the same commit hash and parameters from the manifest.
