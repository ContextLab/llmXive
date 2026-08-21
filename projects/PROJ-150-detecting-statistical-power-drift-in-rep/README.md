# Detecting Statistical Power Drift in Replicated Studies

**Project ID**: PROJ-150-detecting-statistical-power-drift-in-rep

## Overview

This project implements an automated pipeline to detect and quantify statistical power drift over time in replicated studies. It analyzes the relationship between study year and post-hoc power estimates using Linear Mixed-Effects Models (LMM) and validates findings through robustness checks (permutation tests, sensitivity analysis) and cross-field aggregation.

The pipeline is designed to run on CPU-only environments within a 6-hour window, handling large datasets via streaming where necessary.

## Key Features

- **Data Ingestion**: Downloads and validates the OSF Reproducibility Project dataset.
- **Preprocessing**: Cleans data, handles missing values, and validates grouping variables.
- **Power Estimation**: Calculates post-hoc power estimates based on effect sizes and sample sizes.
- **Drift Analysis**: Fits a Linear Mixed-Effects Model (LMM) to test for temporal decline in power (`power_residual ~ year + (1|field) + (1|original_study_id)`).
- **Robustness Checks**:
 - Non-parametric permutation tests (shuffling year labels).
 - Sensitivity analysis across alpha thresholds.
- **Cross-Field Aggregation**: Combines drift estimates across fields using DerSimonian-Laird weighting.
- **Visualization**: Generates scatter plots of residual power vs. year and null distribution comparisons.

## Directory Structure

```text
PROJ-150-detecting-statistical-power-drift-in-rep/
├── code/ # Python implementation modules
│ ├── download.py # Data fetching and validation
│ ├── preprocess.py # Data cleaning and validation
│ ├── power_calc.py # Power calculation logic
│ ├── models.py # LMM fitting and pilot OLS
│ ├── robustness.py # Permutation tests and aggregation
│ ├── visualize.py # Plot generation
│ ├── main.py # Pipeline orchestrator
│ └── timing.py # Execution time instrumentation
├── data/
│ ├── raw/ # Downloaded raw data (e.g., data.csv)
│ └── derived/ # Cleaned data, residuals, intermediate models
├── results/ # Final outputs (JSON summaries, plots)
├── state/ # Project state tracking (SHA-256 hashes)
├── tests/ # Unit and integration tests
├── docs/ # Documentation (methodology, etc.)
└── README.md # This file
```

## Prerequisites

- Python 3.8+
- pip (package manager)
- Access to the internet (for initial dataset download)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

3. Ensure the `data/raw` directory is writable.

## Usage

### Running the Full Pipeline

Execute the main pipeline script to run the entire workflow from data download to final report generation:

```bash
python code/main.py
```

This will:
1. Download and validate the dataset.
2. Preprocess data and calculate power estimates.
3. Fit the LMM and extract drift metrics.
4. Run robustness checks (permutation, sensitivity).
5. Generate visualizations and final JSON reports.
6. Update the project state file with artifact hashes.

### Running with Timing Instrumentation

To generate a timing report (`results/timing_report.json`) to verify the 6-hour execution limit:

```bash
python code/timing.py
```

### Running on a Subset (Testing/Debugging)

For faster execution during development, run the pipeline on a static subset of the data:

```bash
python code/run_subset_pipeline.py
```

### Individual Modules

You can also run specific modules independently:

- **Download & Validate**:
 ```bash
 python code/download.py
 ```
- **Preprocess**:
 ```bash
 python code/preprocess.py
 ```
- **Fit Models**:
 ```bash
 python code/models.py
 ```
- **Robustness Checks**:
 ```bash
 python code/robustness.py
 ```
- **Visualize**:
 ```bash
 python code/visualize.py
 ```

## Output Artifacts

Upon successful completion, the following artifacts will be generated:

- `data/derived/cleaned_data.csv`: Filtered and validated dataset.
- `data/derived/residuals.csv`: Residualized power estimates.
- `results/lmm_final_summary.json`: Primary drift metrics (slope, SE, CI, LRT p-value).
- `results/permutation_pvalue.json`: Empirical p-value from permutation test.
- `results/sensitivity_report.json`: Drift significance across alpha thresholds.
- `results/aggregated_drift.json`: Cross-field aggregated drift estimate.
- `results/power_drift_scatter.png`: Visualization of drift trend.
- `results/timing_report.json`: Execution duration and stage timings.

## Methodology

The core analysis uses a **Linear Mixed-Effects Model (LMM)** to test the hypothesis that statistical power drifts over time.

1. **Power Calculation**: Post-hoc power is estimated using Cohen's d and sample sizes.
2. **Residualization**: A pilot OLS model (`power_est ~ effect_size + sample_size`) is fitted to capture deterministic relationships. The residuals (`power_residual`) serve as the outcome variable to isolate temporal effects.
3. **LMM Fitting**: The primary model is:
 `power_residual ~ year + (1|field) + (1|original_study_id)`
 - **Fixed Effect**: `year` (tests for drift).
 - **Random Effects**: `field` and `original_study_id` (accounts for hierarchical structure).
4. **Robustness**:
 - **Permutation**: Shuffling `year` labels to generate a null distribution.
 - **Sensitivity**: Sweeping alpha thresholds to check result stability.
 - **Aggregation**: Combining field-specific slopes using inverse-variance weighting.

## Testing

Run the test suite to verify functionality:

```bash
pytest tests/ -v
```

## License

This project is part of the llmXive automated science pipeline.