# Data Model: Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

## Entity Definitions

### 1. SurveyDataset
Represents the raw or pre‑processed survey data.

- `id`: Unique identifier (string).  
- `source`: Source URL (string).  
- `weight_col`: Name of the sampling weight column (string).  
- `psu_col`: Name of the Primary Sampling Unit column (string).  
- `strata_col`: Name of the stratification column (string).  
- `target_col`: Name of the variable to analyze (string).  
- `missingness_rate`: Float (0.0 – 1.0).  
- `psu_cluster_warning`: Boolean – **true** if any PSU has size = 1 (triggered in Task T009b).  
- `data`: Pandas DataFrame (internal representation).  

### 2. SyntheticData
Represents generated data with known ground truth.

- `id`: Unique identifier.  
- `true_mean`: Float.  
- `true_variance`: Float.  
- `missingness_mechanism`: Enum ["MCAR", "MAR", "MNAR"].  
- `missingness_rate`: Float.  
- `data`: Pandas DataFrame.  

### 3. ImputationResult
Output of a specific imputation run.

- `method`: Enum ["CompleteCase", "SingleMean", "MICE"].  
- `n_imputations`: Integer (1 for CC/Single, `m` for MICE).  
- `seed`: Integer (base seed for reproducibility).  
- `imputed_data`: Pandas DataFrame (or list of DataFrames for MICE).  
- `convergence_r_hat`: Float (1.0 if not applicable, < 1.05 if converged).  
- `status`: Enum ["success", "failed", "warning"].  
- `error_message`: String (optional).  
- `estimated_variance`: Float (pooled variance after imputation).  
- `missingness_mechanism`: Enum ["MCAR", "MAR", "MNAR", "Unknown"].  

### 4. BiasMetric
Calculated performance metric.

- `method`: String.  
- `estimated_variance`: Float.  
- `benchmark_variance`: Float (true variance for synthetic, Jackknife for real).  
- `percentage_bias`: Float.  
- `ratio_to_single`: Float (MICE deviation / Single Mean deviation).  
- `is_pass_sc002`: Boolean (True if `ratio_to_single ≤ 0.8`).  
- `p_value`: Float (raw p‑value from paired t‑test).  
- `p_value_adjusted`: Float (Holm‑Bonferroni adjusted).  

### 5. SensitivitySweepResult
Aggregated results from parameter sweeps.

- `parameter_name`: String (e.g., "m").  
- `parameter_values`: List of Integers.  
- `bias_rates`: List of Floats (percentage bias for each value).  
- `stability_score`: Float (standard deviation of `bias_rates`).  

## Data Flow

1. **Ingest** → `SurveyDataset` (validated columns, checksum).  
2. **Synthesize** → `SyntheticData` (known ground truth).  
3. **Impute** → `ImputationResult` (per method, with convergence diagnostics).  
4. **Calculate** → `BiasMetric` (including SC‑002 ratio check).  
5. **Sweep** → `SensitivitySweepResult` (stability score).  
6. **Report** → Final Markdown/JSON includes explicit “Associational Findings” footer.
