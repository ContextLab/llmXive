# Data Model: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **FigureTask** | One figure editing instance (source image, injected error, ground‑truth layout). | `task_id` (str), `source_image_path` (str), `error_type` (enum: `color`, `label`, `legend`), `ground_truth_vector_path` (str) |
| **ParticipantSession** | Collection of tasks performed by a single participant, with assigned interface order. | `session_id` (str), `participant_id` (str, anon), `interface_order` (list[`mode`]), `task_order` (list[`task_id`]), `tasks` (list[`FigureTask`]), `start_timestamp_ms` (int), `end_timestamp_ms` (int) |
| **InteractionLog** | Single edit action recorded during a task. | `log_id` (str), `session_id` (str), `task_id` (str), `timestamp_ms` (int), `iteration` (int), `mode` (`structured`/`chat`), `payload` (str), `response_image_path` (str) |
| **SemanticValidation** | Result of the semantic similarity check for a completed task. | `validation_id` (str), `task_id` (str), `similarity_score` (float, 0‑1), `vector_match` (bool), `semantic_pass` (bool) |
| **AnalysisResult** | Aggregated statistical output for the study. | `result_id` (str), `metric` (enum: `time_to_success`, `iteration_count`), `structured_median` (float), `chat_median` (float), `wilcoxon_stat` (float), `p_value` (float), `effect_size_r` (float), `ci_lower` (float), `ci_upper` (float), `bonferroni_corrected` (bool) |

## Relationships
- One **ParticipantSession** contains 50 **FigureTask** instances (same across participants).  
- Each **InteractionLog** belongs to exactly one **FigureTask** and one **ParticipantSession**.  
- **SemanticValidation** is computed per **FigureTask** after the final edit and is stored as a separate JSON line; it is validated against `contracts/semantic_validation.schema.yaml`.  

## Contract Schemas
- `contracts/interaction_log.schema.yaml` validates each JSON line written by the logger.  
- `contracts/semantic_validation.schema.yaml` validates the semantic validation records.  
- `contracts/analysis_result.schema.yaml` validates the final aggregated report structure.

---

