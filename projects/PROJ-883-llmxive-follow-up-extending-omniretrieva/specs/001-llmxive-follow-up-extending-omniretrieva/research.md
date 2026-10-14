# Research: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question

Does the end‑to‑end latency of a unified retrieval router exhibit a non‑linear scaling penalty (“structural mismatch cost”) for high‑complexity (multi‑hop) queries against **graph‑based** knowledge sources compared to text or relational sources, under strict CPU constraints?

## Hypothesis

**H1** – There is a statistically significant interaction between `query_complexity` (treated as a **categorical** factor) and `source_type` on `latency_ms`. The slope for **graph** sources is steeper than for **text** or **relational** sources.

**H2** – Translation‑error rates (binary mismatch to deterministic greedy ground‑truth) remain **stable** across low‑ and high‑complexity groups (no statistically significant difference).

## Dataset Strategy

All datasets are open and directly downloadable via HuggingFace `datasets.load_dataset`. No gated data is used.

| Source Type | Dataset (Verified) | URL(s) | Usage Strategy |
|-------------|-------------------|--------|----------------|
| **Text** | MS MARCO (subset) | ` | Extract passages; synthetic queries simulate chained look‑ups. |
| **Relational** | Spider benchmark (subset) | `https://huggingface.co/datasets/allenai/spider/resolve/main/dev-00000-of-00001.parquet` | Load into SQLite; provides genuine multi‑table joins **independent** of DBpedia. |
| **Graph** | DBpedia (RDF) | ` | Load with `rdflib`; queries traverse real edges. |

**Synthetic Fallback Protocol** (depth insufficiency)  
1. `query_generator` inspects the DBpedia graph; if depth ≥ 4 is unavailable, the run **ABORTS** with error `ERR_DEPTH_INSUFFICIENT`.  
2. Synthetic topology may be generated **only** for stress‑testing; rows receive `synthetic_flag=1` and are excluded from primary ANCOVA and H2 analysis.

## Methodology

### 1. Query Generation
- Input: Verified datasets above.  
- For each source type, generate **125 queries** per complexity level (depth 1, 2, 3, 4+), totaling **1 500 queries**.  
- Each query receives a UUID, `source_type`, integer `complexity_level`, and a logical plan.

### 2. Ground‑Truth Engine (FR‑008)
- Deterministic greedy algorithm uses a **separate pre‑computed cost table** derived from a held‑out sample, **not** the router’s live cost model, ensuring independence.  
- Produces `ground_truth_plan` stored in `generation_log.json`.

### 3. Execution Engine & Throttling (FR‑001, FR‑002, FR‑003)
- **CPU constraint**: **Only** Linux `cgroups` are used (`--throttle cgroups`). If `cgroups` cannot be applied (e.g., permission error), the benchmark **fails fast** with error code `ERR_THROTTLE_UNAVAILABLE`.  
- Engines:  
  - Text – BM25 over MS MARCO passages.  
  - Relational – SQLite in‑memory DB built from Spider tables.  
  - Graph – `rdflib` SPARQL‑style traversal.  
- Wall‑clock latency measured with `time.perf_counter()`; no `sleep`‑based simulation.

### 4. Metric Collection (FR‑003, FR‑004)
- For each query we log: `query_id`, `source_type`, `complexity_level`, `latency_ms`, `timestamp` (ISO‑8601), `translation_error` (boolean), `success_flag` (boolean), `timeout_flag` (boolean), `synthetic_flag`, `throttling_mode`.  
- Output written atomically to `data/processed/execution_logs.csv`.

### 5. Statistical Analysis (FR‑005, FR‑006, FR‑007, H2)

#### 5.1 ANCOVA (Interaction Test)
- Model: `latency_ms ~ C(source_type) * C(complexity_level) + C(source_type)` (complexity categorical).  
- **Diagnostics**: Shapiro‑Wilk normality test, Levene’s homogeneity test. If violations detected, apply **log‑transform** or **Huber robust regression** and report both results.  
- Multiple‑comparison correction via **Tukey HSD** on pairwise source‑type contrasts.  
- Significance threshold `p < 0.05`.  

#### 5.2 Translation‑Error Stability (H2)
- **Chi‑square test of independence** on a contingency table of `translation_error` vs. `complexity_level` (collapsed into low (1‑2) vs. high (3‑4+)).  
- If any cell count < 5, fall back to **Fisher’s exact test**.  
- Report χ² statistic, p‑value, and effect size (Cramér’s V).  

#### 5.3 Sensitivity Sweep (FR‑007)
- For cutoffs 2, 3, 4, fit **piecewise linear regression** on mean latency per complexity level; compute `spike_point` (max absolute latency jump) and `slope_change` (difference of slopes before/after spike).  
- Store results in `sensitivity_analysis.json`.

### 6. Visualization (FR‑006)
- Interaction plot (latency vs. complexity) with separate lines per `source_type`.  
- Graph line highlighted; vertical marker at identified `spike_point`. Saved as PNG.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Tukey HSD controls family‑wise error rate.  
- **Power**: With 1 500 observations, a medium effect (f = 0.25) yields > 0.99 power for the interaction term (computed via `statsmodels.stats.power.FTestPower`).  
- **Causal Framing**: Observational within a controlled CPU‑constrained environment; claims are associative.  
- **Collinearity**: Full factorial design ensures orthogonality of `source_type` and `complexity_level`.  
- **Measurement Validity**: Ground‑truth plans derived from an **independent** cost table; translation‑error metric is not tautological.

## Decision Rationale

- **CPU‑First**: SQLite, RDFLib, BM25, statsmodels run efficiently on the free‑tier runner.  
- **Open Data**: DBpedia, MS MARCO, and Spider are fully downloadable via `datasets.load_dataset`.  
- **Statistical Soundness**: Diagnostics, robust fallback, categorical treatment of complexity, and explicit H2 test satisfy methodological standards.
