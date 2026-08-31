# Quick Start Guide

This guide provides detailed steps to execute the full pipeline for assessing the sensitivity of regression coefficients to dataset subset selection.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Access to the required datasets (configured in `test_config.yaml`)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

The pipeline uses a YAML configuration file to define datasets, random seeds, and sample size tiers.

1. **Verify or create your config file** (`test_config.yaml`):
 ```yaml
 datasets:
 - name: "Auto"
 source: "uci"
 target: "mpg"
 features: ["cylinders", "displacement", "horsepower", "weight", "acceleration"]
 random_seed: 42
 sample_size_tiers:
 - 0.10
 - 0.25
 - 0.50
 - 0.75
 - 0.90
 num_subsets_per_tier: 200
 ```

2. **Ensure directory structure exists**:
 Run the setup script to create necessary directories:
 ```bash
 python code/run_setup.py
 ```

## Pipeline Execution

The pipeline consists of three main stages: Ingestion & Profiling, Resampling & Stability Estimation, and Meta-Analysis.

### Step 1: Data Ingestion and Violation Profiling (User Story 1)

This stage downloads datasets, profiles OLS assumption violations, and saves results.

```bash
python -m src.cli --config test_config.yaml --stage ingestion
```

**Outputs**:
- `artifacts/profiles/dataset_profiles.json`: Contains Breusch-Pagan stats, Cook's Distance, and Condition Numbers.

### Step 2: Subset Resampling and Stability Estimation (User Story 2)

This stage generates random subsets, fits OLS models, and computes coefficient stability.

```bash
python -m src.cli --config test_config.yaml --stage resampling
```

**Outputs**:
- `artifacts/stability/subsets_*.json`: Indices of generated subsets.
- `artifacts/stability/coefficient_sd.json`: Empirical standard deviation of coefficients.
- `artifacts/convergence.log`: Convergence verification logs.

### Step 3: Interaction Analysis and Sensitivity Visualization (User Story 3)

This stage performs multiple regression with interaction terms and generates visualizations.

```bash
python -m src.cli --config test_config.yaml --stage analysis
```

**Outputs**:
- `artifacts/meta_analysis/interaction_model.json`: Regression model results.
- `artifacts/meta_analysis/stability_curves.png`: Visualization of stability vs. condition number.
- `artifacts/meta_analysis/final_report.md`: Comprehensive summary report.
- `artifacts/meta_analysis/sensitivity_sweep.json`: Variance in classification rates from sensitivity sweep.

## Running the Full Pipeline

To execute the entire pipeline in one command:

```bash
python -m src.cli --config test_config.yaml --stage full
```

Or simply:
```bash
python -m src.cli --config test_config.yaml
```

## Individual Script Execution

You can also run specific analysis scripts directly if you need to re-run parts of the pipeline:

- **Compute Coefficient SD**:
 ```bash
 python code/compute_coefficient_sd.py --input artifacts/stability/subsets_*.json --output artifacts/stability/coefficient_sd.json
 ```

- **Run Sensitivity Sweep**:
 ```bash
 python code/sensitivity_sweep.py --input artifacts/profiles/dataset_profiles.json --output artifacts/meta_analysis/sensitivity_sweep.json
 ```

- **Generate Final Report**:
 ```bash
 python code/generate_final_report.py --input artifacts/meta_analysis/interaction_model.json --output artifacts/meta_analysis/final_report.md
 ```

## Verification

After execution, verify the results:

1. Check `artifacts/run.log` for any warnings or errors.
2. Ensure all expected output files exist in `artifacts/`.
3. Run the verification script to check artifact hashes:
 ```bash
 python scripts/verify_hashes.py
 ```

## Troubleshooting

- **Memory Errors**: If you encounter memory issues, ensure your `test_config.yaml` uses appropriate subsampling or streaming settings. The pipeline is designed to handle large datasets via streaming, but extremely large datasets may require a GPU-enabled environment (as per plan.md).
- **Dataset Fetch Failures**: The pipeline will fail loudly if a dataset cannot be fetched. Check your internet connection and the dataset URLs in your configuration.
- **Singular Matrix Errors**: These are handled gracefully in the resampling stage, but may indicate high multicollinearity in your data. Check the `condition_number` in the dataset profiles.

## Next Steps

- Review the `final_report.md` for detailed findings.
- Explore the visualizations in `stability_curves.png`.
- Consider running the pipeline with different datasets or configurations to compare results.