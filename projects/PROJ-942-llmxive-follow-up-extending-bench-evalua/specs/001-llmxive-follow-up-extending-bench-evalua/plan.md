# Implementation Plan: Extend “$π$‑Bench: Evaluating Proactive Personal Assistant Agents in Long‑Horizon Workflows”

**Branch**: `001-intent-graph-proactive-eval` | **Date**: 2026-10-21 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-intent-graph-proactive-eval/spec.md`

## Summary
The project builds a deterministic, CPU‑only pipeline that (1) parses raw π‑Bench interaction traces, (2) constructs a directed **Intent Graph** per task using a **deterministic LLM prompt** (fixed seed, greedy decoding), (3) runs a modest‑size CPU‑tractable agent that consumes only the Intent Graph (plus the current turn) to produce proactive actions, (4) runs two baselines (raw‑history with model‑max context truncation, and null‑history), (5) computes micro‑averaged F1, latency, and statistical significance, and (6) reports results with full reproducibility.

All functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑005) are addressed; each is mapped to a concrete phase or task below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `datasets>=2.14`, `networkx>=3.2`, `scikit-learn>=1.4`, `torch>=2.2` (CPU‑only), `transformers>=4.40` (for the deterministic LLM used in graph construction), `pandas>=2.2`, `numpy>=1.26`, `matplotlib>=3.8`, `pyyaml>=6.0`, `statsmodels>=0.14`, `spacy>=3.7` (only for optional preprocessing, not for intent inference)  
- **Storage**: Files under `data/` (raw traces, derived CSV/JSON, logs)  
- **Testing**: `pytest` + contract validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: Total wall‑clock time ≤ 6 h, peak RAM ≤ 7 GB.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (`seed.py`), data is downloaded via a single canonical HuggingFace identifier, scripts are deterministic. |
| II. Verified Accuracy | No new external citations are introduced; only the publicly‑available π‑Bench dataset is referenced. |
| III. Data Hygiene | Every file written under `data/` receives a SHA‑256 checksum recorded in `state/projects/PROJ-942-...yaml`. Transformations write new files; raw files remain unchanged. |
| IV. Single Source of Truth | All figures, tables, and numeric claims trace back to files produced in `data/derived/` and the code that generated them. |
| V. Versioning Discipline | Artifact hashes are computed automatically; any change updates the project state file. |
| VI. Structured Memory Fidelity | The Intent Graph preserves temporal order (edges `temporal`) and explicit conflict‑resolution patterns; any pruning is documented with confidence scores. |
| VII. Latency‑Performance Trade‑off Quantification | **Online** inference latency per turn is recorded for each condition; **offline** graph‑construction latency is reported separately (not mixed into the online reduction claim). |

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
│   ├── raw/                # π‑Bench raw JSON files (downloaded)
│   └── derived/
│       ├── normalized_traces.csv
│       ├── intent_graphs/          # one JSON per task
│       ├── graph_construction_latency.csv
│       ├── inference_logs/
│       │   ├── lightweight_seed101.csv
│       │   ├── raw_seed101.csv
│       │   └── null_seed101.csv
│       └── eval_results/
│           ├── summary.csv
│           ├── report.md
│           └── figures/
│               ├── f1_barplot.png
│               └── latency_boxplot.png
├── pipelines/
│   ├── download_pi_bench.py
│   ├── parse_traces.py
│   ├── build_intent_graph_llm.py   # deterministic LLM‑based extractor
│   ├── run_lightweight_agent.py
│   ├── run_raw_baseline.py
│   ├── run_null_baseline.py
│   └── evaluate.py
└── utils/
    └── seed.py
tests/
└── contract/
    └── test_intent_graph_schema.py
```

## Phase Overview & FR/SC Mapping
| Phase | Tasks (ordered) | FR(s) addressed | SC(s) addressed |
|-------|-----------------|-----------------|-----------------|
| **0️⃣ Setup** | 0.1 Install dependencies (requirements.txt) 0.2 Pin seeds via `utils/seed.py` | – | – |
| **1️⃣ Data Acquisition** | 1.1 `download_pi_bench.py`: programmatic download using `datasets.load_dataset("pi_bench", streaming=True)`; verify SHA‑256 checksum; retry up to 3 times on failure. | – | – |
| **2️⃣ Parse & Normalize** | 2.1 `parse_traces.py`: extract `task_id`, `turn_index`, `speaker`, `utterance`, optional `ground_truth_intent`; write `normalized_traces.csv`. | FR‑001 | – |
| **3️⃣ Intent Graph Construction** | 3.1 Load `normalized_traces.csv`. 3.2 For each turn, invoke a **deterministic LLM prompt** (e.g., `google/flan-t5-small`) with a fixed seed (`torch.manual_seed(42)`, `torch.backends.cudnn.deterministic=True`) and greedy decoding to infer intents when ground‑truth is missing; assign confidence = 1.0 for exact matches, 0.8 for partial matches, 0.0 otherwise. 3.3 Build a `networkx.DiGraph` with nodes `{id, label, confidence}` and edges `{source, target, type}` (temporal edges between consecutive turns; special edges for detected conflict patterns). 3.4 Serialize each graph to JSON under `intent_graphs/`. 3.5 Record per‑task wall‑clock time in `graph_construction_latency.csv`. 3.6 Enforce **model‑max token budget** (e.g., 2048 tokens) by estimating token count (`len(json.dumps(graph))/4`). If exceeded, prune lowest‑confidence nodes iteratively, logging pruning actions. | FR‑002, FR‑007, FR‑009 | SC‑004 |
| **4️⃣ Baseline & Agent Execution** | 4.1 `run_lightweight_agent.py`: load each Intent Graph, current turn text, feed to a **CPU‑only 200 M‑parameter OPT model** (`facebook/opt-125m`); output `ProactiveAction` or `"no_action"`; log latency per turn. Repeat for seeds = {101, 202, 303}. 4.2 `run_raw_baseline.py`: for each turn, **use the full dialogue history**; if the total token count exceeds the model’s maximum context (2048 tokens), truncate the *oldest* tokens to fit. Feed the (possibly truncated) history to the same OPT model; log latency. 4.3 `run_null_baseline.py`: feed only the current prompt (no prior context) to the model; log latency. | FR‑003, FR‑004, FR‑008 | – |
| **5️⃣ Scoring & Latency Aggregation** | 5.1 `evaluate.py`: for tasks **with ground‑truth intents**, compute micro‑averaged multi‑label F1 (`sklearn.metrics.f1_score(..., average='micro')`) between predicted and true actions for each seed. 5.2 Aggregate per‑task mean F1 across seeds. 5.3 Compute **average online inference latency** per turn for each condition; add **offline graph‑construction latency** (from Phase 3) as a separate column (`graph_construction_mean_latency_sec`). 5.4 Export `summary.csv` with columns: `condition, mean_f1, std_f1, mean_online_latency, total_latency, latency_reduction_pct, graph_construction_mean_latency_sec`. | FR‑005, FR‑006 | SC‑001, SC‑002 |
| **6️⃣ Statistical Validation** | 6.1 Primary test: Wilcoxon signed‑rank on paired per‑task mean F1 (Graph vs Raw, Graph vs Null). 6.2 Secondary test: paired *t*‑test. 6.3 Bootstrap 10 000 resamples for 95 % CI of mean differences. 6.4 Non‑parametric power estimate via 1 000 bootstrap samples (report detectable effect size). 6.5 Record all p‑values, CIs, and power estimate in `summary.csv`. | FR‑005 | SC‑003 |
| **7️⃣ Reporting** | 7.1 Generate `report.md` with tables, p‑values, CIs, latency reduction (online only) and **separate** offline graph‑construction cost, and graph‑construction success rate (≥ 95 %). 7.2 Create PNG figures (`f1_barplot.png`, `latency_boxplot.png`). 7.3 List any tasks flagged as “Null Graph” for manual review. | FR‑005, FR‑006 | SC‑005 |
| **8️⃣ Contract Validation** | 8.1 Run `pytest tests/contract` to validate each JSON graph against `contracts/intent_graph.schema.yaml`. 8.2 Fail the pipeline if any graph violates the schema. | – | – |

## Compute Feasibility
All steps run on CPU only. The deterministic LLM used for intent extraction is a small model (on the order of tens of millions of parameters) that processes a turn in < 0.3 s on the CI runner. A large‑scale OPT model processes a turn within a short latency. With ~100 tasks × ≈ 30 turns each, total inference time stays well under the 6 h CI limit. Graph construction is lightweight (LLM inference on short prompts) and fits within RAM limits. No GPU escape hatch is required.

## Risk Mitigation
- **Download reliability (T001)**: `download_pi_bench.py` now uses HuggingFace `datasets` streaming with three automatic retries and SHA‑256 checksum verification; aborts with a clear error if the dataset cannot be retrieved.
- **Latency accounting**: Offline graph‑construction cost is reported separately; the primary latency‑reduction claim (SC‑002) concerns only **online inference**. This avoids accounting confounds.
- **Determinism**: Fixed random seeds (`torch.manual_seed`, `numpy.random.seed`, `random.seed`) guarantee identical graphs and model outputs across runs. The LLM prompt uses greedy decoding to remain deterministic.
- **Baseline fairness**: Raw‑history baseline uses the model’s actual maximum context window (e.g., 2048 tokens) rather than a token budget derived from the graph, ensuring a fair comparison.

---

