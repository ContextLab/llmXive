# Quickstart Guide: The Influence of Simulated Social Status on Risk-Taking Behavior

This guide details the execution of the automated research pipeline for **PROJ-423**.
It covers environment setup, data generation, analysis, and report generation.

## Prerequisites

- Python 3.9+
- `pip` package manager
- Access to the project root directory

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv.venv
source.venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Simulation Parameters

Ensure `code/simulation_parameters.json` exists. This file acts as the Single Source of Truth for effect sizes, sample sizes, and seeds.

```bash
# Verify parameters exist
cat code/simulation_parameters.json
```

## 3. Data Generation

Generate the synthetic datasets for both the Effect and Null conditions.

```bash
# Generate Effect Condition Data
python code/simulate.py --condition effect --seed 42 --n 500

# Generate Null Condition Data
python code/simulate.py --condition null --seed 42 --n 500
```

*Note: If `code/simulation_parameters.json` is missing, the script will fail. Ensure Phase 0 tasks (T000i-T000h) are complete.*

## 4. Preprocessing

Clean and prepare the raw data for analysis. This step handles binning, missing values, and data integrity checks.

```bash
# Process Effect Condition
python code/preprocess.py --input data/raw/simulated_data_effect.csv --output data/processed/cleaned_data_effect.csv --structure-output data/processed/structure_config_effect.json

# Process Null Condition
python code/preprocess.py --input data/raw/simulated_data_null.csv --output data/processed/cleaned_data_null.csv --structure-output data/processed/structure_config_null.json
```

## 5. Analysis

Run the adaptive regression analysis, calculating VIFs, confidence intervals, and parameter recovery metrics.

```bash
# Run Analysis on Effect Condition
python code/analysis.py --input data/processed/cleaned_data_effect.csv --config data/processed/structure_config_effect.json --output data/processed/model_output_effect.json

# Run Analysis on Null Condition
python code/analysis.py --input data/processed/cleaned_data_null.csv --config data/processed/structure_config_null.json --output data/processed/model_output_null.json
```

## 6. Reporting

Generate the final HTML report and forest plot.

```bash
python code/report.py --effect-output data/processed/model_output_effect.json --null-output data/processed/model_output_null.json --output reports/analysis_report.html
```

---

## Edge Case Handling

This pipeline includes robust mechanisms to handle data integrity issues, degenerate conditions, and file tampering. The following sections detail the specific behaviors of these edge case handlers.

### T053: Data Integrity Validation (Participant ID Uniqueness)

**Location**: `code/preprocess.py` (Validation Step)

**Behavior**:
Before writing `cleaned_data.csv`, the pipeline strictly validates the `participant_id` column.
1. **Null Check**: It verifies that no `participant_id` is null or empty.
2. **Duplicate Check**: It verifies that no `participant_id` appears more than once within the same experimental condition.

**Failure Mode**:
If duplicates or nulls are detected, the script raises a `DataIntegrityError` and halts execution immediately with exit code 1. No partial data is written.
*Error Message Example*: `DataIntegrityError: Duplicate participant_id 'P123' found in condition 'High-Risky'. Data integrity violated.`

**Rationale**:
Prevents silent data corruption that could invalidate the design detection logic (T021b) and downstream statistical modeling.

### T055: Zero Variance in Cells (Sensitivity Analysis)

**Location**: `code/analysis.py` (Sensitivity Sweep)

**Behavior**:
During the sensitivity analysis sweep (T030), the pipeline calculates cell means for the four experimental conditions.
1. **Variance Check**: For each condition, it checks if the standard deviation of the `risk_taking_score` is exactly zero.
2. **Degenerate Handling**: If a condition has zero variance (all values identical), the script logs a `CriticalWarning` and **excludes that specific condition** from the sensitivity sweep calculation.

**Failure Mode**:
The pipeline does **not** crash or produce NaN values. Instead, it proceeds with the remaining valid conditions and logs the exclusion.
*Warning Message Example*: `CriticalWarning: Condition 'Low-Conservative' has zero variance. Excluding from sensitivity sweep to prevent NaN calculation.`

**Rationale**:
Handles edge cases where the simulation or data generation produces degenerate conditions, ensuring the sensitivity analysis remains robust and mathematically valid.

### T057: Checksum Verification (Report Reproducibility)

**Location**: `code/report.py` (Pre-Generation Step)

**Behavior**:
Before generating the final report, the pipeline validates the integrity of all input artifacts against the master checksum registry (`data/checksums.json`).
1. **File Hashing**: It calculates the SHA256 hash of `cleaned_data.csv` and `model_results.json`.
2. **Comparison**: It compares these hashes against the values stored in `data/checksums.json` recorded during the preprocessing/analysis phases.

**Failure Mode**:
If a mismatch is detected, the report generation **fails immediately** with a clear error message indicating which file has been tampered with or modified. No report is generated.
*Error Message Example*: `File Integrity Error: Mismatch detected for 'cleaned_data_effect.csv'. Expected checksum 'abc123...', found 'def456...'. Report generation aborted.`

**Rationale**:
Enforces Constitution Principle III (Data Hygiene) by ensuring the final report is generated from verified, untampered artifacts, preventing the dissemination of results based on modified data.