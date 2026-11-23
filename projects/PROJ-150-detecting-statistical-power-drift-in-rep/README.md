# Detecting Statistical Power Drift in Replicated Studies

This project implements an automated pipeline to detect temporal drift in statistical power across replicated scientific studies, using data from the OSF Reproducibility Project.

## Prerequisites

- Python 3.8+
- `pip` for dependency management

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-150-detecting-statistical-power-drift-in-rep
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 pip install -r requirements.txt
 ```

## Execution Instructions

The pipeline is executed sequentially via the following steps. Ensure all steps complete successfully before proceeding to the next.

### Step 1: Data Download
Fetches the raw dataset from the OSF repository via Hugging Face Datasets.
```bash
python code/download_data.py
```
**Output**: `data/raw/data.csv`

### Step 2: Schema Validation
Validates the presence of required columns (`year`, `effect_size`, `sample_size`, `field`).
```bash
python code/validate_schema.py
```
**Output**: `data/derived/schema_validation.json`

### Step 3: Preprocessing & Power Calculation
Cleans data, handles missing values, and calculates statistical power estimates.
```bash
python code/preprocess.py
```
**Output**: `data/derived/cleaned_data.csv`, `data/derived/grouping_validation.json`

### Step 4: Model Fitting (LMM)
Fits a Linear Mixed-Effects Model with crossed random effects to test for temporal drift.
```bash
python code/model_fit.py
```
**Output**: `results/lmm_final_summary.json`, `data/derived/residuals.csv`

### Step 5: Visualization
Generates a scatter plot of residual power vs. year with confidence intervals.
```bash
python code/visualize.py
```
**Output**: `results/power_drift_scatter.png`

### Step 6: Robustness Checks
Performs permutation tests and sensitivity analysis.
```bash
python code/robustness.py
```
**Output**: `results/permutation_pvalue.json`, `results/input_permutation.json`, `results/sensitivity_report.json`

### Step 7: Cross-Field Aggregation
Aggregates drift statistics across fields using DerSimonian-Laird method.
```bash
python code/aggregate.py
```
**Output**: `results/aggregated_drift.json`

### Step 8: Final Report
Generates a comprehensive markdown report summarizing all findings.
```bash
python code/generate_final_report.py
```
**Output**: `results/final_report.md`

## Expected Outputs

Upon successful execution, the following artifacts will be generated:

- **Raw Data**: `data/raw/data.csv`
- **Derived Data**:
 - `data/derived/cleaned_data.csv`
 - `data/derived/residuals.csv`
 - `data/derived/grouping_validation.json`
- **Results**:
 - `results/lmm_final_summary.json` (Model coefficients and LRT stats)
 - `results/power_drift_scatter.png` (Visualization)
 - `results/permutation_pvalue.json` (Permutation test results)
 - `results/aggregated_drift.json` (Cross-field aggregation)
 - `results/final_report.md` (Executive summary)

## Troubleshooting

- **Missing Data**: If `data/raw/data.csv` is missing, ensure `code/download_data.py` ran successfully and network access to Hugging Face is available.
- **Schema Errors**: If `data/derived/cleaned_data.csv` is empty, check `data/derived/schema_validation.json` for missing columns.
- **Model Convergence**: Warnings about convergence in `code/model_fit.py` logs are non-fatal but should be reviewed if results seem unstable.

## License

This project is part of the llmXive automated science pipeline.