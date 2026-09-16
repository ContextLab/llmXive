# Feature Specification: Evaluating the Impact of Code Generation on Code Review Burden

**Feature Branch**: `001-code-gen-review-burden`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Review Burden"

## User Scenarios & Testing

### User Story 1 - Data Extraction and Provenance Classification (Priority: P1)

The system MUST extract pull request metadata from a curated list of public GitHub repositories and classify each code change as either "LLM-generated" or "Human-written" based on specific provenance signals (commit messages, file headers, or diff patterns).

**Why this priority**: This is the foundational step. Without a reliable, automated method to distinguish between LLM and human code, no comparative analysis of review burden can occur. This represents the core data acquisition capability.

**Independent Test**: Can be fully tested by running the extraction script against a small, fixed set of 10 known repositories and verifying that the output CSV contains the correct `provenance` label for each PR based on manual ground-truth verification of the first 5 samples.

**Acceptance Scenarios**:

1. **Given** a list of target repositories with active pull requests, **When** the extraction script runs, **Then** it outputs a dataset containing `pr_id`, `lines_changed`, `review_duration`, `comment_count`, and `provenance_label` for every PR meeting the minimum size criteria.
2. **Given** a pull request with a commit message containing the keyword "Copilot", **When** the classification logic runs, **Then** the `provenance_label` is set to "LLM-generated" (unless overridden by a conflicting manual header).
3. **Given** a pull request with no LLM keywords in metadata or diff, **When** the classification logic runs, **Then** the `provenance_label` is set to "Human-written".

### User Story 2 - Statistical Comparison of Review Metrics (Priority: P2)

The system MUST perform statistical hypothesis tests (Mann-Whitney U or t-test) comparing review metrics (time, comment density, cycles) between the LLM-generated and Human-written groups, calculating effect sizes (Cohen's d).

**Why this priority**: This addresses the primary research question. Once data is extracted, the statistical engine must determine if observed differences are significant or due to chance, providing the core scientific insight.

**Independent Test**: Can be fully tested by feeding a synthetic dataset with known differences (e.g., Group A mean=10, Group B mean=20) into the analysis script and verifying that the p-value is < 0.05 and the effect size matches the theoretical expectation.

**Acceptance Scenarios**:

1. **Given** two groups of review data (LLM vs. Human) with non-normal distributions, **When** the analysis script runs, **Then** it automatically selects the Mann-Whitney U test and reports the U-statistic, p-value, and Cohen's d.
2. **Given** two groups with normal distributions and equal variance, **When** the analysis script runs, **Then** it selects the independent samples t-test and reports the t-statistic, p-value, and Cohen's d.
3. **Given** a result where p ≥ 0.05, **When** the report is generated, **Then** it explicitly states "No statistically significant difference found at α=0.05" rather than claiming equivalence without power analysis.

### User Story 3 - Validation and Sensitivity Reporting (Priority: P3)

The system MUST perform a manual validation check on a random sample of classified PRs to calculate inter-rater agreement (Cohen's κ) and conduct a sensitivity analysis on the outlier removal threshold (IQR multiplier) to ensure robustness.

**Why this priority**: This ensures the scientific validity of the findings. It addresses potential biases in the automated classification and verifies that the results are not artifacts of arbitrary data cleaning choices.

**Independent Test**: Can be fully tested by running the validation script on a small, manually labeled subset and verifying that the generated `sensitivity_report.csv` contains results for IQR multipliers of 1.0, 1.5, and 2.0, and that the `validation_report.md` contains a calculated Cohen's κ value.

**Acceptance Scenarios**:

1. **Given** a random sample of 50 PRs per group manually labeled by a human, **When** the validation script runs, **Then** it calculates Cohen's κ and flags any group with κ < 0.6 for manual review.
2. **Given** the default IQR outlier removal threshold of 1.5, **When** the sensitivity analysis runs, **Then** it re-runs the statistical test with thresholds of 1.0 and 2.0 and reports the percentage change in the headline p-value.
3. **Given** a significant result in the primary test, **When** the sensitivity analysis shows the p-value becomes non-significant at a threshold of 1.0, **Then** the final report highlights this instability as a limitation.

### Edge Cases

- What happens when a pull request has multiple contributors with mixed provenance (some LLM, some human)? The system must handle this by either excluding the PR or tagging it as "Mixed" and excluding it from the primary binary comparison.
- How does the system handle GitHub API rate limiting ([deferred] requests/hour)? The system must implement exponential backoff and pause execution if the limit is reached, resuming only when the window resets.
- What happens if a repository has no LLM-generated code in the target date range? The system must log a warning and exclude that repository from the analysis to prevent empty group errors.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract pull request metadata (creation time, merge time, comment count, lines changed) from GitHub repositories using the REST API, ensuring no more than 5,000 requests per hour. (See US-1)
- **FR-002**: The system MUST classify code provenance as "LLM-generated" if commit messages contain keywords (e.g., "Copilot", "GPT", "Codeium") OR file headers contain attribution, otherwise defaulting to "Human-written". (See US-1)
- **FR-003**: The system MUST filter the dataset to include only pull requests with ≥5 lines of changed code and ≥1 review comment to ensure sufficient signal. (See US-1)
- **FR-004**: The system MUST automatically detect data distribution normality and select the appropriate statistical test (Mann-Whitney U for non-normal, t-test for normal) with α=0.05. (See US-2)
- **FR-005**: The system MUST calculate Cohen's d effect size for all significant comparisons to assess practical significance beyond p-values. (See US-2)
- **FR-006**: The system MUST perform a sensitivity analysis by sweeping the outlier removal IQR multiplier across {1.0, 1.5, 2.0} and reporting the variation in p-values. (See US-3)
- **FR-007**: The system MUST generate a validation report calculating Cohen's κ against a manual sample of 50 PRs per group. (See US-3)

### Key Entities

- **PullRequest**: Represents a GitHub PR; attributes include `pr_id`, `repo_name`, `created_at`, `merged_at`, `lines_changed`, `comment_count`, `provenance_label`.
- **ReviewMetric**: Represents a calculated metric for a PR; attributes include `review_duration_seconds`, `comment_density` (comments/lines), `review_cycles`.
- **StatisticalResult**: Represents the outcome of a hypothesis test; attributes include `test_type`, `p_value`, `effect_size`, `significant` (boolean).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of PRs classified as "LLM-generated" is measured against the manual validation sample to ensure Cohen's κ ≥ 0.6. (See US-3)
- **SC-002**: The difference in mean review duration (LLM vs. Human) is measured against the null hypothesis (no difference) using a two-sample test at α=0.05. (See US-2)
- **SC-003**: The stability of the primary finding is measured by the percentage change in p-value when the IQR outlier threshold is swept from 1.0 to 2.0; a change > 20% triggers a "Low Robustness" flag. (See US-3)
- **SC-004**: The effect size (Cohen's d) of the difference in comment density is measured against standard benchmarks (small=0.2, medium=0.5, large=0.8) to determine practical significance. (See US-2)
- **SC-005**: The computational resource usage is measured against the GitHub Actions free-tier limit (≤ 6 hours CPU time, ≤ 7 GB RAM) to ensure the analysis completes without failure. (See Assumptions)

## Assumptions

- **Dataset-variable fit**: It is assumed that the selected public repositories contain sufficient "LLM-generated" code samples (defined by commit messages or headers) to form a statistically valid group (n ≥ 30) for comparison. If the dataset lacks sufficient LLM samples, the study will be limited to descriptive statistics only.
- **Inference framing**: Since this is an observational study using existing public data without random assignment, all findings regarding "impact" are framed strictly as **associational** differences, not causal effects. We do not claim LLMs *cause* higher review burden, only that they are *associated* with it.
- **Multiplicity & power**: The analysis involves multiple hypothesis tests (time, comments, severity). We will apply a Bonferroni correction (α_corrected = 0.05 / k) to control the family-wise error rate. Sample size power is `[deferred]` pending initial data extraction; if power < 0.8, the report will explicitly state this limitation.
- **Threshold justification & sensitivity**: The outlier removal threshold (IQR multiplier) is set to 1.5 based on standard Tukey boxplot conventions. A sensitivity analysis sweeping this value over {1.0, 1.5, 2.0} is required to ensure the headline results are not artifacts of this specific choice.
- **Measurement validity**: Review metrics (duration, comments) are extracted directly from GitHub's REST API, which provides authoritative source data. No external or proxy instruments are used.
- **Predictor collinearity**: If "lines changed" and "comment density" are highly correlated (r > 0.8), we will not claim independent predictive effects for both; instead, we will report them as a joint relationship and include a Variance Inflation Factor (VIF) diagnostic.
- **Compute feasibility**: The analysis assumes the dataset fits within ~7 GB of RAM after sampling. If the raw data exceeds this, the system will sample [deferred] PRs or process data in chunks. No GPU acceleration or large-model inference is used; all statistical tests are CPU-tractable.
- **API constraints**: The system assumes the GitHub REST API rate limits ([deferred] req/h) are sufficient to complete the data extraction within the 6-hour CI window. If not, the process will pause and resume, extending the wall-clock time but staying within the CPU-time budget.
