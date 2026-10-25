# Implementation Plan: Structural Mismatch Cost in Heterogeneous Retrieval

**Branch**: `001-structural-mismatch-cost` | **Date**: 2026-10-24 | **Spec**: `specs/001-structural-mismatch-cost/spec.md`

**Input**: Feature specification from `/specs/001-structural-mismatch-cost/spec.md`

## Summary
We will build a fully reproducible benchmarking suite that measures the **structural mismatch cost**—the non‑linear latency increase for high‑complexity (multi‑hop) queries on **graph** sources compared with **text** and **relational** sources—under strict CPU‑only throttling. The plan covers **every** functional requirement (FR‑001 … FR‑015) and success criterion (SC‑001 … SC‑005), provides a deterministic data pipeline, statistical analysis, and visualisation, and respects all constitution principles.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`):  
  `pandas==2.2.2`, `numpy==1.26.4`, `pyarrow==15.0.0`, `datasets==2.19.0`, `statsmodels==0.14.2`, `scipy==1.13.0`, `networkx==3.3`, `rdflib==7.0.0`, `ir-datasets==0.5.6`, `ruff==0.4.5`, `pytest==8.2.2`  
- **Storage**: Local filesystem under `data/` (raw, processed, results).  
- **Testing**: `pytest` (unit & integration).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: No artificial `sleep`; enforce CPU quota via cgroups (≤ 1 000 ms per query); 60 s wall‑clock timeout.  
- **Compute Placement**: **CPU‑first** – all libraries run on the CPU runner; no GPU‑only components.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic loaders, pinned dependencies. |
| II. Verified Accuracy | PASS | All citations limited to the verified URLs in the “Verified datasets” block. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place mutation; synthetic flag distinguishes generated topology. |
| IV. Single Source of Truth | PASS | `execution_logs.csv`, `anova_results.json`, `interaction_plot.png` are the sole sources for figures/tables. |
| V. Versioning Discipline | PASS | Artifact hashes stored in project state; `requirements.txt` pins exact versions. |
| VI. Heterogeneous Source Execution Fidelity | PASS | Real engines (BM25, SQLite, RDFLib) run under cgroups; datasets derived from open DBpedia triples. |
| VII. Statistical Validation of Non‑Linear Scaling | PASS | Two‑way ANOVA, Tukey HSD, Bonferroni‑corrected sensitivity sweep, slope‑ratio, and diagnostics satisfy the principle. |

## Project Structure

```
specs/001-structural-mismatch-cost/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── query_instance.schema.yaml
│   ├── execution_log.schema.yaml
│   ├── execution_metric.schema.yaml
│   └── statistics_result.schema.yaml
└── tasks.md               # generated later
```

Source code (root of the repository)

```
code/
├── __init__.py
├── config.py
├── data_loader.py               # downloads & checksums datasets
├── query_generator.py           # synthetic queries + complexity labels
├── reference_engine.py          # deterministic greedy planner
├── optimal_planner.py           # exhaustive optimal planner (sampled subset)
├── engine_simulator.py          # BM25, SQLite, RDFLib wrappers w/ cgroups
├── benchmark_runner.py          # orchestrates execution & logging
├── baseline_overhead.py         # measures trivial query latency
├── stats.py                     # ANOVA, Tukey, chi‑square, sensitivity sweep, slope‑ratio
├── visualize.py                 # interaction plot generator
├── generate_execution_metric.py # builds execution_metric.json
├── quickstart.py                # CLI entry point (supports --run-optimal-planner, --baseline-reps)
└── main.py                      # top‑level CLI (help, version, stage selection)
tests/
├── unit/
│   ├── test_query_generator.py
│   ├── test_reference_engine.py
│   ├── test_optimal_planner.py
│   └── test_data_loader.py
└── integration/
    ├── test_cpu_throttle.py
    ├── test_benchmark.py
    └── test_skeleton.py
requirements.txt
.ruff.toml                       # corrected TOML (valid syntax)
```

## Phase Breakdown & FR/SC Mapping

| Phase | Tasks | Deliverable(s) | Covered FR / SC |
|-------|-------|----------------|-----------------|
| **0 – Optimal Planner (Sampled Subset)** | • Stratified sampling (200 queries).<br>• Exhaustive search over all join/order permutations → `optimal_plan_id`.<br>• Store mapping in `optimal_ground_truth.json`. | `optimal_ground_truth.json` | FR‑004, FR‑008 |
| **1 – Data Acquisition & Checksum** | • Programmatic download of MS MARCO parquet via `ir_datasets`.<br>• Download DBpedia triples parquet from HuggingFace.<br>• Compute SHA‑256 checksums, write `checksums.txt`. | `data/raw/`, `checksums.txt` | FR‑001 |
| **2 – Query Generation & Greedy Reference** | • Generate 1 500 synthetic queries (125 per source × 4 complexity levels).<br>• Assign UUID, `source_type`, `complexity_level`, `logical_plan`.<br>• Run deterministic greedy reference engine → `reference_plan_id` (hash‑named `greedy_plan_<8hex>`).<br>• Log depth overflow warnings (`DEPTH_OVERFLOW: query_id=…`).<br>• Validate `generation_log.json` against `query_instance.schema.yaml`. | `generation_log.json` | FR‑002, FR‑008, FR‑015 |
| **3 – Baseline Overhead Calibration** | • Execute 5 trivial single‑hop queries per engine under cgroups.<br>• Record median latency per engine → `baseline_overhead.json`. | `baseline_overhead.json` | FR‑010 |
| **4 – Benchmark Execution (CPU‑Throttled)** | • Verify cgroups quota; abort with exit 99 if unavailable (FR‑014).<br>• Enforce ≤ 1 000 ms CPU quota per query; 60 s wall‑clock timeout.<br>• For each query record:<br>  `latency_ms` (baseline‑corrected), `translation_error` (true error vs. optimal **only** for sampled subset), `reference_deviation` (boolean indicating mismatch vs. greedy plan for non‑sampled), `precision_at_10`, `success_flag`, `timeout_flag`, `synthetic_flag`, `throttling_mode`.<br>• Write `execution_logs.csv` (validated by `execution_log.schema.yaml`) and aggregated `execution_metric.json` (validated by `execution_metric.schema.yaml`). | `execution_logs.csv`, `execution_metric.json` | FR‑001, FR‑002, FR‑003, FR‑004, FR‑009, FR‑010, FR‑012, FR‑014, FR‑015 |
| **5 – Statistical Analysis** | • Two‑way ANOVA on `latency_ms` with factors `source_type` × `complexity_level`; report interaction F, p, 95 % CI.<br>• Diagnostics (Shapiro‑Wilk, Levene); if violated, apply log‑transform or Huber regression.<br>• Tukey HSD post‑hoc (family‑wise ≤ 0.05).<br>• Chi‑square test for `translation_error` vs. `complexity_group` (low = 1‑2, high = 3‑4+).<br>• Sensitivity sweep for cut‑offs {2, 3, 4}: piecewise linear regression → `spike_point`, `slope_change`; Bonferroni‑corrected p‑values (FR‑007, FR‑011).<br>• Slope‑ratio regression (graph vs. text) → `slope_ratio` (must exceed 1.5 for SC‑001).<br>• Precision@10 per source; verify pairwise differences ≤ 0.02 (SC‑002).<br>• Export JSON results (`anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`). | `anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json` | FR‑005, FR‑007, FR‑011, SC‑001, SC‑002, SC‑004 |
| **6 – Visualization** | • Interaction plot (`latency_ms` vs. `complexity_level`) with distinct colors per `source_type`; highlight graph line; annotate `spike_point` and slope differences.<br>• Save as `interaction_plot.png`. | `interaction_plot.png` | FR‑006, SC‑005 |
| **7 – Reporting & Quickstart** | • Assemble figures & tables into `results/`.<br>• Update `quickstart.md` with exact CLI flags (`--run-optimal-planner`, `--baseline-reps=5`).<br>• Provide reproducibility checklist. | Documentation | All SCs (traceability) |

## Compute Feasibility
- All engines are pure‑Python or std‑lib; memory footprint < 7 GB; total runtime ≤ 5 h on the free runner.  
- No GPU‑only libraries are imported, satisfying the CPU‑first policy.

## Decision/Rationale
1. **CPU‑First** – Chosen libraries run efficiently on the free runner; no need for Kaggle offload.  
2. **Open Data** – MS MARCO parquet and DBpedia triples parquet are directly downloadable via verified URLs; they satisfy heterogeneous source fidelity.  
3. **Statistical Rigor** – Multiple‑comparison corrections (Tukey, Bonferroni), power analysis (≥ 0.99 for medium effect), diagnostics, and explicit non‑causal framing meet Constitution Principle VII.  
4. **Ground‑Truth Clarification** – The **optimal** plan (exhaustive search) is the only true ground truth; the greedy plan is a *reference* used for all non‑sampled queries. The `translation_error` flag is defined **only** for the sampled subset; a separate `reference_deviation` flag records disagreement with the greedy reference for the remainder. This addresses reviewer concerns about conflating heuristic and truth.  
5. **Edge‑Case Handling** – Depth overflow warnings and cgroup‑failure aborts are explicitly logged and tested (FR‑015, FR‑014).  
6. **Schema Consolidation** – Duplicate contracts removed; all four required schemas are present and validated.  
7. **Linting** – `.ruff.toml` will be corrected to a valid TOML configuration, ensuring `ruff check code/` exits 0 and produces `artifacts/ruff_output.txt`.  

---
