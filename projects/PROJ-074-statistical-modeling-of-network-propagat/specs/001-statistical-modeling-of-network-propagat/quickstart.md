# Quickstart: Bayesian Hierarchical Modeling of Misinformation Cascade Size

## Prerequisites

- Python 3.10+
- Linux environment (or WSL)
- Sufficient RAM available
- Valid cascade data (JSON format only for topology)

## Installation

1.  **Clone & Setup**:
    ```bash
    git checkout 001-bayesian-misinformation-cascade
    cd code/
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Environment**:
    ```bash
    python -c "import numpyro; print('NumPyro Ready')"
    ```

## Data Preparation

1.  **Prepare Cascade Data**:
    Ensure your data file (e.g., `data/raw/cascade_001.json`) contains:
    - `cascade_id` (string)
    - `nodes` (list of node IDs)
    - `edges` (list of [source, target] pairs)
    - `timestamps` (list of UTC ISO strings)
    - `platform_id` (optional, if multi-platform)

    **IMPORTANT**: JSON format required for cascade topology. CSV format is NOT supported for cascade files (see data-model.md).

    **Node Limit**: Cascades exceeding 2,000 nodes will be skipped to ensure CPU feasibility within 6-hour runtime budget.

    *Note: No verified public dataset exists for this specific schema in the provided list. Use local data or the synthetic generator in `code/feature_engineering/generate_synthetic.py` for testing.*

2.  **Place Data**:
    ```bash
    mkdir -p data/raw
    cp your_cascade_data.json data/raw/
    ```

## Running the Pipeline

Execute the main pipeline script:

```bash
bash code/pipeline/run_pipeline.sh --data data/raw/ --out results/
```

**Expected Outputs**:
- `results/features.csv`
- `results/model_trace.nc`
- `results/posterior_summary.csv`
- `results/manifest.json`
- `results/susceptibility_method.md`
- `results/collinearity_report.txt`

## Diagnostics & Validation

1.  **Collinearity Report**:
    ```bash
    bash code/pipeline/diagnostics.sh
    cat results/collinearity_report.txt
    ```
    Check for predictors with |r| > 0.8 (SC-005).

2.  **Susceptibility Documentation**:
    Review `results/susceptibility_method.md` for exact formula and thresholds used (FR-003 Clarification requirement).

3.  **Schema Validation**:
    ```bash
    pytest tests/contract/test_schemas.py
    ```

## Troubleshooting

- **RAM Error**: Reduce cascade size (limit is [deferred] nodes per cascade for CPU feasibility) or increase swap.
- **Convergence Warning**: Check `results/pipeline.log` for divergent transitions.
- **Missing Data**: Ensure all required columns (FR-001) exist in JSON file.
- **Format Error**: Cascade files must be JSON, not CSV (topology structure requires JSON).
- **Node Limit Warning**: Cascades > 2,000 nodes will be logged to `skipped_cascades.log` and excluded from analysis.