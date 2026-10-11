# Data Model: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

## Overview
All artifacts are stored under `data/` as JSON, JSONL, CSV, or Parquet files. Schemas are enforced via the YAML contracts in `contracts/`.

### 1. Ingested Dataset Schema (`dataset.schema.yaml`)
*File*: `data/raw/ultrafeedback_filtered.parquet`  
*Description*: Subset of UltraFeedback/Dolly with ≥ 4 rationales per prompt.

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Unique identifier. |
| `prompt_text` | `string` | Original user query. |
| `rationales` | `array[string]` | All distinct high‑quality rationales (≥ 4). |
| `rationale_count` | `integer` | Must be ≥ 4. |
| `source` | `string` | Dataset origin (`UltraFeedback`, `Dolly`). |

### 2. Context Simulation State (`context_split.jsonl`)
*File*: `data/processed/context_split.jsonl`  
*Description*: Result of random privileged‑context sampling.

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Reference to original prompt. |
| `privileged_rationale_idx` | `integer` | Index of sampled privileged context. |
| `privileged_context` | `string` | Text of the privileged rationale. |
| `unselected_indices` | `array[integer]` | Indices of remaining rationales. |
| `unselected_texts` | `array[string]` | Texts of the target distribution. |
| `teacher_logits_path` | `string` | Path to the corresponding `teacher_logits_raw.jsonl` entry (see schema below). |

### 3. Teacher Logits (`teacher_logits_raw.jsonl`)
*File*: `data/processed/teacher_logits_raw.jsonl`  
*Description*: Logits (pre‑softmax) averaged across all **unselected** rationales for each prompt (used to compute the teacher distribution).

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Prompt reference. |
| `teacher_logits` | `array[number]` | Averaged logits vector (same length as model vocab). |
| `logits_source` | `string` | Identifier of the source dataset shard. |

### 4. Training Trajectory Log (`training_run_<run_id>.jsonl`)
*File*: `data/results/training_run_*.jsonl`  
*Schema*: `training_output.schema.yaml`

| Field | Type | Description |
|---|---|---|
| `step` | `integer` | Training step (1‑250). |
| `prompt_id` | `string` | Prompt reference. |
| `condition` | `string` | `"AntiSD"` or `"StandardSD"`. |
| `loss` | `number` | Current loss. |
| `js_divergence` | `number` | JS divergence (student vs. teacher). |
| `gradient_dot_product` | `number` | Dot product of AntiSD gradient and standard gradient (negative expected). |
| `generated_trajectory` | `string` | Tokens generated at this step (or final). |
| `deliberation_count` | `integer` | Number of deliberation tokens in the trajectory. |
| `deliberation_tokens` | `array[string]` | List of detected deliberation tokens. |

### 5. Human Evaluation Proxy Scores (`human_eval_scores.csv`)
*File*: `data/results/human_eval_scores.csv`  
*Schema*: `output.schema.yaml` (aggregated per‑prompt/condition).

| Field | Type | Description |
|---|---|---|
| `trajectory_id` | `string` | Unique trajectory identifier. |
| `prompt_id` | `string` | Prompt reference. |
| `condition` | `string` | `"AntiSD"` or `"StandardSD"`. |
| `rater_1_score` | `integer` | 1‑5 Likert. |
| `rater_2_score` | `integer` | 1‑5 Likert. |
| `rater_3_score` | `integer` | 1‑5 Likert. |
| `median_score` | `number` | Median of three raters. |

### 6. Analysis Results (`analysis_results.json`)
*File*: `data/results/analysis_results.json`  
*Schema*: `analysis_results.schema.yaml`

| Field | Type | Description |
|---|---|---|
| `sample_size` | `integer` | Number of prompts included after filtering. |
| `power_analysis` | `object` | Contains `power`, `effect_size`, `n`. |
| `metrics` | `object` | Aggregated per‑condition means for deliberation frequency, BLEU, quality score. |
| `wilcoxon_results` | `object` | p‑values & statistics for each primary metric. |
| `correlation_results` | `object` | Pearson `r` and p‑value linking deliberation frequency ↔ Human‑Eval Proxy. |

All files are version‑controlled; any modification produces a new hash recorded in `state/projects/…yaml`.

---
