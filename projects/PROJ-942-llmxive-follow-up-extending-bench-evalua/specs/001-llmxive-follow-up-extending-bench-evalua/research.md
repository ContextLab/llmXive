# Research: Extend “$π$‑Bench” with Intent Graphs

## Overview
The research tests whether a **structured Intent Graph** can replace raw conversation history for proactive assistance while reducing inference latency. The pipeline follows the phases described in `plan.md`. All analyses are reproducible on a GitHub Actions free‑tier runner.

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| Raw Interaction Traces | π‑Bench (public repository) | `datasets.load_dataset("pi_bench", data_dir="data/raw")` | Programmatic download; checksum recorded. |
| Ground‑Truth Hidden Intents | Embedded in the π‑Bench task files (where provided) | Parsed in `parse_traces.py` | Used **only** for scoring, never for graph construction. |
| No‑Ground‑Truth Tasks | Same π‑Bench files (missing annotation) | Deterministic LLM prompt in `build_intent_graph.py` (seed = 42) | Confidence ≥ 0.8 → included in **latency and descriptive analysis ONLY**. No F1 scoring performed on this subset to avoid circularity. |

If any required variable is missing, the pipeline aborts with a clear error (fatal). No gated datasets are used.

## Methodology
1. **Parsing** – Convert raw JSON logs into a tidy CSV of `task_id`, `turn_index`, `speaker`, `utterance`, `ground_truth_intent` (optional).  
2. **Intent Graph Construction** – For each task:  
   * If ground‑truth intents exist, they are **not** used to create nodes.  
   * Otherwise, a **deterministic inference model** (seed = 42) is invoked with a fixed prompt to infer intents; confidence scores are extracted.  
   * Nodes are created with fields `{id, label, confidence}`; edges encode temporal order (`source` → `target`) and special patterns (e.g., `Conflict Detected → Resolution Strategy`).  
   * Graph is serialized to JSON; **graph‑construction latency** is recorded per task.  
   * **Token‑budget enforcement**: estimated token count of the JSON is measured; if it exceeds the median token budget used for the raw‑history baseline, lowest‑confidence nodes are pruned until it fits.  
   * Graph is validated against `contracts/intent_graph.schema.yaml`.  
3. **Agent Execution** – The lightweight agent receives two inputs per turn: (a) the current user prompt, (b) the serialized Intent Graph (full graph for the task). It outputs a `ProactiveAction` label or `"no_action"`. Execution is repeated three times with seeds = {101, 202, 303}.  
4. **Baseline Execution** –  
   * **Raw‑History**: Full dialogue is **truncated to the same token budget** as the median Intent Graph size before being fed to the reference model (same architecture as the lightweight agent).  
   * **Null‑History**: Only the current prompt is provided.  
5. **Scoring** – For each turn **with ground‑truth intent**, compute **micro‑averaged multi‑label F1** (`sklearn.metrics.f1_score(..., average='micro')`) between predicted actions and ground‑truth labels.  
   * Aggregate per‑task mean F1 across seeds.  
   * Tasks lacking ground‑truth are strictly excluded from F1 calculations.  
6. **Latency Measurement** – Record wall‑clock time per turn for inference (high‑resolution `time.perf_counter`). Total latency for the Graph condition is defined as: `Total Latency = Graph Construction Time + Inference Time`. Compute average total latency per condition and percentage reduction relative to the raw‑history baseline.  
7. **Statistical Tests** –  
   * Primary: Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null).  
   * Secondary: Paired *t*‑test.  
   * Bootstrap 10 000 resamples for 95 % CI of mean differences.  
   * **Non‑parametric power check**: use bootstrap resampling (1 000 iterations) to estimate the detectable effect size at N≈100 for the Wilcoxon test.  

All statistical code uses `scipy.stats` and `statsmodels` (non‑parametric utilities).  

## Compute Decision & Rationale
*All steps are CPU‑first.* The lightweight agent is a transformer with a billion‑scale parameter count running in `torch.float` on CPU (with a sub‑second latency per turn). No GPU is required; the pipeline fits comfortably within the allotted CI time limit..  

If future extensions require a larger model, the plan would switch to a **GPU escape hatch** (Kaggle free GPU) with 8‑bit quantization, but that is not needed for the current FRs.

## Expected Deliverables
* `data/derived/intent_graphs/*.json` – validated Intent Graphs.  
* `data/derived/inference_logs/*.csv` – actions + timestamps for each condition.  
* `data/derived/eval_results/report.md` – tables, figures, statistical conclusions, total latency (including graph construction).  
* Contract validation script (`tests/contract/test_intent_graph_schema.py`).  