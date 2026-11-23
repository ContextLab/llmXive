# Quick Start Guide: Sensory Deprivation Simulation Study

This guide provides instructions for setting up and running the full simulation pipeline for the study on the effect of sensory deprivation on dream recall and bizarreness.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- A Unix-like environment (Linux/macOS) or WSL on Windows

## 1. Project Setup

Navigate to the project root directory:

```bash
cd projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre
```

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r code/requirements.txt
```

## 2. Configuration Verification

Ensure the simulation protocol is correctly defined in `data/protocols/protocol.yaml`. This file contains the parameters for the three threshold scenarios (strict, moderate, partial) and the effect sizes to be simulated.

```bash
cat data/protocols/protocol.yaml
```

Expected key parameters:
- `N=200` (participants per scenario)
- Effect sizes: `d=0.5` (positive), `d=0.0` (null), `d=-0.2` (negative)
- Threshold labels matching FR-004 requirements.

## 3. Running the Pipeline

The pipeline consists of three main stages: Data Generation, Analysis, and Reporting.

### Step 1: Generate Synthetic Data

Run the data generation script to create the synthetic datasets based on the protocol. This will generate datasets for all three ground-truth effect sizes and save them to `data/synthetic/`.

```bash
python code/generate_data.py
```

Then, process the data to derive the condition columns based on the thresholds:

```bash
python code/process_data.py
```

This produces three processed datasets in `data/processed/`:
- `data_threshold_strict.csv`
- `data_threshold_moderate.csv`
- `data_threshold_partial.csv`

### Step 2: Run Statistical Analysis

Execute the modeling pipeline to fit the logistic and linear mixed-effects models (and the ordinal approximation) on the processed data.

```bash
python code/models.py
```

This step:
- Fits logistic mixed-effects models for dream recall.
- Fits linear mixed-effects models for dream bizarreness.
- Runs the ordinal approximation validation (T023).
- Saves results to `results/models/`.

### Step 3: Sensitivity and Robustness Analysis

Run the sensitivity analysis to sweep thresholds and perform bootstrap validation.

```bash
python code/sensitivity.py
```

This step:
- Sweeps across the three threshold datasets.
- Performs dynamic bootstrap resampling (up to 5,000 iterations).
- Compares parametric vs. bootstrap confidence intervals.
- Saves sensitivity results to `results/models/`.

### Step 4: Generate Final Report

Compile all results into a comprehensive HTML and JSON report.

```bash
python code/report.py
```

The final report will be available at:
- `results/reports/simulation_report.html`
- `results/reports/simulation_report.json`

### Step 5: Timing Verification (Optional)

To verify the pipeline meets the 6-hour execution constraint on a standard runner:

```bash
python code/run_pipeline_timing.py
```

This generates `results/timing_log.json` with the total duration.

## 4. Validation

### Schema Validation

Ensure all outputs conform to the defined contracts:

```bash
python -m pytest tests/contract/ -v
```

### Unit Tests

Run unit tests for data ingestion and model fitting:

```bash
python -m pytest tests/unit/ -v
```

## 5. Output Artifacts

Upon successful completion, the following artifacts will be present:

- **Data**:
 - `data/synthetic/`: Raw generated datasets.
 - `data/processed/`: Processed datasets with condition columns for each threshold.
- **Models**:
 - `results/models/`: JSON files containing model coefficients, standard errors, and p-values.
- **Reports**:
 - `results/reports/simulation_report.html`: Human-readable analysis summary.
 - `results/reports/simulation_report.json`: Machine-readable results.
- **Logs**:
 - `results/timing_log.json`: Execution time metrics.

## Notes

- **Simulation-Based**: All data is synthetic. The study is designed to validate the analysis pipeline against known ground truths (d=0.5, d=0.0, d=-0.2).
- **Associational Findings**: Results are framed as associational, not causal.
- **Reproducibility**: All random seeds are pinned in `code/generate_data.py` to ensure reproducibility.
- **Ordinal Approximation**: Due to library limitations, a fixed-effects ordered model is used as an approximation for the mixed-effects ordinal model, validated against the synthetic ground truth.