# Implementation Plan: Structural Mismatch Cost in Heterogeneous Retrieval

**Branch**: `001-structural-mismatch-cost` | **Date**: 2026-10-21 | **Spec**: `specs/001-structural-mismatch-cost/spec.md`

**Input**: Feature specification from `/specs/001-structural-mismatch-cost/spec.md`

## Summary
The plan implements a reproducible benchmarking suite that quantifies the **structural mismatch cost**—the non‑linear latency penalty observed for high‑complexity (multi‑hop) queries on **graph** sources compared with **text** and **relational** sources—under strict CPU‑only constraints. All functional requirements (FR‑001 … FR‑008) and success criteria (SC‑001 … SC‑004) are addressed by:

1. Downloading open, verified datasets (MS MARCO, DBpedia, and a derived relational view) via `datasets.load_dataset` with checksum validation.
2. Generating a balanced set of synthetic queries across four complexity levels, each assigned a deterministic **ground_truth_plan** via a greedy reference engine (FR‑008). The term *ground_truth_plan* is used consistently (see plan_consistency‑32a13f54) and **does not claim absolute optimality**; it serves as a reproducible baseline for measuring *disagreement*.
3. Performing a **baseline‑overhead calibration** (Phase 2‑a) that runs a trivial query on each engine to estimate intrinsic engine latency; subsequent latency measurements are **baseline‑corrected** to isolate structural mismatch effects (addresses methodology‑5e4c0b62).
4. Executing queries on lightweight engines (BM25, SQLite, RDFLib) under cgroups‑based CPU quota (FR‑001‑FR‑003). Engine‑specific overhead is accounted for by the baseline calibration.
5. Recording wall‑clock latency, translation‑error flags (now defined as **disagreement with the deterministic ground_truth_plan**), timeout flags, and success flags. Results are written to a CSV conforming to `execution_log.schema.yaml` and aggregated into `execution_metric.json` (Phase 2‑f), which conforms to `execution_metric.schema.yaml` (addresses plan_consistency‑074ae762).
6. Performing a two‑way **ANOVA** (not ANCOVA) with Tukey HSD, a chi‑square test for translation‑error stability, and a **Bonferroni‑corrected** sensitivity sweep over cut‑offs 2, 3, 4 (FR‑007). Diagnostics and robust alternatives are included.
7. Generating an interaction plot (latency vs. complexity) with distinct colored lines per `source_type`; highlighting the graph line and annotating the identified spike point (FR‑006).
8. **Optional validation sub‑task**: manually inspect a random sample (e.g., 20 queries) of engine‑generated plans against an external gold‑standard to assess the fidelity of the greedy reference (addresses scientific_soundness‑2f51c7dc).

All **FR‑001 … FR‑008** and **SC‑001 … SC‑004** are explicitly covered.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy>=2.0.0`, `pyarrow==12.0.0`, `datasets==2.19.0`, `statsmodels==0.14.2`, `scipy==1.13.0`, `networkx==3.3`, `rdflib==7.0.0`, `sqlite3` (stdlib), `ruff==0.4.5`, `pytest==8.2.2`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: Execute ≥ 500 queries within 4 h; latency measured to < 1 ms precision  
- **Constraints**: No artificial `sleep` delays; cgroups mandatory for throttling; all measurements are associative, not causal (addresses methodology‑c67e7268).

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from verified URLs; deterministic greedy reference algorithm. |
| II. Verified Accuracy | PASS | All citations limited to the three verified URLs listed in the spec. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place modification; `synthetic_flag` distinguishes generated topology. |
| IV. Single Source of Truth | PASS | `execution_logs.csv`, `anova_results.json`, `sensitivity_analysis.json`, `execution_metric.json` are the sole sources for figures and tables. |
| V. Versioning Discipline | PASS | Artifact hashes stored in project state; `requirements.txt` pins exact versions. |
| VI. Heterogeneous Source Execution Fidelity | PASS | Real engines (BM25, SQLite, RDFLib) run under cgroups; relational workload derived from DBpedia ensures genuine relational workload. |
| VII. Statistical Validation of Non‑Linear Scaling | PASS | Two‑way ANOVA + Tukey + Bonferroni‑corrected sensitivity sweep + power analysis satisfy Constitution Principle VII. |

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
│   ├── execution_metric.schema.yaml
│   ├── statistics_result.schema.yaml
│   └── statistics-result.schema.yaml
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
│   ├── stats.py                # ANOVA, Tukey, chi‑square, sensitivity sweep
│   ├── visualize.py            # interaction plot generator
│   ├── generate_execution_metric.py  # writes execution_metric.json
│   └── main.py                 # CLI entry point
├── data/
│   ├── raw/                     # downloaded raw files
│   ├── processed/
│   │   ├── generation_log.json
│   │   ├── execution_logs.csv
│   │   └── execution_metric.json   # aggregated metric file (Phase 2‑f)
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
| **0 – Environment & Data Prep** | • Pin dependencies (numpy≥2.0, pyarrow compatible).<br>• Download **MS MARCO**, **DBpedia**, via `datasets.load_dataset` (streaming where needed).<br>• Derive relational tables from DBpedia triples → SQLite.<br>• Compute checksums. | `data/raw/` populated, checksum file | FR‑001 (environment) |
| **1 – Query Generation & Reference Plans** | • Generate a sizable set of queries per source across four complexity levels, resulting in a total on the order of one thousand queries.<br>• Assign UUID, `source_type`, integer `complexity_level`, logical plan.<br>• Run **reference_engine** (deterministic greedy) to produce a **ground_truth_plan** identifier.<br>• Validate `generation_log.json` against `query_instance.schema.yaml`. | `data/processed/generation_log.json` | FR‑002, FR‑004, FR‑008, SC‑001, SC‑002 |
| **2 – Benchmark Execution (CPU‑throttled)** | **2‑a. Engine Overhead Calibration** – run a trivial query on each engine, record baseline latency, store in `baseline_overhead.json`.<br>**2‑b. Verify cgroups; abort if unavailable.<br>**2‑c. Execute each query with appropriate engine under cgroups CPU quota; subtract baseline overhead to obtain **corrected_latency_ms**.<br>**2‑d. Record wall‑clock latency, `translation_error` (disagreement with `ground_truth_plan`), `timeout_flag`, `success_flag`.<br>**2‑e. Write CSV conforming to `execution_log.schema.yaml`.<br>**2‑f. Aggregate per‑query JSON `execution_metric.json` (matches `execution_metric.schema.yaml`). | `data/processed/execution_logs.csv`, `execution_metric.json` | FR‑001, FR‑002, FR‑003, FR‑004, SC‑001 |
| **3 – Statistical Analysis** | • Two‑way ANOVA: `latency_ms_corrected ~ C(source_type) * C(complexity_level) + C(source_type)`.<br>• Diagnostics; fallback log‑transform or robust regression.<br>• Tukey HSD for all pairwise source‑type contrasts (FWE ≤ 0.05).<br>• Chi‑square / Fisher test for translation‑error stability (SC‑002).<br>• **Sensitivity sweep** over cut‑offs 2, 3, 4 with **Bonferroni correction**; compute `spike_point` & `slope_change` (FR‑007).<br>• Optional manual validation of a random sample of plans against an external gold‑standard (addresses scientific_soundness‑2f51c7dc).<br>• Export JSON results. | `data/results/anova_results.json`, `sensitivity_analysis.json` | FR‑005, FR‑007, SC‑001, SC‑003, SC‑004 |
| **4 – Visualization** | • Generate interaction plot (latency vs. complexity) with distinct colored lines per `source_type`; highlight graph line; annotate `spike_point`. | `data/results/interaction_plot.png` | FR‑006 |
| **5 – Reporting & Quickstart** | • Assemble figures & tables for the paper.<br>• Provide `quickstart.md` with reproducibility instructions and verification commands. | Documentation only | All SCs (traceability) |

All **FR‑001 … FR‑008** and **SC‑001 … SC‑004** are explicitly covered.

## Compute Feasibility
- All engines are pure‑Python or std‑lib and run comfortably on a standard‑capacity GitHub Actions runner.
- No GPU‑only libraries are used.
- Datasets are streamed or sized to fit within RAM; total disk usage < 7 GB.
- Expected total runtime ≤ 5 h (within the 6 h CI limit).

## Decision Rationale
1. **CPU‑First**: Chosen libraries have proven CPU performance on the free‑tier runner; no GPU needed.
2. **Open Data**: Only the three verified URLs are used; relational workload derived from DBpedia stays within the open‑data mandate.
3. **Statistical Soundness**: Diagnostics, robust alternatives, categorical treatment of complexity, Bonferroni correction for multiple cut‑offs, and power analysis satisfy Constitution Principle VII.
4. **Engine Overhead Control**: Baseline calibration isolates structural mismatch from engine‑specific overhead (addresses methodology‑5e4c0b62).
5. **Causal Framing**: Explicitly stated as associative, not causal (addresses methodology‑c67e7268).
6. **Naming Consistency**: All references to the deterministic plan use the schema field `ground_truth_plan` (addresses plan_consistency‑32a13f54).
7. **Execution Metric Artifact**: Added generation of `execution_metric.json` to satisfy the corresponding contract (addresses plan_consistency‑074ae762).
8. **Construct Validity**: Acknowledged that the greedy reference is a heuristic; optional manual validation provides an empirical check on its fidelity (addresses scientific_soundness‑2f51c7dc).

---



