# Data Model: Visual Detail and False Memory Susceptibility

## Entities

### Stimulus (Image)
| Field | Type | Description |
|-------|------|-------------|
| `image_id` | `string` (UUID) | Unique identifier for the baseline image. |
| `baseline_path` | `string` | Relative path to the original image file. |
| `enhanced_path` | `string` | Path to the enhanced‑detail version. |
| `reduced_path` | `string` | Path to the reduced‑detail version. |
| `complexity_score` | `number` (0 – 1) | Derived metric (edge density + object count). |
| `manipulation_params` | `object` | JSON with `objects_added`, `objects_removed`, `blur_radius`, etc. |
| `created_at` | `string` (ISO‑8601) | Timestamp of generation. |
| `script_version` | `string` | Git commit hash of the generator script. |
| `checksum` | `string` (SHA‑256) | File‑level checksum for reproducibility. |

### Participant
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | `string` (pattern `^P-\d{3}$`) | Pseudonymous identifier. |
| `condition_order` | `array[string]` | Latin‑square randomized sequence of the three stimulus conditions. |
| `consent_verified` | `boolean` | True if consent was recorded. |
| `completion_timestamp` | `string` (ISO‑8601) | End‑of‑session time. |
| `status` | `string` (`complete`, `partial`, `dropped`) | Session outcome flag. |

### Response
| Field | Type | Description |
|-------|------|-------------|
| `response_id` | `string` (UUID) | Unique response identifier. |
| `participant_id` | `string` | FK → Participant. |
| `question_id` | `string` | Identifier for the recognition item (e.g., `Q_001`). |
| `condition` | `string` (`enhanced`, `reduced`, `baseline`) | Stimulus condition for this question. |
| `is_false_detail` | `boolean` | True if the item is a lure. |
| `lure_source_query` | `string` | Query used to generate the lure (e.g., “objects in kitchen not in image”). |
| `response_value` | `boolean` | Participant answered “Yes”. |
| `response_timestamp` | `string` (ISO‑8601) | When the answer was recorded. |
| `latency_ms` | `integer` | Time taken to answer, in milliseconds. |
| `semantic_plausibility` | `number` (0 – 1) | WordNet‑based plausibility score for the lure (0 = implausible, 1 = highly plausible). |
| `trial_position` | `integer` | Ordinal position of the trial within the condition block (used to model fatigue effects). |
| `trial_type` | `string` (`true`, `lure`) | Indicates true‑detail vs. lure question (ensures balanced representation across conditions). |

## Data Flow
1. **Acquisition** – `utils/data_loader.py` streams Visual Genome (or loads pre‑bundled subset) → creates `Stimulus` records in `data/stimuli/`.  
2. **Manipulation** – `stimuli/generator.py` produces enhanced/reduced images and writes `metadata.yaml` per stimulus.  
3. **Collection** – `participants/interface.py` runs sessions, writes `Response` rows to `data/responses/{participant_id}.jsonl`.  
4. **Analysis** – `analysis/glmm.py` (primary) and `analysis/anova.py` (secondary) aggregate responses, fit models, output `data/analysis/glmm_results.json` and `false_memory_rates.png`.  

## Constraints
- **No PII** in any `data/responses/` file.  
- **Uniqueness**: `image_id`, `response_id`, and `participant_id` must be globally unique.  
- **Integrity**: Every `Response` must reference an existing `Participant` and a valid `question_id` derived from the associated stimulus.  
- **Versioning**: All generated files include a SHA‑256 checksum recorded in the project state YAML.  

---


