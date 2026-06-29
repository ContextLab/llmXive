# Quick Start Guide

This document provides step-by-step instructions for running the Bayesian
hierarchical modeling pipeline for misinformation cascade analysis.

## Prerequisites

1. Python 3.10 or higher
2. All dependencies installed from `requirements.txt`
3. Raw cascade data in JSON edge-list format under `data/raw/`

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: install development tools
pip install pytest ruff black
```

## Pipeline Configuration

### Model Specification

The Bayesian model configuration is defined in `model_spec.yaml`. Before
running the pipeline, review this file to understand:
- Prior distributions for all parameters
- Hyperparameter settings for the negative binomial likelihood
- Random effect structure (user_id, message_id, platform_id)
- HMC/NUTS sampling configuration

**Important**: Modify `model_spec.yaml` before pipeline execution to adjust
priors or hyperparameters. Changes to this file affect all downstream results.

### Data Requirements

Place JSON cascade files in `data/raw/`. Each file must contain:
- `node_id`: Unique node identifier
- `timestamp`: Event timestamp (normalized to UTC)
- `cascade_id`: Cascade identifier
- `historical_degree`: Pre-cascade node degree
- `historical_shares`: User's historical sharing count
- `user_id`, `message_id`, `platform_id`: Random effect groupings

See `contracts/` directory for JSON schema validation rules.

## Running the Pipeline

```bash
# Execute the full pipeline
./run_pipeline.sh --data data/raw/ --out results/

# The pipeline will:
# 1. Load and validate cascade data (T021a)
# 2. Extract network and user features (T021b)
# 3. Fit the Bayesian hierarchical model (T021c)
# 4. Generate posterior summaries (T021d)
```

## Expected Outputs

After successful execution, the following files will be created:

| File | Description |
|------|-------------|
| `results/features.csv` | Feature matrix with all predictors |
| `results/model_trace.nc` | Posterior samples in NetCDF format |
| `results/posterior_summary.csv` | Posterior mean, SD, credible intervals |
| `pipeline.log` | Detailed execution log |
| `skipped_cascades.log` | IDs of cascades exceeding node limit |

## Validation

Run contract tests to verify output schemas:

```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **Memory errors**: Ensure `OMP_NUM_THREADS=2` is set in `run_pipeline.sh`
- **Sampling divergence**: Check `model_spec.yaml` for appropriate priors
- **Schema validation failures**: Verify input JSON files match contracts/ schemas
- **Node limit exceeded**: Oversized cascades are logged to `skipped_cascades.log`

## Next Steps

After the pipeline completes, review:
1. `posterior_summary.csv` for effect estimates and credible intervals
2. `cv_metrics.json` (after User Story 2) for predictive performance
3. `collinearity_report.txt` (after User Story 3) for predictor diagnostics