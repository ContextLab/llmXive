# Implementation Plan: Extend “$π$‑Bench: Evaluating Proactive Personal Assistant Agents in Long‑Horizon Workflows”

**Branch**: `001-intent-graph-proactive-eval` | **Date**: 2026-10-20 | **Spec**: [link to spec.md]  
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
| I. Reproducibility | All random seeds are pinned; data is fetched from a single canonical source; scripts are deterministic. |
| II. Verified Accuracy | No external citations are introduced beyond the $\pi$‑Bench paper (already verified). |
| III. Data Hygiene | Checksums recorded; transformations write new files under `data/derived/`. |
| IV. Single Source of Truth | **SSoT**: `specs/001-intent-graph-proactive-eval/plan.md`. Every figure, statistic, or interpretation traces back to this file. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Structured Memory Fidelity | Graph construction preserves temporal/causal edges; any loss is documented. |
| VII. Latency‑Performance Trade‑off Quantification | Total latency (Construction + Inference) is recorded for all conditions and reported alongside F1. |

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
│   ├── raw/                # downloaded π‑Bench raw traces
│   └── derived/
│       ├── intent_graphs/  # JSON graphs per task
│       ├── inference_logs/ # agent outputs, timestamps
│       └── eval_results/   # F1, latency, statistical tables
├── pipelines/
│   ├── download_pi_bench.py          # robust download via datasets library (streaming fallback)
│   ├── parse_traces.py               # deterministic CSV conversion with error handling
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
| **1️⃣ Parse & Normalize** | 1.1 Load raw π‑Bench traces via `datasets.load_dataset("pi_bench", ...)` (streaming fallback) 1.2 Extract turns, ground‑truth hidden intents, store as normalized CSV (`data/derived/normalized_traces.csv`) with validation and explicit error handling | FR‑001 | – |
| **2️⃣ Intent Graph Construction** | 2.1 Deterministic inference model for tasks lacking ground‑truth → `Inferred (unverified)` nodes (seed = 42) 2.2 Build directed graph with `networkx` preserving temporal order and conflict‑resolution patterns 2.3 Serialize each graph to JSON under `data/derived/intent_graphs/` 2.4 **Record per‑task graph construction latency** (seconds) 2.5 **Enforce token budget**: compute estimated token count of the JSON (≈ len(json.dumps(graph))/4) and ensure it does **not exceed** the median token budget used for the raw‑history baseline; if it does, prune lowest‑confidence nodes until it fits | FR‑002, FR‑007, FR‑009 | SC‑004 |
| **3️⃣ Baseline Executions** | 3.1 Run lightweight agent (CPU‑tractable 1B‑param model or rule‑based engine) using only the JSON graph + current prompt → log proactive actions & timestamps 3.2 **Raw‑History baseline**: truncate raw dialogue to the **same token budget** as the median Intent Graph size before feeding to the reference model (same architecture as the lightweight agent) 3.3 Run null‑history baseline (empty history) | FR‑003, FR‑004, FR‑008 | – |
| **4️⃣ Scoring & Latency** | 4.1 **Primary analysis**: compute **micro‑averaged multi‑label F1** (`sklearn.metrics.f1_score(..., average='micro')`) between predicted actions and ground‑truth actions **only for tasks that have ground‑truth intents** (exclude inferred subset to prevent circularity) 4.2 **Secondary descriptive analysis**: report total latency for tasks without ground‑truth (no F1) 4.3 Aggregate per‑task mean F1 over three seeds 4.4 Record three inference repeats per turn per seed (median used as final latency) **plus** the graph‑construction latency from Phase 2 4.5 Compute average total latency per turn for each condition (Total = Construction + Inference), and calculate percentage reduction relative to the raw‑history baseline | FR‑005, FR‑006 | SC‑001, SC‑002 |
| **5️⃣ Statistical Validation** | 5.1 Wilcoxon signed‑rank test (primary) on paired per‑task mean F1 (Graph vs Raw, Graph vs Null) 5.2 Paired *t*‑test (secondary) 5.3 Bootstrap 10 000 resamples for 95 % CI of mean differences 5.4 **Non‑parametric power check**: use bootstrap resampling (1 000 iterations) to estimate detectable effect size at N≈100 for the Wilcoxon test (report result, no formal claim) | FR‑005 | SC‑003 |
| **6️⃣ Reporting** | 6.1 Generate `data/derived/eval_results/report.md` with tables, p‑values, CI, total latency reduction, graph‑construction success rate 6.2 Create figures (F1 barplot, latency boxplot) 6.3 Log any “Null Graph” tasks for manual review | FR‑005, FR‑006 | SC‑005 |
| **7️⃣ Validation Contracts** | 7.1 Validate each JSON graph against `contracts/intent_graph.schema.yaml` 7.2 Unit tests for each pipeline stage | – | – |

All phases respect the compute budget (each script processes data streaming where possible; full π‑Bench comprises a substantial number of tasks, < 200 MB total, well within RAM).