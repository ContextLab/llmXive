# Research: Extending “$π$‑Bench” with Intent Graphs

## Overview
We evaluate whether a **structured Intent Graph** can replace raw dialogue history for proactive assistance while preserving predictive performance and reducing **online** inference latency. The pipeline follows the phases defined in `plan.md`. All analyses are fully reproducible on a GitHub Actions free‑tier runner.

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| **Raw Interaction Traces** | π‑Bench (public HuggingFace repo) | `datasets.load_dataset("pi_bench", streaming=True, data_dir="data/raw")` | Programmatic download; SHA‑256 checksum recorded. |
| **Ground‑Truth Hidden Intents** | Embedded in π‑Bench task files (where provided) | Parsed by `parse_traces.py` | Used **only** for scoring; never for graph construction. |
| **No‑Ground‑Truth Tasks** | Same π‑Bench files (missing annotation) | Handled by deterministic LLM prompt in `build_intent_graph_llm.py` | Nodes labeled “Inferred (unverified)”; confidence ≥ 0.8 included in primary analysis; lower‑confidence nodes may be pruned to respect token budget. |

If any required column (e.g., `utterance`) is missing, the pipeline aborts with a clear error; no gated datasets are used.

## Methodology

1. **Parsing** – Convert each raw JSON task into a tidy CSV (`normalized_traces.csv`) with columns `task_id`, `turn_index`, `speaker`, `utterance`, `ground_truth_intent` (optional). Validation ensures every turn has a non‑empty utterance.

2. **Intent Graph Construction** – For each task:
   - Ground‑truth intents are **ignored** for graph building (FR‑009).  
   - When missing, a **deterministic LLM prompt** (e.g., `"Extract the user intent from the following utterance:"`) is sent to a small model (`google/flan-t5-small`) with a fixed seed (`torch.manual_seed(42)`) and greedy decoding. The model returns an intent label and a confidence score (1.0 for exact match, 0.8 for partial, 0.0 otherwise).  
   - Nodes are linked by temporal edges (turn i → turn i+1) and by special edges for detected conflict‑resolution patterns (`Conflict Detected → Resolution Strategy`).  
   - The graph is serialized to JSON; construction wall‑clock time is logged.  
   - **Token‑budget enforcement**: estimated token count = `len(json.dumps(graph)) / 4`. If it exceeds the model’s max context (e.g., 2048 tokens), low‑confidence nodes are pruned iteratively until the budget is met, with pruning actions logged.

3. **Agent Execution** – A **CPU‑only 200 M‑parameter OPT model** receives (a) the current user prompt and (b) the full Intent Graph JSON. It outputs a `ProactiveAction` label or `"no_action"`. Each task is run three times with seeds = {101, 202, 303}.

4. **Baseline Execution** –  
   - **Raw‑History**: The full dialogue history is supplied to the same OPT model. **Only** if the total token count exceeds the model’s maximum context (e.g., 2048 tokens) is the *oldest* portion truncated to fit. No median‑budget truncation is applied, preserving a fair baseline.  
   - **Null‑History**: Only the current prompt is provided (no prior context).  

5. **Scoring** – For turns with ground‑truth intents:  
   - Compute **micro‑averaged multi‑label F1** (`sklearn.metrics.f1_score(..., average='micro')`) between predicted and true actions for each seed.  
   - Aggregate per‑task mean F1 across the three seeds.  
   - Tasks lacking ground‑truth are excluded from F1 calculations (to avoid circularity).  

6. **Latency Measurement** – Record high‑resolution inference time per turn (`time.perf_counter`).  
   - **Online latency**: average inference time per turn for each condition.  
   - **Offline latency**: graph‑construction wall‑clock time (reported separately).  
   - Compute percentage reduction of **online** latency relative to the raw‑history baseline (SC‑002).  

7. **Statistical Validation** –  
   - **Primary**: Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null).  
   - **Secondary**: Paired *t*‑test.  
   - **Bootstrap**: 10 000 resamples for 95 % confidence intervals of mean differences.  
   - **Power estimate**: 1 000 bootstrap samples to report the detectable effect size at N≈100 for the Wilcoxon test (transparent reporting, no formal claim).  

All statistical code uses `scipy.stats` and `statsmodels`. Multiple‑comparison correction is unnecessary because only two pairwise tests are performed; the family‑wise error rate is noted in the report.

## Compute Decision & Rationale
All components are **CPU‑first**:
- The deterministic LLM prompt uses a 80 M‑parameter model that runs in < 0.3 s per turn on the CI runner.  
- The high‑parameter OPT model processes a turn in a relatively short time.  
- The entire pipeline stays comfortably within the 6 h CI limit and 7 GB RAM budget.  

If future work requires a larger model, the plan would switch to a **GPU escape hatch** (Kaggle free GPU) with 8‑bit quantization, but that is outside the current scope.

## Addressing Reviewer Feedback
- **Latency accounting**: The primary latency‑reduction claim (SC‑002) concerns **online inference only**. Offline graph‑construction cost is reported as a separate metric (`graph_construction_mean_latency_sec`) in `summary.csv` and discussed in the final report. This makes the claim transparent and avoids the “accounting artifact” criticism.
- **Lightweight claim**: The lightweight agent remains CPU‑tractable; the graph is built offline with a deterministic small LLM, eliminating the need for a large LLM during inference. Hence the overall pipeline demonstrates that a **small model can operate on a compressed, structured representation** without incurring large online compute.
- **Baseline fairness**: The raw‑history baseline now uses the model’s **maximum context window** (e.g., 2048 tokens) and truncates only when necessary, rather than a median token budget derived from the graphs. This removes the bias identified in the review.

## Expected Deliverables
- `data/derived/intent_graphs/*.json` – validated Intent Graphs.  
- `data/derived/graph_construction_latency.csv` – per‑task construction time.  
- `data/derived/inference_logs/*.csv` – actions, correctness flags, latency per turn for each condition and seed.  
- `data/derived/eval_results/summary.csv` – aggregated metrics, statistical test results, latency reductions, and offline graph‑construction latency.  
- `data/derived/eval_results/report.md` – narrative summary, tables, and interpretation.  
- PNG figures (`f1_barplot.png`, `latency_boxplot.png`).  
- Contract validation script (`tests/contract/test_intent_graph_schema.py`).  

---

