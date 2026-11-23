# Data Model: Detecting Statistical Power Drift in Replicated Studies

## Entity Definitions

### ReplicationStudy
Represents a single replication event derived from the raw dataset.
- `study_id`: string (unique identifier)
- `year`: integer (publication year)
- `field`: string (discipline, e.g., "Psychology", "Economics")
- `original_study_id`: string (identifier of the study being replicated)
- `effect_size`: float (Cohen's *d* or log odds ratio)
- `sample_size`: integer (total N)
- `power_estimate`: float (calculated post-hoc power, 0.0 to 1.0)
- `residual_power`: float (residual from the preliminary regression of Power on EffectSize and SampleSize)

### DriftModel
Represents the output of the statistical modeling phase.
- `slope_year`: float (estimated drift per year)
- `se_slope`: float (standard error of the slope)
- `p_value_parametric`: float (from LRT)
- `p_value_permutation`: float (from 10k shuffles)
- `random_effects_variance`: dict (variance components for `field` and `original_study_id`)
- `model_converged`: boolean

### SensitivityResult
Represents the outcome of the alpha-threshold sweep.
- `alpha_value`: float (threshold tested)
- `drift_significant`: boolean (is p < alpha?)
- `false_positive_rate`: float (estimated rate under null at this alpha, derived from permutation null distribution)
- `robust`: boolean (is significance stable across the sweep?)

## Data Flow

1. **Raw Input**: `data/raw/osf_data.parquet` (or CSVs).
2. **Preprocessing**:
   - Filter: Remove rows with missing `effect_size` or `sample_size`.
   - Calculate: `power_estimate` for each row.
   - Output: `data/derived/power_estimates.csv`.
3. **Modeling**:
   - Fit preliminary model `Power ~ EffectSize + SampleSize` to get residuals.
   - Fit LMM/GLMM on `residual_power ~ Year + (1|field)`.
   - Extract residuals.
   - Output: `data/derived/residuals.csv` (contains `year`, `residual_power`).
4. **Robustness**:
   - Run permutation tests on `residuals.csv` (Year shuffle).
   - Run sensitivity sweep (calculate FPR from null distribution).
   - Run Input Permutation (shuffle EffectSize/SampleSize).
   - Output: `results/robustness_summary.json`.
5. **Visualization**:
   - Plot `residuals.csv` with fitted line.
   - Output: `results/power_drift_scatter.png`.
6. **Validation**:
   - `validate_source.py` writes `data/derived/schema_validation.json` (T007).

## Schema Constraints

- `year`: Must be between 1900 and current year.
- `sample_size`: Must be > 0.
- `effect_size`: No hard bounds (can be negative), but extreme outliers (> 10 or < -10) will be flagged and capped.
- `power_estimate`: Must be in [0.0, 1.0].