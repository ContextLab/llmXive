# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

## Dataset Strategy

| Dataset | Purpose | Verified URL | Notes |
|---------|---------|--------------|-------|
| Public A/B Test Summaries (corpus) | Primary audit input | NO verified source found (do NOT cite a URL for it) | Users provide `input/urls.csv` with URLs to public summaries; no centralized dataset exists. |
| Synthetic Validation Dataset (FR-030) | Performance evaluation (precision, recall, F1) | NO verified source found (do NOT cite a URL for it) | Generated programmatically using `synthetic_data_generator.py` with known ground-truth p-values and effect sizes. |
| Manual Validation Set (SC-001) | Extraction accuracy benchmark (≥100 summaries) | NO verified source found (do NOT cite a URL for it) | Curated manually by researchers; stratified across five major domains. |
| John et al., 2022 (baseline proportion) | Binomial test baseline justification | NO verified source found (do NOT cite a URL for it) | Cited for baseline proportion of 0.05; validation by Reference-Validator Agent required. |
| Kohavi et al., 2020 (synthetic dataset size) | Synthetic dataset size justification (10k+) | NO verified source found (do NOT cite a URL for it) | Cited for synthetic dataset size recommendation; validation by Reference-Validator Agent required. |
| MUST (parquet) | External dataset for tool-calling evaluation | https://huggingface.co/datasets/Mustafaege/qwen3.5-toolcalling-v2/resolve/main/data/test-00000-of-00001.parquet | Not used in this project (FR-030/FR-031/SC-030 have NO verified source). |
| MUSTC (parquet) | External dataset for text-only evaluation | https://huggingface.co/datasets/kudo-research/mustc-en-es-text-only/resolve/main/data/dev-00000-of-00001.parquet | Not used in this project (FR-030/FR-031/SC-030 have NO verified source). |

**Note**: FR-030, FR-031, and SC-030 have NO verified source found. This project generates synthetic validation data programmatically rather than relying on external datasets.

## Statistical Methodology

### Two-Proportion Z-Test (Binary Outcomes)

For binary conversion metrics, reconstruct p-value using:

```
z = (p_a - p_b) / sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
p_pool = (x_a + x_b) / (n_a + n_b)
```

where `p_a = x_a / n_a`, `p_b = x_b / n_b`, `x_a` and `x_b` are conversion counts, `n_a` and `n_b` are sample sizes.

**Implementation**: `scipy.stats.proportions_ztest` (two-sided, alpha=0.05).

**Fisher's Exact Test Fallback**: When any cell count ≤5, use `scipy.stats.fisher_exact` (two-sided).

### Welch's Two-Sample T-Test (Continuous Outcomes)

For continuous metrics (e.g., revenue lift), reconstruct p-value using:

```
t = (mean_a - mean_b) / sqrt(s_a^2/n_a + s_b^2/n_b)
df = (s_a^2/n_a + s_b^2/n_b)^2 / ((s_a^2/n_a)^2/(n_a-1) + (s_b^2/n_b)^2/(n_b-1))
```

**Implementation**: `scipy.stats.ttest_ind` with `equal_var=False`.

### Binomial Prevalence Test (FR-005a)

Test overall inconsistency proportion against baseline (0.05) using two-sided binomial test:

```
H0: p = 0.05 (baseline inconsistency rate)
H1: p ≠ 0.05
```

Report p-value (3 decimals), Wilson 95% CI (width ≤0.10), raw inconsistency rate.

**Implementation**: `scipy.stats.binomtest` with `alternative='two-sided'`.

**Wilson CI**: `statsmodels.stats.proportion.proportion_confint(method='wilson')`.

### Sensitivity Analysis (FR-005b)

Repeat binomial test for baseline proportions 0.02–0.10 (step 0.01). Report maximum variation in estimated prevalence (must be <0.02 per SC-015).

### Monte Carlo Validation (FR-026, SC-003, SC-026)

Validate each statistical test (z-test, Welch's t-test, binomial test) with 10,000 replicates:

1. Generate synthetic data with known ground-truth parameters.
2. Compute test statistic using `scipy` implementation.
3. Compute Monte Carlo estimate (proportion of replicates exceeding observed statistic).
4. Verify absolute difference ≤0.01.

**Rationale**: Independent verification of statistical-test correctness; prevents implementation bugs from corrupting audit results.

### Bias Assessment (FR-027, SC-027)

1. Compute proportion of summaries per domain.
2. Flag violation if any domain >30% (must subsample or report violation).
3. Compute bias-adjusted inconsistency rate using domain-weighted averaging.
4. Include both raw and bias-adjusted rates in output.

### Subgroup Analysis (FR-032, SC-032)

For each subgroup (domain or publication year) with ≥10 summaries:

1. Compute subgroup inconsistency prevalence.
2. Perform Fisher's exact test comparing inconsistent vs. consistent counts.
3. Report subgroup p-value and indicate whether prevalence differs from overall rate (α=0.05).

## Power Analysis (FR-025, SC-025)

**Goal**: Ensure N≥300 (or calculated minimum) to achieve power≥0.80 at α=0.05 for detecting inconsistency proportion of 0.10 (double baseline 0.05).

**Calculation**:
- Baseline proportion (p0): 0.05
- Alternative proportion (p1): 0.10
- α: 0.05
- Power (1-β): 0.80
- Test: Two-sided binomial test

Using `statsmodels.stats.power.zt_ind_solve_power` or G*Power, minimum N ≈ 293 (rounded to 300 for margin).

**Justification**: Power analysis is essential to avoid inconclusive prevalence estimates. A corpus with N<300 may fail to detect a true inconsistency proportion of 0.10 with adequate power.

## Monte Carlo Simulation Design (FR-030, FR-031)

**Synthetic Dataset Size**: 10,000+ simulated A/B test summaries (per FR-030, justified by Kohavi et al., 2020).

**Generation Process**:
1. Sample outcome type (binary/continuous) with 50/50 split.
2. For binary: Sample `n_a`, `n_b` from log-normal distribution (mean=500, std=0.5); sample `p_a`, `p_b` from Beta distribution (α=2, β=8 for low conversion rates).
3. For continuous: Sample `n_a`, `n_b` from log-normal; sample `mean_a`, `mean_b` from normal (μ=100, σ=20); sample `sd_a`, `sd_b` from log-normal.
4. Compute ground-truth p-value using analytical formula.
5. Introduce inconsistency in 10% of cases by perturbing reported p-value by ±0.05 to ±0.15.
6. Store ground-truth and reported values for performance evaluation.

**Performance Metrics** (FR-031, SC-030):
- Precision: True positives / (True positives + False positives) ≥0.90
- Recall: True positives / (True positives + False negatives) ≥0.80
- F1: 2 * (Precision * Recall) / (Precision + Recall) ≥0.85

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| HTML structure changes break extraction | Medium | High | Modular parser with multiple extraction strategies; error logging (FR-007). |
| Rate-limiting blocks URL fetches | Medium | Medium | Implement exponential backoff; cache responses; sample subset for CI. |
| Statistical test implementation bugs | Low | Critical | Monte Carlo validation (FR-026); contract tests against schemas. |
| Corpus dominated by single domain | Medium | High | Bias assessment (FR-027); subsampling if >30% threshold exceeded. |
| Runtime exceeds 6h CI limit | Low | High | Profile pipeline; limit corpus size for CI; parallelize independent tasks. |
| Memory exceeds 2GB limit | Low | High | Stream processing; limit DataFrame sizes; sample data if needed. |

## Assumptions & Limitations

1. **Associational claims only**: Audit does not involve random assignment; findings framed as "reported metrics are inconsistent with statistical theory" (not causal).
2. **Two-sided tests**: Reported p-values assumed two-sided unless explicitly indicated otherwise.
3. **No imputation**: If only total sample size N is present, entry flagged as "missing metric" (no equal-allocation imputation).
4. **CPU-only execution**: All computation on CPU; no GPU dependencies.
5. **Verified citations**: All external references (John et al., 2022; Kohavi et al., 2020) validated by Reference-Validator Agent before use.
