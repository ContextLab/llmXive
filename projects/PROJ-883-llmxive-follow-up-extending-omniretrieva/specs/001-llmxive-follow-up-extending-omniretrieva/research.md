# Research: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question
*Does end‑to‑end latency of a unified retrieval router exhibit a non‑linear **association** (“structural mismatch cost”) for high‑complexity (multi‑hop) queries on **graph** sources relative to **text** and **relational** sources when executed under strict CPU constraints?*  
(The claim is framed as associative, not causal, per Constitution Principle VII.)

## Hypotheses
- **H1 (Latency Interaction)** – A statistically significant interaction exists between **query complexity** (categorical levels 1‑4+) and **source type** (text, relational, graph) on **baseline‑corrected latency_ms**. The slope for graph queries is steeper than for text or relational queries.
- **H2 (Translation‑Error Stability)** – The binary **translation_error** rate (deviation from the *optimal* plan on the sampled subset) does **not** differ appreciably between low‑complexity (levels 1‑2) and high‑complexity (levels 3‑4+) queries (difference ≤ 0.02).

## Methodology

### 1. Dataset Strategy
| Source | Verified URL | Role |
|--------|--------------|------|
| MS MARCO passage dev set | https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/v1.1/test-00000-of-00001.parquet | Text corpus for BM25 engine; relevance (qrels) derived via `ir-datasets` loader (see “Verified loader recipe” below). |
| DBpedia triples (2023) | https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet | Provides `<subject, predicate, object>` triples; used to construct relational SQLite tables and an RDFLib graph for graph queries. |

Both datasets are open, directly downloadable, and fit within the CI runner’s disk quota. Checksums are recorded under `data/raw/checksums.txt`.

**Verified loader recipe (used in `code/data_loader.py`):**
```python
import ir_datasets, pandas as pd, hashlib, pathlib, json, requests

# MS MARCO
marco = ir_datasets.load('msmarco-passage/dev')
queries = [{ 'query_id': q.query_id, 'query_text': q.text } for q in marco.queries_iter()]
qrels = { qid: max(rel.relevance for rel in marco.qrels_iter() if rel.query_id == qid)
          for qid in { rel.query_id for rel in marco.qrels_iter() } }
for q in queries:
    q['relevance_label'] = qrels.get(q['query_id'])
df = pd.DataFrame(queries)
df.to_parquet('data/raw/ms_marco.parquet')
# checksum
hash_md5 = hashlib.sha256()
with open('data/raw/ms_marco.parquet','rb') as f:
    for chunk in iter(lambda: f.read(8192), b''):
        hash_md5.update(chunk)
pathlib.Path('data/raw/checksums.txt').write_text(f"ms_marco.parquet {hash_md5.hexdigest()}\n")
```

A similar routine streams the DBpedia parquet file.

### 2. Synthetic Query Generation & Reference Plans
- **Quantity**: 1 500 queries total (125 per `source_type` × 4 `complexity_level`).  
- **Construction**:  
  - *Text*: random MS MARCO passage IDs combined into multi‑hop logical plans (e.g., sequential BM25 retrievals).  
  - *Relational*: join keys derived from DBpedia triples (e.g., `entities ↔ entity_relation ↔ entities`).  
  - *Graph*: edge‑traversal sequences over the RDF graph.  
- Each query gets a UUID, exact `complexity_level` (plan depth), and a deterministic `logical_plan` (list of operations).  
- **Depth overflow**: If the generator’s maximum recursion depth (set to 6) would be exceeded, the query is either capped at depth 6 or dropped; a warning `DEPTH_OVERFLOW: query_id=<id>` is logged (FR‑015).  
- **Reference Plan**: Every query is passed through the **deterministic greedy reference engine** (`reference_engine.py`). The engine uses a pre‑computed cost table and returns a reproducible identifier `greedy_plan_<8hexhash>` stored as `reference_plan_id`. This plan is *not* treated as ground truth; it serves as a stable baseline for non‑sampled queries.  
- **Optimal Ground‑Truth (Sampled Subset)**: A stratified random sample of 200 queries (balanced across source and complexity) is processed by the **exhaustive optimal planner** (`optimal_planner.py`) which enumerates all feasible join orders and selects the minimum‑cost plan. The resulting `optimal_plan_id` is stored in `optimal_ground_truth.json`.  

All query instances are written to `data/processed/generation_log.json` and validated against `contracts/query_instance.schema.yaml`.

### 3. Relevance & Precision@10 (FR‑009)
- **Text**: Use the official MS MARCO qrels (available from the same `ir-datasets` load) to define relevant passages.  
- **Relational & Graph**: For each synthetic query, the *target entities* (leaf nodes of the logical plan) are defined as the relevance set. Precision@10 is computed as the proportion of these targets appearing among the top‑10 retrieved items.  

### 4. Baseline Overhead Calibration (FR‑010)
- Execute five trivial (single‑hop) queries per engine under identical cgroups settings.  
- Record wall‑clock latency; store the median per engine in `baseline_overhead.json`.  
- All subsequent latency measurements are **baseline‑corrected** by subtracting the corresponding median. If subtraction yields a negative value, we fall back to a log‑ratio normalization (`log(1 + latency) - log(1 + baseline)`).

### 5. Benchmark Execution (CPU‑Throttled) (FR‑001‑FR‑004, FR‑009‑FR‑015)
- **CPU quota enforcement**: Use `cgroups` to set a CPU time limit of **≤ 1 000 ms** per query. Failure to apply the limit aborts the run with **exit code 99** and a clear error message (FR‑014).  
- **Wall‑clock timeout**: 60 seconds; timed‑out queries are recorded with `timeout_flag=true`, latency set to the timeout value, and excluded from the primary ANOVA (but included in a secondary Tobit sensitivity check).  
- **Metrics per query** (written to `execution_logs.csv` and aggregated into `execution_metric.json`):  
  - `latency_ms` (baseline‑corrected)  
  - `translation_error` (boolean, **only** for the sampled subset where an optimal plan exists)  
  - `reference_deviation` (boolean, mismatch vs. greedy reference for all other queries)  
  - `precision_at_10` (float ∈ [0,1])  
  - `success_flag`, `timeout_flag`, `synthetic_flag`, `throttling_mode` (`cgroups` or `failed`).  

All fields conform to the contracts in `contracts/`.

### 6. Statistical Analysis (FR‑005, FR‑007, FR‑011, H2)

| Analysis | Model / Test | Key Outputs | Multiple‑Comparison Handling |
|----------|--------------|-------------|------------------------------|
| **Two‑way ANOVA** | `latency_ms ~ C(source_type) * C(complexity_level)` (statsmodels) | F‑statistic, p‑value, 95 % CI for interaction term | Post‑hoc Tukey HSD (family‑wise ≤ 0.05) |
| **Diagnostics** | Shapiro‑Wilk (normality), Levene (homogeneity) | If violated → log‑transform or Huber robust regression | – |
| **Translation‑Error Stability** | Chi‑square test of independence (`translation_error` vs. `complexity_group`) | χ², p, Cramér’s V | – |
| **Sensitivity Sweep** | Piecewise linear regression on mean latency per depth for cut‑offs {2, 3, 4} | `spike_point`, `slope_change` per cutoff | **Bonferroni** correction across the three cut‑offs (FR‑011) |
| **Slope‑Ratio** | Simple linear regression (mean latency vs. depth) for `graph` and `text` separately | `slope_ratio = slope_graph / slope_text` (must exceed 1.5 for SC‑001) | – |
| **Precision@10 Summary** | Mean per source type | `avg_precision_at_10` per source; max pairwise diff ≤ 0.02 (SC‑002) | – |
| **Timeout Sensitivity** | Tobit (censored) regression as a secondary check | Consistency of interaction effect | – |

All results are stored as JSON files (`anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`).

### 7. Visualization (FR‑006)
- Generate an interaction plot (`latency_ms` vs. `complexity_level`) with distinct colors for each `source_type`.  
- Highlight the graph line, annotate the identified `spike_point`, and display the slope‑ratio annotation.  
- Save as `interaction_plot.png` (PNG, non‑empty).  

### 8. Reproducibility & Quickstart (All SCs)
- All random generators are seeded (`np.random.seed(42)`, `random.seed(42)`).  
- `quickstart.md` documents the exact CLI commands, required flags, and verification steps (lint, help output, integration test).  

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Tukey HSD for pairwise source contrasts; Bonferroni across three sensitivity cut‑offs.  
- **Power**: With 1 500 observations, a medium effect size (f = 0.25) yields > 0.99 power for the interaction term (computed via `statsmodels.stats.power.FTestPower`).  
- **Causal Framing**: Findings are **associational**; the controlled CPU environment is experimental, but we do not claim hardware‑agnostic causality.  
- **Collinearity**: Full factorial design ensures orthogonal `source_type` and `complexity_level`.  
- **Measurement Validity**: Optimal plans are exhaustive; greedy reference is deterministic and documented; relevance for relational/graph queries is defined by target entities, providing a valid Precision@10 metric.  

## Decision/Rationale: Compute Placement
- **CPU‑First**: All components (BM25 via `pyserini`‑style scoring, SQLite, RDFLib, statsmodels) run on the free runner; no GPU‑only libraries are required.  
- **No GPU Escape**: The methodology does not demand deep learning inference, thus avoiding the need for Kaggle offload.  

---
