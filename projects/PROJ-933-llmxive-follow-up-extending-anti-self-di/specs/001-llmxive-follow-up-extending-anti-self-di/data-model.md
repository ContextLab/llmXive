# Data Model: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

## Overview
This document defines the data structures for the ingestion, training, and analysis phases. All data is stored in `data/` as JSON/Parquet/CSV.

## 1. Ingested Dataset Schema
**Source**: `data/raw/ultrafeedback_filtered.parquet`
**Description**: The subset of UltraFeedback/Dolly containing only prompts with ≥4 distinct reasoning traces.

| Field | Type | Description |
| :--- | :--- | :--- |
| `prompt_id` | `string` | Unique identifier for the prompt. |
| `prompt_text` | `string` | The user query. |
| `rationales` | `list[string]` | List of all ≥4 annotated reasoning traces for this prompt. |
| `rationale_count` | `int` | Number of rationales (must be ≥4). |
| `source` | `string` | Origin dataset (e.g., "UltraFeedback"). |

## 2. Context Simulation State
**Source**: `data/processed/context_split.jsonl`
**Description**: The state after randomly sampling the "Privileged Context" and separating the "Target Distribution".

| Field | Type | Description |
| :--- | :--- | :--- |
| `prompt_id` | `string` | Reference to the original prompt. |
| `privileged_rationale_idx` | `int` | Index of the sampled privileged context. |
| `privileged_context` | `string` | The text of the sampled privileged rationale. |
| `unselected_indices` | `list[int]` | Indices of the remaining rationales. |
| `unselected_texts` | `list[string]` | Text of the unselected rationales (Target Distribution). |
| `teacher_logits` | `list[float]` | (Optional) Pre-computed average logits from the Inference-Only Pass. |

## 3. Training Trajectory Log
**Source**: `data/results/training_run_<run_id>.jsonl`
**Description**: Log of the training process, including loss, divergence, and generated tokens.

| Field | Type | Description |
| :--- | :--- | :--- |
| `step` | `int` | Training step number (1 to 250). |
| `prompt_id` | `string` | Reference to the prompt. |
| `condition` | `string` | "AntiSD" or "StandardSD". |
| `loss` | `float` | Current loss value. |
| `js_divergence` | `float` | Jensen-Shannon divergence between student and teacher. |
| `gradient_dot_product` | `float` | Dot product of AntiSD gradient and standard gradient (should be negative). |
| `generated_trajectory` | `string` | The generated text at this step (or final step). |
| `deliberation_count` | `int` | Count of deliberation tokens in the trajectory. |
| `deliberation_tokens` | `list[string]` | List of specific tokens found (e.g., ["Wait", "However"]). |

## 4. Analysis Results
**Source**: `data/results/analysis_results.json`
**Description**: Aggregated statistical results for the final report.

| Field | Type | Description |
| :--- | :--- | :--- |
| `sample_size` | `int` | Total number of prompts processed. |
| `power_analysis` | `object` | Calculated statistical power. |
| `metrics` | `object` | Aggregated metrics per condition. |
| `wilcoxon_results` | `object` | P-values, test statistics for each metric comparison. |
| `correlation_results` | `object` | Pearson r and p-value for Deliberation vs. Self-Consistency. |

## 5. Human Evaluation Proxy Data
**Source**: `data/results/human_eval_scores.csv`
**Description**: Scores assigned to generated trajectories.

| Field | Type | Description |
| :--- | :--- | :--- |
| `trajectory_id` | `string` | Unique ID for the generated trajectory. |
| `prompt_id` | `string` | Reference to the prompt. |
| `condition` | `string` | "AntiSD" or "StandardSD". |
| `rater_1_score` | `int` | Score 1-5 from Rater 1. |
| `rater_2_score` | `int` | Score 1-5 from Rater 2. |
| `rater_3_score` | `int` | Score 1-5 from Rater 3. |
| `median_score` | `float` | Median of the three scores. |
