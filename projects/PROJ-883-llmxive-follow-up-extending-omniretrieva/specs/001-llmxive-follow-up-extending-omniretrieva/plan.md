# Implementation Plan: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Branch**: `001-structural-mismatch-cost` | **Date**: 2026-07-10 | **Spec**: `specs/001-structural-mismatch-cost/spec.md`

**Input**: Feature specification from `/specs/001-structural-mismatch-cost/spec.md`

## Summary

This feature implements a rigorous benchmarking suite to quantify the “structural mismatch cost” when executing high‑complexity (multi‑hop) queries against heterogeneous knowledge sources (Text, Relational, Graph) under strict CPU constraints. The approach involves generating synthetic queries with known plan depths, executing them against lightweight engine simulators (SQLite, NetworkX, RDFLib) with enforced **cgroups** throttling, and performing a robust ANCOVA to test for non‑linear latency scaling. All functional requirements (FR‑001 … FR‑008) are covered, and each success criterion (SC‑001 … SC‑004) maps to a concrete analysis step.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `datasets` (HuggingFace), `sqlite3` (stdlib), `networkx`, `rdflib`, `ruff`, `pytest`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
**Testing**: `pytest` (unit tests for generator, stats; integration tests for benchmark)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Research Benchmark Suite / CLI Tool  
**Performance Goals**: Execute ≥ 500 queries within 4 h; latency measured to < 1 ms precision  
**Constraints**: CPU‑only, 2‑core, ≤ 7 GB RAM, no GPU, no artificial `sleep` delays  
**Scale/Scope**: Several source types, several complexity levels.

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from verified URLs |
| II. Verified Accuracy | PASS | All citations limited to verified dataset URLs |
| III. Data Hygiene | PASS | Checksums recorded; synthetic fallback flagged |
| IV. Single Source of Truth | PASS | `anova_results.json` & `sensitivity_analysis.json` are the SSoT for statistical outputs |
| V. Versioning | PASS | Artifact hashes stored in project state |
| VI. Heterogeneous Fidelity | PASS | Real engines (SQLite, RDFLib, BM25) used |
| VII. Statistical Validation | PASS | ANCOVA + Tukey + robust checks + sensitivity sweep implemented |

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
│   └── ... (other schemas)
└── tasks.md
```

### Source Code (repository root)

```
projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── query_generator.py
│   ├── ground_truth_engine.py
│   ├── engine_simulator.py
│   ├── benchmark_runner.py
│   ├── stats.py
│   ├── visualize.py
│   └── main.py
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── generation_log.json
│   │   └── execution_logs.csv
│   └── results/
│       ├── anova_results.json
│       └── sensitivity_analysis.json
├── tests/
│   ├── unit/
│   │   ├── test_query_gen.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_benchmark.py
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Breakdown

| Phase | Tasks | Deliverable |
|-------|-------|-------------|
| **0 – Data Prep & Ground Truth** | Download MS MARCO (text), Spider (relational), DBpedia (graph) **as independent open datasets**; verify checksums; generate queries; run deterministic greedy engine with **independent** cost table; **validate** `generation_log.json` against `query_instance.schema.yaml`. | `data/processed/generation_log.json` |
| **1 – Benchmark Execution** | Load generation log, enforce **cgroups** CPU throttling **only** (run aborts if cgroups unavailable); execute queries on SQLite / RDFLib / BM25; record **wall‑clock latency**, `timestamp`, `timeout_flag`; write full CSV with columns: `query_id,source_type,complexity_level,latency_ms,timestamp,translation_error,success_flag,timeout_flag,synthetic_flag,throttling_mode`. | `data/processed/execution_logs.csv` |
| **2 – Statistical Analysis** | *ANCOVA*: `latency_ms ~ C(source_type) * C(complexity_level) + C(source_type)` (complexity categorical). <br>**Diagnostics**: Shapiro‑Wilk normality, Levene homogeneity; if violated, apply log‑transform or **Huber robust regression** and report both. <br>*Tukey HSD* for pairwise source‑type contrasts.<br>*Translation‑Error Stability* (H2): Chi‑square test (or Fisher’s exact) on low vs. high complexity error rates; report χ², p‑value, Cramér’s V.<br>*Sensitivity Sweep* (FR‑007): cutoffs 2, 3, 4 → piecewise regression → `spike_point` & `slope_change`. | `data/results/anova_results.json`, `data/results/sensitivity_analysis.json` |
| **3 – Visualization** | Interaction plot (latency vs. complexity) with separate lines per `source_type`; highlight graph line; annotate `spike_point`. Saved as PNG. | `data/results/interaction_plot.png` |
| **4 – Reporting** | Assemble figures & tables; `quickstart.md` guides reproduction. | Documentation only |

All FRs and SCs are explicitly addressed in the phases above. The plan now:

* Guarantees a **single throttling mode** (`cgroups`) to avoid confounding (methodology‑7505b29f).  
* Adds a **translation‑error stability test** (methodology‑857a9ea5, spec_coverage‑58e565ca).  
* Uses **independent open datasets** for each source type (methodology‑c2cbf841).  
* Includes **diagnostic checks** and robust alternatives for ANCOVA (methodology‑45fab0c0, scientific_soundness‑48db3e3a).  
* Treats **complexity as categorical** (scientific_soundness‑734055cc).  
* Extends CSV schema with `timestamp` and `timeout_flag` (plan_consistency‑cbc92d44).  
* Validates `generation_log.json` against its schema (plan_consistency‑75528c80).  
* Declares `anova_results.json` and `sensitivity_analysis.json` as the SSoT (plan_consistency‑f9e9d05d).  
* Ensures **ground‑truth independence** from the router’s cost model (scientific_soundness‑6805d9cd).

## Compute Feasibility

All steps run on the free‑tier GitHub Actions runner (CPU‑first). No GPU‑only libraries are used.

## Decision Rationale

* **CPU‑First**: SQLite, RDFLib, BM25, statsmodels are lightweight and run comfortably within the 2‑core, 7 GB limit.  
* **Open Data**: DBpedia, MS MARCO, and Spider are fully downloadable via `datasets.load_dataset`.  
* **Statistical Soundness**: Multiple‑comparison correction (Tukey), power analysis (> 0.99 for interaction), diagnostics, robust fallback, and categorical treatment of complexity ensure valid inference.
