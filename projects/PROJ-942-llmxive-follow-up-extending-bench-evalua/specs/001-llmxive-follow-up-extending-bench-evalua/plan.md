# Implementation Plan: Extend “$π$‑Bench: Evaluating Proactive Personal Assistant Agents in Long‑Horizon Workflows”

**Branch**: `001-intent-graph-proactive-eval` | **Date**: 2026-10-22 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-intent-graph-proactive-eval/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads the public π‑Bench dataset, (2) parses raw interaction traces, (3) constructs deterministic Intent Graphs **without** using ground‑truth hidden‑intent labels, (4) runs a lightweight CPU‑tractable agent on the graph, (5) runs two baselines (raw‑history with max‑context truncation, and null‑history), (6) computes single‑label accuracy/precision/recall/F1, online inference latency, and offline graph‑construction latency, (7) performs a priori power analysis, (8) performs Wilcoxon signed‑rank, paired‑t, and bootstrap confidence‑interval analyses, (9) adds a ground‑truth‑only graph control to isolate the effect of LLM‑inferred intents, and (10) produces a full report and contract‑validated artifacts.

All functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑005) are explicitly addressed in the task list below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `datasets>=2.14`, `networkx>=3.2`, `scikit-learn>=1.4`, `torch>=2.2` (CPU‑only), `transformers>=4.40` (small LLM for missing intents), `pandas>=2.2`, `numpy>=1.26`, `matplotlib>=3.8`, `pyyaml>=6.0`, `statsmodels>=0.14`, `scipy>=1.12`, `jsonschema>=4.22`  
- **Storage**: Files under `data/` (raw, derived, logs, figures)  
- **Testing**: `pytest` + contract validation (`jsonschema`)  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h) – **CPU‑first**; no GPU escape hatch required.  
- **Constraints**: Peak RAM ≤ 7 GB, wall‑clock ≤ 6 h, all scripts deterministic.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed in `src/utils/seed.py`. Data download uses a single canonical HF identifier (`pi_bench`). Scripts are deterministic; no manual steps. |
| II. Verified Accuracy | Only the public π‑Bench dataset (HF) is cited. No new external citations are introduced. |
| III. Data Hygiene | Every file written under `data/` receives a SHA‑256 checksum recorded in `state/projects/PROJ-942-...yaml`. Raw files are never overwritten; derived files are new. |
| IV. Single Source of Truth | Every figure, table, and numeric claim traces back to a row in `data/derived/summary.csv` and the code that generated it. |
| V. Versioning Discipline | Artifact hashes are computed automatically; any change updates the project state file. |
| VI. Structured Memory Fidelity | Intent Graph preserves temporal edges and explicit conflict‑resolution edges. Pruning for token budget is logged with confidence scores; no intent label is altered. |
| VII. Latency‑Performance Trade‑off Quantification | **Online latency** (per‑turn inference) is reported separately from **offline latency** (LLM inference for missing intents + graph‑construction time). Both are included in `summary.csv` and discussed in the final report. |

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
│       ├── inferred_intents.csv
│       ├── intent_graphs/          # one JSON per task (inferred‑only)
│       ├── intent_graphs_gt/       # ground‑truth‑only graphs (control)
│       ├── graph_construction_latency.csv
│       ├── inference_logs/
│       │   ├── lightweight_seed101.csv
│       │   ├── raw_seed101.csv
│       │   ├── null_seed101.csv
│       │   └── graph_gt_seed101.csv   # optional logs for control
│       └── eval_results/
│           ├── summary.csv
│           ├── report.md
│           └── figures/
│               ├── f1_barplot.png
│               └── latency_boxplot.png
├── pipelines/
│   ├── download_pi_bench.py
│   ├── parse_traces.py
│   ├── infer_missing_intents.py          # deterministic LLM for missing intents
│   ├── build_intent_graph.py             # inferred‑only graph
│   ├── build_intent_graph_gt.py          # ground‑truth‑only control graph
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
| **0️⃣ Setup** | 0.1 Install dependencies (`requirements.txt`). 0.2 Initialise deterministic seeds (`utils/seed.py`). | – | – |
| **1️⃣ Data Acquisition** | 1.1 `download_pi_bench.py`: stream `datasets.load_dataset("pi_bench", streaming=True)`, write each task JSON to `data/raw/`, verify SHA‑256 checksum, retry up to 3 times. | – | – |
| **2️⃣ Parse & Normalize** | 2.1 `parse_traces.py`: read all raw JSON, extract `task_id`, `turn_index`, `speaker`, `utterance`, optional `ground_truth_intent`; write `data/derived/normalized_traces.csv`. | FR‑001 | – |
| **3️⃣ Infer Missing Intents** | 3.1 `infer_missing_intents.py`: for rows where `ground_truth_intent` is missing, invoke a **deterministic small LLM** (`google/flan-t5-small`) with fixed seed (`torch.manual_seed(42)`) and greedy decoding. Output `inferred_intents.csv` with columns `task_id, turn_index, inferred_intent, confidence`. Record wall‑clock time in `graph_construction_latency.csv` (LLM inference component). | FR‑007 (deterministic inference) | – |
| **4️⃣ Intent Graph Construction** | 4.1 `build_intent_graph.py`: merge `normalized_traces.csv` + `inferred_intents.csv`. Create `networkx.DiGraph` where nodes = inferred intents only (ground‑truth never used). Add temporal edges between consecutive turns; add conflict‑resolution edges via rule‑based regex. Serialize each graph to `data/derived/intent_graphs/<task_id>.json`. 4.2 Record per‑task wall‑clock time (graph‑construction latency) in `graph_construction_latency.csv`. 4.3 Validate each JSON against `contracts/intent_graph.schema.yaml`. | FR‑002, FR‑007, FR‑009 (no ground‑truth) | SC‑004 |
| **4b️⃣ Ground‑Truth‑Only Graph (Control)** | 4b.1 `build_intent_graph_gt.py`: same pipeline but **uses only ground‑truth intents** when available and **omits any inferred intents**. Serialized to `data/derived/intent_graphs_gt/<task_id>.json`. 4b.2 Validate against schema. | Provides a control for construct validity (addresses methodology‑e0443735). | – |
| **5️⃣ Agent & Baseline Execution** | 5.1 `run_lightweight_agent.py`: load inferred‑only Intent Graph + current turn, feed to CPU‑only `facebook/opt-125m` (`torch.device("cpu")`). Output `ProactiveAction` or `"no_action"`; log latency per turn. Run for seeds = {101, 202, 303}. 5.2 `run_raw_baseline.py`: feed full dialogue history (truncated to model max‑context = 2048 tokens by removing oldest tokens) to the same OPT model; log latency. 5.3 `run_null_baseline.py`: feed only the current turn (no history) to OPT; log latency. 5.4 `run_lightweight_agent_gt.py` (optional): run the agent on the ground‑truth‑only graphs to evaluate the effect of inferred intents. | FR‑003, FR‑004, FR‑008 | – |
| **6️⃣ Scoring & Latency Aggregation** | 6.1 `evaluate.py`: for turns with ground‑truth intents, compute **single‑label** accuracy, precision, recall, and F1 (`sklearn.metrics.classification_report`). 6.2 Aggregate per‑task mean metrics across seeds. 6.3 Compute **online** average inference latency per turn for each condition. 6.4 Merge **offline** latency components (LLM inference + graph‑construction) from `graph_construction_latency.csv`. 6.5 Export `summary.csv` with columns: `condition, mean_accuracy, mean_f1, std_f1, mean_online_latency, total_latency, latency_reduction_pct, graph_construction_mean_latency_sec, success_rate_graphs`. | FR‑005, FR‑006 | SC‑001, SC‑002, SC‑005 |
| **7️⃣ Statistical Validation** | 7.1 **A priori power analysis**: compute required N for paired Wilcoxon to detect Cohen's d = 0.3 with power = 0.8 (α = 0.05); confirm that ≈ 100 tasks satisfy this. 7.2 Primary test: Wilcoxon signed‑rank on paired per‑task mean F1 (Graph vs Raw, Graph vs Null, Graph vs Graph‑GT). 7.3 Secondary test: paired *t*‑test. 7.4 Bootstrap 10 000 resamples for 95 % CI of mean differences. 7.5 Record power estimate in `summary.csv`. | FR‑005 | SC‑003 |
| **8️⃣ Reporting** | 8.1 Generate `report.md` containing: tables of accuracy/F1, latency, p‑values, CIs, graph‑construction success rate (≥ 95 %), offline latency breakdown, and discussion of offline cost. 8.2 Create PNG figures (`f1_barplot.png`, `latency_boxplot.png`). 8.3 List tasks flagged as “Null Graph” for manual review. | FR‑005, FR‑006 | SC‑005 |
| **9️⃣ Contract Validation** | 9.1 Run `pytest -q tests/contract` to validate every Intent Graph JSON against `contracts/intent_graph.schema.yaml`. Pipeline aborts on any schema violation. | – | – |

## Compute Feasibility
All steps run on CPU only:  
- **LLM for missing intents**: `flan-t5-small` (~80 M params) processes a turn in ≈ 0.25 s on the CI runner.  
- **OPT‑125M inference**: ~0.4 s per turn.  
- With A large number of tasks × ≈ 30 turns each, total compute ≈ 2 h, well under the 6 h CI limit.  
- Peak RAM < 5 GB (streaming download, lightweight graph objects).  

No GPU escape hatch is required.

## Risk Mitigation & Reviewer Concerns
- **Latency accounting**: Offline LLM + graph‑construction latency are measured and reported separately from online inference (addressing methodology‑0b24f58e).  
- **Lightweight claim**: The agent remains CPU‑tractable; the one‑time LLM pass is disclosed and its cost is not mixed into the online latency metric.  
- **Baseline fairness**: Both raw and graph conditions respect the same max‑token budget; raw truncates oldest tokens, graph prunes lowest‑confidence nodes only when needed (methodology‑0996ea35).  
- **Construct validity**: Added a ground‑truth‑only graph control (methodology‑e0443735) to isolate the effect of inferred intents.  
- **FR‑009 compliance**: Graph construction never uses ground‑truth labels (spec_coverage‑90a83e60).  
- **Independence of predictor/target**: Ground‑truth intents are used only for scoring, never as graph inputs (scientific_soundness‑864e6779).  
- **Metric appropriateness**: Switched to single‑label accuracy/F1 (scientific_soundness‑907bb9d1).  
- **Power analysis**: Conducted a priori (methodology‑3b6aee12).  

---

