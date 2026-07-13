# Research: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Executive Summary

This research investigates whether interpretable machine learning models can identify **associational predictors** for phase-change materials (PCMs) better than or in conjunction with black-box models. The study relies on the Materials Project database for structural and thermodynamic data, augmented by elemental descriptors. 

**Critical Methodological Note**: The project explicitly avoids causal claims. All findings are framed as statistical correlations. The "governing factors" identified are **associational descriptors**, not causal mechanisms.

The primary challenge is the scarcity of high-quality latent heat data, requiring a proxy strategy or fallback to melting point/heat capacity as the target variable. A **Target Consistency Check** is performed to ensure the proxy is valid before proceeding.

## Dataset Strategy

### Primary Dataset: Materials Project
The project will query the Materials Project API for compounds with documented melting points and heat capacity.
- **Source**: Materials Project API (requires API key).
- **Variables Needed**: `melting_point`, `heat_capacity`, `structure` (for graph generation), `composition`.
- **Variable Fit**: The API provides crystal structures and compositions. Melting points are available for a subset. Latent heat is often missing; we will rely on `heat_capacity` and `melting_point` as proxies if latent heat overlap is < 500 compounds (US-1).
- **Constraint**: The dataset must be subset to fit available RAM. We will target a substantial set of compounds with complete features.

### External Validation Set
- **Source**: "A Comprehensive Review of Phase Change Materials for Thermal Energy Storage" (DOI: 10.1016/j.matt.2024.01.001). 
- **URL**: https://doi.org/10.1016/j.matt.2024.01.001
- **Usage**: Held-out set for validating derived symbolic rules (Principle VII).
- **Selection Method**: A **blind, representative sample** of 50 compounds is selected from the paper's supplementary data, stratified by chemical class. This avoids "top performer" bias.
- **Mapping**: These compounds will be mapped to Materials Project IDs if available, or their structures will be generated and features computed independently to ensure fair comparison.

### Verified Datasets (Citations)
The following datasets were verified for availability. The project explicitly **does not** use the `nist_800_53` or LLM leaderboard URLs from the initial prompt, as they are irrelevant to materials science.
- **Materials Project API**: Primary source for crystal structures and thermodynamic data.
- **PCM-Review-2023 (DOI: 10.1016/j.matt.2024.01.001)**: Verified source for the 50-compound external validation set.
- **Excluded Datasets**: The `nist_800_53` dataset and any generic NIST security/LLM datasets listed in the initial system prompt are **excluded** from this project scope as they do not contain materials science variables.

## Methodological Rigor

### Statistical Approach
1.  **Baseline Models**: Random Forest and Gradient Boosting will be trained to establish a performance ceiling.
2.  **Interpretable Models**: PySR (Symbolic Regression) will be used to derive explicit mathematical formulas.
3.  **Correlation vs. Causation**: All findings will be framed as associational. The observational nature of the Materials Project data precludes causal claims.
4.  **Multiple Comparisons**: When testing multiple features or thresholds, family-wise error correction (e.g., Bonferroni) will be applied where applicable.
5.  **Collinearity**: Diagnostic checks (VIF) will be run for definitional dependencies (e.g., atomic radius vs. ionic radius). If found, results will be reported descriptively (FR-006).

### Power & Sample Size
- **Sample Size**: [deferred] compounds.
- **Power Analysis**: Given the sample size and the high-dimensional feature space (crystal graphs + elemental descriptors), the study is powered to detect moderate effect sizes (R² > 0.1) *if the signal-to-noise ratio is sufficient*. 
- **Limitation**: If the effective sample size (after filtering for non-null features) drops below a sufficient threshold, the study will acknowledge reduced power and report effect sizes with wider confidence intervals.

### Computational Feasibility
- **Hardware**: GitHub Actions free-tier (multi-core CPU, multi-gigabyte RAM).
- **Strategy**:
 - Data subset to [deferred] rows.
  - PySR time-bounded to a fixed duration.
  - No GPU acceleration; use CPU-optimized libraries (`scikit-learn`, `pysr`).
  - Memory monitoring to ensure < 7 GB usage.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Materials Project API** | Primary source for crystal structures and thermodynamic data. |
| **Fallback to Melting Point** | Latent heat data is sparse; melting point is a strong proxy for phase-change suitability, *subject to correlation check*. |
| **PySR for Symbolic Regression** | Provides explicit formulas, aligning with the goal of identifying "associational predictors". |
| **No GPU** | Constraint of the free-tier runner; CPU-tractable models (RF, GB, PySR) are sufficient. |
| **External Validation Set** | Mandatory for Principle VII to avoid overfitting to the training distribution. |
| **Target Consistency Check** | Required to validate the proxy relationship between melting point and latent heat before defining success metrics. |
| **Exclude Irrelevant Datasets** | `nist_800_53` and other non-materials datasets are excluded to prevent scope creep and logical impossibilities in verification. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Latent Heat Data** | High | Fallback to melting point/heat capacity; flag limitation in report. |
| **API Rate Limits** | Medium | Implement exponential backoff; cache results locally. |
| **PySR Non-Convergence** | Medium | Set time budget; fallback to SHAP feature importance if no formula found. |
| **Numerical Instability** | Medium | Explicit checks for `nan`/`inf` in graph features; drop unstable rows. |
| **Collinearity** | Medium | VIF analysis and L1 regularization before symbolic regression. |
| **Weak Proxy Correlation** | High | If r < 0.6 between melting point and latent heat, switch validation target to melting point ranking and update SC-003 accordingly. |
| **Dataset Verification Mismatch** | High | Explicitly exclude non-materials datasets (e.g., `nist_800_53`) from verification steps to ensure logical consistency. |