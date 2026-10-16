# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Objective

Identify the library‑size “tipping point” where retrieval noise degrades the Digital Colleague agent, and evaluate whether the Skill‑Pruning heuristic restores performance.

## Methodology

### 1. Synthetic Environment Construction (FR‑001, FR‑002)

* **Generation** – `generate_data.py` creates 500 tasks (3‑5 steps each) and 100 Python skill functions.  
* **Embedding Model** – `sentence-transformers/all-MiniLM-L6-v2` (CPU‑only).  
* **Overlap Levels** –  
  * **Low**: mean pairwise cosine < 0.30.  
  * **Medium**: mean > 0.50, ≥ 30 % of pairs > 0.50.  
  * **High**: mean > 0.80, ≥ 30 % of pairs > 0.80.  
* **Reproducibility** – Fixed seeds (`random.seed(42)`, `np.random.seed(42)`). Checksums stored in state YAML.

### 2. Agent Execution Loop (FR‑003)

* **Configurations** – Library sizes 10, 30, 50, 100; Pruning = {enabled, disabled}; Overlap = {low, medium, high}.  
* **Task Processing** – For each task: retrieve top‑k = 5 skills (cosine similarity), compare retrieved set to ground‑truth, record success flag, latency, estimated token usage, Retrieval Precision (Jaccard), Retrieval Diversity (inverse variance of cosine similarities).  
* **Pruning** – After every 10 tasks (if enabled), `pruning.py` removes any skill with `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill < 0.70`.  

### 3. Statistical Analysis (FR‑005, FR‑006, FR‑007)

| Analysis Component | Method | Rationale |
|--------------------|--------|-----------|
| **Piecewise Linear Regression (PLR)** | `pwlf` (or `scipy.optimize.curve_fit` implementing a two‑segment linear model) | Detects a single breakpoint `x₀` where the slope of Success Rate vs. Library Size changes. |
| **Variance Inflation Factor (VIF)** | `statsmodels.stats.outliers_influence.variance_inflation_factor` | Checks collinearity between “Library Size” and “Total Redundancy” (mean pairwise cosine). Must satisfy VIF < 5.0 (FR‑007). |
| **Pruning Effect Test** | Paired t‑test (or Wilcoxon if normality fails) comparing success rates with vs. without pruning at library sizes 50 and 100. | Quantifies performance recovery (SC‑003). |
| **Sensitivity Sweeps** | Additional runs varying pruning threshold (e.g., 0.60, 0.70, 0.80) and library‑size granularity. Results are saved as `sensitivity_analysis.json` for exploratory purposes only. | Provides robustness checks but **does not** affect the primary “tipping point” metric. |

#### Selecting the Final Tipping Point (SC‑004)

* The **primary** tipping point is the breakpoint `x₀` obtained from the PLR fitted on the **baseline configuration**: **High overlap**, **pruning disabled**, using the four library sizes (10, 30, 50, 100).  
* Sensitivity sweeps generate alternative `x₀` estimates; they are reported in a supplemental appendix but are **not** used to satisfy SC‑004. This rule eliminates ambiguity identified in the unresolved T035 concern.

### 4. Multiple‑Comparison & Power

* **Multiple Comparisons** – The only family of hypothesis tests is the pruning‑effect comparison (two levels). No correction is needed; if additional tests are added in future sweeps, a Bonferroni correction will be applied.  
* **Power** – With 500 tasks per configuration, a post‑hoc power analysis will be reported; if power falls below 0.80, the limitation will be noted (SC‑005).  

## Compute Feasibility & Data Strategy

* **CPU‑First** – All embeddings and similarity calculations are performed with the CPU‑only `sentence-transformers` model; memory usage ≈ 200 MB.  
* **Runtime Estimate** – Empirical profiling predicts ~30 seconds per library‑size/overlap/pruning combo; total < 1 hour on the free‑tier runner.  
* **Data Availability** – Synthetic; no external download required.  

## Decision Rationale

| Decision | Reason |
|----------|--------|
| Synthetic data | Guarantees deterministic ground truth; real codebases lack this guarantee. |
| CPU‑only execution | Dataset is tiny; GPU would add unnecessary complexity. |
| PLR for tipping point | Provides an explicit breakpoint estimate, directly matching SC‑004. |
| Jaccard for Retrieval Precision | Standard set‑overlap metric for discrete skill retrieval. |
| Fixed “primary” PLR configuration | Removes ambiguity from multiple sensitivity results (addresses T035). |

## Limitations

* **External Validity** – Findings apply to the synthetic environment; real‑world codebases may exhibit additional sources of noise.  
* **Skill Representation** – Embeddings are derived from natural‑language descriptions of code, not from execution traces.  
* **Token Estimate** – Tokens are approximated from function length; actual LLM API usage may differ.

---
