# Data Model: Statistical Power Analysis of Openly Available fMRI Datasets

## Entity Definitions

### Dataset
Represents an OpenNeuro study.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dataset_id` | str | OpenNeuro dataset ID (e.g., `"ds000030"`). |
| `paradigm_type` | str | Cognitive paradigm (e.g., `"motor"`). |
| `original_sample_size` | int | Number of subjects in the original dataset. |
| `raw_data_path` | str | Local path to the downloaded raw BIDS data. |
| `checksum` | str | SHA‑256 hash of the raw data for integrity verification. |

### SimulationConfig
Represents a single run configuration.

| Attribute | Type | Description |
|-----------|------|-------------|
| `sample_size_target` | int | Desired number of subjects (e.g., 10, 20, 40). |
| `smoothing_kernel` | float | Temporal smoothing kernel size (time‑points). |
| `num_iterations` | int | Number of bootstrap iterations (≥ 50). |
| `random_seed` | int | Fixed seed for reproducibility. |
| `dataset_id` | str | Associated dataset ID. |
| `target_effect_size` | float | Ground‑truth Cohen's d (e.g., 0.0, 0.2, 0.5). |
| `snr_level` | float | Signal‑to‑noise ratio used in signal injection. |
| `alpha_threshold` | float | Significance threshold (e.g., 0.05). |
| `pipeline_config_hash` | str | SHA‑256 hash of ROI‑extraction + smoothing configuration. |

### ReplicationResult
Outcome of a single bootstrap iteration.

| Attribute | Type | Description |
|-----------|------|-------------|
| `effect_size_est` | float | Cohen's d estimated on the training set. |
| `p_value` | float | P‑value from the test‑set significance test. |
| `replication_success` | int | 1 if direction matches and p < α on test set; 0 otherwise. |
| `smoothing_kernel_used` | float | Temporal smoothing kernel applied. |
| `iteration_id` | int | Bootstrap iteration identifier. |
| `sample_size_actual` | int | Actual sample size used (may be clamped). |
| `failure_reason` | str | Optional reason for failure (`"GLM_convergence"`, `"data_corruption"`, `"memory_overflow"`, null). |
| `pipeline_config_hash` | str | Hash of the preprocessing pipeline used. |
| `alpha_threshold` | float | Alpha used for this iteration. |
| `target_effect_size` | float | Ground‑truth effect size. |
| `magnitude_tolerance_pct` | float | Magnitude tolerance used for this iteration (e.g., 20.0 for ±20%). |

### PowerCurve
Aggregated analysis for a paradigm.

| Attribute | Type | Description |
|-----------|------|-------------|
| `paradigm_type` | str | Cognitive paradigm. |
| `sample_sizes_tested` | list[int] | Sample sizes evaluated. |
| `empirical_rates` | list[float] | Replication rates (0 – 1) per sample size. |
| `logistic_model_coef` | dict | Coefficients from the logistic regression. |
| `fdr_corrected` | bool | Whether Benjamini‑Hochberg correction was applied. |
| `alpha_threshold` | float | Alpha threshold used for this curve. |
| `target_effect_size` | float | Ground‑truth effect size. |
| `interaction_terms` | dict | Coefficients for interaction terms (e.g., sample × kernel). |
| `grid_type` | str | Grid type used: `"primary"` (10, 20, 40, 60) or `"fine"` (10, 15, 20, 30, 40, 50, 60). |

## Data Flow

1. **Download** → `openneuro_fetcher.py` → `data/raw/` (checksummed).  
2. **Noise Estimation** → `noise_estimator.py` → `data/derived/noise_profiles/`.  
3. **Signal Injection** → `signal_injector.py` → `data/derived/signal_injected/`.  
4. **Preprocess** → `roi_extractor.py` + `temporal_smoothing.py` → `data/derived/processed_roi/` (produces `roi_timeseries.csv` – **T044a**).  
5. **Split‑Half Validation** → `split_half_validator.py` (bootstraps) → `data/derived/replication_results/`.  
6. **Aggregate** → `power_curve_generator.py` → `data/aggregated/power_curves/`.  
7. **Collinearity Check** → `collinearity_checker.py` (T090) → `data/aggregated/predictor_correlation.csv`.  
8. **Model** → Logistic regression → `data/aggregated/logistic_models/`.  

## File Naming Conventions

- Raw data: `data/raw/{dataset_id}_{checksum}.tar.gz`  
- Noise profile: `data/derived/noise_profiles/{dataset_id}_{paradigm}.json`  
- Signal-injected data: `data/derived/signal_injected/{dataset_id}_{effect_size}_{seed}.nii.gz`  
- ROI timeseries: `data/derived/processed_roi/{dataset_id}_{kernel}.csv` (≥ 100 rows) – **T044a**  
- Replication result: `data/derived/replication_results/{dataset_id}_{kernel}_{seed}_{iter}.json`  
- Power curve: `data/aggregated/power_curves/{paradigm}_{kernel}_{effect_size}_{grid_type}.csv`  
- Predictor correlation: `data/aggregated/predictor_correlation.csv` (T090 output)  
- Logistic model: `data/aggregated/logistic_models/{paradigm}_{kernel}_{effect_size}_model.pkl`  
