# Research: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

## Objective
Identify the library‑size “tipping point” where retrieval noise degrades the Digital Colleague agent, and evaluate whether the **Skill‑Pruning** heuristic restores performance, while controlling for semantic overlap.

## Methodology

### 1. Synthetic Environment Construction (FR‑001, FR‑002)

| Step | Detail |
|------|--------|
| **Random Seeds** | `random.seed(42)`, `np.random.seed(42)` for full reproducibility. |
| **Skill Generation** | Auto‑generate multiple Python functions (simple arithmetic, string ops, list manipulation). Each receives a short NL description; embeddings computed with `sentence‑transformers/all-MiniLM-L6-v2` (384‑dim). Overlap levels enforced by iteratively adjusting descriptions until pairwise cosine‑similarity statistics meet the thresholds (Low < 0.30; Medium > 0.50 with ≥30 % > 0.50; High > 0.80 with ≥30 % > 0.80). |
| **Task Generation** | Create 500 tasks; each task randomly selects 3‑5 distinct skills as its **ground_truth_skills** and stores an ordered **solution_path** of function calls. |
| **Checksums** | SHA‑256 of `tasks.json` and `skills.json` written to `data/checksums.json`. |

### 2. Agent Execution Loop (FR‑003, FR‑006)

**Configurations**  
- Library sizes = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100}.  
- Overlap levels = {low, medium, high}.  
- Pruning = {enabled, disabled}.  

**Per‑Task Process** (executed **independently** for each configuration)  
1. **Randomize task order** and draw a fresh **without‑replacement** sample of the 500 tasks for the current configuration (ensuring independence across runs).  
2. Retrieve top‑k = 5 skills by cosine similarity to the task description.  
3. **Retrieval Precision** = Jaccard(`retrieved_ids`, `ground_truth_skills`).  
4. **Retrieval Diversity** = `1 / variance(cosine_similarities_to_ground_truth)`.  
5. **Exact‑Match Success**: `True` if the executed trace **exactly** matches `solution_path`; otherwise `False`. *(This is the binary outcome used for breakpoint analysis.)*  
6. Record latency (wall‑clock ms) and estimated token usage (`len(description.split())*2 + Σ len(code.split())`).  
7. Append a row to `metrics.csv` with the exact header required by the spec.  

**Edge‑Case Handling**  
- **Missing Skill** → `edge_case="missing_skill"`; `success=False`.  
- **Memory Pressure** → `generate_data.py` aborts with “Memory Limit Exceeded” (SC‑005).  
- **Maximal Overlap** (`mean cosine ≥ 0.95`) → ties may occur; Jaccard will be 0 if none of the top‑5 match ground truth; `edge_case="max_overlap"` logged.  

### 3. Skill‑Pruning Heuristic (FR‑004)

After **every 10 tasks** (if pruning enabled):
1. Identify **unused** skills (`usage_count == 0`).  
2. For each unused skill compute its **maximum** cosine similarity to any other skill in the *active* library.  
3. **Remove** the skill **if** this maximum similarity **exceeds** `0.70` (i.e., the skill is highly redundant).  
4. Update `usage_count` and `last_used` metadata accordingly.  

*Rationale*: This corrects the earlier mis‑specification (prune *highly similar* redundant skills rather than dissimilar unique ones).

### 4. A‑Prior Power Analysis (SC‑005)

Before data collection we performed an a‑priori power analysis for a binary outcome using `statsmodels.stats.proportion.proportion_effectsize` with an assumed medium effect size (Cohen’s h = 0.5) and α = 0.05. Power calculations show that **500 tasks** across the 10 × 3 × 2 factorial design yields > 0.80 power to detect the expected breakpoint and pruning effects. This justification is recorded in `analysis_report.json` under `power_analysis`.

### 5. Statistical Analysis (FR‑005, FR‑006, FR‑007, SC‑001 – SC‑006)

| Component | Method | Details |
|-----------|--------|---------|
| **Pre‑Orthogonalization** | Center `library_size` and `total_redundancy`, then apply QR‑decomposition to obtain orthogonal predictors before model fitting. |
| **Piecewise Logistic Regression (PLR)** | `statsmodels` GLM (Binomial) + breakpoint optimization via `pwlf` | Fit a two‑segment logistic model on **binary exact‑match success** vs. orthogonalized `library_size` and `overlap_level`. Breakpoint `x₀` is the “tipping point”. |
| **Bootstrap CI** | 1 000 resamples of task‑level data | 95 % CI for `x₀`. |
| **Hold‑out Validation** | Random train/test split ([deferred] hold‑out) | Fit PLR on train, evaluate log‑likelihood on test to avoid circularity. |
| **Permutation Test** | Shuffle `library_size` labels 1 000 times, refit PLR each time | Null distribution of breakpoint locations; report permutation p‑value. |
| **Likelihood‑Ratio Test** | Compare PLR vs. single‑segment logistic model | Report p‑value for breakpoint significance. |
| **VIF Calculation** | Compute VIF on the orthogonalized predictors (`statsmodels.stats.outliers_influence.variance_inflation_factor`). Must be < 5.0; if not, redesign predictors (preventive design). |
| **Pruning Effect Evaluation** | **Direct comparison** of success rates between pruning‑enabled and baseline (no covariate adjustment). Additionally, a **mediation analysis** quantifies the indirect effect of pruning via the change in total redundancy (using `statsmodels` mediation utilities). Report p‑values and effect sizes (Cohen’s d for direct effect). |
| **Multiple‑Comparison** | Only one family of tests (breakpoint, pruning direct, mediation); no correction needed. Future extensions would use Bonferroni. |
| **Power Check** | Post‑hoc power analysis on binary outcome (α = 0.05) | If power < 0.80, note limitation in `analysis_report.json`. |
| **Runtime Profiling** | Total wall‑clock time recorded in `data/results/runtime_report.json` (Phase 5 of plan). | Ensures SC‑005 compliance. |

All results are written to `data/results/analysis_report.json` with fields:

- `breakpoint_estimate`, `breakpoint_ci`
- `vif_library_size`, `vif_total_redundancy`
- `pruning_direct_pvalue`, `pruning_direct_effect_size`
- `pruning_mediation_pvalue`, `pruning_mediation_effect_size`
- `permutation_pvalue`, `likelihood_ratio_pvalue`
- `power_analysis` (sample size, effect size, achieved power)
- `runtime_seconds`

### 6. Compute Feasibility & Data Strategy

- **CPU‑First**: All embeddings computed with the CPU‑only MiniLM model; peak RAM < 2 GB; total wall‑clock < 1 h on a comparable runner.  
- **No External Data**: Synthetic generation avoids gated datasets; everything is programmatically downloadable.  
- **Scalability**: If memory pressure is detected, `generate_data.py` aborts cleanly (SC‑005) rather than crashing.

### 7. Decision Rationale

| Decision | Reason |
|----------|--------|
| **Synthetic data** | Guarantees deterministic ground truth; sidesteps gated data restrictions. |
| **CPU‑only MiniLM** | Fits within free‑tier compute budget; no GPU escape needed. |
| **Pruning based on high similarity** | Aligns with reviewer feedback that the heuristic must remove *redundant* skills. |
| **Piecewise logistic regression** | Provides a statistically principled breakpoint for a binary outcome. |
| **Exact‑match success only** | Removes arbitrary retrieval‑precision threshold, ensuring the breakpoint reflects true execution fidelity. |
| **Direct + mediation pruning analysis** | Avoids adjusting for a mediator while still quantifying indirect effects. |
| **Pre‑orthogonalization** | Guarantees VIF < 5 by design, eliminating reactive predictor removal. |
| **Runtime logging** | Satisfies SC‑005 by explicitly recording total compute time. |
| **Full overlap coverage** | Tests low, medium, and high semantic overlap as originally claimed. |
| **Contract validation** | Guarantees all logs conform to their schemas, addressing T001 and execution‑log consistency. |
| **Checksum‑driven contract copy** | Provides verifiable evidence (T001) that contract files are verbatim copies of the spec version. |
| **Project‑owned output paths** | Avoids writing to platform‑owned `state/` (fixes T003). |
| **CLI alignment** | Ensures the agent CLI matches the documented arguments, fixing T006. |
| **Pruning function naming** | Implements `prune_redundant(library)` as required (fixes T007). |
| **Robust error handling** | Agent exits with clear messages and logs failures, fixing T008. |

---

