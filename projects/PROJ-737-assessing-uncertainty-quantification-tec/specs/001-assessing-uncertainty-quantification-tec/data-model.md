# Data Model: Assessing Uncertainty Quantification Techniques

## Entity Overview

| Entity | Description |
|--------|-------------|
| **MaterialsDataset** | Represents a specific property dataset (Band Gap, Thermal Conductivity, Formation Energy). |
| **UQMethod** | Encapsulates a UQ technique and its configuration. |
| **EvaluationMetric** | Stores a scalar metric (Calibration Error, Sharpness, Coverage Error) for a method‑dataset pair. |
| **StatisticalTestResult** | Holds the outcome of a paired Wilcoxon test between two methods on a given dataset. |
| **PipelineExecution** | Log of the overall pipeline run (status, resource usage). |

### MaterialsDataset
| Field | Type | Notes |
|-------|------|-------|
| dataset_id | string | e.g., `band_gap`, `...` |
| source_url | string (URI) | Verified URL from the research block. |
| property_name | string | Human‑readable target name. |
| n_samples | integer ≥ 1 | Total rows after loading. |
| n_train | integer ≥ 1 | Training rows (capped at 2000). |
| n_val | integer ≥ 0 | Validation rows. |
| n_test | integer ≥ 200 | Test rows (≥ 200). |
| features | array[string] | Feature column names after featurization. |
| target | string | Name of the target column. |
| checksum | string | SHA256 of the processed CSV. |

### UQMethod
| Field | Type |
|-------|------|
| method_id | enum: `gpr`, `mrp` (placeholder) |
| baseline_model | string |
| hyperparams | object |
| n_iterations | integer |
| status | enum: `success`, `failed`, `skipped` |
| error_msg | string (optional) |

### EvaluationMetric
| ... (truncated) ...
