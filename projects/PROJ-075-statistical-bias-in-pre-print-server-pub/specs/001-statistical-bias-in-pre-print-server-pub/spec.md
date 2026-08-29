# Feature Specification: Statistical Bias in Pre-Print Server Publication Trends

**Feature Branch**: `001-statistical-bias-in-pre-print-server-pub`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "Statistical Bias in Pre-Print Server Publication Trends statistics"

## User Scenarios & Testing

### User Story 1 - Matched Dataset Construction and Extraction (Priority: P1)

As a researcher, I want the system to automatically identify pairs of pre-print and peer-reviewed journal articles for the same study, extract their reported p-values and effect sizes, and store them in a structured dataset, so that I have a clean, matched foundation for statistical comparison.

**Why this priority**: This is the core data acquisition step. Without a valid matched dataset, no subsequent statistical analysis (distribution shifts, effect size comparisons) can occur. It represents the Minimum Viable Product for the data pipeline.

**Independent Test**: Can be fully tested by running the scraping and matching script on a small, known subset of 10 pre-print/journal pairs and verifying the output CSV contains exactly 10 rows with non-null p-value and effect-size fields for both versions.

**Acceptance Scenarios**:

1. **Given** a list of pre-print IDs from arXiv/bioRxiv and a query to OpenAlex, **When** the matching algorithm runs, **Then** the system identifies the corresponding journal DOI for at least 80% of the input pre-prints within the defined time window (2018–2023).
2. **Given** a matched pair of PDFs, **When** the extraction module runs, **Then** it successfully parses at least one p-value and one effect size from the pre-print version and at least one of each from the journal version, recording them in a unified row.
3. **Given** a paper where the p-value is reported as an inequality (e.g., "p < 0.05"), **When** the parser encounters it, **Then** it records the inequality type and the threshold value (e.g., `type: inequality, value: 0.05`) rather than discarding the entry.

---

### User Story 2 - Distributional and Magnitude Analysis (Priority: P2)

As a researcher, I want the system to perform p-curve analysis and local density ratio tests on p-value distributions and paired t-tests (or Wilcoxon signed-rank tests) on effect sizes to quantify the shift between pre-print and journal versions, so that I can determine if peer review acts as a statistical filter.

**Why this priority**: This delivers the primary scientific insight. It directly answers the research question regarding "p-value distribution anomalies" and "effect-size inflation signatures."

**Independent Test**: Can be fully tested by running the analysis module on a synthetic dataset with known differences (e.g., pre-print p-values skewed toward 0.04, journal p-values uniform, with a defined ground truth of [deferred] p-hacking prevalence in pre-prints) and verifying the output correctly flags the distribution shift and calculates the expected mean difference in effect size with a confidence interval excluding zero.

**Acceptance Scenarios**:

1. **Given** a dataset of matched p-values, **When** the distribution analysis runs, **Then** it generates a histogram for pre-prints and journals separately, performs a p-curve analysis, and outputs the magnitude of the density ratio at p=0.05 to indicate if the distributions differ meaningfully.
2. **Given** a dataset of matched effect sizes, **When** the magnitude analysis runs, **Then** it calculates the difference ($\Delta$ES) for each pair (applying interval-censoring for inequalities) and performs a paired t-test (or Wilcoxon if normality fails) to determine if the mean difference is statistically different from zero.
3. **Given** a specific field (e.g., Quantitative Biology), **When** the analysis runs, **Then** it outputs the results stratified by field to allow for domain-specific bias detection.

---

### User Story 3 - Sensitivity Analysis and Robustness Reporting (Priority: P3)

As a researcher, I want the system to perform a sensitivity analysis on the p-value inclusion threshold (sweeping across a range of significance levels) and report how the detected bias rates change, so that I can ensure the findings are not artifacts of a single arbitrary cutoff.

**Why this priority**: This addresses the methodological soundness requirement for "Threshold justification & sensitivity." It ensures the results are robust and defensible against critiques regarding arbitrary decision boundaries.

**Independent Test**: Can be fully tested by running the sensitivity module on a fixed dataset and verifying that the output report contains three distinct sections (one for each threshold) with calculated bias rates that vary (or remain stable) as expected (e.g., bias rate decreases as threshold increases from 0.01 to 0.1 in a known p-hacked dataset).

**Acceptance Scenarios**:

1. **Given** a fixed dataset of p-values, **When** the sensitivity analysis runs with thresholds {, 0.05, 0.1}, **Then** it calculates the proportion of "significant" results (p < threshold) for both pre-print and journal versions at each threshold.
2. **Given** the sensitivity results, **When** the report is generated, **Then** it explicitly states the variation in the "significance flip rate" (difference between pre-print and journal significance) across the swept thresholds.
3. **Given** a null result in the primary analysis, **When** the sensitivity analysis runs, **Then** it confirms that the null result holds across the swept thresholds, reinforcing the robustness of the finding.

---

### Edge Cases

- What happens when a pre-print has no corresponding journal publication within the dataset timeframe? (System must exclude it from the matched analysis but log it as "unmatched" for potential future expansion).
- How does the system handle papers where the statistical method changes between pre-print and journal (e.g., switching from t-test to regression)? (System must flag these pairs as "methodological shift" and exclude them from paired effect-size comparison to avoid invalid $\Delta$ES).
- How does the system handle missing effect size data in the journal version but present in the pre-print? (System must exclude the pair from magnitude analysis but retain it for distribution analysis if p-values are present).

## Requirements

### Functional Requirements

- **FR-001**: System MUST scrape arXiv and bioRxiv metadata for the period 2018–2023 and query the OpenAlex 'Works' raw dumps (from the official OpenAlex S3 bucket) to match pre-prints with journal DOIs by implementing a fuzzy-matching algorithm using title/author similarity scores. (See US-1)
- **FR-002**: System MUST parse full-text PDFs to extract reported p-values (supporting exact values and inequalities like $p < 0.05$) and effect sizes (Cohen's d, Hedges' g, odds ratios, risk ratios, or Pearson's r) with their confidence intervals for both pre-print and journal versions; unsupported types MUST be logged as extraction failures. Inequalities MUST be treated as interval-censored data (e.g., "p < 0.05" is recorded as range [0, 0.05]) for general reporting, but MUST be EXCLUDED from p-curve analysis per Simonsohn et al. to avoid noise. For paired effect-size analysis, the system MUST apply a method for censored effect sizes (e.g., Tobit regression or survival analysis for paired data) rather than simple imputation. (See US-1)
- **FR-003**: System MUST filter the dataset to exclude case studies, theoretical papers, and pairs where the primary statistical method changes between versions (specifically tracking t-test, ANOVA, Chi-square, Regression, and Wilcoxon methods), flagging such pairs as "methodological shift" before exclusion to ensure a clean matched cohort for analysis. (See US-1)
- **FR-004**: System MUST perform a separate p-curve analysis on the p-value distributions of pre-prints and journals to detect evidential value within each, then compare the *results* (e.g., estimated power or p-hacking prevalence) rather than raw density ratios across venues. For effect sizes, the system MUST perform a paired t-test (or Wilcoxon if normality fails) on the difference ($\Delta$ES) between versions, EXCLUDING pairs where the sample size (N) changes by > 20% or where p-values are identical (within rounding error) to avoid confounding and tautological results. (See US-2)
- **FR-005**: System MUST execute a sensitivity analysis sweeping the significance threshold across a range of conventional levels and report the variation in the "significance flip rate" (proportion of pairs where p crosses the threshold in opposite directions) for each threshold. (See US-3)
- **FR-006**: System MUST extract and compare sample sizes (N) for each pair and flag pairs where N increases by > 20% between pre-print and journal versions for exclusion from the paired effect-size difference calculation. (See US-2)

### Key Entities

- **MatchedPaperPair**: Represents a single study with two artifacts: `preprint_artifact` (source, date, extracted stats) and `journal_artifact` (source, date, extracted stats).
- **StatisticalMetric**: Represents a single extracted value, including `type` (p-value, effect-size), `value`, `unit`, `inequality_flag`, `interval_bounds` (for censored values), and `source_version` (pre-print or journal).
- **AnalysisResult**: Represents the output of a statistical test, including `test_type` (p-curve, density-ratio, t-test), `statistic_value`, `p_value`, `interpretation`, and `threshold_context` (for sensitivity analysis).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The match rate between pre-prints and journal versions is measured against the total number of pre-prints queried, with a target of ≥ 60% successful linkage for the target sample size of a representative corpus of papers. (See US-1)
- **SC-002**: The distribution shift (density ratio magnitude) is measured against a null distribution generated via permutation or bootstrapping, requiring that the observed ratio falls outside the confidence interval of the null to indicate a meaningful difference. (See US-2)
- **SC-003**: The mean difference in effect size ($\Delta$ES) is measured against zero, with a confidence interval that excludes zero indicating a systematic inflation or deflation in pre-prints. (See US-2)
- **SC-004**: The sensitivity of the bias detection is measured across the swept thresholds {0.01, 0.05, 0.1}, requiring that the direction of the bias (pre-print > journal or vice versa) remains consistent across all thresholds. (See US-3)

## Assumptions

- **Dataset Variable Fit**: The selected pre-print/journal pairs from arXiv and bioRxiv contain sufficient metadata (title, authors, DOI) to enable reliable matching via OpenAlex; if a match fails, the paper is excluded rather than imputed.
- **Observational Framing**: The analysis is framed as observational; findings regarding "bias" or "correction" describe associations between publication stage and statistical values, not causal effects of peer review itself, as no random assignment exists.
- **Compute Feasibility**: The entire pipeline (scraping, parsing, analysis) for a representative set of matched pairs will execute within the GitHub Actions free-tier limit, using lightweight Python libraries (requests, regex, pandas, scipy) without GPU acceleration. (See Constraints)
- **Text Parsing Validity**: The regex and NLP tools used for extraction can reliably identify statistical metrics in the standard LaTeX/HTML formats used by arXiv and major journal publishers; complex or non-standard formatting may result in exclusion of specific metrics for those pairs.
- **Threshold Justification**: The sensitivity sweep thresholds {0.01, 0.05, 0.1} are chosen based on community-standard significance levels to ensure the analysis captures the most relevant decision boundaries for scientific reporting.
- **Collinearity Handling**: Since the pre-print and journal versions of the same study are not independent samples but distinct artifacts of the same research, the analysis focuses on the *difference* between them rather than treating them as independent predictors; no collinearity diagnostics are required for the paired difference test.
- **Sample Size Control**: The analysis assumes that sample size changes (N) are a primary confounder; the system controls for this by flagging pairs with > 20% N increase (FR-006) and excluding them from the effect-size difference calculation.
- **Target Metrics**: The target match rate is ≥ 60% on a a sample of valid pairs; this is a planning estimate, not a functional pass/fail criterion. To achieve this with expected match/extraction failure rates, the initial query size must be at least N=1000 papers.
- **Single Source of Truth**: All analysis outputs trace to specific rows in the `MatchedPaperPair` entity stored in `matched_pairs.csv`.
- **Constraints**: The system MUST optimize for lightweight execution to ensure feasibility within standard CI/CD environments, though specific resource limits are not hard requirements for the analysis logic itself.