# Data Model: Intent‑Graph Proactive Evaluation

## Core Entities
| Entity | Description | File Location |
|--------|-------------|---------------|
| **InteractionTrace** | Raw π‑Bench task JSON containing ordered dialogue turns and optional hidden‑intent annotations. | `data/raw/<task_id>.json` |
| **NormalizedTrace** | Tidy CSV representation of an InteractionTrace (one row per turn). | `data/derived/normalized_traces.csv` |
| **IntentNode** | JSON object `{id: str, label: str, confidence: float}` representing an inferred or ground‑truth intent. | Embedded in `IntentGraph` |
| **IntentEdge** | JSON object `{source: str, target: str, type: str}` describing a temporal or causal dependency. | Embedded in `IntentGraph` |
| **IntentGraph** | Directed graph with `nodes` and `edges`; serialized per task. | `data/derived/intent_graphs/<task_id>.json` |
| **GraphConstructionLatency** | Row `{task_id, latency_sec}` recorded for each graph build. | `data/derived/graph_construction_latency.csv` |
| **ProactiveActionLog** | Row `{task_id, turn_index, condition, seed, predicted_action, is_correct, latency_sec}`. | `data/derived/inference_logs/<condition>_seed<seed>.csv` |
| **EvaluationResult** | Summary row `{condition, mean_f1, std_f1, mean_inference_latency, total_latency, latency_reduction_pct, graph_construction_mean_latency_sec, wilcoxon_p, ttest_p, bootstrap_ci_low, bootstrap_ci_high, power_estimate}`. | `data/derived/eval_results/summary.csv` |
| **Report** | Human‑readable markdown with tables, figures, and narrative. | `data/derived/eval_results/report.md` |

## Relationships
- Each **InteractionTrace** → exactly one **IntentGraph** (1‑to‑1).  
- Each **IntentGraph** → multiple **ProactiveActionLog** rows (one per turn, per seed, per condition).  
- **EvaluationResult** aggregates over the logs for a given `condition`.  
- **GraphConstructionLatency** links to the same `task_id` as the corresponding **IntentGraph**.

## Versioning & Checksums
- Every file under `data/derived/` has a SHA‑256 checksum stored in `state/projects/PROJ-942-...yaml`.  
- Transformations never overwrite source files; they create new files with a timestamped suffix if needed.  

## JSON Schema
The formal schema for `IntentGraph` is defined in `contracts/intent_graph.schema.yaml`.

---
