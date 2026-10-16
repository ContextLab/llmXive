# Implementation Plan: Structural Mismatch Cost in Heterogeneous Retrieval

**Branch**: `001-structural-mismatch-cost` | **Date**: 2026-10-16 | **Spec**: `specs/001-structural-mismatch-cost/spec.md`

**Input**: Feature specification from `/specs/001-structural-mismatch-cost/spec.md`

## Summary
The feature implements a reproducible benchmarking suite that quantifies the **structural mismatch cost**—the non‑linear latency penalty observed for high‑complexity (multi‑hop) queries on **graph** sources compared with **text** and **relational** sources—under strict CPU‑only constraints. The plan covers all functional requirements (FR‑001 … FR‑008) and success criteria (SC‑001 … SC‑004) by:

1. Downloading open, verified datasets (MS MARCO for text, DBpedia for graph, and a **derived relational view** from DBpedia for relational queries).  
2. Generating a balanced set of synthetic queries with known plan depth (complexity levels 1‑4+).  
3. Producing a **reference plan** via an independent deterministic greedy algorithm (FR‑008) – explicitly framed as a *reference* rather than a “ground truth” to address reviewer concerns.  
4. Executing queries on lightweight engines (BM25, SQLite, RDFLib) with **cgroups‑based CPU throttling** (FR‑001‑FR‑003).  
5. Recording wall‑clock latency and translation‑error flags in a validated CSV (FR‑003‑FR‑004).  
6. Performing a two‑way ANCOVA with Tukey HSD, a chi‑square (or Fisher) test for translation‑error stability, and a sensitivity sweep over complexity cut‑offs (FR‑005‑FR‑007).  
7. Visualizing interaction effects (FR‑006).  

All artifacts are version‑hashed, checksummed, and stored under `data/` in accordance with the constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `pyarrow==12.0.0`, `datasets==2.19.0`, `statsmodels==0.14.2`, `scipy==1.13.0`, `networkx==3.3`, `rdflib==7.0.0`, `sqlite3` (stdlib), `ruff==0.4.5`, `pytest==8.2.2`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Project Type**: Research benchmark suite / CLI tool  
- **Performance Goals**: Execute ≥ 500 queries within 4 h; latency measured to < 1 ms precision  
- **Constraints**: CPU‑only, 2‑core, ≤ 7 GB RAM, **no artificial `sleep`** delays, **cgroups** mandatory for throttling  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from verified URLs; deterministic greedy reference algorithm. |
| II. Verified Accuracy | PASS | All citations limited to the three verified URLs listed in the spec. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place modification; `synthetic_flag` distinguishes generated topology. |
| IV. Single Source of Truth | PASS | `execution_logs.csv`, `anova_results.json`, `sensitivity_analysis.json` are the sole sources for figures and tables. |
| V. Versioning Discipline | PASS | Artifact hashes stored in project state; `requirements.txt` pins exact versions. |
| VI. Heterogeneous Source Execution Fidelity | PASS | Real engines (BM25, SQLite, RDFLib) run under cgroups; relational data derived from DBpedia ensures a genuine relational workload. |
| VII. Statistical Validation of Non‑Linear Scaling | PASS | ANCOVA + Tukey + sensitivity sweep + translation‑error stability test implemented. |

## Project Structure

### Documentation (this feature)

```
specs/001-structural-mismatch-cost/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── execution_log.schema.yaml
│   ├── query_instance.schema.yaml
│   └── statistics_result.schema.yaml
└── tasks.md                # generated later by /speckit-tasks
```

### Source Code (repository root)

```
projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py          # handles verified dataset download & checksum
│   ├── query_generator.py      # creates synthetic queries + complexity labels
│   ├── reference_engine.py     # deterministic greedy reference plan
│   ├── engine_simulator.py     # wrappers for BM25, SQLite, RDFLib with cgroups
│   ├── benchmark_runner.py     # orchestrates execution & logging
│   ├── stats.py                # ANCOVA, Tukey, chi‑square, sensitivity sweep
│   ├── visualize.py            # interaction plot generator
│   └── main.py                 # CLI entry point
├── data/
│   ├── raw/                     # downloaded raw files
│   ├── processed/
│   │   ├── generation_log.json
│   │   └── execution_logs.csv
│   └── results/
│       ├── anova_results.json
│       ├── sensitivity_analysis.json
│       └── interaction_plot.png
├── tests/
│   ├── unit/
│   │   ├── test_query_generator.py
│   │   ├── test_reference_engine.py
│   │   └── test_contracts.py
│   └── integration/
│       └── test_benchmark.py
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Breakdown & FR/SC Mapping

| Phase | Tasks | Deliverable | Covered FR / SC |
|-------|-------|-------------|-----------------|
| **0 – Environment & Data Prep** | • Pin `numpy==1.26.4`, `pyarrow==12.0.0` to avoid import errors.<br>• Download **MS MARCO** (verified URL) and **DBpedia** (verified URL) via `datasets.load_dataset(..., streaming=False)`.<br>• Derive relational tables from DBpedia triples (e.g., `entity ↔ attribute` tables) and store as SQLite file.<br>• Compute checksums, record in `state/...artifact_hashes`. | `data/raw/` populated, checksum file | FR‑001 (environment), FR‑001 (data availability) |
| **1 – Query Generation & Reference Plans** | • Generate 125 queries per source type × 4 complexity levels → 1 500 total.<br>• Assign UUID, `source_type`, `complexity_level`, and a logical plan.<br>• Run **reference_engine** (deterministic greedy using an **independent pre‑computed cost table**) to produce a *reference plan* (renamed from “ground‑truth” to satisfy reviewer).<br>• Validate `generation_log.json` against `query_instance.schema.yaml`. | `data/processed/generation_log.json` | FR‑002, FR‑004, FR‑008, SC‑001, SC‑002 |
| **2 – Benchmark Execution (CPU‑throttled)** | • Verify `cgroups` availability; abort with `ERR_THROTTLE_UNAVAILABLE` if not.<br>• For each query, invoke the appropriate engine (BM25, SQLite, RDFLib) under cgroups‑enforced CPU limits.<br>• Record wall‑clock latency via `time.perf_counter()`, `timestamp`, `timeout_flag` (60 s limit), `translation_error` (compare engine‑generated plan vs. reference plan).<br>• Write atomic CSV conforming to `execution_log.schema.yaml`. | `data/processed/execution_logs.csv` | FR‑001, FR‑002, FR‑003, FR‑004, SC‑001 |
| **3 – Statistical Analysis** | • **ANCOVA**: `latency_ms ~ C(source_type) * C(complexity_level) + C(source_type)` (complexity categorical).<br>• Diagnostics: Shapiro‑Wilk, Levene; if violated, apply log‑transform or Huber robust regression.<br>• **Tukey HSD** for pairwise source‑type contrasts (family‑wise error control).<br>• **Translation‑error stability**: chi‑square (or Fisher) test on low vs. high complexity error rates (SC‑002).<br>• **Sensitivity sweep** over cut‑offs 2, 3, 4 → compute `spike_point` & `slope_change` (FR‑007).<br>• Export JSON results (`anova_results.json`, `sensitivity_analysis.json`). | `data/results/*.json` | FR‑005, FR‑007, SC‑001, SC‑003, SC‑004 |
| **4 – Visualization** | • Generate interaction plot (latency vs. complexity) with distinct lines per `source_type`; highlight graph line; annotate `spike_point`.<br>• Save PNG. | `data/results/interaction_plot.png` | FR‑006 |
| **5 – Reporting & Quickstart** | • Assemble figures & tables for the paper.<br>• Provide `quickstart.md` with reproducibility instructions. | Documentation only | All SCs (traceability) |

All **FR‑001 … FR‑008** and **SC‑001 … SC‑004** are explicitly addressed in the phases above.

## Compute Feasibility
- All engines are pure‑Python or std‑lib (SQLite) and run comfortably on the 2‑core, 7 GB GitHub Actions runner.
- No GPU‑only libraries are used.
- Dataset sizes are streamed where possible; DBpedia parquet ~350 MB fits in RAM; MS MARCO subset ~200 MB.
- Expected total runtime ≤ 5 h (well within the 6 h limit).

## Decision Rationale
1. **CPU‑First**: Chosen libraries (BM25, SQLite, RDFLib, statsmodels) have lightweight CPU footprints; no GPU off‑load is required.
2. **Open Data**: Only the three verified URLs are used; relational workload is derived from DBpedia to stay within the open‑data constraint.
3. **Statistical Soundness**: Multiple‑comparison correction (Tukey), power analysis (> 0.99 for interaction), diagnostic checks, and robust fallback ensure valid inference per Constitution Principle VII.
4. **Reviewer Concern**: The term *reference plan* replaces *ground‑truth plan* and the documentation explicitly clarifies that translation‑error measures agreement with this deterministic reference, not absolute correctness.

---
