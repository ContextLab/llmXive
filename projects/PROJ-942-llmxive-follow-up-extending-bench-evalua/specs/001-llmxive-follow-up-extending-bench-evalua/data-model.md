# Data Model: Intent‑Graph Proactive Evaluation

## Core Entities
| Entity | Description | File Location |
|--------|-------------|---------------|
| **InteractionTrace** | Raw π‑Bench task containing ordered turns, optional ground‑truth hidden intents. | `data/raw/<task_id>.json` |
| **NormalizedTrace** | Tabular representation of an `InteractionTrace` (one row per turn). | `data/derived/normalized_traces.csv` |
| **IntentNode** | JSON object `{id: str, label: str, confidence: float}` representing an inferred or ground‑truth intent. | Embedded in `IntentGraph` |
| **IntentEdge** | JSON object `{source: str, target: str, type: str}` describing temporal/causal dependency. | Embedded in `IntentGraph` |
| **IntentGraph** | Directed graph (list of `nodes`, list of `edges`). Serialized as JSON per task. | `data/derived/intent_graphs/<task_id>.json` |
| **ProactiveActionLog** | Row `{task_id, turn_index, condition, seed, predicted_action, is_correct, latency_sec}`. | `data/derived/inference_logs/<condition>_log.csv` |
| **EvaluationResult** | Summary `{condition, mean_f1, std_f1, mean_total_latency, latency_reduction_pct, wilcoxon_p, ttest_p, bootstrap_ci, graph_construction_mean_latency_sec}`. | `data/derived/eval_results/summary.csv` |

## JSON Schema (IntentGraph)
See `contracts/intent_graph.schema.yaml`.

## Relationships
* Each **InteractionTrace** → one **IntentGraph** (1‑to‑1).  
* Each **IntentGraph** → many **ProactiveActionLog** rows (one per turn, per seed, per condition).  
* **EvaluationResult** aggregates over the logs for a given condition.

## Versioning & Checksums
* Every file under `data/derived/` is accompanied by a SHA‑256 checksum stored in `state/projects/PROJ-942-...yaml`.  
* Transformations produce new files; original raw files remain unchanged.