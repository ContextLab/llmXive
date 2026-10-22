# Quickstart: Running the Doubly Robust Simulation Study

The following steps assume you have a fresh GitHub Actions runner (or a local Linux environment with Python 3.11).

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Environment
```bash
python -c "import numpy, pandas, statsmodels, causalml; print('All imports OK')"
```

## 3. Prepare a Configuration File
Create `config.yaml` (example below). Adjust `seed`, `sample_size`, and model families as desired.

```yaml
seed: 12345
sample_size: 1000
dgp_params:
  beta: [0.2, -0.1, 0.05, 0.0, 0.0]   # logistic coefficients for X1‑X5
  sigma: 1.0
outcome_model: nonlinear_correct          # options: nonlinear_correct, quadratic, interaction_omitted
propensity_model: logistic_misspecified   # options: logistic_correct, logistic_misspecified, logistic_interaction_heavy
```

## 4. Run the Full Grid (CPU‑only)
```bash
python -m src.cli --config config.yaml \
    --grid-outcome nonlinear_correct quadratic interaction_omitted \
    --grid-propensity logistic_correct logistic_misspecified logistic_interaction_heavy \
    --sample-sizes 500 1000 2000 \
    --replications 1000
```
- The command streams results to `data/interim/` and writes aggregated metrics to `data/processed/`.
- Progress is logged to `logs/run_{timestamp}.log`.

## 5. Post‑Processing
Generate the meta‑regression table and heatmap visualizations:

```bash
python -m src.analysis.meta_regression --aggregated data/processed/aggregated_metrics.parquet
python -m src.analysis.visualizations --aggregated data/processed/aggregated_metrics.parquet --output-dir figures/
```

Outputs:
- `figures/bias_heatmap.png`
- `figures/interaction_coeff.png`
- `data/processed/meta_regression_summary.csv`

## 6. Validate Contracts (optional)
```bash
pytest tests/contract/test_estimation_result_schema.py
```
All generated `EstimationResult` records must satisfy `contracts/estimation_result.schema.yaml`.

## 7. Clean Up (optional)
```bash
rm -rf data/raw/* data/interim/* figures/*
```

You now have a reproducible set of bias, coverage, and interaction analyses that satisfy all FRs and SCs outlined in the specification.

---

