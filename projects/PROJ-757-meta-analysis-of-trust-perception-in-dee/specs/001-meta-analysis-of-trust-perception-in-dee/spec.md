# Feature Specification: Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli

**Feature Branch**: `001-meta-analysis-trust-deepfake`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Meta‑Analysis of Trust Perception in Deepfake Facial Stimuli"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Literature Search and Study Screening (Priority: P1)

The researcher MUST be able to execute automated searches across OpenAlex, Semantic Scholar, and arXiv using specific query strings, export the results as a CSV, and perform a dual-review screening process to filter studies based on inclusion criteria (peer-reviewed, experimental, explicit trust judgments, **and reporting of media-literacy metrics or stimulus realism stratification**).

**Why this priority**: Without a reproducible, complete dataset of primary studies, no meta-analysis can occur. This is the foundational data ingestion step.

**Independent Test**: Can be fully tested by running the search script against a mock API or a small subset of known studies and verifying that the output CSV contains the correct metadata fields and that the screening logic correctly includes/excludes test cases based on the defined criteria.

**Acceptance Scenarios**:

1. **Given** a query string for "deepfake" AND "trust", **When** the search script executes against the configured APIs, **Then** the system exports a CSV containing at least the title, year, source, and abstract for every hit, and logs the exact query parameters used.
2. **Given** a list of candidate studies with abstracts, **When** the screening module applies the inclusion criteria (e.g., "must measure explicit trust", "must compare authentic vs. deepfake", **"must report media-literacy scores OR stratified effect sizes by realism level"**), **Then** the system flags studies for exclusion with a specific reason code (e.g., "NO_TRUST_METRIC", "NO_CONTROL_CONDITION", "NO_MODERATOR_DATA") and retains only valid candidates.
3. **Given** two independent reviewer inputs for the same study set, **When** the system compares their screening decisions, **Then** it calculates and reports the inter-rater reliability (Cohen's Kappa) and flags any discrepancies for resolution.

---

### User Story 2 - Effect Size Calculation and Data Harmonization (Priority: P2)

The researcher MUST be able to extract statistical data (means, SDs, sample sizes, or odds ratios) from the screened studies and automatically convert them into a common effect size metric (Cohen's d or log-odds ratio) using validated formulas, handling missing data or non-standard reporting formats gracefully.

**Why this priority**: Heterogeneous reporting formats in primary studies prevent direct comparison. Harmonization is required to pool results.

**Independent Test**: Can be fully tested by providing a synthetic dataset of study statistics with known ground-truth effect sizes and verifying that the calculation engine reproduces these values within a tolerance of 0.001.

**Acceptance Scenarios**:

1. **Given** a study report containing mean trust ratings, standard deviations, and sample sizes for both authentic and deepfake conditions, **When** the extraction module processes the data, **Then** it calculates Cohen's d and its standard error with at least 4 decimal places of precision.
2. **Given** a study report containing only an odds ratio and confidence interval, **When** the extraction module processes the data, **Then** it converts the odds ratio to a log-odds ratio and estimates the standard error using the reported confidence interval bounds.
3. **Given** a study with missing standard deviations but a reported p-value and t-statistic, **When** the extraction module processes the data, **Then** it attempts to reconstruct the standard deviation; **if** the p-value is rounded (e.g., "p < 0.05"), **Then** the system **excludes** this reconstructed value from the primary pooled estimate and flags the study for the sensitivity analysis defined in FR-006. **If** the standard deviation is missing entirely and cannot be reconstructed, **Then** the system imputes it using the mean SD of studies with similar sample sizes (n ± 10) and flags it for sensitivity analysis.

---

### User Story 3 - Meta-Analysis and Moderator Modeling (Priority: P3)

The researcher MUST be able to fit a random-effects meta-analysis model to pool effect sizes, run mixed-effects meta-regressions to test the moderating effects of stimulus realism and media literacy, and generate robustness checks (leave-one-out, publication bias tests).

**Why this priority**: This is the core analytical output that answers the research question and provides the scientific conclusion.

**Independent Test**: Can be fully tested by running the analysis on a small, pre-calculated synthetic dataset with known heterogeneity and moderator effects, verifying that the pooled effect size and moderator coefficients match the expected values within statistical tolerance.

**Acceptance Scenarios**:

1. **Given** a dataset of extracted effect sizes and study-level moderators, **When** the random-effects model is fitted, **Then** the system outputs a pooled Cohen's d with a 95% confidence interval and a p-value, and reports the heterogeneity statistic (I²) and Q-statistic.
2. **Given** the pooled model, **When** the meta-regression is executed with "realism" and "media-literacy" as predictors, **Then** the system outputs the regression coefficients, standard errors, and p-values for each predictor, explicitly stating whether the association is significant at p < 0.05.
3. **Given** the full set of included studies, **When** the leave-one-out sensitivity analysis is performed, **Then** the system generates a table showing how the pooled effect size changes when each individual study is removed, and flags any single study whose removal shifts the significance of the result.

### Edge Cases

- What happens when a study reports multiple effect sizes for the same outcome (e.g., different trust scales)? The system MUST aggregate them or select the most appropriate one based on a pre-defined rule (e.g., "use the scale with the highest reliability coefficient") and log the decision.
- How does the system handle studies where the standard deviation is reported as zero or missing entirely? The system MUST apply a conservative imputation method (e.g., using the average SD of similar studies) and flag these entries for manual review or sensitivity analysis.
- How does the system handle non-convergent meta-regression models? The system MUST detect convergence failures, attempt a simpler model (e.g., fixed-effects or removing one moderator), and report the failure reason clearly in the output log.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST search OpenAlex, Semantic Scholar, and arXiv using the queries `"deepfake" AND "trust"` and `"AI‑generated face" AND "trustworthiness"` and export results to a CSV with fields: title, year, source, abstract, DOI. (See US-1)
- **FR-002**: System MUST implement a dual-reviewer screening workflow that flags studies for exclusion based on specific criteria (e.g., "not peer-reviewed", "no explicit trust metric", "no moderator data") and calculates inter-rater reliability (Cohen's Kappa). **If** Cohen's Kappa < 0.6, **Then** the system MUST flag the disputed studies for adjudication by a third reviewer. (See US-1)
- **FR-003**: System MUST convert diverse statistical outputs (means/SDs, odds ratios, t-statistics) into a unified effect size metric (Cohen's d or log-odds ratio) with standard errors. **If** standard deviation is missing, the system MUST impute it using the mean SD of studies with similar sample sizes (n ± 10). **If** standard deviation is reconstructed from a rounded p-value, the system MUST exclude it from the primary pooled estimate. (See US-2)
- **FR-004**: System MUST fit a random-effects meta-analysis model to pool effect sizes and calculate heterogeneity statistics (I², Q-statistic) with 95% confidence intervals. (See US-3)
- **FR-005**: System MUST execute mixed-effects meta-regressions to test the moderating effects of stimulus realism and media-literacy, reporting coefficients, standard errors, and p-values for each predictor. **Studies lacking stratified effect sizes by realism level or reported media-literacy metrics MUST be excluded from this specific regression analysis.** (See US-3)
- **FR-006**: System MUST perform leave-one-out sensitivity analysis and Egger's test for publication bias. **Additionally, the system MUST perform a sensitivity analysis excluding all studies with reconstructed standard deviations (especially from rounded p-values) to verify the pooled effect is not driven by imputed data.** The system MUST generate forest plots and funnel plots as **PDF** files with **labeled axes and visible confidence intervals**. (See US-3)

### Key Entities

- **Study**: Represents a primary research paper; attributes include title, DOI, year, inclusion status, and extracted statistics.
- **EffectSize**: Represents a calculated metric from a study; attributes include value (Cohen's d or log-odds), standard error, and source study ID.
- **Moderator**: Represents a study-level characteristic; attributes include type (realism, media-literacy), value (continuous or categorical), and source study ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pooled effect size (Cohen's d) and its 95% confidence interval are measured against the random-effects model output to determine if the trust bias is statistically significant (p < 0.05). (See US-3)
- **SC-002**: Moderator regression coefficients (for realism and media-literacy) are measured against the null hypothesis (coefficient ≠ 0) to assess significance, and the model fit (R²) is measured against the null model to assess explanatory power. (See US-3)
- **SC-003**: Heterogeneity (I² statistic) is measured against the random-effects model output to quantify the proportion of variance due to true differences between studies rather than sampling error. (See US-3)
- **SC-004**: Publication bias is measured against Egger's test p-value; **bias is considered absent if p > 0.10**. (See US-3)
- **SC-005**: Sensitivity of results is measured against the leave-one-out analysis output to ensure no single study disproportionately drives the significance of the findings, **and specifically against the sensitivity analysis excluding studies with reconstructed standard deviations to ensure the primary result is not driven by imputed data**. (See US-3)

## Assumptions

- The primary studies included in the meta-analysis will report sufficient statistical data (means, SDs, sample sizes, or test statistics) to allow for the calculation of effect sizes; if data is missing, the system will rely on the imputation rules defined in FR-003.
- The APIs for OpenAlex, Semantic Scholar, and arXiv will remain accessible and rate-limited within the constraints of the free-tier GitHub Actions runner (2 CPU, ~7 GB RAM) during the search phase.
- The `metafor` R package (or its Python equivalent `statsmodels`/`pymeta` if R is not feasible on the runner) will be available and compatible with the CPU-only environment for fitting random-effects models and meta-regressions.
- The definition of "realism" and "media-literacy" as moderators will be consistent across the included studies, or the system will use a standardized coding scheme to harmonize these variables.
- The total number of included studies will be small enough (< 1000) to ensure that the meta-analysis and sensitivity checks complete within the 6-hour time limit of the GitHub Actions free tier.