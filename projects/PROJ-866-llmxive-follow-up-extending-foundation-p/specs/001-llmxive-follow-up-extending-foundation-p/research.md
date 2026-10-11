# Research: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Research Question
What functional relationship exists between context compression (graph‑traversal depth limits) and policy‑violation error rate in synthetic multi‑agent workflows, and where does the “safe operating zone” threshold (error ≤ 1 %) lie?

## Dataset Strategy

### Verified Datasets
The experiment relies exclusively on **synthetically generated data**; no external open‑source dataset contains the required “policy graph” and “compression error” variables.

| Dataset | Source Type | Loader | Notes |
|---|---|---|---|
| Synthetic Workflows | Local generation (pm4py‑inspired) | `src/services/generator.py` | Deterministic, seeded, A substantial set of unique workflows with uniform depth distribution and varied policy complexity. |
| Execution Logs | Local simulation | `src/services/executor.py` | Generates Full‑Context and Compressed‑Context logs; each log entry conforms to `execution_log.schema.yaml`. |

All data are produced on‑the‑fly; no download step is required, satisfying the CI runner’s offline constraints.

### Data Generation & Simulation Logic
1. **Workflow Generation** (`generator.py`):  
   - Uses `networkx` to build directed graphs.  
   - Delegation depth sampled uniformly from 1‑10, guaranteeing ≥ 25 workflows per depth.  
   - Policy complexity sampled uniformly from 1‑20 (number of policy nodes).  
   - Fixed random seed (`42`) guarantees reproducibility (Constitution I).  
   - Each workflow is validated against the Oracle; unsolvable workflows are flagged `is_valid=False` and **excluded** from error‑rate calculations. The proportion of invalid workflows is recorded in `invalid_exclusion_report.json` (see T‑Invalid‑Exclusion‑Report).  

2. **Oracle Policy Engine** (`models/policy.py`):  
   - Deterministic state machine that **deduces** validity of each step from the *provided* policy context.  
   - Returns a violation only when required deduction fails, not merely because a node is missing.  
   - Completely independent of the compression algorithm (Constitution VI).

3. **Compression Simulation** (`compression.py` + `executor.py`):  
   - Implements BFS/DFS with configurable depth limit `k`.  
   - Token count obtained via `tiktoken` (`cl100k_base`) on the serialized subgraph.  
   - Edge cases: `k=0` → `context_reduction_pct="[deferred]"`; single‑node graphs → same marker.  

## Statistical Analysis Plan

### 1. Regression (Binomial GEE)
- **Model**: Binomial Generalized Estimating Equations (GEE) with logit link, exchangeable correlation structure, clustering by `workflow_id`. Implemented via `statsmodels.genmod.generalized_estimating_equations.GEE`.  
- **Fixed Effects**: `context_reduction_pct` (continuous), `policy_complexity`, `delegation_depth`.  
- **Goal**: Estimate the monotonic relationship; test significance of `context_reduction_pct`.

### 2. Multiple‑Comparison Correction
- Primary ordered comparisons (depth levels) use **Cochran‑Armitage trend test** (no correction needed for ordered test).  
- Any secondary pairwise depth comparisons receive **Bonferroni correction** to maintain family‑wise α = 0.05.

### 3. Threshold Detection
- Target: Identify the smallest `context_reduction_pct` where the **predicted** error rate first exceeds **[deferred]**.
- Method: Interpolate the fitted GEE curve; apply a **monotonicity diagnostic** (see below).  
- Confidence interval: Obtain a 95 % CI via **bootstrap** with **1000 resamples** (verified fact).  
- Output rounded to two decimal places.

### 4. Monotonicity Diagnostic
- After fitting the GEE, we verify that the predicted error rates are monotonic increasing with context reduction.  
- If violations are detected, we refit using **isotonic regression** (`sklearn.isotonic.IsotonicRegression`) to enforce monotonicity before threshold extraction.

### 5. Power Analysis (formal, simulation‑based)
- **Procedure**: Simulate 1000 synthetic datasets matching the planned design (500 workflows, the same depth/compression grid).  
- For each simulated dataset, fit the GEE and test whether the model detects a ≥ 1 % error jump at the true threshold.  
- The proportion of simulations where the effect is detected provides an empirical power estimate, which is reported in `run_metrics.json`.  
- This replaces the previous informal statement and satisfies the methodological requirement.

### 6. Edge‑Case Handling (already in plan)
- Single‑node graphs and `compression_depth=0` produce `context_reduction_pct="[deferred]"`.  
- Invalid workflows are excluded from error‑rate denominators; the exclusion rate is logged and reported.

### 7. Invalid‑Workflow Proportion Monitoring
- The pipeline records `invalid_workflow_count` and `total_workflows` in `invalid_exclusion_report.json`.  
- `run_metrics.json` includes the proportion `invalid_workflow_ratio = invalid_workflow_count / total_workflows`.  
- This metric is examined during analysis to assess potential bias; if the ratio exceeds 10 % a warning is issued.

## Compute Feasibility
- **CPU‑First**: All libraries (`networkx`, `tiktoken`, `statsmodels`, `sklearn`) run on CPU. No GPU‑only components.  
- **Memory**: 500 small graphs + JSON logs ≈ 200 MB; well under 7 GB limit.  
- **Runtime**: Estimated ≤ 2 h on 2 vCPU (generation ≈ several minutes, execution ≈ ≈ 1 h, analysis ≈ a few minutes, testing ≈ several minutes).  

## Decision / Rationale
- **Synthetic data** eliminates the need for unavailable external datasets and gives full control over depth/complexity variables.  
- **CPU‑only** respects the resource‑constrained constraint (Constitution VII) and enables execution on free GitHub Actions runners.  
- **Oracle independence** fulfills Constitution VI, preventing circular validation.  
- **Binomial GEE** provides a statistically valid approach for clustered binary outcomes, correcting the earlier mis‑specified MixedLM.  
- **Simulation‑based power analysis** offers a rigorous, documented estimate of statistical power.  
- **Monotonicity check** safeguards against non‑monotonic fitted curves that could mislead threshold estimation.  
- **Invalid‑workflow proportion monitoring** ensures that exclusion does not bias the estimated trade‑off curve.  

---


