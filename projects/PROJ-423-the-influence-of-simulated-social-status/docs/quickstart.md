# Quick Start Guide

This guide provides instructions for setting up and running the research pipeline for "The Influence of Simulated Social Status on Risk-Taking Behavior".

## Prerequisites

- Python 3.10+
- pip
- git

## Setup

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-423-the-influence-of-simulated-social-status
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Ensure directories exist**:
 ```bash
 mkdir -p data/raw data/processed logs reports/templates
 ```

## Execution Pipeline

Run the following commands in order to execute the full pipeline. Ensure you are in the project root directory.

### 1. Simulation
Generate synthetic data based on meta-analytic effect sizes.
```bash
python code/simulate.py --condition effect --seed 42 --n 1000 --output data/raw/simulated_data_effect.csv
python code/simulate.py --condition null --seed 42 --n 1000 --output data/raw/simulated_data_null.csv
```

### 2. Preprocessing
Clean and transform the raw data.
```bash
python code/preprocess.py --input data/raw/simulated_data_effect.csv --output data/processed/cleaned_data_effect.csv
python code/preprocess.py --input data/raw/simulated_data_null.csv --output data/processed/cleaned_data_null.csv
```

### 3. Analysis
Fit adaptive regression models and calculate statistics.
```bash
python code/analysis.py
```
*Note: This script reads `data/processed/cleaned_data_*.csv` and `code/simulation_parameters.json`.*

### 4. Reporting
Generate the final HTML/PDF report.
```bash
python code/report.py
```

## Edge Case Handling

The pipeline includes robust handling for specific edge cases to ensure data integrity and statistical validity.

### Data Integrity (T053)
**Behavior**: The `code/preprocess.py` script performs strict validation on the `participant_id` column before writing cleaned data.
- **Null Check**: If any `participant_id` is null or missing, the script raises a `DataIntegrityError` and halts.
- **Duplicate Check**: If duplicate `participant_id` entries are found for the same experimental condition, the script raises a `DataIntegrityError` and halts.
- **Rationale**: Prevents silent data corruption that could invalidate design detection and subsequent analysis.

### Zero Variance in Cells (T055)
**Behavior**: During the sensitivity analysis sweep in `code/analysis.py` (Task T030), the script checks for zero variance in experimental condition cells.
- **Detection**: If any of the four experimental conditions has zero variance (all values identical), the script logs a `CriticalWarning`.
- **Action**: The specific condition with zero variance is excluded from the sensitivity sweep calculation to prevent NaN values or crashes.
- **Rationale**: Handles degenerate simulation cases where a condition might produce identical outcomes, ensuring the sensitivity analysis remains robust.

### Checksum Verification (T057)
**Behavior**: Before generating the final report in `code/report.py` (Task T033), the script verifies the integrity of input data files.
- **Verification**: It compares the SHA256 checksums of `cleaned_data.csv` and `model_results.json` against the records in `data/checksums.json`.
- **Failure**: If a mismatch is detected, the report generation fails immediately with a clear error message indicating which file has been tampered with or corrupted.
- **Rationale**: Enforces Constitution Principle III (Data Hygiene) by ensuring the final report is generated only from verified, untampered artifacts.

## Troubleshooting

- **Missing `logs/` directory**: Ensure the `logs` directory exists before running `analysis.py` or `report.py`.
- **Argument Errors**: Ensure all required CLI arguments (`--input`, `--output`, `--condition`, etc.) are provided as shown in the execution pipeline.
- **Missing Parameters**: Ensure `code/simulation_parameters.json` exists and contains `injected_interaction_effect` before running analysis tasks.