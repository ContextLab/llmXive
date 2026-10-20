# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Objective
Identify the library‑size “tipping point” where retrieval noise begins to degrade the Digital Colleague agent, and assess whether the Skill‑Pruning heuristic restores performance, while accounting for semantic overlap.

## Methodology

### 1. Synthetic Environment Construction (FR‑001, FR‑002)

| Step | Detail |
|------|--------|
| **Random Seeds** | `random.seed(42)`, `np.random.seed(42)` for full reproducibility. |
| **Skill Generation** | Several Python functions are auto‑generated (simple arithmetic, string manipulation, list processing). Each function receives a short natural‑language description; embeddings are computed with `sentence-transformers/all-MiniLM-L6-v2` (384‑dim). Overlap levels are enforced by iteratively adjusting descriptions until the pairwise cosine‑similarity statistics meet the thresholds (Low < 0.30; Medium > 0.50 with ≥30 % > 0.50; High > 0.80 with ≥30 % > 0.80). |
| **Task Generation** | A sufficiently large number of tasks are created; each task randomly selects 3‑5 distinct skills as its ground‑truth solution path. The `solution_path` is a deterministic ordered list of function calls. |
| **Checksums** | SHA‑256 of `tasks.json` and `skills.json` written to `data/checksums.json` (project‑owned). |

### 2. Agent Execution Loop (FR‑003, FR‑006)

*Configurations*:  
- Library sizes = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100} (active subset of the 100‑skill pool).  
- Overlap levels = {low, medium, high}.  
- Pruning = {enabled, disabled}.  

*Per‑Task Process*:
1. Retrieve top‑k = 5 skills by cosine similarity to the task description.  
2. Compute **Retrieval Precision** as Jaccard similarity between retrieved IDs and the task’s `ground_truth_skills`.  
3. Compute **Retrieval Diversity** as `1 / variance(cosine_similarities_to_ground_truth)` (higher = more diverse).  
4. **Composite Success Definition**: a task is marked **success** if **(Retrieval Precision ≥ 0.8) OR (executed trace exactly matches `solution_path`)**. This captures partial retrieval success while preserving a strict correctness check.  
5. Record latency (wall‑clock ms) and estimate token usage (`len(description.split()) * 2 + sum(len(code.split()) for code in retrieved_skills)`).  
6. Append a row to `metrics.csv` with the exact column order required by the specification.

*Edge‑Case Handling*:
- **Missing Skill**: If a required ground‑truth skill is absent from the active library, log `edge_case="missing_skill"` and `success=False`.  
- **Memory Pressure**: `generate_data.py` monitors RAM; if usage > 6 GB it aborts with a clear `Memory Limit Exceeded` error (SC‑005).  
- **Maximal Overlap** (`mean cosine ≥ 0.95`): Retrieval may return ties; Jaccard will be 0 if none of the top‑5 match ground truth, and `edge_case="max_overlap"` is logged.

### 3. Skill‑Pruning Heuristic (FR‑004)

After every **10** tasks (if pruning enabled):
1. Identify **unused** skills (`usage_count == 0`).  
2. For each unused skill compute its **maximum** cosine similarity to any other skill in the active library.  
3. **Remove** the skill if this maximum similarity **exceeds** `0.70` (i.e., it is highly redundant).  
4. Update the active library size accordingly.

*Rationale*: This corrects the earlier specification‑implementation mismatch – we prune *redundant* unused skills, directly targeting retrieval noise.

### 4. Statistical Analysis (FR‑005, FR‑006, FR‑007, SC‑001 – SC‑006)

| Component | Method | Details |
|-----------|--------|---------|
| **Piecewise Logistic Regression (PLR)** | `statsmodels` GLM with `Binomial` family, segmented via `pwlf`‑style breakpoint optimization | Fit a two‑segment logistic model on **task‑level composite success** vs. `library_size`, `overlap_level`, and orthogonalized `total_redundancy`. The breakpoint `x₀` is the “tipping point”. |
| **Bootstrap CI** | 1,000 resamples of task‑level data | Provides a 95 % confidence interval for `x₀`. |
| **Hold‑out Validation** | Split tasks [deferred] train / [deferred] test; fit PLR on train, evaluate log‑likelihood improvement on test | Guarantees an independent assessment of breakpoint relevance (avoids circular validation). |
| **Permutation Validation** | Shuffle `library_size` labels [deferred] times, refit PLR each time, build a null distribution of breakpoint locations | Confirms the observed breakpoint is not an artifact of the data. |
| **Likelihood‑Ratio Test** | Compare the piecewise logistic model against a single‑segment logistic model (no breakpoint) | Report p‑value for breakpoint significance (addresses trivial breakpoint concern). |
| **Granularity Validation** | Run a dense grid (library sizes 10‑100 in steps of 10) on a random subset of tasks. Verify that the breakpoint from the sparse grid (10,30,50,100) lies within the bootstrap CI of the dense‑grid estimate. |
| **VIF Calculation** | Center `library_size`, `overlap_level`, and `total_redundancy`; orthogonalize via residual regression; compute VIF on the orthogonalized set (`statsmodels.stats.outliers_influence.variance_inflation_factor`). If VIF for any predictor exceeds 5, drop that predictor from the final model. |
| **Pruning Effect Test** | ANCOVA: compare pruning‑enabled vs. baseline success rates while controlling for **post‑pruning total redundancy** (covariate). Report p‑value and Cohen’s d. |
| **Multiple‑Comparison** | Only one family (pruning effect) → no correction needed; if future tests added, Bonferroni will be applied. |
| **Power Check** | Post‑hoc power analysis on the binary success outcome (α = 0.05). If power < 0.80, note limitation in `analysis_report.json`. |

All results are written to `data/results/analysis_report.json` with fields:
- `breakpoint_estimate`
- `breakpoint_ci`
- `vif_library_size`, `vif_total_redundancy`
- `pruning_effect_pvalue`, `pruning_effect_size`
- `permutation_pvalue`
- `likelihood_ratio_pvalue`
- `sensitivity_analysis` (optional supplemental data)

### 5. Compute Feasibility & Data Strategy

- **CPU‑First**: All embeddings computed with the CPU‑only MiniLM model; Memory footprint is on the order of a few hundred MB.  
- **Runtime**: Empirical profiling (on a comparable runner) shows total wall‑clock < 1 hour for the full factorial experiment.  
- **Data**: Synthetic; no external download required, satisfying the “no gated data” rule.

### Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic data** | Guarantees deterministic ground truth; avoids gated datasets. |
| **CPU‑only embeddings (384‑dim)** | Aligns model output with schema, prevents dimension mismatch (T006). |
| **Pruning based on high similarity** | Aligns heuristic with reviewer feedback and the intended purpose of reducing redundancy. |
| **Task‑level PLR (logistic)** | Provides a statistically sound breakpoint estimate for binary outcomes. |
| **Exact CSV header** | Meets the explicit requirement (T005) and simplifies contract validation. |
| **Checksums in project‑owned file** | Avoids writing to platform‑owned `state/` path (T003). |
| **Timeout‑guarded generation** | Uses memory‑monitoring to avoid the earlier timeout (T002). |

### Limitations

- Findings are limited to the synthetic environment; real‑world codebases may introduce additional noise sources.  
- Embedding‑based semantic overlap is a proxy; actual execution semantics could differ.  
- Token usage is estimated, not measured from a live LLM API.  

---


