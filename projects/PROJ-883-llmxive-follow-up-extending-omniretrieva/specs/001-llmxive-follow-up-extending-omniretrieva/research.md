# Research: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question
*Does end‑to‑end latency of a unified retrieval router exhibit a non‑linear scaling **association** ("structural mismatch cost") for high‑complexity (multi‑hop) queries on **graph** sources relative to **text** and **relational** sources when executed under strict CPU constraints?*
*(Re‑framed as an associative relationship rather than a causal claim; see Constitution Principle VII.)*

## Hypotheses
- **H1 (Latency Interaction)** – A statistically significant interaction exists between **query complexity** (categorical levels 1‑4+) and **source type** (categorical) on **latency_ms** (baseline‑corrected). The slope for **graph** sources is steeper than for text or relational sources.
- **H2 (Disagreement Stability)** – The binary **translation_error** rate (engine‑generated plan deviates from the *true* optimal plan on the sampled subset, otherwise from the greedy reference) does **not** differ significantly between low‑complexity (levels 1‑2) and high‑complexity (levels 3‑4+) queries.

## Methodology

### 1. Query Generation & Ground‑Truth Plans
- For each source type, generate **125 queries** per complexity level (1, 2, 3, 4+), totaling **1 500** queries.
- Logical plans are constructed from **real structural metadata**:
  - **Text** – MS MARCO passage IDs.
  - **Relational** – Join keys derived from DBpedia triples (tables `entities`, `relations`, `entity_relation`).
  - **Graph** – Edge traversals over DBpedia triples.
- Each query receives a UUID, `source_type`, integer `complexity_level`, and a `logical_plan` (`steps` list).
- **Depth overflow**: Queries exceeding the generator's maximum recursion depth are capped or dropped; a warning `DEPTH_OVERFLOW: query_id=<id>` is logged (FR‑015).
- **Ground‑truth**:
  - **Sampled subset (200 queries)**: Run an **exhaustive optimal planner** (brute‑force search) to obtain the true optimal plan; stored in `optimal_ground_truth.json`.
  - **Full set**: Run the deterministic **greedy reference engine** (pre‑computed cost table) to obtain a reproducible `ground_truth_plan`.
- Store all query instances in `data/processed/generation_log.json` and validate against `query_instance.schema.yaml`.

### 2. Relevance Ground‑Truth & Precision@10 (FR‑009)
- **Text**: Use the official MS MARCO qrels (downloaded alongside the corpus) to define relevant passages per query.
- **Relational & Graph**: For each synthetic query, the **target entities** (the leaf nodes of the logical plan) are defined as the relevant set. This deterministic relevance set enables a meaningful Precision@10 calculation.
- Precision@10 is computed per query and aggregated per `source_type`; the average difference between source types must be ≤ 0.02 (SC‑002).

### 3. Baseline Overhead Calibration (FR‑010)
- Run **five** trivial (single‑hop) queries per engine under identical cgroups settings.
- Record wall‑clock latency; store the **median** per engine in `baseline_overhead.json`.
- Subsequent query latencies are **baseline‑corrected** by subtracting the median. If subtraction yields negative values, fall back to a log‑ratio normalization (scientific_soundness‑c93bd729).

### 4. Execution & CPU Throttling (FR‑001–FR‑003)
- **CPU quota**: Enforce a **≤ 1 000 ms** CPU time limit per query via cgroups. If the quota cannot be applied, the run aborts with exit code 99 (FR‑014, concern‑71ee64ce).
- **Timeout**: 60‑second wall‑clock timeout; recorded as `timeout_flag=true` and excluded from the primary ANOVA (scientific_soundness‑511c8ca8). A censored‑regression sensitivity analysis is also performed.
- **Metrics recorded** (per query): `latency_ms` (baseline‑corrected), `translation_error` (true error for sampled subset, heuristic error otherwise), `precision_at_10`, `success_flag`, `timeout_flag`, `synthetic_flag`, `throttling_mode`.
- Results are written to `execution_logs.csv` (validated by `execution_log.schema.yaml`) and aggregated into `execution_metric.json` (validated by `execution_metric.schema.yaml`).

### 5. Statistical Analysis (FR‑005, FR‑007, FR‑011, H2)

#### 5‑a. Two‑way ANOVA (Interaction Test)
- Model: `latency_ms ~ C(source_type) * C(complexity_level)`.
- Report F‑statistic, p‑value, 95 % CI for the interaction term; flag hypothesis ‘supported’ only if p < 0.05.
- **Diagnostics**: Shapiro‑Wilk normality, Levene homogeneity. If violated, apply log‑transform or Huber robust regression (scientific_soundness‑c93bd729).

#### 5‑b. Post‑hoc Tukey HSD
- Pairwise source‑type contrasts; family‑wise error ≤ 0.05.

#### 5‑c. Translation‑Error Stability
- Contingency table of `translation_error` vs. `complexity_group` (low = 1‑2, high = 3‑4+).
- **Chi‑square** test (Fisher fallback); report χ², p, Cramér’s V. Stability claimed if absolute error‑rate difference ≤ 0.02 (SC‑002).

#### 5‑d. Sensitivity Sweep & Bonferroni (FR‑007, FR‑011)
- For cut‑offs {2, 3, 4}, fit piecewise linear regression on **mean latency per depth**.
- Compute `spike_point` (complexity level with maximal absolute latency jump) and `slope_change` (post‑spike slope – pre‑spike slope).
- Apply **Bonferroni correction** across the three cut‑offs; store results in `sensitivity_analysis.json`.

#### 5‑e. **Slope‑Ratio Computation** (SC‑001 second conjunct)
- Simple linear regression of **mean latency** vs. **depth** for `graph` and `text` separately.
- Compute `slope_ratio = slope_graph / slope_text`; store in `anova_results.json`. SC‑001 is satisfied if `slope_ratio > 1.5`.

#### 5‑f. **Precision@10 Summary** (SC‑002 second conjunct)
- Compute average Precision@10 per source type; store `avg_precision_at_10` per source in `statistics_results.json`. Verify that pairwise differences ≤ 0.02.

#### 5‑g. **Timeout Treatment**
- Exclude timeout rows from primary ANOVA; run a secondary censored‑regression (Tobit) as a sensitivity check.

### 6. Visualization (FR‑006)
- Interaction plot (latency vs. complexity) with distinct colored lines per `source_type`; highlight the graph line; annotate the identified `spike_point` and slope differences; save as `interaction_plot.png`.

### 7. Reproducibility & Quickstart
- All steps are deterministic given the seeded random generators.
- `quickstart.md` documents required flags (`--run-optimal-planner`, `--baseline-reps=5`) and environment checks.

## Dataset Strategy

| Source | Verified URL | Role |
|--------|--------------|------|
| MS MARCO (parquet) | https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/v1.1/test-00000-of-00001.parquet | Text corpus for BM25 engine and text query construction; qrels downloaded from the same repo for relevance. |
| DBpedia triples (parquet) | https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet | Provides explicit `<subject, predicate, object>` triples; used to build both a relational SQLite view (tables `entities`, `relations`, `entity_relation`) and an RDFLib graph for graph queries. |

Both datasets are open, directly downloadable parquet files fetched on the CI runner; checksums recorded under `data/`. The relational workload is derived from the explicit triples, ensuring genuine join‑key structure (concern‑728fc9d5). No gated or unverified sources are used.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Tukey HSD controls family‑wise error for pairwise contrasts; Bonferroni correction applied across the three sensitivity cut‑offs (FR‑011).
- **Power**: With 1 500 observations, a medium effect size (f = 0.25) yields > 0.99 power for the interaction (computed via `statsmodels.stats.power.FTestPower`); the balanced factorial design avoids collinearity between factors.
- **Causal Framing**: Observational within a controlled CPU‑constrained environment; findings are **associational**, not causal across hardware platforms.
- **Collinearity**: Full factorial design ensures orthogonal `source_type` × `complexity_level`.
- **Measurement Validity**: Ground‑truth plans from the exhaustive optimal planner guarantee a correct translation‑error baseline; the greedy reference engine provides a scalable baseline for the full set. Relevance sets are defined deterministically (text via official qrels, relational/graph via target entities), satisfying FR‑009.

## Decision/Rationale: Compute Placement
- **CPU**: all methods (BM25, SQLite, RDFLib, ANOVA/Tukey/chi‑square, piecewise regression, slope‑ratio, plotting) run on the 2‑core CPU runner in default precision.
- **GPU escape hatch**: NOT used — no method in this study requires CUDA; no GPU‑dependent libraries are imported.

---

