# Implementation Plan: Extend “$π$‑Bench: Evaluating Proactive Personal Assistant Agents in Long‑Horizon Workflows”

**Branch**: `001-intent-graph-proactive-eval` | **Date**: 2026-10-17 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-intent-graph-proactive-eval/spec.md`

## Summary
The core requirement is to replace raw interaction histories with a structured **Intent Graph** and evaluate whether a lightweight CPU‑tractable agent can achieve parity with a raw‑history baseline while reducing latency. The plan implements:

* **FR‑001–FR‑009** – parsing, graph construction, inference, baselines, scoring, latency measurement, deterministic inference for missing annotations, null‑history baseline, and isolation of ground‑truth from graph construction.  
* **SC‑001–SC‑005** – performance thresholds, latency reporting, statistical testing, graph‑construction success rate, and reproducibility across seeds.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets>=2.14`, `networkx>=3.2`, `scikit‑learn>=1.4`, `torch>=2.2` (CPU‑only), `pandas>=2.2`, `numpy>=1.26`, `matplotlib>=3.8`, `pyyaml>=6.0`, `statsmodels>=0.14`  
**Storage**: Files under `data/` (raw traces, derived graphs, logs)  
**Testing**: `pytest` + contract validation (`jsonschema`)  
**Target Platform**: Linux runner on GitHub Actions (Multiple CPU cores, ~7 GB RAM) – all steps are CPU‑first; no GPU is required.  
**Constraints**: Must finish within a single CI job (< 6 h).  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | All random seeds are pinned; data is fetched from a single canonical URL; scripts are deterministic. |
| II. Verified Accuracy | No external citations are introduced beyond the $\pi$‑Bench paper (already verified). |
| III. Data Hygiene | Checksums recorded; transformations write new files under `data/derived/`. |
| IV. Single Source of Truth | **SSoT**: `specs/001-llmxive-follow-up-extending-bench-evalua/plan.md`. Every figure, statistic, or interpretation traces back to this file. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Structured Memory Fidelity | Graph construction preserves temporal/causal edges; any loss is documented. |
| VII. Latency‑Performance Trade‑off Quantification | Latency per turn is recorded for all conditions and reported alongside F1. |

## Project Structure
```text
specs/001-intent-graph-proactive-eval/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── intent_graph.schema.yaml

src/
├── data/
│   ├── raw/                # downloaded $\pi$‑Bench raw traces
│   └── derived/
│       ├── intent_graphs/  # JSON graphs per task
│       ├── inference_logs/ # agent outputs, timestamps
│       └── eval_results/   # F1, latency, statistical tables
├── pipelines/
│   ├── parse_traces.py
│   ├── build_intent_graph.py
│   ├── run_lightweight_agent.py
│   ├── run_raw_baseline.py
│   ├── run_null_baseline.py
│   └── evaluate.py
└── utils/
    └── seed.py
```

## Phase Overview & FR/SC Mapping
| Phase | Tasks (ordered) | FR addressed | SC addressed |
|-------|-----------------|--------------|--------------|
| **0️⃣ Setup** | 0.1 Install dependencies (requirements.txt) 0.2 Pin seeds | – | – |
| **1️⃣ Parse & Normalize** | 1.1 Load raw $\pi$‑Bench traces (programmatic download) 1.2 Extract turns, ground‑truth hidden intents, store as normalized CSV (`data/derived/normalized_traces.csv`) | FR‑001 | – |
| **2️⃣ Intent Graph Construction** | 2.1 **Separate inference model**: deterministic LLM (or rule‑based) distinct from the Graph‑condition agent, fixed seed, for tasks lacking ground‑truth → `Inferred (unverified)` nodes 2.2 Build directed graph using `networkx` preserving temporal order and conflict‑resolution patterns 2.3 Serialize each graph to JSON under `data/derived/intent_graphs/` | FR‑002, FR‑007, FR‑009 (updated to note distinct model) | SC‑004 |
| **3️⃣ Baseline Executions** | 3.1 Run lightweight agent (CPU‑tractable 1B‑param model or rule‑based engine) using only the JSON graph + current prompt → log proactive actions & timestamps 3.2 **Raw‑History baseline**: feed the **same token budget** as the graph (truncate raw dialogue to the graph token count, e.g., ≤ 2 k tokens) 3.3 Run null‑history baseline (empty history) | FR‑003, FR‑004, FR‑008 | – |
| **4️⃣ Scoring & Latency** | 4.1 **Primary analysis**: compute per‑turn F1 against ground‑truth actions **only for tasks that have ground‑truth intents** 4.2 **Secondary analysis**: repeat scoring on tasks where inferred intents have confidence ≥ 0.8 (high‑confidence subset) 4.3 Aggregate per‑task mean F1 over three seeds 4.4 Record **three latency repeats per turn per seed** (median used as final latency) 4.5 Compute average inference latency per turn for each condition | FR‑005, FR‑006 | SC‑001, SC‑002 |
| **5️⃣ Statistical Validation** | 5.1 Wilcoxon signed‑rank test (primary) on paired per‑task mean F1 (Graph vs Raw, Graph vs Null) 5.2 Paired *t*‑test (secondary) 5.3 Bootstrap 95 % CI for mean differences 5.4 **Power analysis**: using `statsmodels.stats.power.TTestPower` to show N≈100 yields ≈80 % power to detect d=0.5 at α=0.05; report limitation if effect smaller | FR‑005 | SC‑003 |
| **6️⃣ Reporting** | 6.1 Generate `data/derived/eval_results/report.md` with tables, p‑values, CI, latency reduction, graph‑construction success rate 6.2 Create figures (F1 barplot, latency boxplot) 6.3 Log any “Null Graph” tasks for manual review | FR‑005, FR‑006 | SC‑005 |
| **7️⃣ Validation Contracts** | 7.1 Validate each JSON graph against `contracts/intent_graph.schema.yaml` 7.2 Unit tests for each pipeline stage | – | – |

All phases respect the compute budget (each script processes data streaming where possible; full $\pi$‑Bench ≈ 100 tasks, < 200 MB total, well within RAM).

---


## projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/specs/001-llmxive-follow-up-extending-bench-evalua/research.md

# Research: Extend “$π$‑Bench” with Intent Graphs

## Overview
The research aims to test whether a **structured Intent Graph** can replace raw conversation history for proactive assistance while reducing inference latency. The pipeline follows the phases described in `plan.md`. All analyses are reproducible on a GitHub Actions free‑tier runner.

## Dataset Strategy
| Role | Source | Loader | Notes |
|------|--------|--------|-------|
| Raw Interaction Traces | Official $\pi$‑Bench release (public GitHub repo) | `datasets.load_dataset("pi_bench", data_dir="data/raw")` | Programmatic download; checksum recorded. |
| Ground‑Truth Hidden Intents | Embedded in the $\pi$‑Bench task files (where provided) | Parsed in `parse_traces.py` | Used only for scoring, never for graph construction. |
| No‑Ground‑Truth Tasks | Same $\pi$‑Bench files (missing annotation) | Deterministic LLM prompt in `build_intent_graph.py` | Confidence ≥ 0.8 → included in secondary analysis. |

If any required variable is missing, the pipeline aborts with a clear error (fatal). No gated datasets are used.

## Methodology
1. **Parsing** – Convert raw JSON logs into a tidy CSV of `task_id`, `turn_index`, `speaker`, `utterance`, `ground_truth_intent` (optional).  
2. **Intent Graph Construction** – For each task:
   * If ground‑truth intents exist, they are **not** used to create nodes.
   * Otherwise, a **separate deterministic inference model** (distinct from the Graph‑condition agent) is invoked with a fixed seed (42) to infer intents; confidence scores are extracted.
   * Nodes are created with fields `{id, label, confidence}`; edges encode temporal order (`source` → `target`) and special patterns (e.g., `Conflict Detected → Resolution Strategy`).
   * Graph is serialized to JSON; validated against `contracts/intent_graph.schema.yaml`.  
3. **Agent Execution** – The lightweight agent receives two inputs per turn: (a) the current user prompt, (b) the serialized Intent Graph (full graph for the task). It outputs a `ProactiveAction` label or `"no_action"`. Execution is repeated three times with seeds = {101, 202, 303}.  
4. **Baseline Execution** –  
   * **Raw‑History**: Full dialogue is **truncated to the same token budget** used by the Intent Graph (e.g., ≤ 2 k tokens) before being fed to the reference model (same architecture as the lightweight agent).  
   * **Null‑History**: Only the current prompt is provided.  
5. **Scoring** –  
   * **Primary analysis**: For tasks that have ground‑truth hidden intents, compute binary F1 between predicted action and ground‑truth label per turn.  
   * **Secondary analysis**: For tasks where inferred intents have confidence ≥ 0.8, repeat the same F1 computation; results are reported separately.  
   * Aggregate per‑task mean F1 across seeds.  
6. **Latency Measurement** – For each turn, record three latency measurements (high‑resolution `time.perf_counter`) per seed; use the median of the three as the final latency value. Compute average latency per condition.  
7. **Statistical Tests** –  
   * Primary: Wilcoxon signed‑rank test on paired per‑task mean F1 (Graph vs Raw, Graph vs Null).  
   * Secondary: Paired *t*‑test.  
   * Bootstrap 10 000 resamples for 95 % CI of mean differences.  
 * **Power analysis**: Using `statsmodels.stats.power.TTestPower`, N≈100 tasks provides [deferred] power to detect an effect size d = 0.5 at α = 0.05. If the observed effect is smaller, the limitation is reported.

All statistical code uses `scipy.stats` and `statsmodels.stats.weightstats`.

## Compute Decision & Rationale
*All steps are CPU‑first.* The lightweight agent is a transformer with a substantial parameter count. running in `torch.float32` on CPU (≈ a brief interval per turn). No GPU is required; the pipeline fits comfortably within the 6 h CI limit.  

If future extensions require a larger model, the plan would switch to a **GPU escape hatch** (Kaggle free GPU) with 8‑bit quantization, but that is not needed for the current FRs.

## Expected Deliverables
* `data/derived/intent_graphs/*.json` – validated Intent Graphs.  
* `data/derived/inference_logs/*.csv` – actions + timestamps for each condition.  
* `data/derived/eval_results/report.md` – tables, figures, statistical conclusions.  
* Contract validation script (`tests/contract/test_intent_graph_schema.py`).  

---

