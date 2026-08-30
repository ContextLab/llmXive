# Data Model: Detecting Statistical Power Drift in Replicated Studies

## Entity Definitions

### 1. ReplicationStudy
Represents a single replication event after cleaning, power calculation, and residualization.
- `study_id` (str): Unique identifier (from source).
- `year` (int): Calendar year of the replication.
- `field` (str): Discipline (e.g., "Psychology", "Economics").
- `original_study_id` (str): ID of the original study being replicated.
- `effect_size` (float): Reported effect size (Cohen's *d* or log-odds).
- `sample_size` (int): Total sample size of the replication.
- `power_estimate` (float): Calculated post-hoc power (0.0 to 1.0).
- `residual_power` (float): Residual of `power_estimate` after regressing on `effect_size` and `sample_size`. This is the primary outcome for the LMM.
- `exclusion_reason` (str | null): Reason for exclusion if missing data (e.g., "missing_sample_size").

### 2. DriftModelResults
Aggregated output from the LMM and validation tests.
- `slope_year` (float): Estimated drift per year (on residual power).
- `se_slope` (float): Standard error of the slope.
- `p_value_parametric` (float): LRT p-value for `year`.
- `p_value_permutation` (float): Empirical p-value from permutation test (year shuffle).
- `random_effects_variance` (dict): Variance components for `field`.
- `iterations_run` (int): Number of permutations actually executed.
- `is_approximate` (bool): True if iterations were reduced due to timeout.

### 3. SensitivityResult
Output from the alpha-sweep analysis.
- `alpha_value` (float): The alpha threshold used.
- `drift_significant` (bool): Was the drift slope significant at this alpha?
- `slope_year` (float): Slope estimate at this alpha.

### 4. AggregatedDrift
Output from the cross-field aggregation.
- `aggregated_slope` (float): Combined drift slope across fields.
- `aggregated_se` (float): Standard error of the aggregated slope.
- `heterogeneity_i2` (float): I-squared statistic for heterogeneity.
- `method` (str): "DerSimonian-Laird".

## Data Flow

1. **Raw Input**: `data/raw/*.parquet` or `*.csv`.
   - Columns: `year`, `effect_size`, `sample_size`, `field`, `original_study_id`, ...
2. **Derived Input**: `data/derived/cleaned_data.csv`.
   - Filtered rows (no missing critical vars).
   - Added `power_estimate`.
3. **Residualization**: `data/derived/power_estimates.csv`.
   - Added `residual_power` (residuals of `power_estimate ~ effect_size + sample_size`).
4. **Output**: `results/*.json`.
   - `lmm_final_summary.json`: DriftModelResults.
   - `permutation_pvalue.json`: Permutation stats.
   - `sensitivity_report.json`: List of SensitivityResult.
   - `aggregated_drift.json`: AggregatedDrift.
5. **Visualization**: `results/plots/residual_power_vs_year.png`.

## Data Hygiene Rules

- **Immutability**: Raw files in `data/raw/` are never modified.
- **Checksums**: Every file in `data/raw/` and `data/derived/` is checksummed (SHA-256) and recorded in `state/`.
- **Missing Data**: Rows with missing `sample_size` or `effect_size` are moved to a "dropped" log and excluded from analysis.
- **Outliers**: Extreme effect sizes (e.g., |d| > 10) are capped or flagged, but not removed unless they cause model convergence failure.
- **Stratified Sampling**: If sampling is required, it is performed using `stratify=[year, field]` to preserve temporal and disciplinary distribution.