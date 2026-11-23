# Data Model: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

## 1. Entity Definitions

### Episode
| Field | Type | Description |
|---|---|---|
| `episode_id` | string | Unique identifier. |
| `domain` | enum (`medical`, `office`, `education`, `household`) | Context domain. |
| `user_role` | string | Role of the user (e.g., doctor, admin). |
| `intent` | string | Classified intent (`query`, `deletion`, `extraction`, `other`). |
| `query` | string | User query text. |
| `memory_state` | string | Retrieved or full memory context. |
| `leak_target` | boolean | Ground‑truth: *True* = allowed, *False* = should be blocked. |
| `deletion_request` | boolean | Whether a deletion request is present. |
| `deletion_log` | array[string] | History of deletion actions (if applicable). |
| `ground_truth_success` | boolean | Human‑annotated task success label. |
| `ground_truth_deletion` | boolean | Ground truth indicating successful deletion compliance. |
| `ground_truth_answer` | string | Human‑annotated correct answer for utility calculation. |
| `ground_truth_leak` | boolean | Ground truth label indicating if a leak occurred in this episode. |

### EvaluationResult
| Field | Type | Description |
|---|---|---|
| `episode_id` | string | Reference to the input episode. |
| `pipeline_type` | enum (`gatekeeper`, `retrieval_only`, `long_context`) | Pipeline executed. |
| `allowed` | boolean | Whether the query passed the gate. |
| `generated_response` | string (optional) | LLM output (empty if blocked). |
| `task_success` | boolean | Success vs. ground truth. |
| `latency_ms` | number ≥ 0 | Wall‑clock inference time. |
| `peak_ram_mb` | number ≥ 0 | Peak RAM usage. |

### MetricAggregation (per pipeline & domain)
| Field | Type | Description |
|---|---|---|
| `pipeline_type` | enum (`gatekeeper`, `retrieval_only`, `long_context`) | |
| `domain` | enum (`medical`, `office`, `education`, `household`) | |
| `access_control_score` | float ∈ [0, 1] | Unauthorized exposure rate. |
| `utility_score` | float ∈ [0, 1] | Task success rate. |
| `conditional_utility` | float ∈ [0, 1] | Utility among queries allowed by the gate. |
| `forgetting_score` | float ∈ [0, 1] | Deletion compliance rate. |
| `avg_latency_ms` | float ≥ 0 | Mean inference latency. |
| `avg_peak_ram_mb` | float ≥ 0 | Mean peak RAM. |
| `total_episodes` | integer ≥ 0 | Number of episodes aggregated. |

## 2. Data Flow
1. **Ingestion** – `utils/data_loader.py` streams GateMem JSONL → `data/raw/`.  
2. **Validation** – Each record validated against `gatemem_episode.schema.yaml`.  
3. **Processing** – `gatekeeper/pipeline.py` & `baselines/*.py` produce `EvaluationResult` objects written to `data/processed/<pipeline>_results.jsonl`.  
4. **Aggregation** – `metrics/*` compute per‑episode scores; write `data/processed/unified_metrics.json` (list of objects containing `episode_id`, `domain`, and the three core scores).  
5. **Statistical Analysis** – `stats/comparison.py` reads `unified_metrics.json`, fits GLMM or fallback tests, and writes `data/processed/statistical_results.json`.  
6. **Failure‑Case Sampling** – `cli/run_evaluation.py` filters `unified_metrics.json` for false positives/negatives, stratifies by `domain`, and outputs `data/samples/failure_cases.json`.  

---

