# Research: Statistical Analysis of GitHub Issue Resolution Times

## Research Questions

1. What is the distribution shape of GitHub issue resolution times across repositories?
2. Which issue-level and repository-level factors are associated with resolution time differences?
3. How much variance in resolution time is explained by repository-level random effects vs. issue-level covariates?
4. What is the predictive performance of mixed-effects models in leave-one-repository-out cross-validation?

## Dataset Strategy

| Dataset Name | Purpose | Source/Loader | Verified URL | Notes |
|--------------|---------|---------------|--------------|-------|
| GitHub Issues (Primary) | Raw issue metadata for analysis | GitHub REST API (`requests` + `api_client.py`) | NO verified source found (do NOT cite URL) | Per spec assumption: API provides `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, `language` |
| SC-001: Dataset completeness | Validation target | GitHub API response structure | NO verified source found (do NOT cite URL) | Measured against API response structure requirements |
| US-1: Collection pipeline | Data collection | GitHub API | NO verified source found (do NOT cite URL) | ≥1000 issues from ≥100 repos |
| RAM: Memory constraints | Compute feasibility | GitHub Actions runner specs | NO verified source found (do NOT cite URL) | Adequate RAM and disk storage |

**Dataset Fit Verification**: The GitHub API provides all required variables per spec assumptions: `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, and repository `language` field. If empirical verification reveals missing variables (e.g., `assignee` null for many issues), the plan will flag this as a dataset-variable fit mismatch and adjust analysis accordingly.

## Methodological Approach

### Data Collection Strategy

- **API Endpoint**: `GET /repos/{owner}/{repo}/issues?state=closed&since=2020-01-01`
- **Pagination**: Handle `Link` header for paginated results
- **Rate Limiting**: Exponential backoff with ≥60s wait per FR-001
- **Authentication**: GitHub token via `GITHUB_TOKEN` environment variable (optional; unauthenticated limited to a defined rate per hour)
- **Error Handling**: Retry on 5xx errors, log 4xx errors per issue

### Preprocessing Pipeline

1. Parse ISO 8601 timestamps to UTC
2. Compute `resolution_time_hours = (closed_at - created_at) / 3600`
3. Exclude issues where `resolution_time_hours < 0` or timestamps missing (FR-003)
4. Handle zero resolution time (same second): **add constant of +1 hour before log-transform for distribution fitting only; flag separately in results**
5. Log-transform resolution times for distribution fitting (FR-002) using log(x+1)
6. **Exclude repositories with <10 issues from mixed-effects modeling; log separately**

### Distribution Analysis (SC-002)

**Parametric Families**:
- Log-normal: `scipy.stats.lognorm.fit()`
- Weibull: `scipy.stats.weibull_min.fit()`

**Goodness-of-Fit Metrics**:
- Kolmogorov-Smirnov (KS) statistic and p-value
- Akaike Information Criterion (AIC)
- Report for both families regardless of threshold (US-2, SC-002)

**ECDF Plot**:
- X-axis: resolution time (log scale)
- Y-axis: cumulative probability
- Outliers (>30 days): reported count and percentage (US-2)

**Lilliefors Correction Limitation**: KS test p-values are computed with estimated parameters from the same data. This reduces test power (Lilliefors correction needed). KS statistics reported regardless, but p-values interpreted with caution and Lilliefors limitation noted in results.

### Hypothesis Testing (SC-003)

**Tests**:
- ANOVA (parametric) or Kruskal-Wallis (non-parametric) for categorical predictors (e.g., programming language)
- Multiple comparison correction: Holm-Bonferroni for ≥3 tests (FR-004)

**Effect Sizes**:
- Cohen's f (ANOVA) or epsilon-squared (Kruskal-Wallis)
- 95% confidence intervals

**Significance Threshold**:
- Adjusted α=0.05 per Holm-Bonferroni (US-3, SC-003)

### Mixed-Effects Modeling (SC-004)

**Model Specification**:
```
resolution_time ~ label_count + comments_count + assignee_present + star_count + contributor_count + language + (1 | repository)
```

**Fixed Effects**:
- Issue-level: label_count, comments_count, assignee_present
- **Repository-level controls: star_count, contributor_count, language** (addresses confounding bias)

**Random Effects**: Repository-level random intercepts (FR-005)

**Validation**:
- Leave-one-repository-out cross-validation (**multiple folds for multiple repositories, not 20-fold CV**)
- Metrics: MAE and R² with standard deviation across folds
- Expected R² [deferred] ≥0.15 from prior literature (SC-004)

**Endogeneity Limitation**: comments_count accumulates during issue lifetime and is partially determined by the outcome (resolution_time). Effect sizes for comments_count will be reported as descriptive associations only, not independent effects.

### Collinearity Diagnostics (FR-006)

**VIF Calculation**:
- From full model design matrix after fitting
- Flag VIF ≥5
- Pairwise |r| ≥0.7 triggers VIF calculation

**Reporting**:
- Joint relationships reported descriptively
- No independent effects claimed when collinear predictors exist (per spec rigor panel)

### Sensitivity Analysis (FR-007, SC-005)

**Cutoff Sweep**:
- α ∈ {0.01, 0.05, 0.1}
- **Report threshold sensitivity (how significance status changes across cutoffs), not FP/FN rates**
- FP/FN rates cannot be computed without ground truth in observational study (spec-root cause; FR-007 flagged for kickback)

**Power Considerations**:

**Formal Power Analysis Required Before Analysis Proceeds**:
- For mixed-effects models, power depends on:
  - Number of groups (repositories): ≥100
  - Observations per group: ≥10 (minimum for stable random effects)
  - Expected effect size: [deferred] from prior literature
- Power calculation formula: Based on number of groups and within-group variance
- **Blocking requirement**: Power analysis must confirm ≥100 repos × ≥10 issues/repo is sufficient to detect expected effect sizes (R² ≥0.15)
- If power analysis indicates insufficient sample, repository selection criteria will be adjusted

### Associational Language (FR-008)

All result text MUST include "associational" or "correlational" when describing variable relationships. No causal claims permitted due to observational design.

## Decision Rationale

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| Log-normal and Weibull fitting | Prior SE literature suggests right-skewed resolution times | Normal distribution inappropriate for skewed data |
| Holm-Bonferroni (not Bonferroni) | More powerful while still controlling family-wise error | Bonferroni overly conservative for ≥3 tests |
| Mixed-effects (not fixed-effects only) | Repository-level variance must be captured | Fixed-effects would violate independence assumption |
| VIF threshold ≥5 (not ≥10) | Conservative threshold for collinearity flagging | ≥10 may miss meaningful collinearity in smaller samples |
| CPU-only methods | GitHub Actions free-tier has no GPU | GPU methods would fail CI |
| log(x+1) transform | Handles zero resolution times for distribution fitting | Excluding zeros would bias distribution estimates |
| Repository-level controls | Reduces confounding bias in fixed effects | Without controls, fixed effects may be biased |

## Compute Feasibility Assessment

| Component | Expected Resource Usage | Constraint | Status |
|-----------|------------------------|------------|--------|
| Data collection (multiple repos × multiple issues) | A substantial number of API calls, [deferred] | ≤6 hours | ✅ PASS |
| Preprocessing (10000 issues) | ~2GB RAM, [deferred] | ≤7GB RAM | ✅ PASS |
| Distribution fitting | ~1GB RAM, [deferred] | ≤7GB RAM | ✅ PASS |
| Mixed-effects model | ~4GB RAM, [deferred] | ≤7GB RAM, ≤6h | ✅ PASS (with sampling if needed) |
| **LOO-CV (100 folds)** | **[deferred] additional** | **≤6h total** | **⚠️ MAY REQUIRE ISSUE SAMPLING** |
| Total runtime | [deferred] (with buffer) | ≤6 hours | ✅ PASS (tight) |

**Sampling Strategy**: If dataset exceeds memory budget or LOO-CV runtime exceeds 6h, sample to a sufficiently large number of issues to ensure statistical power. (7GB RAM / 1KB per row) while maintaining ≥1000 issues and ≥10 issues per repository for SC-001.

## Limitations

1. **Observational design**: All associations are correlational; no causal claims (FR-008)
2. **API rate limits**: May limit repository sample size in 6-hour window
3. **Missing variables**: If GitHub API lacks required fields (e.g., `assignee` null), analysis adjusted accordingly
4. **Power**: Repositories with <10 issues may lack statistical power for mixed-effects modeling; formal power analysis required before proceeding
5. **Generalizability**: Results apply to GitHub-hosted projects; may not generalize to other platforms
6. **Endogeneity**: comments_count is partially determined by resolution_time; effect sizes reported as descriptive associations only
7. **Lilliefors correction**: KS test p-values computed with estimated parameters; interpreted with caution
8. **Zero resolution times**: Handled via log(x+1) transform; may affect distribution fit for very short-resolution issues

## Reproducibility Checklist

- [ ] Random seeds pinned in `code/utils/config.py`
- [ ] `requirements.txt` at `code/` with pinned versions
- [ ] GitHub API token via environment variable (not committed)
- [ ] Raw data checksummed and recorded in `state/*.yaml`
- [ ] All scripts runnable end-to-end without manual intervention
- [ ] Contract schemas validate outputs in `code/tests/contract/`
- [ ] Power analysis completed before mixed-effects modeling