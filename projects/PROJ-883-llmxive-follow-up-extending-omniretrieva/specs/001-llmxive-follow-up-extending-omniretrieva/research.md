# Research: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question
*Does end‑to‑end latency of a unified retrieval router exhibit a non‑linear scaling penalty (“structural mismatch cost”) for high‑complexity (multi‑hop) queries on **graph** sources relative to **text** and **relational** sources when executed under strict CPU constraints?*

## Hypotheses
- **H1 (Latency Interaction)** – A statistically significant interaction exists between **query complexity** (categorical levels 1‑4+) and **source type** on **latency_ms**; the slope for **graph** sources is steeper than for text or relational sources.
- **H2 (Translation‑Error Stability)** – The binary **translation error** rate does **not** differ significantly between low‑complexity (levels 1‑2) and high‑complexity (levels 3‑4+) queries.

## Dataset Strategy
All datasets are openly downloadable via HuggingFace `datasets`. No gated data is used.

| Source Type | Verified Dataset (URL) | Loading Method | Role |
|-------------|------------------------|----------------|------|
| **Text** | `https://huggingface.co/datasets/nlpconnect/ms_marco_subset_v2.1/resolve/main/data/test-00000-of-00001.parquet` | `datasets.load_dataset("nlpconnect/ms_marco_subset_v2.1", split="test")` | Provides passages for BM25 retrieval. |
| **Graph** | `https://huggingface.co/datasets/fancyzhx/dbpedia_14/resolve/main/dbpedia_14/test-00000-of-00001.parquet` | `datasets.load_dataset("fancyzhx/dbpedia_14", split="test")` → `rdflib` ingestion | Supplies RDF triples for SPARQL‑style traversal. |
| **Relational** | **Derived relational view** from the DBpedia parquet (tables `entity_attributes` and `entity_links` generated programmatically). | `sqlite3` in‑memory DB built from the derived CSV files. | Enables multi‑table joins emulating a relational workload. |

*If the DBpedia graph lacks sufficient depth for 4‑hop queries, the pipeline aborts with `ERR_DEPTH_INSUFFICIENT`; no synthetic topology is used for primary analysis (synthetic queries are logged with `synthetic_flag=true` and excluded from ANCOVA).*

## Methodology

### 1. Query Generation
- For each source type, generate **125 queries** per complexity level (1, 2, 3, 4+), totaling **1 500** queries.
- Each query receives a UUID, `source_type`, integer `complexity_level`, and a logical plan (list of operations).
- Queries are stored in `data/processed/generation_log.json` and validated against `query_instance.schema.yaml`.

### 2. Reference Engine (FR‑008)
- Implements a deterministic greedy algorithm that selects the next step with the **lowest pre‑computed cost** (cost table derived from a held‑out sample, independent of the router’s live cost model).
- Produces a **reference plan** identifier stored alongside each query instance.
- The term *reference* (not “ground‑truth”) addresses the reviewer’s note that a greedy heuristic is a model.

### 3. Execution & CPU Throttling (FR‑001‑FR‑003)
- **cgroups** are applied (`--cpu-quota=50000` for 50 % of a core) before each query execution. If cgroups cannot be set, the run aborts with `ERR_THROTTLE_UNAVAILABLE`.
- Engines:  
  - Text → BM25 over MS MARCO passages.  
  - Relational → SQLite queries over the derived relational tables.  
  - Graph → RDFLib SPARQL traversal over DBpedia triples.
- Wall‑clock latency measured with `time.perf_counter()`; no `time.sleep` is used.
- Results (including `timestamp`, `translation_error`, `timeout_flag`, `success_flag`) are written to `data/processed/execution_logs.csv`.

### 4. Statistical Analysis (FR‑005, FR‑007, H2)

#### 4.1 ANCOVA (Interaction Test)
- Model: `latency_ms ~ C(source_type) * C(complexity_level) + C(source_type)`.
- **Diagnostics**: Shapiro‑Wilk normality, Levene homogeneity. If violated, a log‑transform or Huber robust regression is applied and both results reported.
- **Multiple‑comparison correction**: Tukey HSD on all pairwise source‑type contrasts (family‑wise error rate ≤ 0.05).
- Significance threshold: `p < 0.05` for the interaction term (SC‑001).

#### 4.2 Translation‑Error Stability (H2)
- Contingency table of `translation_error` vs. `complexity_group` (low = 1‑2, high = 3‑4+).  
- Perform **Chi‑square test of independence**; if any expected cell < 5, fall back to **Fisher’s exact test**.  
- Report χ², p‑value, and effect size (Cramér’s V). Stability is claimed if `p ≥ 0.05` (SC‑002).

#### 4.3 Sensitivity Sweep (FR‑007)
- For cut‑offs 2, 3, 4, fit piecewise linear regression on mean latency per complexity level.  
- Compute:  
  - `spike_point` = complexity level where `|Δ latency|` between consecutive levels is maximal.  
  - `slope_change` = slope after `spike_point` minus slope before.  
- Store results in `sensitivity_analysis.json`.

### 5. Visualization (FR‑006)
- Interaction plot (latency vs. complexity) with separate colored lines for each `source_type`.  
- Graph line highlighted; vertical marker at the identified `spike_point`.  
- Saved as `interaction_plot.png`.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Tukey HSD controls family‑wise error.
- **Power**: With 1 500 observations, a medium effect size (f = 0.25) yields > 0.99 power for the interaction (computed via `statsmodels.stats.power.FTestPower`).
- **Causal Framing**: Observational within a controlled CPU‑constrained environment; claims are associative, not causal across hardware platforms (Constitution Principle VII).
- **Collinearity**: Full factorial design ensures orthogonal `source_type` × `complexity_level`.
- **Measurement Validity**: Reference plans are derived from an *independent* cost table; translation‑error metric measures deviation from this deterministic reference.

## Decision Rationale
- **CPU‑First**: All chosen libraries have proven CPU performance on the free‑tier runner; no GPU‑only components are needed.
- **Open Data**: Only the three verified URLs are used; relational workload is derived from DBpedia to stay within the open‑data mandate.
- **Statistical Soundness**: Diagnostics, robust alternatives, categorical treatment of complexity, and explicit H2 test satisfy Constitution Principle VII.
- **Reviewer Feedback**: Re‑framed “ground‑truth plan” as a *reference plan* and clarified that translation‑error measures agreement with this deterministic baseline, not correctness.

---
