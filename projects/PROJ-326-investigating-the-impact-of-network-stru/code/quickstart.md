# Quickstart Guide

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository
2. Navigate to the `code/` directory
3. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
4. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Edit `config.yaml` to set global seeds, topology targets, and simulation parameters.
Ensure `global_seed` is set for reproducibility (FR-007).

## Execution Order

The pipeline must be executed in the following order to ensure all dependencies are met and artifacts are generated correctly.

### 1. Initialize Project Structure (Optional if already done)
```bash
python setup_directories.py
```

### 2. Verify Configuration
```bash
python scripts/verify_config_reproducibility.py --config code/config.yaml
```

### 3. Inject Seeds into Run Log (T004b)
This step ensures the specific random seeds are recorded for reproducibility.
```bash
python scripts/inject_seed.py --config code/config.yaml --output data/run_log.json
```

### 4. Generate Batch of Networks (US1)
```bash
python src/generators/batch_runner.py --config code/config.yaml
python src/generators/aggregate_batch.py --config code/config.yaml
```

### 5. Run Simulations (US2)
```bash
python src/simulation/run_simulation.py --config code/config.yaml
```

### 6. Run Analysis (US3)
```bash
python src/analysis/run_analysis.py --config code/config.yaml
python src/analysis/power.py --config code/config.yaml
python src/analysis/sensitivity.py --config code/config.yaml
```

### 7. Generate Figures and Report
```bash
python src/analysis/plotting.py --config code/config.yaml
python src/analysis/report.py --config code/config.yaml
python src/analysis/verify_report.py --config code/config.yaml
```

### 8. Validate Batch (T045)
```bash
python scripts/validate_batch.py --config code/config.yaml
```

## Validation

Run the full validation suite to ensure all success criteria are met:
```bash
python scripts/validate_quickstart.py
```

## Troubleshooting

- If `data/run_log.json` is missing, ensure `scripts/inject_seed.py` has been run.
- If simulation fails, check `simulation_timeout_seconds` in `config.yaml`.
- Ensure all output directories (`data/raw`, `data/analysis`, `figures`) exist.
