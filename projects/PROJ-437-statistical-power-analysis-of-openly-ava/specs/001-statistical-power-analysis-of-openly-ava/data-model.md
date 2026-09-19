# Data Model: Statistical Power Analysis of Openly Available fMRI Datasets

## Entity Definitions

### Dataset
Represents an OpenNeuro study.

| Attribute | Type | Description |
|-----------|------|-------------|
| `dataset_id` | str | OpenNeuro dataset ID (e.g., "ds000030") |
| `paradigm_type` | str | Cognitive paradigm (e.g., "motor", "working_memory") |
| `original_sample_size` | int | Number of subjects in original dataset |
| `raw_data_path` | str | Local path to downloaded raw BIDS data |
| `checksum` | str | SHA256 hash of raw data for integrity verification |

### SimulationConfig
Represents a single run configuration.

| Attribute | Type | Description |
|-----------|------|-------------|
| `sample_size_target` | int | Target number of subjects (e.g., 10, 20, 40) |
| `smoothing_kernel` | float | Temporal smoothing kernel size (e.g., 2.0, 4.0 time points) |
| `num_iterations` | int | Number of bootstrap iterations (≥50) |
| `random_seed` | int | Fixed random seed for reproducibility |
| `dataset_id` | str | Associated dataset ID |
| `target_effect_size` | float | Known ground-truth effect size (Cohen's d) (e.g., 0.0, 0.2, 0.5) |
| `snr_level` | float | Signal-to-Noise Ratio input for simulation (e.g., 0.5, 1.0, 2.0) |
| `alpha_threshold` | float | Significance threshold for power calculation (e.g., 0.01, 0.05) |
| `pipeline_config_hash` | str | SHA256 hash of the ROI extraction + smoothing configuration |

### ReplicationResult
Represents outcome of a single simulation iteration.

| Attribute | Type | Description |
|-----------|------|-------------|
| `effect_size_est` | float | Cohen's d estimated on training set |
| `p_value` | float | P-value from test set significance test |
| `replication_success` | int | Binary (1 if known effect detected AND direction matches) |
| `smoothing_kernel_used` | float | Temporal smoothing kernel applied |
| `iteration_id` | int | Bootstrap iteration number |
| `sample_size_actual` | int | Actual sample size used (may be clamped) |
| `failure_reason` | str | Optional: "GLM_convergence", "data_corruption", etc. |
| `pipeline_config_hash` | str | Hash of the pipeline configuration used for this run |
| `alpha_threshold` | float | Alpha threshold used for this run |
| `target_effect_size` | float | Known ground-truth effect size |

### PowerCurve
Represents aggregated analysis for a paradigm.

| Attribute | Type | Description |
|-----------|------|-------------|
| `paradigm_type` | str | Cognitive paradigm |
| `sample_sizes_tested` | list[int] | List of sample sizes tested (e.g., [10, 20, 40]) |
| `empirical_rates` | list[float] | Empirical replication rates for each sample size |
| `logistic_model_coef` | dict | Logistic regression coefficients (sample_size, kernel, snr, interaction) |
| `fdr_corrected` | bool | Whether Benjamini-Hochberg correction applied |
| `alpha_threshold` | float | Alpha threshold used for this curve |
| `target_effect_size` | float | Known ground-truth effect size |
| `interaction_terms` | dict | Coefficients for interaction terms (e.g., sample_size × kernel) |

## Data Flow

1. **Download**: `openneuro_fetcher.py` → `data/raw/` (checksummed)
2. **Noise Estimation**: `noise_estimator.py` → `data/derived/noise_profiles/`
3. **Simulation**: `synthetic_data_gen.py` (uses noise profiles + known effect) → `data/derived/synthetic_data/`
4. **Preprocess**: `roi_extractor.py` + `temporal_smoothing.py` → `data/derived/processed_roi/`
5. **Simulate**: `split_half_validator.py` (loop over `SimulationConfig`) → `data/derived/replication_results/`
6. **Aggregate**: `power_curve_generator.py` → `data/aggregated/power_curves/`
7. **Model**: Logistic regression on aggregated results → `data/aggregated/logistic_model/`

## File Naming Conventions

- Raw data: `data/raw/{dataset_id}_{checksum}.tar.gz`
- Noise profile: `data/derived/noise_profiles/{dataset_id}_{paradigm}.json`
- Synthetic data: `data/derived/synthetic_data/{dataset_id}_{effect_size}_{seed}.nii.gz`
- Results: `data/derived/replication_results/{dataset_id}_{kernel}_{seed}_{iter}.json`
- Aggregated: `data/aggregated/power_curves/{paradigm}_{kernel}_{effect_size}.csv`
- Model: `data/aggregated/logistic_model/{paradigm}_{kernel}_{effect_size}_model.pkl`
