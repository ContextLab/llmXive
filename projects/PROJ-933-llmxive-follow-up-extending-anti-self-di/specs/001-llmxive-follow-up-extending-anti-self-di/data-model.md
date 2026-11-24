# Data Model: llmXive follow‑up: extending “Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information”

## Overview
All artifacts live under `data/` as JSON, JSONL, CSV, or Parquet files. Schemas are enforced via the YAML contracts in `contracts/`.

### 1. Ingested Dataset Schema (`dataset.schema.yaml`)
*File*: `data/raw/filtered_bigbench.parquet`  
*Description*: Subset of the three BigBench shards with **at least three** rationales per prompt.

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Unique identifier. |
| `prompt_text` | `string` | Original user query. |
| `rationales` | `array[string]` | All distinct rationales (must be ≥ 3). |
| `rationale_count` | `integer` | Number of rationales (≥ 3). |
| `source` | `string` | Dataset origin (`bigbench_hard`, `bigbench_ethics`, `bigbench_causal`). |

### 2. Context Simulation State (`context_split.jsonl`)
*File*: `data/processed/context_split.jsonl`  
*Description*: Result of random privileged‑context sampling with quality‑score stratification.

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Reference to original prompt. |
| `privileged_rationale_idx` | `integer` | Index of sampled privileged context. |
| `privileged_context` | `string` | Text of the privileged rationale. |
| `privileged_quality_score` | `number` | Simple quality metric (log‑length × token‑type‑ratio). |
| `unselected_indices` | `array[integer]` | Indices of remaining rationales. |
| `unselected_texts` | `array[string]` | Texts of the target distribution. |
| `teacher_logits_path` | `string` | Path to the corresponding entry in `teacher_logits_raw.jsonl`. |

### 3. Teacher Logits (`teacher_logits_raw.jsonl`)
*File*: `data/processed/teacher_logits_raw.jsonl`  
*Description*: Averaged pre‑softmax logits over all **unselected** rationales for each prompt (used as the teacher distribution).

| Field | Type | Description |
|---|---|---|
| `prompt_id` | `string` | Prompt reference. |
| `teacher_logits` | `array[number]` | Averaged logits vector (same length as model vocab). |
| `logits_source` | `string` | Identifier of the source dataset shard. |

### 4. Training Trajectory Log (`training_run_<run_id>.jsonl`)
*File*: `data/results/training_run_*.jsonl`  
*Schema*: `contracts/training_output.schema.yaml`

| Field | Type | Description |
|---|---|---|
| `step` | `integer` | Training step (1‑200). |
| `prompt_id` | `string` | Prompt reference. |
| `condition` | `string` | `"AntiSD"` or `"StandardSD"`. |
| `loss` | `number` | Current loss. |
| `js_divergence` | `number` | Jensen‑Shannon divergence (student vs. teacher). |
| `gradient_dot_product` | `number` | Dot product of AntiSD gradient and standard gradient (expected negative). |
| `generated_trajectory` | `string` | Tokens generated at this step (or final). |
| `deliberation_count` | `integer` | Number of deliberation tokens in the trajectory. |
| `deliberation_tokens` | `array[string]` | List of specific deliberation tokens found. |
| `entropy_per_token` | `array[number]` | Token‑level entropy values (one per generated token). |
| `training_time_seconds` | `number` | Wall‑clock time for this step (seconds). |
| `peak_memory_mb` | `number` | Peak RAM usage observed during this step (megabytes). |

### 5. Human Evaluation Proxy Scores (`human_eval_scores.csv`)
*File*: `data/results/human_eval_scores.csv`  
*Schema*: `contracts/output.schema.yaml` (aggregated per‑prompt/condition).

| Field | Type | Description |
|---|---|---|
| `trajectory_id` | `string` | Unique trajectory identifier. |
| `prompt_id` | `string` | Prompt reference. |
| `condition` | `string` | `"AntiSD"` or `"StandardSD"`. |
| `rater_1_score` | `integer` | 1‑5 Likert. |
| `rater_2_score` | `integer` | 1‑5 Likert. |
| `rater_3_score` | `integer` | 1‑5 Likert. |
| `median_score` | `number` | Median of three raters. |

### 6. Final Analysis Results (`final_report.json`)
*File*: `data/results/final_report.json`  
*Schema*: `contracts/analysis_results.schema.yaml`

| Field | Type | Description |
|---|---|---|
| `sample_size` | `integer` | Number of prompts after filtering. |
| `power_analysis` | `object` | Contains `power`, `effect_size`, `n`. |
| `metrics` | `object` | Per‑condition means for deliberation frequency, BLEU, semantic similarity, quality score, and entropy. |
| `wilcoxon_results` | `object` | p‑values, statistics, and Cliff’s δ for each primary metric (deliberation, BLEU, semantic similarity, quality, entropy). |
| `correlation_results` | `object` | Spearman `rho` and p‑value linking deliberation frequency ↔ Human‑Eval‑Proxy. |
| `human_score_diff_pass` | `boolean` | `true` if AntiSD quality exceeds StandardSD by ≥ 0.2 points (SC‑006). |
| `runtime_summary` | `object` | Average `training_time_seconds` and `peak_memory_mb` per prompt (verifies SC‑004). |

All files are version‑controlled; any modification produces a new hash recorded in `state/projects/…yaml`.

## Single Source of Truth (SSoT)
`data/results/final_report.json` is the definitive artifact for all final statistics, figures, and conclusions, satisfying Constitution Principle IV.

---

