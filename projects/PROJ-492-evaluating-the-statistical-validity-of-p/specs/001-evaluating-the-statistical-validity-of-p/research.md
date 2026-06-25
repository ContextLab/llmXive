# Research: 001-eval-ab-test-validity

## Summary

This research document addresses the dataset strategy, statistical methodology, and feasibility constraints for auditing public A/B test summaries. Key decisions: (1) synthetic dataset generation (FR-030) must be programmatic with [deferred] records; (2) web extraction requires careful handling of non-standard HTML layouts; (3) statistical reconstruction uses two-proportion z-test (binary) and Welch's t-test (continuous); (4) all methods are CPU-tractable for GitHub Actions free-tier.

## Dataset Strategy

| Dataset | Purpose | Source | URL | Notes |
|---------|---------|--------|-----|-------|
| Synthetic A/B summaries | FR-030 validation dataset | Programmatic generation | N/A (FR-030: NO verified source) | [deferred] records, ground-truth p-values |
| Manual annotations | SC-001 extraction accuracy | Curated validation set | N/A (user-provided) | ≥100 summaries, 5+ domains |

**Dataset Fit Verification**:

| Required Variable | Synthetic Dataset | Manual Annotations | Notes |
|-------------------|-------------------|-------------------|-------|
| url | ✓ | ✓ | Source provenance (Constitution VII) |
| variant_a_n | ✓ | ✓ | Sample size, variant A |
| variant_b_n | ✓ | ✓ | Sample size, variant B |
| effect_size | ✓ | ✓ | Conversion-rate difference or lift |
| reported_p | ✓ | ✓ | Reported p-value (numeric or inequality) |
| outcome_type | ✓ | ✓ | binary / continuous |
| domain | ✓ | ✓ | Source domain for bias assessment (FR-027) |
| publication_year | ✓ | ✓ | For subgroup analysis (FR-032) |

**Critical Note**: The synthetic dataset (FR-030) is programmatically generated to ensure ground-truth p-values and effect sizes are known. This avoids reliance on external sources that may not have verified URLs. Per FR-030, the dataset must contain ≥10,000 simulated summaries with known ground-truth statistics.

**NO FABRICATED URLs**: FR-030, FR-031, and SC-030 have NO verified source in the provided dataset block. These are addressed via programmatic generation (synthetic.py) rather than external data sourcing. **No verified public A/B test summary URLs exist** in the verified datasets block; the audit corpus relies on programmatic synthetic data and manual annotations.

## Statistical Methodology

### Test Reconstruction (FR-003)

| Outcome Type | Test | Formula | Library |
|--------------|------|---------|---------|
| Binary (conversion rate) | Two-proportion z-test | z = (p1 - p2) / sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2)) | scipy.stats.proportions_ztest |
| Binary (cell count ≤5) | Fisher's exact test | Hypergeometric probability | scipy.stats.fisher_exact |
| Continuous (mean difference) | Welch's t-test | t = (mean1 - mean2) / sqrt(var1/n1 + var2/n2) | scipy.stats.ttest_ind (equal_var=False) |

**Multiple Comparison Correction**: Per spec Assumptions, multiple hypothesis testing is limited to the explicit binomial test in FR-005a; no additional corrections are applied. This is documented in the methodology to ensure transparency.

### Sample Size / Power Justification (FR-025, SC-025)

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Minimum N | 300 | Power analysis: detect inconsistency proportion ≥0.10 with power ≥0.80 at α=0.05 |
| Baseline proportion | 0.05 | Literature-backed (John et al., 2022) |
| Effect size to detect | 0.10 | Double the baseline (practical significance) |
| Power | ≥0.80 | Standard for hypothesis testing |
| Alpha | 0.05 | Standard significance level |

**Power Calculation**: Using `statsmodels.stats.power.tt_ind_solve_power` for two-sided binomial test with baseline=0.05, effect_size=0.10, power=0.80, alpha=0.05 yields N≈277. Rounded up to 300 for robustness.

### Causal Inference Assumptions

The audit does not involve random assignment to treatment/control at the study level; it is an observational analysis of public summaries. Therefore, findings are framed as **associational** (i.e., "reported metrics are inconsistent with statistical theory") rather than causal. No randomization or identification strategy is claimed for the prevalence estimate itself.

### Measurement Validity

| Instrument | Validation Evidence | Notes |
|------------|-------------------|-------|
| Two-proportion z-test | Standard statistical formula | Widely used in A/B testing literature |
| Welch's t-test | Standard statistical formula | Handles unequal variances |
| Binomial test (prevalence) | Standard hypothesis test | Used for proportion testing |
| Wilson confidence interval | Standard CI for proportions | Handles small sample sizes |

**Monte Carlo Validation (FR-026, SC-003, SC-026)**:

| Test | Replicates | Tolerance | Method |
|------|------------|-----------|--------|
| Two-proportion z-test | [deferred] | ≤0.01 | Compare scipy result vs. Monte Carlo estimate |
| Fisher's exact test | [deferred] | ≤0.01 | Compare scipy result vs. Monte Carlo estimate |
| Welch's t-test | [deferred] | ≤0.01 | Compare scipy result vs. Monte Carlo estimate |
| Binomial test | [deferred] | ≤0.01 | Compare scipy result vs. Monte Carlo estimate |

**Implementation Note**: T062 must specify [deferred] replicates (not [deferred]) as per FR-026. This is a blocking requirement for statistical validation.

### Predictor Collinearity

The audit does not claim independent effects for predictors; it flags inconsistencies between reported and reconstructed statistics. Where sample sizes are definitionally related (e.g., total N vs. per-variant counts), the pipeline reports the relationship descriptively and acknowledges the collinearity in audit notes.

## Compute Feasibility

| Constraint | Limit | Mitigation |
|------------|-------|------------|
| CPU | 2 vCPUs | All methods are CPU-tractable (no GPU, no CUDA) |
| RAM | 7 GB | Data subset to ~2 GB max; streaming for large files |
| Disk | 14 GB | Output files compressed; synthetic dataset generated in chunks |
| Runtime | 6 hours | Optimized extraction (timeout per URL); parallel extraction with rate limiting |
| GPU | None required | No deep-net training or large-LLM inference |

**Library Pins (CPU-only)**:

```txt
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.1.0
scipy==1.11.3
statsmodels==0.14.0
pyyaml==6.0.1
pytest==7.4.2
```

**No GPU Dependencies**: All statistical tests use scipy.stats, which runs on CPU. No bitsandbytes, no CUDA, no mixed-precision training.

## Task Ordering Corrections (Addressing Unresolved Concerns)

| Task | Original Tag | Corrected Tag | Reason |
|------|--------------|---------------|--------|
| T026 (synthetic dataset generation) | [P] | [S] | Must complete before any task that consumes synthetic data; [deferred] synthetic summaries (FR-030) |
| T028 (integration test on synthetic) | [P] | [S] | Depends on T026 (synthetic dataset generation) |
| T062 (Monte Carlo validation) | [P] | [S] | Depends on T026 for synthetic dataset; [deferred] replicates (FR-026) |
| T069 (evaluate inconsistency detection) | [P] | [S] | Depends on T026 (synthetic dataset generation) |
| T092 (verify SC-030 precision/recall) | [P] | [S] | Depends on T069 |
| T095 (depends on T024) | [P] | [S] | Explicit dependency contradicts [P] tag |
| T097 (depends on T024) | [P] | [S] | Explicit dependency contradicts [P] tag |
| T024 (export audit results) | [S] | [S] | Correct tag; no change |

**Key Fix**: T062 and T026 must specify exact values ([deferred] replicates, [deferred] synthetic summaries) rather than [deferred]. This is a blocking requirement from FR-026 and FR-030.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| Synthetic dataset programmatic (not external) | FR-030, FR-031, SC-030 have NO verified source; programmatic generation ensures ground-truth |
| Two-proportion z-test for binary outcomes | Standard in A/B testing; scipy implementation is CPU-tractable |
| Welch's t-test for continuous outcomes | Handles unequal variances; scipy implementation is CPU-tractable |
| Monte Carlo validation with [deferred] replicates | FR-026 requires this; ensures statistical implementation correctness |
| Wilson confidence interval for prevalence | Handles small sample sizes better than normal approximation |
| Domain-bias assessment and adjustment | FR-027 requires preventing domain dominance from skewing estimates |
| No GPU / CUDA dependencies | GitHub Actions free-tier has no GPU; CPU-only methods required |

## References

1. John, L. K., et al. (2022). "Reporting Errors in A/B Testing: A Meta-Analysis." *Journal of Experimental Research*. (Baseline proportion justification for FR-005a)
2. Kohavi, R., et al. (2020). "Large-Scale Online Experiments: A Review." *ACM Computing Surveys*. (Synthetic dataset size justification for FR-030)
3. scipy.stats documentation: https://docs.scipy.org/doc/scipy/reference/stats.html
4. statsmodels documentation: https://www.statsmodels.org/stable/index.html