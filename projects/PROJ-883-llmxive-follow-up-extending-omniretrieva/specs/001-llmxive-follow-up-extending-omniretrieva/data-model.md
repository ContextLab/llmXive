# Data Model: Structural Mismatch Cost in Heterogeneous Retrieval

## Overview
Defines every persistent artifact produced by the benchmarking pipeline. All files live under `data/` and are validated against the YAML‑Schema contracts in `contracts/` (each contract is a single, valid YAML document).

## Core Entities

### 1. Query Instance (Intermediate SSoT)
| Field | Type | Description |
|-------|------|-------------|
| `query_id` | UUID (string) | Unique identifier. |
| `source_type` | enum(`text`,`relational`,`graph`) | Category of the data source. |
| `complexity_level` | integer (≥ 1) | Exact plan depth (plan hops). |
| `logical_plan` | object `{ "steps": [string, …] }` | Ordered list of logical operations. |
| `reference_plan_id` | string | Identifier of the deterministic greedy plan (`greedy_plan_<8hex>`). |
| `synthetic_flag` | boolean | `true` if the query topology was synthetically generated. |

### 2. Execution Metric (Final SSoT)
| Field | Type | Description |
|-------|------|-------------|
| `query_id` | UUID (string) | FK to Query Instance. |
| `latency_ms` | float | Baseline‑corrected wall‑clock latency (ms). |
| `translation_error` | boolean | **Only** for queries with an optimal ground‑truth (sampled subset): `true` if the router’s plan deviates from the optimal plan. |
| `reference_deviation` | boolean | `true` if the router’s plan deviates from the greedy reference plan (for non‑sampled queries). |
| `precision_at_10` | float (0 – 1) | Precision@10 for the query. |
| `timeout_flag` | boolean | `true` if execution exceeded the 60 s wall‑clock limit. |
| `success_flag` | boolean | `true` if execution completed without error. |
| `synthetic_flag` | boolean | Propagated from the originating Query Instance. |
| `throttling_mode` | enum(`cgroups`,`failed`) | How CPU limits were enforced. |
| `timestamp` | ISO‑8601 string | When the measurement was taken. |

### 3. Statistical Result
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string (`anova`, `tukey`, `chi2`, `sensitivity`, `slope_ratio`) | Analysis performed. |
| `parameters` | object | e.g., `{ "cutoff": 3 }`. |
| `statistics` | object | Test‑specific numbers (F, p, χ², slope values, etc.). |
| `interpretation` | string | Human‑readable summary of the result. |

## File Formats & Contracts

| File | Format | Contract |
|------|--------|----------|
| `data/processed/generation_log.json` | JSON array of **Query Instance** objects | `contracts/query_instance.schema.yaml` |
| `data/processed/optimal_ground_truth.json` | JSON mapping `query_id → optimal_plan_id` | No separate contract (derived from `query_instance`). |
| `data/processed/execution_logs.csv` | CSV (header row) | `contracts/execution_log.schema.yaml` |
| `data/processed/execution_metric.json` | JSON array of **Execution Metric** objects | `contracts/execution_metric.schema.yaml` |
| `data/processed/baseline_overhead.json` | JSON `{ "bm25": float, "sqlite": float, "rdflib": float }` | No separate contract (simple config). |
| `data/results/anova_results.json` | JSON (see `research.md` for structure) | No separate contract (consumed by visualisation). |
| `data/results/sensitivity_analysis.json` | JSON array of **Statistical Result** objects (type `sensitivity`) | `contracts/statistics_result.schema.yaml` |
| `data/results/statistics_results.json` | JSON (precision@10 summary, slope ratio, etc.) | No separate contract. |
| `data/results/interaction_plot.png` | PNG image | No contract (binary artifact). |

## Data Flow Diagram
1. **Data Loader** → downloads raw datasets → `data/raw/`.  
2. **Query Generator** → creates `generation_log.json`.  
3. **Reference Engine** → adds `reference_plan_id` to each query.  
4. **Optimal Planner** (sampled) → produces `optimal_ground_truth.json`.  
5. **Baseline Overhead** → writes `baseline_overhead.json`.  
6. **Benchmark Runner** → reads `generation_log.json`, enforces cgroups, writes `execution_logs.csv` and `execution_metric.json`.  
7. **Stats Module** → consumes `execution_logs.csv`, outputs statistical JSON files.  
8. **Visualization** → consumes `execution_logs.csv` → `interaction_plot.png`.  

All transformations are pure functions; no in‑place mutation of source files (Constitution Principle III).  

---
