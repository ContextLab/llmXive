# Data Model: Evaluating Calibration of Probabilistic Weather Forecasts

## Overview
Defines the entities, schemas, and data flow for the calibration pipeline. All files conform to the JSON‑Schema contracts in `contracts/`.

## Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Forecast Record** | Single ensemble forecast instance | `grid_id` (str), `lead_time` (int), `forecast_date` (datetime), `probability_value` (float 0‑1) **or** `precip_prob`, optional `raw_ensemble_mean`, optional `ensemble_members` |
| **Observation Record** | Ground‑truth event | `grid_id` (str), `observation_date` (datetime), `event_occurred` (bool), optional `event_value`, `variable` (str) |
| **Aligned Record** | Joined forecast & observation | All fields from Forecast + `event_occurred`, `observation_date`, `variable` |
| **Calibration Metric** | Computed statistic | `metric_name`, `lead_time`, `variable`, `method`, `value`, optional `confidence_interval`, `sample_size` |
| **Recalibrator Model** | Fitted post‑processing function | `method_type`, `lead_time`, `variable`, `parameters` (knots or coefficients), `training_sample_size`, `convergence_status` (for Bayesian), `fallback_reason` |
| **Statistical Test Result** | DM or Bootstrap outcome | `comparison`, `lead_time`, `variable`, `test_method`, `p_value`, `alternative`, `normality_test_p` |
| **Prior Sensitivity Record** | Prior‑impact log | `prior_type`, `prior_parameters`, `metric_name`, `lead_time`, `variable`, `value`, `difference_from_flat` |

## Data Flow
1. **Raw download** → `data/raw/` (immutable).  
2. **Verification** → checksum logged; Data Availability Gate applied.  
3. **Alignment** (`analysis/baseline/align.py`) → `data/aligned.parquet`.  
4. **Baseline metrics** (`metrics.py`) → `results/results_baseline.csv`.  
5. **Isotonic model** (`isotonic/train.py`) → `contracts/forecast.schema.yaml` entry + `results_isotonic.csv`.  
6. **Bayesian model** (`bayesian/model.py`) → `contracts/recalibrator_model.schema.yaml` entry + `results_bayesian.csv` *or* `results_fallback.csv`.  
7. **Statistical tests** (`comparison/diebold_mariano.py`) → `contracts/metrics.schema.yaml` section.  
8. **Final aggregation** (`comparison/summary.py`) → `results/` directory and `contracts/output.schema.yaml`.

## File Formats
- **Parquet**: Raw and aligned records (efficient columnar storage).  
- **CSV**: Metric tables (`results_*.csv`).  
- **PNG**: Reliability diagrams, PIT histograms.  
- **JSON**: Convergence diagnostics, logs.  
- **YAML**: Contract schemas (see `contracts/`).

## Constraints
- No in‑place modification of raw data (Principle III).  
- All derived files receive a content hash recorded in the project state.  
- Streaming mode (`datasets.load_dataset(..., streaming=True)`) used when dataset size exceeds RAM.  
- Fixed random seed (`np.random.seed(42)`, `torch.manual_seed(42)`) for reproducibility (Principle I).

---
