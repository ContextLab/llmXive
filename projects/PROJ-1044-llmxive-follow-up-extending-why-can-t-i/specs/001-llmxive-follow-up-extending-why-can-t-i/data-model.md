# Data Model: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Overview
Two primary data artifacts require formal schemas for reproducibility and contract validation:

1. **Counterfactual Pair Metadata** – provenance of each synthetic video pair.  
2. **Evaluation Results** – aggregated model performance, robustness metrics, and statistical test outcomes.

Both schemas live under `specs/001-llmxive-counterfactual-consistency/contracts/`.

---

### 1. Counterfactual Pair Schema (`counterfactual_pair.schema.yaml`)

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `original_video_path` | string | Relative path to the original synthetic video (e.g., `data/videos/orig/vid_001.mp4`). | Yes |
| `counterfactual_video_path` | string | Relative path to the generated counterfactual video. | Yes |
| `original_object_class` | string | Semantic label of the primary object in the original video. | Yes |
| `swapped_object_class` | string | Semantic label of the object used for swapping; must differ from `original_object_class`. | Yes |
| `bbox` | list[float] | Normalized `[x_min, y_min, x_max, y_max]` of the detected primary object in the original frame (values in `[0,1]`). | Yes |
| `patch_source_id` | string | Identifier of the patch image used for swapping. | Yes |
| `optical_flow_divergence` | number | Normalized L2 distance between original and counterfactual optical‑flow fields (must be ≤ 0.15). | Yes |
| `generation_timestamp` | string | ISO‑8601 UTC timestamp of when the pair was created. | Yes |
| `status` | string | `"accepted"` if divergence ≤ 0.15, otherwise `"rejected"`. | Yes |

*Rows are stored in `data/counterfactuals/metadata.csv` and validated against this schema.*

---

### 2. Evaluation Results Schema (`evaluation_results.schema.yaml`)

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `model_id` | string | Human‑readable identifier for the trained model. | Yes |
| `lambda` | number | Weight of the counterfactual consistency loss used during training. | Yes |
| `seed` | integer | Random seed for reproducibility. | Yes |
| `accuracy_original` | number | Classification accuracy on the original validation set (0‑1). | Yes |
| `accuracy_counterfactual` | number | Accuracy on the swapped (counterfactual) validation set (0‑1). | Yes |
| `delta_accuracy` | number | `accuracy_original - accuracy_counterfactual`. | Yes |
| `accuracy_motion_only` | number | Accuracy on the motion‑only test set (objects blurred). | Yes |
| `paired_t_statistic` | number | t‑statistic from paired t‑test (present only in the aggregated summary row). | No |
| `p_value` | number | Two‑tailed p‑value from paired t‑test (present only in the aggregated summary row). | No |
| `lambda_sweep` | boolean | `true` if this row belongs to the λ‑sweep experiment. | Yes |
| `timestamp` | string | ISO‑8601 UTC timestamp of evaluation completion. | Yes |

*Per‑seed rows are saved in `results/per_seed.csv`; the aggregated summary (including t‑statistic, p‑value, bootstrap CI) is saved in `results/summary.csv`.*

---

## Data Flow (textual)

```
synthetic_generator.py --> data/videos/orig/*.mp4
counterfactual.py --> data/videos/cf/*.mp4 + metadata.csv
optical_flow.py (Farneback) --> data/flow/*.npy
trainer.py --> checkpoints/*.pt
evaluator.py --> results/per_seed.csv + summary.csv
report.py --> figures/*.png + tables/*.csv
```

All files are version‑hashed and recorded in the project state YAML per Constitution V.

---
