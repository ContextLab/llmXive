# Implementation Plan: Structural Mismatch Cost in Heterogeneous Retrieval

**Branch**: `001-structural-mismatch-cost` | **Date**: 2026-10-21 | **Spec**: `specs/001-structural-mismatch-cost/spec.md`

**Input**: Feature specification from `/specs/001-structural-mismatch-cost/spec.md`

## Summary
The plan implements a reproducible benchmarking suite that quantifies the **structural mismatch cost**—the non‑linear latency penalty observed for high‑complexity (multi‑hop) queries on **graph** sources compared with **text** and **relational** sources—under strict CPU‑only constraints. All functional requirements (FR‑001 … FR‑015) and success criteria (SC‑001, SC‑002, SC‑004, SC‑005) are addressed by:

1. **Phase 0 – Exhaustive Optimal Planner (Ground‑Truth Generation)**
   - Sample a stratified subset of queries (balanced across source types and complexity levels).
   - Run an **exhaustive optimal planner** (brute‑force search over all possible execution orders) to obtain the true optimal plan for each sampled query.
   - Store the optimal plan identifiers in `data/processed/optimal_ground_truth.json`.
   - This ground‑truth is used to compute the **true translation error** for the sampled subset (FR‑004). For all other queries, translation error is measured against the deterministic greedy **reference engine** (FR‑008).

2. **Phase 1 – Data Download & Checksum**
   - Download open, verified datasets:
     - MS MARCO test set (parquet) – https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/v1.1/test-00000-of-00001.parquet
     - DBpedia triples (parquet) – https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet
   - Verify SHA‑256 checksums; record in `data/raw/checksums.txt`.
   - Derive:
     - **Text engine**: BM25 index over MS MARCO passages.
     - **Relational engine**: SQLite tables (`entities`, `relations`, `entity_relation`) built from DBpedia triples (see Data‑Model § Relational Schema).
     - **Graph engine**: RDFLib SPARQL endpoint over the same triples.

3. **Phase 2 – Query Generation & Reference Plans**
   - **2‑a.** Generate a large collection of synthetic queries spanning multiple sources and complexity levels. Each query receives:
     - `query_id` (UUID)
     - `source_type` (`text`, `relational`, `graph`)
     - `complexity_level` (integer ≥ 1)
     - `logical_plan` (list of operations derived from real structural metadata; e.g., join keys for relational, edge traversals for graph)
   - **2‑b.** For each query, run the **deterministic greedy reference engine** (cost table pre‑computed from a held‑out sample) to obtain a reproducible `ground_truth_plan` identifier (FR‑008).
   - **2‑c.** Depth overflow handling: queries whose required recursion depth exceeds the generator's maximum are either capped or dropped, and a warning `DEPTH_OVERFLOW: query_id=<id>` is logged (FR‑015).
   - **2‑d.** Store all query instances in `data/processed/generation_log.json` (validated by `query_instance.schema.yaml`).

4. **Phase 3 – Baseline Overhead Calibration**
   - Run **five** trivial (single‑hop) queries per engine under the same cgroups settings.
   - Record wall‑clock latency for each; store the **median** per engine in `data/processed/baseline_overhead.json`.
   - Subsequent query latencies are **baseline‑corrected** by subtracting the median engine overhead (FR‑010). If subtraction yields negative values, fall back to a log‑ratio normalization.

5. **Phase 4 – Benchmark Execution (CPU‑Throttled)**
   - **4‑a.** Verify cgroups CPU quota of **≤ 1 000 ms** per query. Abort with exit code 99 and clear error if quota cannot be applied (FR‑014, FR‑001, concern‑71ee64ce).
   - **4‑b.** Execute each query on its native engine (BM25, SQLite, RDFLib) under the enforced quota and a **60‑second wall‑clock timeout**; timeouts are recorded as `timeout_flag=true` and latency is set to the timeout value but excluded from ANOVA (concern‑511c8ca8).
   - **4‑c.** Record for every query:
     - `latency_ms` (baseline‑corrected)
     - `translation_error` (true error for sampled subset vs. optimal; heuristic error otherwise)
     - `precision_at_10` (see Phase 5)
     - `success_flag`, `timeout_flag`, `synthetic_flag`, `throttling_mode` (`cgroups` or `failed`).
   - Write to `data/processed/execution_logs.csv` (validated by `execution_log.schema.yaml`) and aggregate per‑query into `data/processed/execution_metric.json` (validated by `execution_metric.schema.yaml`) (FR‑003, FR‑009, FR‑012).

6. **Phase 5 – Statistical Analysis**
   - **5‑a.** Two‑way ANOVA on `latency_ms` with factors `source_type` and `complexity_level`; report F‑statistic, p‑value, 95 % CI for interaction; flag supported if p < 0.05 (FR‑005).
   - **5‑b.** Diagnostics: Shapiro‑Wilk, Levene; if violated, apply log‑transform or robust Huber regression (scientific_soundness‑c93bd729).
   - **5‑c.** Post‑hoc Tukey HSD for all source‑type pairwise contrasts (family‑wise error ≤ 0.05).
   - **5‑d.** Translation‑error stability: chi‑square test of independence between `translation_error` and `complexity_group` (low = 1‑2, high = 3‑4+); report χ², p, Cramér’s V (SC‑002).
   - **5‑e.** **Sensitivity sweep** over cut‑offs {2, 3, 4}: piecewise linear regression on mean latency per depth; compute `spike_point` and `slope_change`; apply **Bonferroni correction** across the three cut‑offs (FR‑007, FR‑011). Results stored in `sensitivity_analysis.json`.
   - **5‑f.** **Slope‑ratio computation**: simple linear regressions of mean latency vs. depth for `graph` and `text`; compute ratio of slopes; store as `slope_ratio` in `anova_results.json` (methodology‑96c8dcc0, spec_coverage‑ab090b4c).
   - **5‑g.** **Precision@10 analysis**: compute per‑source average Precision@10; store `avg_precision_at_10` per source in `statistics_results.json`; verify that pairwise differences ≤ 0.02 (SC‑002, spec_coverage‑bda000d2).

7. **Phase 6 – Visualization**
   - Generate interaction plot (`latency_ms` vs. `complexity_level`) with distinct colored lines per `source_type`; highlight graph line; annotate `spike_point` and slope differences; save as `interaction_plot.png` (FR‑006, SC‑005).

8. **Phase 7 – Reporting & Quickstart**
   - Assemble figures and tables; produce reproducibility checklist; update `quickstart.md` with new flags (`--run-optimal-planner`, `--baseline-reps=5`). (All SCs satisfied)

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4` (pinned for pyarrow compatibility), `pyarrow==15.0.0`, `datasets==2.19.0`, `statsmodels==0.14.2`, `scipy==1.13.0`, `networkx==3.3`, `rdflib==7.0.0`, `sqlite3` (stdlib), `ruff==0.4.5`, `pytest==8.2.2`
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)
- **Testing**: `pytest` (unit & integration)
- **Target Platform**: Linux (GitHub Actions free‑tier runner)
- **Performance Goals**: Execute ≥ 500 queries within 4 h; latency measured to < 1 ms precision
- **Constraints**: No artificial `sleep` delays; cgroups mandatory for throttling; all measurements are associative, not causal.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Random seeds pinned; datasets fetched from verified URLs; deterministic greedy reference algorithm; exhaustive optimal planner runs on a fixed random seed. |
| II. Verified Accuracy | PASS | All citations limited to the verified URLs listed in the spec. |
| III. Data Hygiene | PASS | Checksums recorded; no in‑place modification; `synthetic_flag` distinguishes generated topology. |
| IV. Single Source of Truth | PASS | `execution_logs.csv`, `anova_results.json`, `sensitivity_analysis.json`, `execution_metric.json` are the sole sources for figures and tables. |
| V. Versioning Discipline | PASS | Artifact hashes stored in project state; `requirements.txt` pins exact versions. |
| VI. Heterogeneous Source Execution Fidelity | PASS | Real engines (BM25, SQLite, RDFLib) run under cgroups; relational and graph workloads derived from verified DBpedia triples dataset. |
| VII. Statistical Validation of Non‑Linear Scaling | PASS | Two‑way ANOVA + Tukey + Bonferroni‑corrected sensitivity sweep + slope‑ratio computation satisfy Constitution Principle VII. |

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
│   ├── execution_metric.schema.yaml
│   ├── query_instance.schema.yaml
│   ├── statistics_result.schema.yaml
│   └── statistics-result.schema.yaml   # deprecated duplicate
└── tasks.md                # generated later by /speckit-tasks
```

### Source Code (repository root)

```
projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/
├── code/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py          # verified dataset download & checksum
│   ├── query_generator.py      # synthetic queries + complexity labels
│   ├── reference_engine.py     # deterministic greedy reference plan
│   ├── optimal_planner.py      # exhaustive optimal planner for sampled subset
│   ├── engine_simulator.py     # wrappers for BM25, SQLite, RDFLib with cgroups
│   ├── benchmark_runner.py     # orchestrates execution & logging
│   ├── stats.py                # ANOVA, Tukey, chi‑square, sensitivity sweep, slope‑ratio
│   ├── visualize.py            # interaction plot generator
│   ├── generate_execution_metric.py  # writes execution_metric.json
│   └── main.py                 # CLI entry point (supports --help, --stage, --run-optimal-planner)
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── generation_log.json
│   │   ├── optimal_ground_truth.json
│   │   ├── execution_logs.csv
│   │   ├── execution_metric.json
│   │   └── baseline_overhead.json
│   └── results/
│       ├── anova_results.json
│       ├── sensitivity_analysis.json
│       ├── statistics_results.json
│       └── interaction_plot.png
├── tests/
│   ├── unit/
│   │   ├── test_query_generator.py
│   │   ├── test_reference_engine.py
│   │   └── test_optimal_planner.py
│   └── integration/
│       └── test_benchmark.py
├── requirements.txt
├── pyproject.toml
└── .ruff.toml
```

## Phase Breakdown & FR/SC Mapping

| Phase | Tasks | Deliverable | Covered FR / SC |
|-------|-------|-------------|-----------------|
| **0 – Exhaustive Optimal Planner** | • Sample a set of queries.<br>• Run exhaustive search to obtain true optimal plans.<br>• Store in `optimal_ground_truth.json`. | Ground‑truth for translation error (sample) | FR‑004, FR‑008 |
| **1 – Environment & Data Prep** | • Pin dependencies.<br>• Download MS MARCO & DBpedia triples via verified URLs.<br>• Compute checksums. | `data/raw/` populated, checksum file | FR‑001 |
| **2 – Query Generation & Reference Plans** | • Generate a sizable collection of queries that span the four complexity levels across all sources.<br>• Assign UUID, `source_type`, `complexity_level`, logical plan.<br>• Run greedy reference engine → `ground_truth_plan`.<br>• Handle depth overflow warnings.<br>• Validate `generation_log.json` against `query_instance.schema.yaml`. | `generation_log.json` | FR‑002, FR‑004, FR‑008, FR‑015, SC‑001, SC‑002 |
| **3 – Baseline Overhead Calibration** | • Run **five** trivial queries per engine under same cgroups.<br>• Store median latency per engine in `baseline_overhead.json`. | `baseline_overhead.json` | FR‑010 |
| **4 – Benchmark Execution (CPU‑throttled)** | • Verify cgroups; abort with exit 99 if unavailable (FR‑014).<br>• Enforce **≤ 1 000 ms** CPU quota per query.<br>• Execute queries with 60 s timeout; record latency, `translation_error` (optimal vs. greedy), `precision_at_10`, flags.<br>• Write CSV (`execution_logs.csv`) and aggregated JSON (`execution_metric.json`). | `execution_logs.csv`, `execution_metric.json` | FR‑001, FR‑002, FR‑003, FR‑004, FR‑009, FR‑010, FR‑012, FR‑014, FR‑015 |
| **5 – Statistical Analysis** | • Two‑way ANOVA with interaction term; diagnostics; Tukey HSD.<br>• Chi‑square test for translation‑error stability.<br>• Sensitivity sweep (cut‑offs 2, 3, 4) with Bonferroni.<br>• **Slope‑ratio** (graph vs. text) regression.<br>• Precision@10 per source and differences.<br>• Export JSON results (`anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`). | Statistics JSON files | FR‑005, FR‑007, FR‑011, SC‑001, SC‑002, SC‑004 |
| **6 – Visualization** | • Interaction plot with highlighted graph line, spike annotation, slope‑difference labels. | `interaction_plot.png` | FR‑006, SC‑005 |
| **7 – Reporting & Quickstart** | • Assemble figures & tables; update quickstart with new flags; provide reproducibility checklist. | Documentation | All SCs (traceability) |

## Compute Feasibility
- All engines are pure‑Python or std‑lib and run comfortably on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk).
- No GPU‑only libraries are used; no Kaggle offload needed.
- Datasets are parquet files downloaded directly and sized to fit within RAM; total disk usage < 7 GB.
- Expected total runtime ≤ 5 h (within the 6 h CI limit).

## Decision Rationale
1. **CPU‑First**: Chosen libraries have proven CPU performance on the free‑tier runner; no GPU needed.
2. **Open Data**: Verified HuggingFace URLs for MS MARCO and DBpedia triples are used; relational and graph workloads are derived directly from the triples, satisfying heterogeneous source fidelity.
3. **Statistical Soundness**: Diagnostics, robust alternatives, categorical treatment of complexity, Bonferroni correction for multiple cut‑offs, power analysis, slope‑ratio metric, and explicit handling of timeouts satisfy Constitution Principle VII.
4. **Engine Overhead Control**: Median baseline calibration mitigates scheduler noise; additive correction justified with fallback log‑ratio.
5. **Causal Framing**: Explicitly stated as associative, not causal.
6. **Naming Consistency**: All latency fields are `latency_ms` (baseline‑corrected); `corrected_latency_ms` removed.
7. **Execution Metric Artifact**: `execution_metric.json` now includes `precision_at_10` and satisfies FR‑012.
8. **Construct Validity**: Exhaustive optimal planner provides true ground truth on sampled subset; greedy reference serves as scalable heuristic for the full set.
9. **Relevance Ground‑Truth**: MS MARCO qrels are used for text; for relational/graph queries relevance is defined as the set of target entities/documents reachable by the logical plan, enabling meaningful Precision@10.
10. **Duplicate Schema Removal**: Hyphenated `statistics-result.schema.yaml` deprecated to avoid SSoT ambiguity.

---

