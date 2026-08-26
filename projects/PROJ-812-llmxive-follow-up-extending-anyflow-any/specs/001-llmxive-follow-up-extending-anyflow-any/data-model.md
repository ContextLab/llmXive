# Data Model: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Overview
Defines all persistent artifacts stored under `data/`. Every artifact is immutable once created and is referenced by a checksum recorded in `data/checksums.json`.

## Entity Definitions

### 1. VideoClip
| Field | Type | Description |
|-------|------|-------------|
| `clip_id` | `str` | Unique identifier (e.g., `ucf101_001`). |
| `source` | `str` | `"UCF101"` or `"MovieNet"`. |
| `file_path` | `str` | Relative path to the 16‑frame clip. |
| `has_cut` | `bool` | Ground‑truth cut flag from the MovieNet dataset. |
| `frames` | `int` | Fixed at `16`. |
| `fps` | `int` | Fixed at `30`. |

### 2. ContinuityScore (Human Annotation)
| Field | Type | Description |
|-------|------|-------------|
| `clip_id` | `str` | FK to `VideoClip`. |
| `score` | `float` | Continuous continuity score `[0.0, 1.0]`. |
| `rubric_score` | `int` | Original 5‑point Likert rating. |
| `annotator_id` | `str` | Identifier of the annotator. |
| `status` | `str` | `"valid"` or `"adjudicated"` (after third‑expert resolution). |
| `timestamp` | `datetime` | ISO‑8601 annotation time. |

### 3. DivergenceMetric
| Field | Type | Description |
|-------|------|-------------|
| `clip_id` | `str` | FK to `VideoClip`. |
| `divergence_score` | `float` | Normalized MSE between model and Euler baseline. |
| `baseline_n` | `int` | Euler steps used (`500`, `200`, or `100`). |
| `kurtosis` | `float` | Temporal pattern feature. |
| `clustering` | `float` | Temporal pattern feature. |
| `status` | `str` | `"success"`, `"failed"`, or `"skipped"` |

### 4. SyntheticValidationSubset (FR‑012)
| Field | Type | Description |
|-------|------|-------------|
| `clip_id` | `str` | Unique ID (synthetic). |
| `known_label` | `int` | Binary ground truth (`0` = continuous, `1` = cut). |
| `divergence_score` | `float` | Computed by the pipeline. |
| `baseline_n` | `int` | Euler steps used. |

### 5. ControlAnalysisResult (FR‑004)
| Field | Type | Description |
|-------|------|-------------|
| `group` | `str` | `"continuous"` or `"cut"`. |
| `mean_divergence` | `float` | Mean divergence for the group. |
| `ks_statistic` | `float` | Kolmogorov‑Smirnov statistic comparing groups. |
| `p_value` | `float` | KS test p‑value. |

### 6. SensitivityReport
| Field | Type | Description |
|-------|------|-------------|
| `threshold` | `float` | Classification threshold. |
| `baseline_n` | `int` | Euler steps used. |
| `false_positive_rate` | `float` | FP/(FP+TN). |
| `false_negative_rate` | `float` | FN/(FN+TP). |
| `accuracy` | `float` | Overall accuracy. |

### 7. VarianceReport
| Field | Type | Description |
|-------|------|-------------|
| `variance` | `float` | Variance of `ContinuityScore`. |
| `mean` | `float` | Mean of `ContinuityScore`. |
| `std_dev` | `float` | Standard deviation. |
| `is_bimodal` | `bool` | Result of Hartigan's Dip Test (p < 0.05). |
| `dip_p_value` | `float` | Dip test p‑value. |
| `sample_size` | `int` | Number of annotated clips. |

## Data Flow Summary
1. **Download & stratify** → `VideoClip` records (raw).  
2. **Human annotation** → `ContinuityScore` (immutable, checksummed).  
3. **Divergence computation** → `DivergenceMetric`.  
4. **Control analysis** → `ControlAnalysisResult`.  
5. **Statistical analysis** → `SensitivityReport` + `VarianceReport`.  
6. **Synthetic validation** → `SyntheticValidationSubset` (used only for FR‑012 verification).

All derived CSV/JSON files are written to `data/processed/` and validated against the corresponding YAML schemas in `contracts/`.