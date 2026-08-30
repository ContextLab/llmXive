# Quickstart: Detecting Statistical Power Drift in Replicated Studies

## Prerequisites

- Python 3.11+
- pip
- Access to HuggingFace (public datasets, no token required for these URLs)

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of four sequential steps. Run them in order:

### Step 1: Download Data
Fetches the verified OSF datasets.
```bash
python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/download_data.py
```
*Output*: `data/raw/osf_replication.parquet` (or CSV).

### Step 2: Preprocess & Calculate Power
Cleans data, handles missing values, and calculates post-hoc power.
```bash
python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/preprocess.py
```
*Output*: `data/derived/cleaned_data.csv`, `logs/preprocess.log`.

### Step 3: Fit Model & Run Robustness
Fits the LMM, runs permutation test, and sensitivity analysis.
```bash
python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/model_fit.py
python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/robustness.py
```
*Output*: `results/lmm_final_summary.json`, `results/permutation_pvalue.json`, `results/sensitivity_report.json`.

### Step 4: Visualize
Generates the residual power plot.
```bash
python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/visualize.py
```
*Output*: `results/plots/residual_power_vs_year.png`.

## Verifying Results

1. Check `results/lmm_final_summary.json` for the `slope_year` and `p_value_parametric`.
2. Compare `p_value_parametric` with `p_value_permutation` in `results/permutation_pvalue.json` for consistency.
3. Review `results/sensitivity_report.json` to ensure drift significance is stable across alpha thresholds.

## Troubleshooting

- **Missing Columns**: If the download fails to find `sample_size`, check the `logs/preprocess.log` for "Dataset schema mismatch" warnings. The script will halt if required columns are missing.
- **Convergence Failure**: If the LMM fails to converge, the script will attempt to simplify the random effects (remove `original_study_id`) and log a warning.
- **Memory Error**: If the permutation test runs out of memory, the script will automatically reduce iterations to [deferred] and flag the result as "approximate" in the output JSON.
