# Data Model: llmXive follow‑up – attention sparsity study

## Overview
The pipeline generates a hierarchy of artifacts. The **primary contract‑validated artifact** is the inference‑results table, defined by the JSON Schema below. Intermediate files follow the same column conventions but are not contract‑validated.

## Primary Result Schema (`contracts/inference_results.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `image_id` | string | Unique identifier of the source image (as in the raw dataset). | Must match an entry in the raw dataset. |
| `sparsity_window` | integer | Attention window size in patches; `0` denotes *global* attention. | Allowed values: `0`, `64`, `32`, `16`, `1`. |
| `scene_density` | string | `"dense"` if the image belongs to the dense‑scene subset, otherwise `"non_dense"`. | Enum: `"dense"`, `"non_dense"`. |
| `excluded` | boolean | `true` if the image was flagged as ambiguous and excluded from mIoU calculations (FR‑007). | – |
| `mIoU` | number \| null | Mean Intersection‑over‑Union for this image (null if `excluded`). | `0.0 ≤ value ≤ 1.0`. |
| `latency_ms` | number | Inference latency for this image (milliseconds). | `> 0`. |
| `global_context_activation_proportion` | number \| null | Proportion of Grad‑CAM activation on tokens labelled “global‑context”. Populated only for images used in attribution analysis. | `0.0 ≤ value ≤ 1.0`. |
| `prediction_path` | string | Relative path to the JSON file containing the model’s raw predictions. | Pattern: `^data/predictions/.*\.json$`. |

*All fields are required; `null` is allowed for `mIoU` and `global_context_activation_proportion` when appropriate.*

### Example Row (YAML‑compatible JSON representation)
```yaml
- image_id: "COCO_00012345"
  sparsity_window: 32
  scene_density: "dense"
  excluded: false
  mIoU: 0.74
  latency_ms: 112.5
  global_context_activation_proportion: null
  prediction_path: "data/predictions/COCO_00012345_32.json"
```

## Derived Summary Tables (used for reporting, not contract‑validated)

| File | Description |
|------|-------------|
| `degradation_curve.csv` | Columns: `sparsity_window`, `scene_density`, `mean_mIoU`, `ci_lower`, `ci_upper`. |
| `anova_results.json` | Keys: `method` (`"ANOVA"` or `"Friedman"`), `f_value`, `p_value`. |
| `trend_test.json` | Keys: `jonckheere_terpstra_stat`, `jonckheere_terpstra_p`, `kendall_tau`, `kendall_p`. |
| `tipping_point.json` | Keys: `status` (`"found"` or `"none"`), `window_size` (if found), `mean_mIoU`. |
| `attribution_summary.json` | Keys: `failure_mean`, `success_mean`, `global_context_activation_diff`, `threshold_met` (boolean). |

All CSV/JSON files are stored under `data/analysis/` and are content‑hashed for versioning.

---

