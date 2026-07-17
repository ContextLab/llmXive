# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Clone the repository.
2. Navigate to the `code` directory.
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration
Edit `config.yaml` to set global seeds, topology targets, and simulation parameters.

## Execution
The following commands run the full pipeline:

### 1. Generate Networks
```bash
python src/generators/batch_runner.py --config config.yaml
```

### 2. Run Simulations
```bash
python src/simulation/run_simulation.py --config config.yaml
```

### 3. Run Analysis
```bash
python src/analysis/run_analysis.py --config config.yaml
```

### 4. Run Power Analysis
```bash
python scripts/run_power_analysis.py --config config.yaml
```

### 5. Run Sensitivity Sweep
```bash
python scripts/run_sensitivity_sweep.py --config config.yaml
```

### 6. Validate Batch (SC-001, SC-002, SC-005)
```bash
python scripts/validate_batch.py --config config.yaml --output data/analysis/validation_report.json
```

## Verification
Check `data/analysis/validation_report.json` for the results of the validation checks.
