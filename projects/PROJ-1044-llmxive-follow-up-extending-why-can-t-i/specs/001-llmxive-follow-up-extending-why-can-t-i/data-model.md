# Data Model: llmXive follow-up: extending "Why Can't I Open My Drawer? Mitigating Object-Driven Shortcuts in Zero"

## Overview
Two primary data artifacts require formal schemas for reproducibility and contract validation:

1. **Counterfactual Pair Metadata** – records provenance of each synthetic video pair.
2. **Evaluation Results** – aggregates model performance, robustness metrics, and statistical test outcomes.

Both schemas are stored under `specs/001-llmxive-counterfactual-consistency/contracts/`.

---

### 1. Counterfactual Pair Schema (`counterfactual_pair.schema.yaml`)

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `original_video_path` | string | Relative path to the original synthetic video (e.g., `data/videos/orig/vid_001.mp4`). | Yes |
| `counterfactual_video_path` | string | Relative path to the generated counterfactual video. | Yes |
| `original_object_class` | string | Semantic label of the primary object in the original video (e.g., `"cup"`). | Yes |
| `swapped_object_class` | string | Semantic label of the object used for the swap (must differ from `original_object_class`). | Yes |
| `bbox` | list[float] | Normalized `[x_min, y_min, x_max, y_max]` of the detected primary object in the original frame (values in `[0,1]`). | Yes |
| `patch_source_id` | string | Identifier of the patch image used for the swap (e.g., `"patches/bowl_03.png"`). | Yes |
| `optical_flow_divergence` | float | Normalized L2 distance between original and counterfactual optical‑flow fields (≤ 0.15 required). | Yes |
| `generation_timestamp` | string | ISO‑8601 UTC timestamp of when the pair was created. | Yes |
| `status` | string | `"accepted"` if divergence ≤ 0.15, otherwise `"rejected"`. | Yes |

*All rows are stored in `data/counterfactuals/metadata.csv` and validated against this schema.*

---

### 2. Evaluation Results Schema (`evaluation_results.schema.yaml`)

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `model_id` | string | Human‑readable identifier (e.g., `"linear_lambda0.5_seed42"`). | Yes |
| `lambda` | float | Weight of the consistency loss used during training. | Yes |
| `seed` | integer | Random seed for reproducibility. | Yes |
| `accuracy_original` | float | Classification accuracy on the original validation set (0‑1). | Yes |
| `accuracy_counterfactual` | float | Accuracy on the swapped (counterfactual) validation set (0‑1). | Yes |
| `delta_accuracy` | float | `accuracy_original - accuracy_counterfactual`. | Yes |
| `accuracy_motion_only` | float | Accuracy on the motion‑only test set (objects blurred). | Yes |
| `paired_t_statistic` | float | t‑statistic from the paired t‑test comparing `delta_accuracy` vs baseline. | No (only present for the aggregated summary row). |
| `p_value` | float | Two‑tailed p‑value from the paired t‑test. | No (only present for the aggregated summary row). |
| `lambda_sweep` | boolean | `true` if this row belongs to the λ‑sweep experiment. | Yes |
| `timestamp` | string | ISO‑8601 UTC timestamp of evaluation completion. | Yes |

*Aggregated summary (averaged across seeds) is stored in `results/summary.csv`; per‑seed rows are stored in `results/per_seed.csv`.*

---

## Data Flow Diagram (textual)

```
synthetic_generator.py --> raw_videos/
counterfactual.py --> counterfactual_videos/ + metadata.csv
optical_flow.py --> flow_features/*.npy
trainer.py --> checkpoints/*.pt
evaluator.py --> per_seed.csv + summary.csv
report.py --> figures/*.png + tables/*.csv
```

All files are version‑hashed and recorded in the project state YAML per Constitution V.

---
