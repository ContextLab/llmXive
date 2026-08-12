# Quickstart: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Prerequisites

- Python 3.11+
- Materials Project API key (set as `MP_API_KEY` environment variable)
- Git
- (Optional) Kaggle account for GPU offloading (not required for this plan)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-229-investigating-the-predictive-power-of-ma
    ```

2.  **Set up the virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set environment variables**:
    ```bash
    export MP_API_KEY="your-api-key"
    ```

## Running the Pipeline

### Step 1: Setup and Target Consistency Check

Run the setup script to create directories and fetch a sample for target consistency check:

```bash
python code/setup.py
python code/data/target_consistency_check.py
```

This will generate:
- `data/raw/mp_sample.csv`
- `data/results/target_decision.json`

### Step 2: Literature Data Acquisition

Run the literature data fetch script:

```bash
python code/data/fetch_literature_data.py
```

This will generate:
- `data/external/literature_pcms.csv` (or fallback set)
- `data/results/mapping_log.json`

### Step 3: Data Retrieval and Preprocessing

Run the data retrieval script to fetch MP data and compute features:

```bash
python code/data/retrieve_mp_data.py
python code/data/compute_features.py
```

This will generate:
- `data/raw/mp_raw.csv`
- `data/processed/features.csv`
- `data/processed/targets.csv`

### Step 4: Model Training

Run the model training script to train baseline and interpretable models:

```bash
python code/models/train_models.py
```

This will generate:
- `data/results/model_metrics.json`
- `data/results/symbolic_formula.json` (or `lasso_formula.json`)
- `data/results/feature_importance.json`

### Step 5: Validation and Sensitivity Analysis

Run the validation script to test derived rules on literature PCMs and perform sensitivity analysis:

```bash
python code/utils/validate_and_sweep.py
```

This will generate:
- `data/results/validation_results.json`
- `data/results/sensitivity_analysis.json`
- `data/results/collinearity_report.json`
- `data/results/multicollinearity_test.json`

### Step 6: Feasibility and Report Generation

Run the feasibility check and report generation:

```bash
python code/utils/feasibility_check.py
python code/main.py --generate-report
```

This will produce:
- `data/results/feasibility_report.json`
- A comprehensive report with all findings, including associational framing and methodological notes.

## Troubleshooting

- **API Rate Limits**: If the MP API returns rate limit errors, the script will automatically pause and retry. If it fails after multiple retries, it will log the error and exit.
- **Missing Data**: If latent heat data is missing for most compounds, the system will fall back to using melting point and heat capacity as predictors and flag the limitation.
- **Symbolic Regression Failure**: If PySR fails to converge, the system will default to Lasso regression and flag the limitation.
- **Literature Data Unavailable**: If the literature data source is inaccessible, the system will use a pre-defined fallback set and flag the limitation.

## Notes

- All random seeds are pinned in `config.yaml` for reproducibility.
- The pipeline is designed to run on a CPU-only environment. If GPU acceleration is required for future extensions, the code can be offloaded to Kaggle.
- Always check the `data/results/` directory for the latest outputs.