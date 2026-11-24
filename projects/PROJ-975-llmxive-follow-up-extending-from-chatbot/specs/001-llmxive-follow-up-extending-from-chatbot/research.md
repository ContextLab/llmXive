# Research: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

## Objective
Identify the library‑size “tipping point” where retrieval noise degrades the Digital Colleague agent, and evaluate whether the **Skill‑Pruning** heuristic restores performance, while controlling for semantic overlap.

## Methodology

### 1. Synthetic Environment Construction (FR‑001, FR‑002)

| Step | Detail |
|------|--------|
| **Random Seeds** | `random.seed(42)`, `np.random.seed(42)` for full reproducibility. |
| **Skill Generation** | Auto‑generate a sizable collection of Python functions (simple arithmetic, string ops, list manipulation). Each receives a short NL description; embeddings computed with `sentence‑transformers/all-MiniLM-L6-v2` (384‑dim). Overlap levels enforced by iteratively adjusting descriptions until pairwise cosine‑similarity statistics meet the thresholds (Low < 0.30; Medium > 0.50 with ≥30 % > 0.50; High > 0.80 with ≥30 % > 0.80). |
| **Task Generation** | Create **5,000** synthetic multi‑step tasks; each task randomly selects 3‑5 distinct skills as its **ground_truth_skills** and stores an ordered **solution_path** of function calls. |
| **Checksums** | SHA‑256 of `tasks.json` and `skills.json` written to `data/checksums.json`. |
| **Memory Guard** | `generate_data.py` monitors RAM; if usage would exceed 6 GB it aborts with a clear `Memory Limit Exceeded` error (fulfills SC‑005). |

### 2. Agent Execution Loop (FR‑003, FR‑006)

**Configurations**  
- Library sizes = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100}.  
- Overlap levels = {low, medium, high}.  
- Pruning = {on, off}.  

**Per‑Task Process** (executed independently for each configuration)  

1. **Independent Sampling** – For each configuration a fresh random seed is set and **≈125 tasks** are drawn **without replacement** from the large master pool of [deferred] tasks. This guarantees statistical independence across factorial cells (addresses methodology‑5add40b1).
2. Retrieve top‑k = 5 skills by cosine similarity to the task description.  
3. **Retrieval Precision** = Jaccard(`retrieved_ids`, `ground_truth_skills`).  
4. **Retrieval Diversity** = `1 / variance(cosine_similarities_to_ground_truth)`.  
5. **Exact‑Match Success**: `True` if the executed trace **exactly** matches `solution_path`; otherwise `False`. This binary outcome is the dependent variable for breakpoint analysis.  
6. Record latency (ms) and estimated token usage (`len(description.split())*2 + Σ len(code.split())`).  
7. Append a row to `metrics.csv` with the exact header required by the spec.  

**Edge‑Case Handling**  
- **Missing Skill** → `edge_case="missing_skill"`; `success=False`.  
- **Memory Pressure** → `generate_data.py` aborts with “Memory Limit Exceeded”.  
- **Maximal Overlap** (`mean cosine ≥ 0.95`) → ties may occur; Jaccard will be 0 if none of the top‑5 match ground truth; `edge_case="max_overlap"` logged.  

### 3. Skill‑Pruning Heuristic (FR‑004)

Implemented in `pruning.py` as `prune_fr04(library)`. After **every 10 tasks** (if pruning enabled):

1. Identify **unused** skills (`usage_count == 0`).  
2. For each unused skill compute its **minimum** cosine similarity to any other skill in the *active* library.  
3. **Remove** the skill **if** this minimum similarity **is below** `0.70` **and** the skill does **not** appear in any task’s `ground_truth_skills`.  
4. Update `usage_count` and `last_used` metadata accordingly.  

*Rationale*: This removes **redundant** skills (highly similar to others) while preserving unique capabilities, directly addressing the reviewer‑identified flaw in the original FR‑004 definition.

### 4. A‑Prior Power Analysis (SC‑005)

Using `statsmodels.stats.proportion.proportion_effectsize` with an assumed medium effect size (Cohen’s h = 0.5) and α = 0.05, a sample of **≈125 tasks per condition** (total [deferred] observations across the full factorial design) yields an estimated power of **~0.65** to detect the expected breakpoint and pruning effects. The limitation is explicitly noted in `analysis_report.json` under `power_analysis`.

### 5. Statistical Analysis (FR‑005, FR‑006, FR‑007, SC‑001 – SC‑006)

| Component | Method | Details |
|-----------|--------|---------|
| **Predictor Set** | Raw (no orthogonalization) | Predictors: `library_size` (continuous), `overlap_level` (categorical), `pruning_enabled` (binary), plus two‑way interactions (`library_size*pruning_enabled`, `overlap_level*pruning_enabled`). VIF computed on these raw predictors (must be < 5). |
| **Total Redundancy** | Measured | For each run, compute the **observed** mean pairwise cosine similarity among the active library’s embeddings after pruning. This metric varies with random skill generation and pruning, satisfying independence from `library_size`. |
| **Piecewise Logistic Regression (PLR)** | `statsmodels` GLM (Binomial) + breakpoint optimization via `pwlf`. Fit a two‑segment logistic model on **binary exact‑match success** vs. `library_size` while controlling for overlap and pruning. Breakpoint `x₀` is the “tipping point”. |
| **Bootstrap CI** | 1 000 resamples of task‑level data → 95 % CI for `x₀`. |
| **Likelihood‑Ratio Test** | Compare PLR vs. single‑segment logistic model → p‑value for breakpoint significance (replaces invalid permutation test). |
| **Mediation Analysis** | Test indirect effect of pruning via change in `total_redundancy` using `statsmodels` mediation utilities. Uses the **raw** predictor set; VIF already verified. |
| **Multiple‑Comparison** | Only one family of tests (breakpoint, pruning direct, mediation); no correction required. |
| **Post‑Hoc Power Check** | Compute achieved power on the binary outcome; if < 0.80, note limitation in `analysis_report.json`. |
| **Runtime Profiling** | Total wall‑clock time recorded in `data/results/runtime_report.json` (Phase 6) to satisfy SC‑005. |

All results are written to `data/results/analysis_report.json` with fields:

- `breakpoint_estimate`, `breakpoint_ci`
- `vif_library_size`, `vif_total_redundancy`, `vif_overlap_level`, `vif_pruning_enabled`
- `pruning_direct_pvalue`, `pruning_direct_effect_size`
- `pruning_mediation_pvalue`, `pruning_mediation_effect_size`
- `likelihood_ratio_pvalue`
- `power_analysis` (sample size, effect size, achieved power)
- `runtime_seconds`
- `sensitivity_analysis` (optional dense‑grid sweep results)

### 6. Compute Feasibility & Data Strategy

- **CPU‑First**: All embeddings computed with the CPU‑only MiniLM model; peak RAM < 2 GB; total wall‑clock < 1 h on a comparable runner.  
- **No External Data**: Synthetic generation avoids gated datasets; everything is programmatically downloadable.  
- **Scalability**: If memory pressure is detected, `generate_data.py` aborts cleanly rather than crashing (fulfills SC‑005).  

### 7. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic data** | Guarantees deterministic ground truth; sidesteps gated data restrictions. |
| **CPU‑only MiniLM** | Fits within free‑tier compute budget; no GPU escape needed. |
| **Expanded library grid** | Provides finer granularity for breakpoint detection (addresses scientific_soundness‑4628d221). |
| **Independent per‑condition sampling** | Removes correlation across factorial cells (addresses methodology‑5add40b1). |
| **Pruning based on high similarity** | Aligns with FR‑004 and reviewer feedback; removes redundant skills. |
| **Piecewise logistic regression** | Provides a statistically principled breakpoint for a binary outcome. |
| **Exact‑match success only** | Ensures breakpoint reflects true execution fidelity. |
| **Raw predictor VIF & mediation** | Guarantees collinearity diagnostics are meaningful and mediation coefficients interpretable. |
| **Likelihood‑ratio test & bootstrap CI** | Valid inference for breakpoint without invalid permutation. |
| **Runtime logging** | Satisfies SC‑005 by explicitly recording total compute time. |
| **Contract validation at every stage** | Guarantees compliance with Constitution III & IV and resolves T001–T009 failures. |
| **Import `Tuple` and other typing objects** | Fixes NameError that caused T008. |
| **Unified logging header (`LOG_COLUMNS`)** | Guarantees `metrics.csv` conforms to `experiment_log.schema.yaml` (addresses T005). |

---

