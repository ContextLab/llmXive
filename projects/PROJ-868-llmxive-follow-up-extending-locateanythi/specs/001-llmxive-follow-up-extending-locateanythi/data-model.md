# Data Model: llmXive follow-up – attention sparsity study

## Overview
The pipeline produces a hierarchy of artifacts. Below we define the schema for the **final inference results** that downstream contracts validate. Additional intermediate files follow the same column conventions but are not contract‑validated.

## Primary Result Schema (`inference_results.schema.yaml`)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `image_id` | string | Unique identifier of the source image (as provided by the original dataset). | Must match an entry in the raw dataset. |
| `sparsity_window` | integer | Size of the attention window in patches. Use `0` to denote *global* attention. | Allowed values: `0`, `64`, `32`, `16`, `1`. |
| `scene_density` | string | `"dense"` if the image belongs to the dense‑scene subset, otherwise `"non_dense"`. | Must be either `"dense"` or `"non_dense"`. |
| `excluded` | boolean | `true` if the image was flagged as ambiguous and excluded from mIoU calculations (FR‑007). | – |
| `mIoU` | float | Mean Intersection‑over‑Union between predicted boxes and ground‑truth (computed per image). | `0.0 ≤ mIoU ≤ 1.0`. If `excluded` is `true`, set to `null`. |
| `latency_ms` | float | Inference latency for this image (milliseconds). | Positive. |
| `global_context_activation_proportion` | float | Proportion of Grad‑CAM (or attention‑rollout) activation mass on tokens labelled “global‑context”. Only populated for images used in attribution analysis; otherwise `null`. | `0.0 ≤ value ≤ 1.0`. |
| `prediction_path` | string | Relative path to the saved prediction JSON (optional, for debugging). | Must point to an existing file under `data/predictions/`. |

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

## Derived Summary Tables
- `degradation_curve.csv` – columns: `sparsity_window`, `density`, `mean_mIoU`, `ci_lower`, `ci_upper`.  
- `anova_results.json` – keys: `f_value`, `p_value`, `method` (`"ANOVA"` or `"Friedman"`).  
- `correlation.csv` – columns: `density`, `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`.  
- `tipping_point.json` – keys: `window_size`, `mIoU`, `status` (`"found"` or `"none"`).  
- `attribution_summary.json` – keys: `global_context_activation_diff`, `failure_mean`, `success_mean`.

All CSV/JSON files are stored under `data/analysis/` and are version‑hashed.

---
