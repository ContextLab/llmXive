# Data Model: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **FigureTask** | One figure editing instance (source image, injected error, ground‑truth layout). | `task_id` (string), `source_image_path` (string), `error_type` (enum: `color`, `label`, `legend`), `ground_truth_vector_path` (string) |
| **ParticipantSession** | Collection of tasks performed by a single participant, with assigned interface order and expertise rating. | `session_id` (string), `participant_id` (string, anonymized), `interface_order` (list[string] – values `"structured"` / `"chat"`), `task_order` (list[string]), `expertise_level` (integer, 0‑5), `start_timestamp_ms` (integer), `end_timestamp_ms` (integer) |
| **InteractionLog** | Single edit action recorded during a task. | `log_id` (string), `session_id` (string), `task_id` (string), `timestamp_ms` (integer), `iteration` (integer, ≥ 1), `mode` (enum: `structured`, `chat`), `payload` (string), `response_image_path` (string), `task_start_ms` (integer), `task_end_ms` (integer), `status` (optional string, e.g., `"aborted"`), `subjective_load` (optional number, 0‑100) |
| **SemanticValidation** | Result of the dual success check for a completed task. | `validation_id` (string), `task_id` (string), `vector_match` (boolean), `semantic_score` (number, 0‑1), `semantic_pass` (boolean, score ≥ 0.95), `overall_success` (boolean) |
| **AnalysisResult** | Aggregated statistical output for a single metric. | `result_id` (string), `metric` (enum: `time_to_success_ms`, `iteration_count`, `subjective_load`), `structured_median` (number), `chat_median` (number), `wilcoxon_statistic` (number), `p_value_corrected` (number, 0‑1), `effect_size_r` (number), `ci_95_lower` (number), `ci_95_upper` (number), `n_participants` (integer) |

## Relationships
- Each **ParticipantSession** contains the same set of 50 **FigureTask** instances (shared across participants).  
- Every **InteractionLog** belongs to exactly one **FigureTask** and one **ParticipantSession**.  
- One **SemanticValidation** record is produced per **FigureTask** after the final edit; **`overall_success` mirrors the `vector_match` result only** (primary success). The `semantic_pass` field records whether the CLIP similarity meets the 0.95 threshold but **does not** affect primary success.  
- **AnalysisResult** aggregates across all sessions for a given metric.

## Contract Schemas
- `contracts/interaction_log.schema.yaml` validates each line written by `interaction_logger.py`.  
- `contracts/semantic_validation.schema.yaml` validates the dual‑check output (with `overall_success` defined as vector_match only).  
- `contracts/analysis_result.schema.yaml` validates the final statistical objects.
