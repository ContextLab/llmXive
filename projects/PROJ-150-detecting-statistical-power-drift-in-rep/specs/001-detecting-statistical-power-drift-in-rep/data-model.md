# Data Model: Detecting Statistical Power Drift in Replicated Studies

## Entities

### ReplicationStudy
Represents a single replication event in the dataset.
- `study_id` (str): Unique identifier for the replication study.
- `year` (int): Calendar year of the replication.
- `field` (str): Discipline/field of the study (e.g., "Psychology", "Economics").
- `original_study_id` (str): ID of the original study being replicated.
- `effect_size` (float): Reported effect size (Cohen's *d* or log odds ratio).
- `sample_size` (int): Total sample size of the replication.
- `power_estimate` (float): Post-hoc power calculated using FR-001 formulas.
- `power_residual` (float): Residual from the pilot model (observed - predicted).

### DriftModel
Represents the output of the Linear Mixed-Effects Model.
- `slope_year` (float): Fixed effect coefficient for `year`.
- `se_slope` (float): Standard error of the slope.
- `p_value_parametric` (float): p-value from the likelihood-ratio test or Wald test.
- `random_effects_variance` (dict): Variance components for `field` and `original_study_id`.
- `model_formula` (str): The R-style formula used (e.g., "power_residual ~ year + (1|field) + (1|original_study_id)").

### SensitivityResult
Represents the outcome of the alpha threshold sweep.
- `alpha_value` (float): The significance threshold tested (e.g., 0.01, 0.05, 0.1).
- `drift_significant` (bool): Whether the drift slope was significant at this alpha.
- `p_value` (float): The p-value for the slope at this alpha.

### PermutationResult
Represents the output of the non-parametric permutation test.
- `iterations_run` (int): Number of permutations actually executed.
- `observed_statistic` (float): The observed slope from the real data.
- `null_distribution` (list[float]): The distribution of slopes from permuted data.
- `empirical_p_value` (float): Proportion of null statistics >= observed statistic.
- `status` (str): "complete" or "approximate" (if fallback triggered).

## File Formats

### Input: `data/raw/osf_replications.parquet`
- **Format**: Apache Parquet
- **Schema**:
  - `study_id`: string
  - `year`: int32
  - `field`: string
  - `original_study_id`: string
  - `effect_size`: float64
  - `sample_size`: int32

### Derived: `data/derived/cleaned_data.csv`
- **Format**: CSV
- **Schema**: Same as input, plus `power_estimate`. Rows with missing `year`, `effect_size`, or `sample_size` are removed.

### Derived: `data/derived/residuals.csv`
- **Format**: CSV
- **Schema**:
  - `study_id`: string
  - `year`: int32
  - `field`: string
  - `original_study_id`: string
  - `power_residual`: float64
  - `predicted_power`: float64

### Output: `results/lmm_final_summary.json`
- **Format**: JSON
- **Schema**:
  ```json
  {
    "slope_year": 0.0012,
    "se_slope": 0.0005,
    "p_value_parametric": 0.015,
    "random_effects_variance": {
      "field": 0.02,
      "original_study_id": 0.005
    },
    "model_formula": "power_residual ~ year + (1|field) + (1|original_study_id)"
  }
  ```

### Output: `results/permutation_pvalue.json`
- **Format**: JSON
- **Schema**:
  ```json
  {
    "iterations_run": 10000,
    "observed_statistic": -0.002,
    "empirical_p_value": 0.03,
    "status": "complete"
  }
  ```

### Output: `results/sensitivity_report.json`
- **Format**: JSON
- **Schema**:
  ```json
  {
    "sweep_results": [
      {"alpha_value": 0.01, "drift_significant": false, "p_value": 0.04},
      {"alpha_value": 0.05, "drift_significant": true, "p_value": 0.015},
      {"alpha_value": 0.1, "drift_significant": true, "p_value": 0.015}
    ]
  }
  ```

### Output: `results/aggregated_drift.json`
- **Format**: JSON
- **Schema**:
  ```json
  {
    "aggregated_slope": -0.0018,
    "aggregated_se": 0.0006,
    "heterogeneity_statistic": 12.5,
    "method": "DerSimonian-Laird"
  }
  ```

## Data Flow

1.  **Ingestion**: `data/raw/osf_replications.parquet` -> `code/preprocess.py` -> `data/derived/cleaned_data.csv` (with `power_estimate` column).
2.  **Residualization**: `data/derived/cleaned_data.csv` -> `code/models.py` -> `data/derived/residuals.csv` (with `power_residual` column).
3.  **Modeling**: `data/derived/residuals.csv` -> `code/models.py` -> `results/lmm_final_summary.json`.
4.  **Robustness**: `results/lmm_final_summary.json` + `data/derived/cleaned_data.csv` -> `code/robustness.py` -> `results/permutation_pvalue.json`, `results/sensitivity_report.json`, `results/aggregated_drift.json`.
5.  **Visualization**: `data/derived/residuals.csv` + `results/lmm_final_summary.json` -> `code/visualize.py` -> `results/power_drift_plot.png`.
