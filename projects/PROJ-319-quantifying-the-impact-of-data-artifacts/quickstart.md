# Quick Start Guide

## Prerequisites

- Python 3.11+
- pip (Python package manager)

## Installation

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via `code/main.py`. Use the `--run-all` flag to execute the full workflow:

```bash
python code/main.py --run-all
```

This will:
1. **Generate** synthetic planetary nebulae with known ground-truth ellipticity and asymmetry.
2. **Inject** noise and saturation artifacts across defined ranges.
3. **Measure** ellipticity and asymmetry for each artifact level.
4. **Compute** bias relative to ground truth.
5. **Fit** calibration models to correct for bias.
6. **Validate** results and generate reports.

### Output Locations

- **Synthetic Images**: `data/synthetic/`
- **Ground Truth**: `data/synthetic/gt_metadata.json`
- **Processed Data**: `data/processed/` (CSVs, models, stats)
- **Validation**: `data/validation/`
- **Logs**: `logs/research.log`
- **Reports**: `docs/reports/001-final-bias-analysis.md`

## Manual Step-by-Step Execution

If you prefer to run steps individually:

### 1. Generate Synthetic Data
```bash
python code/main.py --mode generate --n-images 50 --output data/synthetic
```

### 2. Process Artifacts (Noise & Saturation Sweeps)
```bash
python code/main.py --mode process --input data/synthetic --output data/processed
```
This step:
- Injects noise levels (0.01, 0.05, 0.10)
- Injects saturation fractions (0.00 to 0.50 in 0.05 increments)
- Outputs: `data/processed/noise_sweep_data.csv`, `data/processed/saturation_sweep.csv`

### 3. Calibrate Models
```bash
python code/main.py --mode calibrate --input data/processed/metrics.csv --output data/processed/models.json
```
This fits regression models and outputs: `data/processed/calibration_functions.json`

### 4. Validate Results
```bash
python code/main.py --mode validate --input data/processed/models.json --test-set data/synthetic/validation --output data/processed/validation_results.csv
```

### 5. Verify Pipeline State
```bash
python code/main.py --mode verify --output logs/verification.log
```

## Running Tests

```bash
pytest tests/
```

## Troubleshooting

- **Missing Ground Truth**: Ensure `data/synthetic/gt_metadata.json` exists. If not, run the `generate` mode first.
- **Import Errors**: Verify `code/config.py` is in the Python path. Run from the project root.
- **File Not Found**: Check that all input paths match the expected directory structure.

## Next Steps

- Review `research.md` for detailed analysis and findings.
- Read `docs/reports/001-final-bias-analysis.md` for the final report.
- Examine `data/validation/power_analysis_report.md` for power analysis limitations.
