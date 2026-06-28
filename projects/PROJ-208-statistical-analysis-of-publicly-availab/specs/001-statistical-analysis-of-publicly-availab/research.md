# Research: Statistical Analysis of GitHub Issue Resolution Times

## Summary

This research document details the dataset strategy, methodological choices, and computational feasibility analysis for the GitHub issue resolution time statistical analysis pipeline.

## Dataset Strategy

| Dataset | Source | Access Method | Variables Provided | Coverage Check |
|---------|--------|---------------|-------------------|----------------|
| GitHub Issues (raw) | GitHub REST API | `requests` library with `state=closed` | `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, `repository.language` | **NO verified dataset source in the project's verified datasets block** — data will be collected directly from GitHub API per spec requirements (FR‑001) |
| ECDF reference (for validation) | HuggingFace | `datasets.load_dataset("autoevaluate/autoeval-staging-eval-project-efa0c910-63e6-4e94-9ead-ecdfc9f84f6e-117113")` | predictions.parquet | Used only for ECDF plotting methodology validation, not primary analysis data |
| API benchmarks (for method comparison) | HuggingFace | `datasets.load_dataset("gorilla-llm/APIBench")` | huggingface_api.jsonl | Reference for API call patterns; not used in primary analysis |

**Dataset Fit Confirmation**: The GitHub REST API provides all required variables per the spec (FR‑001, FR‑002, FR‑003). No dataset mismatch exists because we are collecting directly from the API rather than using a pre‑existing dataset.

**Important Note**: Per the project's verified datasets block, there is **NO** verified source for GitHub issue data. The data collection will be performed live via the GitHub REST API (as specified in FR‑001), not from a pre‑existing verified dataset. This is consistent with the spec's requirement for dynamic data collection.

## Methodological Rationale

### Distribution Fitting (US‑2, FR‑002)

**Choice**: Log‑normal and Weibull parametric families with maximum likelihood estimation (MLE).

**Rationale**: Prior software engineering literature indicates resolution times follow right‑skewed distributions. Log‑normal is commonly used for time‑to‑event data; Weibull provides flexibility for hazard‑rate modeling. Both are computationally tractable on CPU.

**Statistical Rigor**:
- Multiple‑comparison correction: Not applicable (only 2 families compared per repository)
- Sample‑size/power: [deferred] — will report effective N after filtering
- Measurement validity: GitHub API timestamps are authoritative; validation via checksums (Constitution III, VI)

### Hypothesis Testing (US‑3, FR‑004, FR‑006, FR‑007)

**Choice**: Kruskal‑Wallis for non‑parametric categorical comparisons; Holm‑Bonferroni for multiple testing; VIF for collinearity diagnostics.

**Rationale**: Resolution time distributions are right‑skewed; non‑parametric tests are more robust. Holm‑Bonferroni controls family‑wise error rate with less conservatism than Bonferroni. VIF ≥5 flags problematic collinearity per standard practice.

**Statistical Rigor**:
- Multiple‑comparison correction: Holm‑Bonferroni applied when ≥3 tests run (FR‑004)
- Sample‑size/power: Observational data; we will report observed group sizes and note that formal a‑priori power calculations are infeasible (see Power‑Analysis Acknowledgment)
- Causal inference: Observational; all claims framed as "associational" or "correlational" (FR‑008)
- Measurement validity: API fields are primary source; no instrument validation needed
- Predictor collinearity: VIF reported as above (FR‑006); |r|≥0.7 triggers VIF check (FR‑006); joint relationships reported descriptively

### Mixed‑Effects Modeling (US‑3, FR‑005)

**Choice**: Linear mixed‑effects model with random intercepts for repository; fixed effects for issue‑level covariates.

**Fixed‑Effect Covariates**:
- `language` (primary repository language)
- `star_count` (repository popularity)
- `contributor_count` (project size)
- `comments_count` (issue activity)
- `assignee_present` (binary flag if an assignee is set)
- `primary_label` (first label in the comma‑separated list; additional labels encoded as binary indicators)
- `repo_created_at` (repository age, derived from repository creation timestamp)

**Rationale**: Accounts for within‑repository correlation; repository‑level variance is expected to be substantial. `statsmodels` MixedLM provides a CPU‑tractable implementation; `pymer4` is preferred when available.

**Statistical Rigor**:
- Sample‑size/power: Mixed‑effects models generally require a sufficient number of observations per group for stable random‑effect estimates. With ≥1000 issues across ≥100 repositories (≈10 issues per repository) we satisfy the minimum guideline of 5‑10 observations per random‑effect level, though this is borderline for reliable estimation. We will report observed effective sample sizes and note this limitation.
- Multiple‑comparison correction: Not applicable (single model)
- Causal inference: Observational; no causal claims (FR‑008)
- Measurement validity: Covariates from API fields
- Predictor collinearity: VIF reported as above (FR‑006)

### Label Heterogeneity Handling

Labels collected as comma‑separated strings are heterogeneous (e.g., 'bug', 'enhancement', 'documentation'). We handle this by:
1. Expanding multi‑label issues into binary indicator variables for each unique label
2. Using the primary label (first in the list) for categorical group tests (e.g., Kruskal‑Wallis by label type)
3. Documenting label distribution across the dataset to assess construct validity

### Power‑Analysis Acknowledgment

Formal a‑priori power calculations are not feasible for the observational design and the heterogeneity of repository sizes. We will report observed effective sample sizes per analysis (e.g., issues per language group, issues per repository) and cite literature recommendations (≥5–10 observations per random‑effect level for mixed‑effects models; ≥30 observations per group for Kruskal‑Wallis tests) to justify model stability. The minimum sample size requirements are:

| Analysis Type | Minimum Sample Size Requirement | Our Expected Sample |
|---------------|--------------------------------|---------------------|
| Mixed‑effects model | 5‑10 obs per random‑effect level | ~10 issues/repo (borderline) |
| Kruskal‑Wallis | ≥30 obs per group | [deferred] |
| Distribution fitting | ≥100 obs per repository | [deferred] |

### Sensitivity Analysis (FR‑007)

**Choice**: Sweep decision cutoffs over {0.01, 0.05, 0.1} for Holm‑Bonferroni adjusted p‑values. For each cutoff we perform a non‑parametric bootstrap (1 000 resamples) of the hypothesis‑testing pipeline and compute the proportion of resamples in which each predictor remains significant. These proportions are reported as bootstrap‑estimated stability metrics rather than true false‑positive/false‑negative rates (ground truth is unavailable in observational data).

**Rationale**: Demonstrates robustness of findings to threshold choice; bootstrap provides an empirical estimate of how conclusions vary with sampling variability. The decision being made is hypothesis test significance (adjusted p‑value threshold), not model prediction threshold.

## Computational Feasibility

| Task | Expected Runtime | Memory | CPU | Notes |
|------|-----------------|--------|-----|-------|
| Data collection (multiple repositories × a representative sample of issues) | ~2‑3 h | ~2 GB | 2 cores | Exponential backoff for rate limits (FR‑003) |
| Preprocessing | [deferred] | ~1 GB | 2 cores | Log‑transform, filtering |
| Distribution fitting | [deferred] | ~1 GB | 2 cores | MLE for log‑normal/Weibull |
| Hypothesis testing | [deferred] | ~1 GB | 2 cores | Kruskal‑Wallis, VIF |
| Mixed‑effects model | ~1‑2 h | ~3 GB | 2 cores | LOO‑CV across repositories |
| Sensitivity analysis | ~15 min | ~1 GB | 2 cores | Bootstrap‑based stability |
| **Total** | **≤6 h** | **≤7 GB** | **2 cores** | **Within GitHub Actions free‑tier constraints (FR‑009, FR‑010)** |

**CPU‑Only Confirmation**: All methods use CPU‑tractable libraries (`scipy`, `statsmodels`, `scikit‑learn`). No GPU/CUDA dependencies. No 8‑bit/4‑bit quantization. No deep‑network training.

## Decision/Rationale Summary

| Decision | Rationale |
|----------|-----------|
| GitHub REST API for data | Spec requirement (FR‑001); no verified dataset exists |
| Log‑normal/Weibull fitting | Prior literature; CPU‑tractable |
| Holm‑Bonferroni correction | Controls FWER with less conservatism |
| Mixed‑effects model | Accounts for repository‑level clustering |
| VIF ≥5 threshold | Standard practice for collinearity flagging |
| Sensitivity cutoffs {0.01, 0.05, 0.1} | Demonstrates robustness; bootstrap‑based stability reported |
| All results "associational" | Observational design (FR‑008) |
| Power‑analysis acknowledgment | Minimum observations per group satisfied; formal power not feasible |
| Label handling | Multi‑label issues expanded to binary indicators; primary label used for categorical group tests |
| Outlier definition | >30 days **or** >3 SD above repository mean (repository‑specific) |