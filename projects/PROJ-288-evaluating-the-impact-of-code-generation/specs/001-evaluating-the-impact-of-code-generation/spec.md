# Feature Specification: Evaluating the Impact of Code Generation on Code Review Time

**Feature Branch**: `001-evaluating-llm-code-review-impact`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Review Time"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Classification (Priority: P1)

As a researcher, I need to download pull request metadata from high-star repositories and classify code changes as LLM-generated or human-written so that I can establish the primary dataset for comparison.

**Why this priority**: Without a correctly classified dataset, no statistical analysis can occur. This is the foundational step that enables all subsequent measurements.

**Independent Test**: Can be fully tested by executing the data extraction script on a small sample (e.g., 50 PRs) and verifying that the output CSV contains the expected columns (repo, PR number, code origin label) and that the classification heuristic matches manual review on the sample subset.

**Acceptance Scenarios**:

1. **Given** a list of repository URLs with ≥1000 stars, **When** the script queries the GitHub REST API for pull requests containing keywords "copilot", "llm", or "generated", **Then** the system retrieves PR metadata including creation and merge timestamps without exceeding 5,000 calls/hour.
2. **Given** a retrieved pull request, **When** the classification heuristic analyzes commit messages and code style (formatting consistency, comment density), **Then** the system assigns a label ("LLM" or "Human") and flags the entry for manual review if confidence is low.
3. **Given** a 50-sample manual review subset, **When** the system compares its automated labels against human-verified labels, **Then** the system calculates an accuracy metric and logs any discrepancies for heuristic tuning.

---

### User Story 2 - Statistical Analysis of Review Duration (Priority: P2)

As a researcher, I need to calculate review durations and perform a linear mixed-effects regression to compare review times between LLM-generated and human-written code, controlling for confounders, so that I can determine if there is a statistically significant difference.

**Why this priority**: This is the core analytical step that directly answers the research question regarding efficiency differences while controlling for known confounders like code size and repository activity.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic CSV with known distributions and verifying that the script outputs the correct coefficients, p-values, and variance components matching manual calculations.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] classified pull requests with review timestamps, **When** the system calculates `first_review_time` and `total_review_time` in minutes, **Then** the system excludes any PRs where the time delta is negative or exceeds 30 days (outliers).
2. **Given** two groups of review times (LLM vs. Human) and covariates (code size, reviewer count), **When** the system executes a linear mixed-effects regression (random intercept by repository), **Then** the system outputs the fixed effect coefficients, p-values, and variance components.
3. **Given** a significance threshold of p < 0.05, **When** the p-value is calculated, **Then** the system flags the result as "Significant" or "Not Significant" and records the direction of the difference (LLM faster/slower).

---

### User Story 3 - Visualization and Reporting (Priority: P3)

As a researcher, I need to generate diagnostic plots and regression visualizations to interpret the model results and communicate the findings effectively.

**Why this priority**: While the statistical test provides the answer, visualizations are required to interpret the distribution shape, identify outliers, and present the results to stakeholders.

**Independent Test**: Can be fully tested by generating the plots from a sample dataset and verifying that the axes are labeled correctly, the groups are color-coded distinctively, and the files are saved in the expected format.

**Acceptance Scenarios**:

1. **Given** the processed dataset with review times and code size, **When** the system generates a boxplot, **Then** the plot displays two distinct distributions (LLM vs. Human) with median lines and whiskers representing the interquartile range.
2. **Given** the dataset, **When** the system generates a scatter plot of code size vs. review time, **Then** the plot includes separate regression lines for each group and a legend identifying the groups.
3. **Given** the analysis is complete, **When** the system saves the output, **Then** it generates a summary report containing the p-value, coefficients, and links to the generated images.

---

### Edge Cases

- What happens when a repository has no pull requests matching the "copilot" or "llm" keywords? (The system logs a warning and skips the repo without failing the job).
- How does the system handle PRs with missing timestamps (e.g., merged before the API stores comment history)? (The system excludes these PRs from the `review_time` calculation but includes them in the count if only creation time is available).
- What if the manual review validation shows the heuristic accuracy is below Cohen's Kappa ≥ 0.6? (The system halts and flags the dataset for manual re-classification rather than proceeding with noisy data).
- How does the system handle repositories where the "generated" commit message is a false positive (e.g., a human named "Copilot")? (The heuristic includes a fallback check for code complexity; if complexity is too low, it defaults to "Human" or flags for review).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST query the GitHub REST API for pull requests from repositories with ≥1000 stars, filtering for keywords "copilot", "llm", or "generated" in commit messages or PR titles (See US-1).
- **FR-002**: The system MUST classify code changes as "LLM-generated" or "Human-written" using a heuristic based on commit message patterns and code style (formatting consistency score > 0.95, comment density < 5% of total lines), validated on a 50-sample subset, and MUST record validation results in `data/validation_log.csv` (See US-1).
- **FR-003**: The system MUST calculate `first_review_time` (time from creation to first comment) and `total_review_time` (time from creation to merge/close) in minutes for each pull request (See US-2).
- **FR-004**: The system MUST perform a linear mixed-effects regression to compare review times between LLM and Human groups, with fixed effects for origin, code size, and reviewer count, and random intercepts for repository, to control for confounders (See US-2).
- **FR-005**: The system MUST generate a boxplot comparing review time distributions, a scatter plot of code size vs. review time with regression lines, and residual plots (residuals vs. predicted values) for each group to check model assumptions (See US-3).
- **FR-006**: The system MUST exclude pull requests with review times exceeding 30 days or negative time deltas to prevent outlier skewing (See US-2).
- **FR-007**: The system MUST implement a rate-limiting mechanism using a token bucket algorithm to ensure API calls do not exceed 5,000 per hour, with exponential backoff (initial 1s, max 60s) upon hitting the limit (See US-1).
- **FR-008**: The system MUST perform a sensitivity analysis sweeping the classification confidence threshold (0.6, 0.7, 0.8) and report how false-positive and false-negative rates vary (See US-1).
- **FR-009**: The system MUST implement stratified sampling across repositories and exclude any repository where >50% of PRs contain LLM keywords to prevent selection bias (See US-1).
- **FR-010**: The system MUST estimate false positive contamination using a human-written baseline corpus and apply a matrix correction method if the estimated contamination rate exceeds 5% (See US-2).

### Key Entities

- **PullRequest**: Represents a single pull request with attributes: `repo_id`, `pr_number`, `author`, `code_lines_changed`, `review_time_first`, `review_time_total`, `reviewer_count`, `origin_label` (LLM/Human).
- **ReviewMetrics**: Aggregated statistics for a group, including `median_time`, `mean_time`, `std_dev`, and `sample_size`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in median review duration between LLM-generated and human-written code is measured against the null hypothesis of no difference, using the linear mixed-effects regression p-value for the origin coefficient (See US-2).
- **SC-002**: The accuracy of the automated LLM classification heuristic is measured against a manually verified 50-sample subset, requiring Cohen's Kappa (κ ≥ 0.6) agreement (See US-1).
- **SC-003**: The impact of code size on review time is measured against the regression slope coefficients for each group to determine if LLM code scales differently (See US-3).
- **SC-004**: The distribution shape of review times is measured against the Shapiro-Wilk test (p < 0.05) to reject normality, justifying the use of non-parametric checks if needed (See US-2).
- **SC-005**: The feasibility of the analysis is measured against the 6-hour GitHub Actions job limit and 7 GB RAM constraint, ensuring the entire pipeline completes without resource exhaustion (See Assumptions).

## Assumptions

- The GitHub REST API free tier provides sufficient access to pull request metadata (timestamps, comments, merge status) for the selected repositories without requiring authentication tokens with elevated scopes.
- The "copilot", "llm", or "generated" keywords in commit messages are a sufficient proxy for LLM-generated code, and false positives (humans using these words) are negligible or detectable via code style heuristics.
- The distribution of review times is skewed (non-normal), justifying the use of non-parametric checks or robust regression.
- The [deferred] pull request sample size ([deferred] LLM, [deferred] human) provides sufficient statistical power to detect a moderate effect size (Cohen's d ≈ 0.5) at p < 0.05.
- All data processing and statistical analysis can be performed on a CPU-only runner with 7 GB RAM and 14 GB disk space without requiring GPU acceleration.
- The [deferred] API calls/hour limit is sufficient to fetch metadata for the target repositories within the 6-hour job window.
- Reviewers' behavior (speed of response) is consistent across repositories of similar activity levels, minimizing the confounding effect of repository-specific culture.
- The code style heuristic (formatting consistency, lack of inline comments) is a valid indicator of LLM generation for the specific repositories selected.