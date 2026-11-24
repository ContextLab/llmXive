# Research: Extending “$π$‑Bench” with Intent Graphs

## Overview
We evaluate whether a **structured Intent Graph** can replace raw dialogue history for proactive assistance while preserving predictive performance and reducing **online** inference latency. The pipeline follows the phases defined in `plan.md`. All analyses are fully reproducible on a GitHub Actions free‑tier runner.

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| **Raw Interaction Traces** | π‑Bench (public HuggingFace repo) | `datasets.load_dataset("pi_bench", streaming=True)` | Programmatic download; SHA‑256 checksum recorded. |
| **Ground‑Truth Hidden Intents** | Embedded in π‑Bench task files (where provided) | Extracted by `parse_traces.py` | Used **only** for scoring; never for graph construction (FR‑009). |
| **Missing‑Intent Inference** | Same π‑Bench files (no annotation) | Handled by deterministic LLM (`google/flan-t5-small`) in `infer_missing_intents.py` | Nodes labeled “Inferred (unverified)”; confidence ≥ 0.8 included in primary analysis; lower‑confidence nodes are pruned. |

If any required column (e.g., `utterance`) is missing, the pipeline aborts with a clear error; no gated datasets are used.

## Methodology

1. **Parsing** – `parse_traces.py` converts each raw JSON task into `normalized_traces.csv` with columns `task_id`, `turn_index`, `speaker`, `utterance`, `ground_truth_intent` (optional). Validation ensures every turn has a non‑empty utterance.

2. **Missing‑Intent Inference** – `infer_missing_intents.py` runs a **deterministic small LLM** prompt  
   `"Extract the user intent from the following utterance:"`  
   with fixed seed (`torch.manual_seed(42)`) and greedy decoding. The script outputs `inferred_intents.csv` (`task_id, turn_index, inferred_intent, confidence`). Confidence is set to 1.0 for exact matches, 0.8 for partial matches, and 0.0 otherwise. Wall‑clock time for this step is recorded in `graph_construction_latency.csv` (offline LLM cost).

3. **Intent Graph Construction (Inferred‑Only)** – `build_intent_graph.py` merges `normalized_traces.csv` + `inferred_intents.csv`. It creates a `networkx.DiGraph` where:
   - **Nodes**: `{id, label, confidence}` derived **only** from inferred intents (ground‑truth never used).  
   - **Temporal edges** between consecutive turns (`type: "temporal"`).  
   - **Conflict‑resolution edges** detected via rule‑based regex (`type: "conflict_resolution"`).  
   The graph is serialized to JSON (`intent_graphs/<task_id>.json`). Token count is estimated; if it exceeds the model’s max‑context (2048 tokens), the lowest‑confidence nodes are pruned iteratively, and each pruning action is logged. Per‑task wall‑clock time is stored in `graph_construction_latency.csv`.

4. **Ground‑Truth‑Only Graph (Control)** – `build_intent_graph_gt.py` builds a graph **using only** ground‑truth hidden intents (when available) and **no** inferred intents. This control isolates the effect of LLM‑inferred intents on downstream performance (addresses methodology‑e0443735).

5. **Agent & Baseline Execution** –  
   - **Lightweight Agent**: `run_lightweight_agent.py` loads the inferred‑only Intent Graph + current turn, feeds them to a CPU‑only `facebook/opt-125m` (`torch.device("cpu")`). It outputs a `ProactiveAction` label or `"no_action"`; latency per turn is recorded. Runs for seeds = {101, 202, 303}.  
   - **Raw‑History Baseline**: `run_raw_baseline.py` feeds the full dialogue history, truncating **oldest** tokens to the model’s max‑context (2048) when necessary. This ensures a fair token‑budget comparison (methodology‑0996ea35).  
   - **Null‑History Baseline**: `run_null_baseline.py` feeds only the current turn (no history).  
   - **Ground‑Truth‑Only Graph Agent** (optional): `run_lightweight_agent_gt.py` runs the agent on the control graphs to assess the contribution of inferred intents.

6. **Scoring & Latency Aggregation** – `evaluate.py`:
   - For turns with ground‑truth intents, compute **single‑label** accuracy, precision, recall, and F1 using `sklearn.metrics.classification_report` (addresses scientific_soundness‑907bb9d1).  
   - Aggregate per‑task mean metrics across seeds.  
   - Compute **online** average inference latency per turn for each condition.  
   - Merge **offline** latency components (LLM inference + graph‑construction) from `graph_construction_latency.csv` to produce a total pipeline latency column.  
   - Export `summary.csv` with columns: `condition, mean_accuracy, mean_f1, std_f1, mean_online_latency, total_latency, latency_reduction_pct, graph_construction_mean_latency_sec, success_rate_graphs`.

7. **Statistical Validation** –  
   - **A priori power analysis** (pre‑data collection): using paired Wilcoxon, target effect size Cohen’s d = 0.3, α = 0.05, power = 0.8 yields a required N ≈ 68 tasks; with ≈ 100 tasks the study is adequately powered (addresses methodology‑3b6aee12).  
   - **Primary test**: Wilcoxon signed‑rank on paired per‑task mean F1 (Graph vs Raw, Graph vs Null, Graph vs Graph‑GT).  
   - **Secondary test**: paired *t*‑test.  
   - **Bootstrap**: 10 000 resamples for 95 % CI of mean differences.  
   - Power estimate is recorded in `summary.csv`.

8. **Reporting** – `report.md` contains:
   - Tables of accuracy/F1, latency, p‑values, CIs, graph‑construction success rate (≥ 95 %), offline latency breakdown, and discussion of the “lightweight” claim (online only).  
   - PNG figures (`f1_barplot.png`, `latency_boxplot.png`).  
   - List of any “Null Graph” tasks for manual review.

## Compute Decision & Rationale
All components are **CPU‑first**:
- Deterministic LLM for missing intents (`flan-t-small`, a small‑parameter model) processes a turn rapidly on the CI runner.  
- OPT‑[model size] inference takes approximately a few‑tenths of a second per turn.  
- With a substantial number of tasks × ≈ 30 turns each, total compute ≈ 2 h, well under the 6 h CI limit and 7 GB RAM budget.  

No GPU escape hatch is required. Future extensions may use a Kaggle free GPU with 8‑bit quantization, but this is outside current scope.

## Addressing Reviewer Feedback
- **Latency accounting**: Offline LLM inference and graph‑construction times are measured, reported, and distinguished from online inference latency (SC‑002).  
- **Lightweight claim**: The agent remains lightweight at inference; the one‑time LLM cost is disclosed and not conflated with online latency.  
- **Baseline fairness**: Both raw and graph conditions respect the same max‑token budget; raw truncates oldest tokens, graph prunes lowest‑confidence nodes only when necessary (methodology‑0996ea35).  
- **Construct validity**: Added a ground‑truth‑only graph control (methodology‑e0443735) to isolate the effect of inferred intents.  
- **FR‑009 compliance**: Graph construction never uses ground‑truth hidden intents; they are reserved for scoring only (spec_coverage‑90a83e60).  
- **Independence of predictor/target**: Ground‑truth intents are used solely for evaluation, preserving independence (scientific_soundness‑864e6779).  
- **Metric appropriateness**: Switched to single‑label accuracy/F1 (scientific_soundness‑907bb9d1).  

## Expected Deliverables
- `data/derived/intent_graphs/*.json` – validated inferred‑only Intent Graphs.  
- `data/derived/intent_graphs_gt/*.json` – ground‑truth‑only control graphs.  
- `data/derived/graph_construction_latency.csv` – per‑task construction time and offline LLM inference time.  
- `data/derived/inference_logs/*.csv` – actions, correctness flags, latency per turn for each condition and seed.  
- `data/derived/eval_results/summary.csv` – aggregated metrics, statistical test results, latency reductions, offline latency, and graph‑construction success rate.  
- `data/derived/eval_results/report.md` – narrative summary, tables, and interpretation.  
- PNG figures (`f1_barplot.png`, `latency_boxplot.png`).  
- Contract validation script (`tests/contract/test_intent_graph_schema.py`).  

---

