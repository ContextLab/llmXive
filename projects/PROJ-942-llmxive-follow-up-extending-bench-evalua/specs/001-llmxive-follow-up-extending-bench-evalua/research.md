# Research: Extend “$π$‑Bench” with Intent Graphs

## Overview
The research aims to test whether a **structured Intent Graph** can replace raw conversation history for proactive assistance while reducing inference latency. The pipeline follows the phases described in `plan.md`. All analyses are reproducible on a GitHub Actions free‑tier runner.

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| Raw Interaction Traces | Official $\pi$‑Bench release (public GitHub repo) | `datasets.load_dataset("pi_bench", data_dir="data/raw")` | Programmatic download; checksum recorded. |
| Ground‑Truth Hidden Intents | Embedded in the $\pi$‑Bench task files (where provided) | Parsed in `parse_traces.py` | Used only for scoring, never for graph construction. |
| No‑Ground‑Truth Tasks | Same $\pi$‑Bench files (missing annotation) | Deterministic LLM prompt in `build_intent_graph.py` | Confidence ≥ 0.8 → included in primary analysis. |

If any required variable is missing, the pipeline aborts with a clear error (fatal). No gated datasets are used.

## Methodology
1. **Parsing** – Convert raw JSON logs into a tidy CSV of `task_id`, `turn_index`, `speaker`, `utterance`, `ground_truth_intent` (optional).  
2. **Intent Graph Construction** – For each task:
   * If ground‑truth intents exist, they are **not** used to create nodes.
   * Otherwise, a deterministic prompt (seed = 42) is sent to the same lightweight LLM used for the agent (CPU‑only) to infer intents; confidence scores are extracted.
   * Nodes are created with fields `{id, label, confidence}`; edges encode temporal order (`source` → `target`) and special patterns (e.g., `Conflict Detected → Resolution Strategy`).
   * Graph is serialized to JSON; validated against `contracts/intent_graph.schema.yaml`.  
3. **Agent Execution** – The lightweight agent receives two inputs per turn: (a) the current user prompt, (b) the serialized Intent Graph (full graph for the task). It outputs a `ProactiveAction` label or `"no_action"`. Execution is repeated three times with seeds = {101, 202, 303}.  
4. **Baseline Execution** –  
   * **Raw‑History**: Full dialogue (truncated to 8 k tokens if needed) is fed to the reference model (same architecture as the lightweight agent).  
   * **Null‑History**: Only the current prompt is provided.  
5. **Scoring** – For each turn, compute binary F1 between predicted action and ground‑truth label (when available). Aggregate per‑task mean F1 across seeds.  
6. **Latency Measurement** – Record wall‑clock time per turn (high‑resolution `time.perf_counter`). Compute average latency per condition.  
7. **Statistical Tests** –  
   * Primary: Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null).  
   * Secondary: Paired *t*‑test.  
   * Bootstrap 10 000 resamples for 95 % CI of mean differences.  
   * Power discussion: with N≈100 tasks, detectable effect size d≈0.5 at α=0.05.  

All statistical code uses `scipy.stats` and `statsmodels.stats.weightstats`.

## Compute Decision & Rationale
*All steps are CPU‑first.* The lightweight agent is a transformer with a billion‑scale parameter count running in `torch.float32` on CPU (≈ 0.3 s per turn). No GPU is required; the pipeline fits comfortably within the 6 h CI limit.  

If future extensions require a larger model, the plan would switch to a **GPU escape hatch** (Kaggle free GPU) with 8‑bit quantization, but that is not needed for the current FRs.

## Expected Deliverables
* `data/derived/intent_graphs/*.json` – validated Intent Graphs.  
* `data/derived/inference_logs/*.csv` – actions + timestamps for each condition.  
* `data/derived/eval_results/report.md` – tables, figures, statistical conclusions.  
* Contract validation script (`tests/contract/test_intent_graph_schema.py`).  

---
