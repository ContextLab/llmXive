# Data Model: Assessing Uncertainty Quantification Techniques

## Entity Overview

| Entity | Description |
|--------|-------------|
| **MaterialsDataset** | Represents a processed property dataset (Band Gap, Thermal Conductivity, Elastic Modulus). |
| **UQMethod** | Encapsulates a UQ technique, its hyper‑parameters, and execution status. |
| **PerSampleResult** | Stores a single test‑sample prediction, interval bounds, ground truth, and absolute error. |
| **EvaluationMetric** | Scalar metric (Calibration Error, Sharpness, Coverage) for a given dataset‑method pair. |
| **StatisticalTestResult** | Outcome of a paired Wilcoxon test between two methods on a specific metric and dataset. |
| **PipelineExecution** | Log of the overall run (run‑id, timestamps, resource usage, overall status). |

### MaterialsDataset
| Field | Type | Notes |
|-------|------|-------|
| dataset_id | string | e.g., `band_gap`, `thermal_conductivity`, `elastic_modulus`. |
| source_url | string (URI) | Verified URL from the research block. |
| property_name | string | Human‑readable target name. |
| n_samples | integer ≥ 1 | Total rows after loading. |
| n_train | integer ≥ 1 | Training rows (capped at 2000). |
| n_val | integer ≥ 0 | Validation rows. |
| n_test | integer ≥ 200 | Test rows (≥ 200 per SC‑005). |
| features | array[string] | Feature column names after featurisation. |
| target | string | Name of the target column. |
| checksum | string | SHA256 of the processed CSV file. |

### UQMethod
| Field | Type |
|-------|------|
| method_id | enum: `gpr`, `mc_dropout`, `deep_ensemble`, `conformal`, `deterministic_mlp` |
| baseline_model | string (e.g., `GaussianProcessRegressor`, `MLP`) |
| hyperparams | object (JSON‑serialisable dict) |
| n_iterations | integer (e.g., MC‑Dropout passes, ensemble size) |
| status | enum: `success`, `failed`, `skipped` |
| error_msg | string (optional) |

### PerSampleResult
| Field | Type |
|-------|------|
| sample_id | string |
| dataset_id | string |
| method_id | string |
| prediction | number |
| lower_bound | number |
| upper_bound | number |
| ground_truth | number |
| abs_error | number |
| interval_width | number |
| covered | integer (0/1) |

### EvaluationMetric
| Field | Type |
|-------|------|
| dataset_id | string |
| method_id | string |
| metric_type | enum: `calibration_error`, `sharpness`, `coverage_error` |
| value | number |
| nominal_coverage | number (0–1, only for interval metrics) |
| timestamp | string (ISO‑8601) |

### StatisticalTestResult
| Field | Type |
|-------|------|
| dataset_id | string |
| metric_type | enum: `abs_error`, `interval_width`, `coverage` |
| method_a | string |
| method_b | string |
| test_name | enum: `wilcoxon` |
| p_value | number (0–1) |
| significant | boolean |
| alpha_adj | number (0–1) |
| timestamp | string (ISO‑8601) |

### PipelineExecution
| Field | Type |
|-------|------|
| run_id | string |
| start_timestamp | string (ISO‑8601) |
| end_timestamp | string (ISO‑8601) |
| status | enum: `success`, `partial_success`, `failure` |
| steps | array[object] (each step records `step_name`, `cpu_seconds`, `peak_ram_gb`, `status`, `notes`) |
| notes | string (optional) |

All entities are persisted as CSV files that conform to the schemas in `contracts/`.

--- End of Data Model ---
