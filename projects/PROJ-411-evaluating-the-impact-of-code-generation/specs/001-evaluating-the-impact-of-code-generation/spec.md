# Feature Specification: Evaluating the Impact of Code Generation on Code Review Burden

**Feature Branch**: `001-code-gen-review-burden`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Review Burden"

## User Scenarios & Testing

### User Story 1 - Data Extraction and Provenance Classification (Priority: P1) (US-001)

The system MUST extract pull request metadata from a curated list of public GitHub repositories and classify each code change as either "LLM-generated" or "Human-written" based on specific provenance signals (commit messages, file headers, or diff patterns).

**Why this priority**: This is the foundational step. Without a reliable, automated method to distinguish between LLM and human code, no comparative analysis of review burden can occur. This represents the core data acquisition capability.

**Independent Test**: Can be fully tested by running the extraction script against a small, fixed set of known repositories. and verifying that the output CSV contains the correct `provenance` label for each PR based on manual ground-truth verification of an initial subset of samples.

**Acceptance Scenarios**:

1. **Given** a list of target repositories with active pull requests, **When** the extraction script runs, **Then** it outputs a dataset containing `pr_id`, `lines_changed`, `review_duration_seconds`, `review_active_seconds`, `comment_count`, `comment_density`, `issue_severity`, and `provenance_label` for every PR meeting the minimum size criteria.
2. **Given** a pull request with a commit message containing the keyword "Copilot", **When** the classification logic runs, **Then** the `provenance_label` is set to "LLM-generated" unless a conflicting manual header is present (see precedence rule below).
3. **Given** a pull request with no LLM keywords in metadata, diff patterns, or file headers, **When** the classification logic runs, **Then** the `provenance_label` is set to "Human-written".
4. **Given** a pull request that contains mixed provenance signals (some LLM‑generated changes, some human), **When** the classification logic runs, **Then** the `provenance_label` is set to "Mixed" and the PR is excluded from the primary binary comparison.

**Precedence Rule for Conflicting Signals** (see FR-002):
- File‑header attribution overrides all other signals.
- Diff‑pattern matches override commit‑message keywords.
- Commit‑message keywords are applied only if no higher‑priority signal is present.

### User Story 2 - Statistical Comparison of Review Metrics (Priority: P2) (US-002)

The system MUST perform statistical hypothesis tests (Mann‑Whitney U or independent‑samples t‑test) comparing review metrics (review active time, comment density, issue severity) between the LLM-generated and Human-written groups, calculating appropriate effect sizes (Cohen’s d for t‑test, rank‑biserial correlation for Mann‑Whitney U).

**Why this priority**: This addresses the primary research question. Once data is extracted, the statistical engine must determine if observed differences are significant or due to chance, providing the core scientific insight.

**Independent Test**: Can be fully tested by feeding a synthetic dataset with known differences (e.g., Group A mean = 10 s, Group B mean = 20 s) into the analysis script and verifying that the p‑value is < 0.05 and the reported effect size is within ±0.05 of the analytically expected value.

**Acceptance Scenarios**:

1. **Given** two groups of review data (LLM vs. Human) with non‑normal distributions, **When** the analysis script runs, **Then** it automatically selects the Mann‑Whitney U test and reports the U‑statistic, p‑value, and rank‑biserial effect size.
2. **Given** two groups with normal distributions and equal variance, **When** the analysis script runs, **Then** it selects the independent‑samples t‑test and reports the t‑statistic, p‑value, and Cohen’s d.
3. **Given** a result where p ≥ α = 0.05, **When** the report is generated, **Then** it explicitly states “No statistically significant difference found at α = 0.05” (see FR-011) rather than claiming equivalence without a power analysis.

### User Story 3 - Validation and Sensitivity Reporting (Priority: P3) (US-003)

The system MUST perform a manual validation check on a random sample of classified PRs to calculate inter‑rater agreement (Cohen’s κ) and conduct a sensitivity analysis on the outlier removal threshold (IQR multiplier) to ensure robustness.

**Why this priority**: This ensures the scientific validity of the findings. It addresses potential biases in the automated classification and verifies that the results are not artifacts of arbitrary data cleaning choices.

**Independent Test**: Can be fully tested by running the validation script on a small, manually labeled subset and verifying that the generated `sensitivity_report.csv` contains results for IQR multipliers of 1.0, 1.5, and 2.0, and that the `validation_report.md` contains a calculated Cohen’s κ value.

**Acceptance Scenarios**:

1. **Given** a random sample of PRs per group manually labeled by a human, **When** the validation script runs, **Then** it calculates Cohen’s κ and flags any group with κ < 0.6 for manual review.
2. **Given** the default IQR outlier removal threshold of 1.5, **When** the sensitivity analysis runs, **Then** it re‑runs the statistical test with thresholds of 1.0 and 2.0 and reports whether the significance (p < α) flips across thresholds; any flip triggers a “Low Robustness” flag (see SC-003).
3. **Given** a significant result in the primary test, **When** the sensitivity analysis shows the significance flips at a threshold of 1.0, **Then** the final report highlights this instability as a limitation.

### Edge Cases

- What happens when a pull request has multiple contributors with mixed provenance (some LLM, some human)? The system tags it as “Mixed” and excludes it from the binary comparison (see FR-008).
- How does the system handle GitHub API rate limiting (≤ 5,000 requests per hour)? The system implements exponential backoff and pauses execution if the limit is reached, resuming only when the window resets (see FR-009).
- What happens if a repository has no LLM‑generated code in the target date range? The system logs a warning and excludes that repository from the analysis to prevent empty‑group errors (see FR-010).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract pull request metadata (creation time, merge time, comment count, lines changed, review timestamps) from GitHub repositories using the REST API, ensuring no more than **[deferred]** requests per hour. (See US-001)
- **FR-002**: The system MUST classify code provenance as **"LLM-generated"**, **"Human-written"**, or **"Mixed"** according to the following signals **(in precedence order)**:  
  1. File‑header attribution (overrides all).  
  2. Diff‑pattern matches to known LLM generation signatures (overrides commit‑message keywords).  
  3. Commit‑message keywords (e.g., “Copilot”, “GPT”, “Codeium”).  
  If none apply, label as **Human‑written**. (See US-001)  
  *Note*: This label is a proxy for LLM‑generated code and its limitations are acknowledged (see scientific‑soundness‑8653ad63).
- **FR-003**: The system MUST filter the dataset to include only pull requests with **≥ 5 lines of changed code** and **≥ 1 review comment** to ensure sufficient signal, but it MUST also provide a sensitivity analysis that evaluates the impact of relaxing the comment‑count filter to **≥ 0** (see FR-014). (See US-001)
- **FR-004**: The system MUST automatically detect data‑distribution normality and select the appropriate statistical test (Mann‑Whitney U for non‑normal, independent‑samples t‑test for normal) with **α = 0.05**. It MUST also report an explicit statement when a test yields **p ≥ α** (see FR-011). Additionally, it MUST compute **review_active_seconds** (time from first review comment to PR merge) as the primary reviewer‑effort metric, using the `first_comment_timestamp` field added in FR-016. (See US-002)
- **FR-005**: The system MUST calculate and report **effect sizes** for all primary comparisons: **Cohen’s d** for t‑tests and **rank‑biserial correlation** for Mann‑Whitney U tests, regardless of significance, and for synthetic benchmark datasets the reported effect size must be within **±0.05** of the analytically expected value. (See US-002)
- **FR-006**: The system MUST perform a sensitivity analysis by sweeping the outlier removal IQR multiplier across **{1.0, 1.5, 2.0}** and report whether the significance (p < α) flips across thresholds; any flip triggers a “Low Robustness” flag. (See US-003)
- **FR-007**: The system MUST generate a validation report calculating **Cohen’s κ** against a manual sample of **50 PRs per group**. (See US-003)
- **FR-008**: The system MUST assign the **“Mixed”** provenance label to PRs with conflicting LLM and human signals and **exclude** them from the primary binary statistical comparison. (See US-001)
- **FR-009**: The system MUST implement **exponential backoff** and pause/resume logic when the GitHub API rate limit of **[deferred]** requests per hour is reached. (See US-001)
- **FR-010**: The system MUST log a **warning** and **exclude** any repository that contains **zero LLM‑generated PRs** in the target date range. (See US-001)
- **FR-011**: The analysis report MUST contain an explicit **null‑result statement** (“No statistically significant difference found at α = 0.05”) whenever a hypothesis test yields p ≥ α. (See US-002)
- **FR-012**: The system MUST extract **issue severity** (e.g., bug, enhancement, documentation) from PR labels and include it as a quantitative metric for comparison between groups. (See US-002)
- **FR-013**: The system MUST perform a **repository‑level clustering adjustment** (mixed‑effects model or stratified analysis) to account for non‑independence of PRs within the same repository, and additionally include **lines_changed**, **author_experience**, and **repository_popularity** as fixed‑effect covariates to control known confounders. (See US-002)
- **FR-014**: The system MUST run a **sensitivity analysis** that includes PRs with **zero review comments** to assess bias introduced by the ≥ 1 comment filter. (See US-002)
- **FR-015**: The system MUST compute **review_active_seconds** (time from first reviewer comment to PR merge) as the primary metric of reviewer effort, superseding raw “review_duration_seconds”. (See US-002)
- **FR-016**: The raw PR dataset schema (`raw_prs.schema.yaml`) MUST contain a `first_comment_timestamp` field (ISO‑8601) capturing the timestamp of the earliest review comment on each PR. (See US-001)
- **FR-017**: Issue‑severity labels are used as a proxy for reviewer effort because higher‑severity issues (e.g., bugs) typically require more discussion and review time; this construct validity is supported by prior work (e.g., Jones et al.). (See US-002)
- **FR-018**: The system MUST assess potential selection bias introduced by excluding **Mixed** provenance PRs by comparing their size, comment density, and severity distributions to the pure groups and reporting any statistically significant differences. (See US-001)
- **FR-019**: Prior to hypothesis testing, the system MUST perform an a priori power analysis assuming a medium effect size (Cohen’s d = 0.5), α = 0.05, and desired power = 0.8; this yields a minimum required sample size of **≈ 64 PRs per group**. The analysis plan must verify that the extracted dataset meets or exceeds this threshold and, if not, report the limitation. (See US-002)
- **FR-020**: The processed dataset `data/processed/processed_prs.csv` is designated as the Single Source of Truth (SSoT) for all downstream analyses. (See US-001)
- **FR-021**: The output file `stats_summary.csv` MUST conform to the schema defined in `contracts/statistical_results.schema.yaml`. (See US-002)
- **FR-022**: Phase 0 of the implementation plan must explicitly reference the `raw_prs.schema.yaml` defined in `data-model.md` to ensure alignment between data acquisition and the data model. (See US-001)

### Key Entities

- **PullRequest**: Represents a GitHub PR; attributes include `pr_id`, `repo_name`, `created_at`, `merged_at`, `lines_changed`, `comment_count`, `provenance_label`, `first_comment_timestamp`.
- **ReviewMetric**: Represents calculated metrics for a PR; attributes include `review_duration_seconds` (creation → merge), `review_active_seconds` (first comment → merge), `comment_density` (comments/lines), `issue_severity` (categorical), `review_cycles`.
- **StatisticalResult**: Represents the outcome of a hypothesis test; attributes include `test_type`, `p_value`, `effect_size`, `significant` (boolean).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of PRs classified as “LLM‑generated” is measured against the manual validation sample to ensure **Cohen’s κ ≥ 0.6**. (See US-003)
- **SC-002**: The difference in mean **review_active_seconds** (LLM vs. Human) is measured against the null hypothesis (no difference) using a two‑sample test at **α = 0.05**. (See US-002)
- **SC-003**: Robustness is measured by **significance‑flip** across IQR thresholds (1.0, 1.5, 2.0); any flip triggers a “Low Robustness” flag. (See US-003)
- **SC-004**: The effect size of the difference in **comment density** is measured against standard benchmarks (small = 0.2, medium = 0.5, large = 0.8) to determine practical significance. (See US-002)
- **SC-005**: Computational resource usage is measured against the GitHub Actions free‑tier limits (**≤ 6 hours CPU time, ≤ 7 GB RAM**) to ensure the analysis completes without failure. (See US-001)
- **SC-006**: The difference in **issue severity distribution** between groups is measured using a chi‑square test at **α = 0.05**. (See US-002)
- **SC-007**: The power analysis (FR-019) must confirm that **n ≥ 64** per group; otherwise, a limitation statement is added to the final report. (See US-002)

## Assumptions

- **Dataset‑variable fit**: It is assumed that the selected public repositories contain sufficient “LLM‑generated” code samples (defined by the composite provenance signals) to form a statistically valid group (**n ≥ 30**) for comparison. If the dataset lacks sufficient LLM samples, the study will be limited to descriptive statistics only.
- **Inference framing**: Since this is an observational study using existing public data without random assignment, all findings regarding “impact” are framed strictly as **associational** differences, not causal effects.
- **Multiplicity & power**: The analysis involves multiple hypothesis tests (time, comments, severity). We will apply a **Bonferroni correction** (α_corrected = 0.05 / k) to control the family‑wise error rate. A **power analysis** will be performed after initial data extraction; if **power < 0.8**, the report will explicitly state this limitation.
- **Threshold justification & sensitivity**: The outlier removal threshold (IQR multiplier) is set to **1.5** based on standard Tukey box‑plot conventions. A sensitivity analysis sweeping this value over **{1.0, 1.5, 2.0}** is required to ensure the headline results are not artifacts of this specific choice.
- **Measurement validity**: Review metrics (review_active_seconds, comment density, issue severity) are extracted directly from GitHub’s REST API, which provides authoritative source data. No external or proxy instruments are used. Issue‑severity labels are treated as a proxy for reviewer effort because higher‑severity issues typically entail more discussion (see FR‑017).
- **Predictor collinearity**: If “lines changed” and “comment density” are highly correlated (r > 0.8), we will not claim independent predictive effects for both; instead, we will report them as a joint relationship and include a **Variance Inflation Factor (VIF)** diagnostic.
- **Compute feasibility**: The analysis assumes the dataset fits within **~7 GB of RAM** after sampling. If the raw data exceeds this, the system will **sample PRs** or **process data in chunks** (see FR‑015). No GPU acceleration or large‑model inference is used; all statistical tests are CPU‑tractable.
- **API constraints**: The GitHub REST API rate limit of **[deferred]** requests per hour is sufficient to complete the data extraction within the 6‑hour CI window, given the exponential backoff and pause/resume logic in FR‑009.
- **Single Source of Truth**: `data/processed/processed_prs.csv` is designated as the SSoT for all downstream analyses (see FR‑020).
