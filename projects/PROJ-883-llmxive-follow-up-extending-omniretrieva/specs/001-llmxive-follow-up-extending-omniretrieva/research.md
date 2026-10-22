# Research: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question
*Does end‑to‑end latency of a unified retrieval router exhibit a non‑linear scaling **association** (“structural mismatch cost”) for high‑complexity (multi‑hop) queries on **graph** sources relative to **text** and **relational** sources when executed under strict CPU constraints?*  
*(Re‑framed as an associative relationship rather than a causal claim; see Constitution Principle VII.)*

## Hypotheses
- **H1 (Latency Interaction)** – A statistically significant interaction exists between **query complexity** (categorical levels 1‑4+) and **source type** (categorical) on **latency_ms** (baseline‑corrected). The slope for **graph** sources is steeper than for text or relational sources.
- **H2 (Disagreement Stability)** – The binary **disagreement** rate (engine‑generated plan deviates from the deterministic **ground_truth_plan**) does **not** differ significantly between low‑complexity (levels 1‑2) and high‑complexity (levels 3‑4+) queries.

## Methodology

### 1. Query Generation
- For each source type, generate **125 queries** per complexity level (1, 2, 3, 4+), totaling **1 500** queries.
- Each query receives a UUID, `source_type`, integer `complexity_level`, and a logical plan (list of operations).
- Stored in `data/processed/generation_log.json` and validated against `query_instance.schema.yaml`.

### 2. Reference Engine (FR‑008)
- Deterministic greedy algorithm selects the next step with the **lowest pre‑computed cost** (cost table derived from a held‑out sample, independent of the router’s live cost model).
- Produces a **ground_truth_plan** identifier stored alongside each query instance.
- The term *ground_truth_plan* is used consistently (see plan_consistency‑32a13f54) and **does not claim absolute optimality**; it serves as a reproducible baseline for measuring **disagreement**.

### 3. Execution & CPU Throttling (FR‑001‑FR‑003)

#### 3.1 Engine Overhead Calibration
- Run a trivial (single‑hop) query on each engine (BM25, SQLite, RDFLib) under the same cgroups settings.
- Record the baseline latency per engine and store in `baseline_overhead.json`.
- Subsequent query latencies are **baseline‑corrected** to isolate structural mismatch effects (addresses methodology‑5e4c0b62).

#### 3.2 Benchmark Execution
- Verify cgroups (`--cpu-quota=50000` for [deferred] of a core) before each query; abort with `ERR_THROTTLE_UNAVAILABLE` if unavailable.
- Engines:  
  - Text → BM25 over MS MARCO passages.  
  - Relational → SQLite queries over derived tables.  
  - Graph → RDFLib SPARQL traversal over DBpedia triples.
- Wall‑clock latency measured with `time.perf_counter()`; no `time.sleep`.
- Results (including `timestamp`, `translation_error` flag, `timeout_flag`, `success_flag`) written to `data/processed/execution_logs.csv` and aggregated per‑query JSON `execution_metric.json` (conforms to `execution_metric.schema.yaml`).

### 4. Statistical Analysis (FR‑005, FR‑007, H2)

#### 4.1 Two‑way ANOVA (Interaction Test)
- Model: `latency_ms_corrected ~ C(source_type) * C(complexity_level) + C(source_type)`.
- **Diagnostics**: Shapiro‑Wilk normality, Levene homogeneity. If violated, apply log‑transform or Huber robust regression; both reported.
- **Multiple‑comparison correction**: Tukey HSD on all pairwise source‑type contrasts (family‑wise error ≤ 0.05).
- Significance threshold: `p < 0.05` for the interaction term (SC‑001).

#### 4.2 Disagreement Stability (H2)
- Contingency table of `translation_error` vs. `complexity_group` (low = 1‑2, high = 3‑4+).  
- Perform **Chi‑square test of independence**; if any expected cell < 5, fall back to **Fisher’s exact test**.  
- Report χ², p‑value, and effect size (Cramér’s V). Stability claimed if `p ≥ 0.05` (SC‑002).

#### 4.3 Sensitivity Sweep (FR‑007)
- For cut‑offs 2, 3, 4, fit piecewise linear regression on mean latency per complexity level.
- Compute:  
  - `spike_point` = complexity level where `|Δ latency|` between consecutive levels is maximal.  
  - `slope_change` = slope after `spike_point` minus slope before.  
- Apply **Bonferroni correction** for the three cut‑offs to control family‑wise error (addresses methodology‑567625c1).  
- Store results in `sensitivity_analysis.json`.

#### 4.4 Optional Manual Validation (addresses scientific_soundness‑2f51c7dc)
- Randomly sample ≈ 20 high‑complexity queries.
- Manually verify the engine‑generated plan against an external gold‑standard (e.g., hand‑crafted optimal plan) to assess the fidelity of the greedy `ground_truth_plan`.
- Report the proportion of cases where the greedy plan matches the external gold‑standard; discuss implications for interpreting `translation_error`.

### 5. Visualization (FR‑006)
- Interaction plot (latency vs. complexity) with distinct colored lines for each `source_type`; graph line highlighted; vertical marker at identified `spike_point`.  
- Saved as `interaction_plot.png`.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Tukey HSD controls family‑wise error; Bonferroni correction applied to sensitivity sweep.
- **Power**: With 1 500 observations, a medium effect size (f = 0.25) yields > 0.99 power for the interaction (computed via `statsmodels.stats.power.FTestPower`).
- **Causal Framing**: Observational within a controlled CPU‑constrained environment; findings are **associational**, not causal across hardware platforms (Constitution Principle VII).
- **Collinearity**: Full factorial design ensures orthogonal `source_type` × `complexity_level`.
- **Measurement Validity**: The *ground_truth_plan* is generated by an **independent deterministic greedy reference engine**, providing a reproducible baseline for measuring *disagreement*. The limitation that this is not an absolute ground truth is explicitly acknowledged (addresses scientific_soundness‑2f51c7dc).

## Decision Rationale
1. **CPU‑First**: All chosen libraries have proven CPU performance on the free‑tier runner; no GPU needed.
2. **Open Data**: Only the three verified URLs are used; relational workload derived from DBpedia stays within the open‑data mandate.
3. **Statistical Soundness**: Diagnostics, robust alternatives, categorical treatment of complexity, Bonferroni correction for multiple cut‑offs, and power analysis satisfy Constitution Principle VII.
4. **Engine Overhead Control**: Baseline calibration isolates structural mismatch from engine‑specific overhead (addresses methodology‑5e4c0b62).
5. **Causal Framing**: Explicitly stated as associative, not causal (addresses methodology‑c67e7268).
6. **Naming Consistency**: All references to the deterministic plan use the schema field `ground_truth_plan` (addresses plan_consistency‑32a13f54).
7. **Execution Metric Artifact**: Added generation of `execution_metric.json` to satisfy the corresponding contract (addresses plan_consistency‑074ae762).

---



