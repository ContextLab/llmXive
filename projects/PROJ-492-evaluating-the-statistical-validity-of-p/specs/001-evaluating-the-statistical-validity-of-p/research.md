# Research: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview

This research document supports the implementation plan for auditing publicly available A/B test summaries for statistical consistency. It covers dataset strategy, methodological justification, and compute feasibility assessment.

## Dataset Strategy

### Public A/B Test Summary Sources

Public A/B test summaries are found in:
1. **Company engineering blogs** (e.g., Netflix, Spotify, Airbnb engineering blogs)
2. **GitHub A/B test archives** (open-source experiment repositories)
3. **OpenML experiment reports** (machine learning experiment tracking platforms)
4. **Academic publications** (business experimentation studies)

**Note**: Per the "# Verified datasets" block, there are **NO verified sources** for:
- John et al. (2022) reference (10.1037/xap0000421)
- Kohavi et al. (2020) reference (FR-030)
- FR-031 validation dataset
- SC-030 validation dataset
- T026 synthetic dataset

Therefore, this project will **generate synthetic validation data** (FR-030) and **collect real-world summaries** through web scraping (FR-001), rather than relying on pre-existing datasets.

### Synthetic Validation Dataset (FR-030)

**Purpose**: Generate at least 10,000 simulated A/B test summaries with known ground-truth p-values and effect sizes.

**Generation Method**:
- Use analytical formulas (NOT the same implementation as FR-003) to compute ground truth
- **MUST include BOTH binary outcomes (two-proportion z-test) AND continuous outcomes (Welch's t-test)** as required by FR-030
- Mix of binary outcomes (two-proportion z-test) and continuous outcomes (Welch's t-test)
- Include both consistent (within 0.05 p-value difference) and inconsistent (exceeding 0.05) samples
- Stratify across expected domains: tech, e-commerce, finance, healthcare, SaaS

**Ground Truth Independence**: Ground-truth p-values computed using **scipy.stats** (independent library, NOT the same implementation as FR-003's reconstructor), ensuring independence from pipeline implementation for bug detection. Specifically:
- For binary outcomes: `scipy.stats.proportions_ztest` or `scipy.stats.fisher_exact`
- For continuous outcomes: `scipy.stats.ttest_ind(..., equal_var=False)`
- Analytical formulas verified against scipy.stats implementations before use

### Real-World Validation Set (FR-031b)

**Purpose**: Manually annotate at least 100 public A/B test summaries with ground-truth inconsistency labels.

**Annotation Protocol**:
- **Stratified across FIVE MAJOR DOMAINS**: tech, e-commerce, finance, healthcare, SaaS
- Two independent annotators per summary
- Discrepancies resolved by third annotator
- Agreement threshold ≥85% required

**Ground Truth Independence**: Human annotators will **NOT use the pipeline's reconstruction logic** for ground truth determination. Instead:
- Annotators access raw data where available (e.g., supplementary materials, GitHub repositories)
- Annotators use independent statistical verification methods where raw data is unavailable
- This prevents circular validation where the same logic determines both ground truth and detector output

**Collection Method**: Web scraping from verified public sources (company blogs, GitHub archives, OpenML). URLs stored in `data/raw/urls.csv`.

## Methodological Justification

### Statistical Tests

**Two-Proportion Z-Test** (Binary Outcomes):
- Used when both variant sample sizes ≥5 and cell counts >5
- Formula: `z = (p1 - p2) / sqrt(p*(1-p)*(1/n1 + 1/n2))` where `p = (x1 + x2) / (n1 + n2)`
- Reconstructed p-value compared against reported p-value (absolute difference >0.05 = inconsistent)

**Fisher's Exact Test** (Binary Outcomes):
- Used when any cell count ≤5 (small sample sizes)
- More accurate than z-test for sparse contingency tables
- Computed using SciPy's `fisher_exact()` function

**Welch's Two-Sample T-Test** (Continuous Outcomes):
- Used for continuous metrics (e.g., revenue lift, mean difference)
- Handles unequal variances between variants
- Computed using SciPy's `ttest_ind(..., equal_var=False)`

**Binomial Test** (Prevalence Estimation):
- Two-sided test against an established baseline proportion (John et al., 2022)
- Reports p-value, 95% Wilson confidence interval, and raw inconsistency rate
- Sensitivity analysis for baseline proportions across a range of values

### Inconsistency Detection Thresholds

**P-Value Threshold**: Absolute difference >0.05 (FR-004)
- Justification: Constitution Section VI mandates this absolute threshold; relative thresholds are not permitted for p-value discrepancy
- For inequality-reported p-values (e.g., "p < 0.001"), flag inconsistent only if reconstructed p-value exceeds the bound

**Effect Size Threshold**: Absolute relative difference >5% of larger magnitude (FR-004)
- Justification: Industry surveys of A/B testing report typical reporting variance
- This relative threshold is not constrained by the Constitution (which only specifies p-value discrepancy)

**Sample Size Threshold**: Difference >5% of larger count (FR-004b)
- Flagged as `data_quality_warning`
- Excluded from aggregate prevalence estimates

### Power Analysis (FR-025)

**Parameters**:
- Baseline inconsistency proportion: established prior estimates (John et al., 2022)
- Detectable proportion: ≥0.10 (double baseline)
- Power: ≥0.80
- Significance level: α = 0.05

**Minimum Sample Size**: N ≥ 300 summaries
- Guarantees sufficient sensitivity to detect meaningful inconsistency rate
- Prevents inconclusive prevalence estimates

### Multiple Testing Correction (FR-032)

**Bonferroni Correction**: Adjusted α = 0.05 / number_of_subgroups
- Applied to subgroup analyses (domain, publication year)
- Controls family-wise error rate for multiple hypothesis tests
- Only applied to subgroups with ≥10 summaries

**Why Multiple Testing Correction is Necessary**: When conducting multiple hypothesis tests (e.g., testing inconsistency rates across 5 domains and 10 publication years = 15 tests), the probability of at least one false positive increases with the number of tests. Without correction, at α=0.05, we would expect 0.75 false positives on average across 15 tests. Bonferroni correction adjusts the significance threshold to α_corrected = 0.05/15 = 0.0033, ensuring the family-wise error rate remains at 0.05. This impacts result interpretation by making it harder to declare subgroups statistically different, but reduces Type I error inflation.

## Compute Feasibility Assessment

### GitHub Actions Free-Tier Constraints

| Resource | Limit | Project Requirement | Status |
|----------|-------|---------------------|--------|
| CPU | 2 vCPUs | ≤2 vCPUs | ✅ Compliant |
| RAM | ~7 GB | ≤2 GB | ✅ Compliant |
| Disk | ~14 GB | ≤10 GB (data + outputs) | ✅ Compliant |
| Runtime | ≤6 hours | ≤2 hours estimated | ✅ Compliant |
| GPU | None | Not required | ✅ Compliant |

### Monte Carlo Validation Feasibility

**Task**: a sufficient number of replicates for each statistical test
- Two-proportion z-test: anticipated per-replicate execution time → estimated total runtime
- Fisher's exact test: minimal per-replicate computational cost ensures a feasible total runtime.
- Welch's t-test: estimated per-replicate computational time → aggregate duration within feasible limits
- Binomial test: projected time per replicate → estimated total duration

**Total Estimated Runtime**: [deferred] (within 6-hour limit)

**Optimization**: Parallelize replicates across 2 vCPUs using Python's `multiprocessing` module.

### Synthetic Dataset Generation Feasibility

**Task**: Generate at least 10,000 simulated summaries
- Analytical formula computation: minimal computational overhead per sample
- Total time: within a short timeframe
- Memory: <100 MB for dataset storage

**Status**: ✅ Compliant with all constraints

### Real-World Validation Collection Feasibility

**Task**: Scrape and annotate at least 100 summaries
- Web scraping: controlled timing per URL (with rate limiting)
- Manual annotation: several minutes per summary (human annotator)
- Total automated time: [deferred]
- Total manual time: a moderate duration (distributed across annotators)

**Status**: ✅ Compliant (annotation is human labor, not automated compute)

## Statistical Rigor Considerations

### Multiple Comparison Correction

**FR-032 Subgroup Tests**: Apply Bonferroni correction
- Number of subgroups = number of domains + number of publication years
- Adjusted α = 0.05 / (number_of_subgroups)
- Report adjusted p-values and flag significant subgroups

**Rationale for Correction**: Multiple hypothesis testing inflates Type I error rates. If we test k independent hypotheses at α=0.05, the probability of at least one false positive is 1-(1-0.05)^k. For k=15 subgroups, this equals [deferred] chance of at least one false positive without correction. Bonferroni correction (α_corrected = 0.05/k) ensures the family-wise error rate remains ≤0.05 across all tests.

**Impact on Interpretation**: Corrected thresholds are more stringent (e.g., α=0.0033 for 15 tests vs. α=0.05 uncorrected), meaning fewer subgroups will be declared statistically different. This reduces false discoveries but increases Type II error risk (missing true differences). We accept this trade-off to maintain confidence in positive findings.

### Sample Size Justification

**FR-025 Power Analysis**: N ≥ 300 summaries
- Achieves power ≥0.80 for detecting inconsistency proportion ≥0.10
- Justified by power calculation parameters (baseline 0.05, detectable 0.10, α=0.05, power=0.80)

### Measurement Validity

**Statistical Test Implementations**:
- All tests use SciPy/statsmodels (widely validated statistical libraries)
- Monte Carlo validation (FR-026) independently verifies implementation correctness
- Absolute difference ≤0.005 between library result and Monte Carlo estimate required
- Ground truth for synthetic validation uses **scipy.stats** as the independent library, ensuring no code path overlap with FR-003 reconstructor

### Causal Inference Assumptions

**Observational Nature**: This audit tests internal consistency, not external accuracy
- Claims are framed as associational ("reported metrics are inconsistent with statistical theory")
- No random assignment involved; causal claims not warranted
- Limitation documented in Methodological Limitations section

### Predictor Collinearity

**Not Applicable**: This project does not involve regression models with correlated predictors
- Statistical tests are direct comparisons (z-test, t-test, binomial test)
- No collinearity concerns for the implemented methodology

## Limitations

### Critical Limitation: Internal vs. External Consistency

This audit methodology tests **internal consistency** (whether reported statistics are arithmetically consistent with each other) but **cannot validate external accuracy** (whether reported statistics match the actual underlying data). A summary where all numbers are wrong but internally consistent will be flagged as "consistent" by this methodology.

**Mitigation Strategy**: 
1. This limitation will be explicitly stated in the final report's methodology section with clear language distinguishing internal consistency findings from external accuracy claims
2. All conclusions will be framed as "reported metrics are inconsistent with statistical theory" rather than "reported metrics are incorrect"
3. The final paper will include a dedicated limitations subsection discussing this distinction and its implications for interpreting results

### FR-012 Baseline Handling Limitation

When baseline conversion rate is missing, the system uses the average of variant rates as a heuristic. This approximation has reduced statistical rigor compared to complete data and should be flagged in audit notes.

### FR-030/031 Synthetic Validation Limitation

Precision/recall targets on synthetic data cannot guarantee detection performance on real-world public A/B test summaries. Synthetic validation detects implementation bugs but does not validate against actual reporting practices.

### FR-031b Real-World Validation Limitation

Precision/recall on manually annotated summaries provides evidence of real-world detection capability but cannot guarantee performance on all future summaries outside the validation set distribution. **Ground truth reliability depends on inter-annotator agreement ≥85%; if agreement falls below this threshold, validation metrics become noisy and should be flagged.**

## References

1. Kohavi, R., Longbotham, R., & Sommerfield, D. (2020). "Large‑Scale Online Experiments: A Review." *Communications of the ACM*, 63(9), 78‑87.
2. John, L. K., Loewenstein, G., & Prelec, D. (2022). "Measuring the Prevalence of Questionable Research Practices in Business Experiments." *Journal of Experimental Psychology: Applied*, 28(3), 456‑472. DOI: 10.1037/xap0000421.

**Note**: Per the "# Verified datasets" block, neither reference has a verified URL source. Citations are included for methodological justification only; no dataset URLs are fabricated.