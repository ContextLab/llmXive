# Feature Specification: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Feature Branch**: `001-evaluating-llm-cognitive-load`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research pipeline must successfully ingest public GitHub Pull Request (PR) metadata from a curated list of repositories, identifying which projects utilize LLM code completion tools and extracting the specific code review metrics (comment length, iteration count, revert frequency) required for analysis.

**Why this priority**: This is the foundational step; without reliable data extraction and the ability to distinguish LLM-adopting projects from control groups, no statistical analysis can occur. It delivers the raw dataset necessary for the entire study.

**Independent Test**: Can be fully tested by running the data ingestion script against a fixed, small subset of 5 known repositories (3 with LLM config, 2 without) and verifying that the output CSV contains the correct number of rows, the binary `llm_adopted` flag is correctly set, and the numeric metrics are populated without nulls. The test must confirm that repositories with <10 PRs are ingested into the raw dataset but flagged for exclusion from the analysis subset.

**Acceptance Scenarios**:

1. **Given** a list of 5 repository URLs where 3 have `.cursorrules` or `copilot` config, **When** the pipeline runs, **Then** the output dataset must contain 3 rows marked `llm_adopted=true` and 2 rows marked `llm_adopted=false`.
2. **Given** a repository with PRs containing varying comment lengths, **When** the pipeline extracts data, **Then** the `comment_length_chars` column must contain integer values ≥ 0 for every PR row.
3. **Given** a repository with no PRs, **When** the pipeline runs, **Then** it must log a warning and skip the repository rather than crashing the entire job.
4. **Given** a repository with < 10 PRs, **When** the pipeline runs, **Then** the repository is included in the raw dataset but marked with `exclude_from_analysis=true`.

---

### User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

The system must execute a propensity score matching (PSM) procedure to balance covariates between LLM-adopted and control groups, followed by a linear regression analysis to test the null hypothesis that LLM tool usage has no effect on cognitive load proxies, controlling for project size, team size, and domain complexity, and output the regression coefficients with 95% confidence intervals.

**Why this priority**: This is the core research activity that directly answers the research question. It transforms raw data into evidence regarding the relationship between LLM usage and cognitive load proxies, while mitigating selection bias.

**Independent Test**: Can be fully tested by running the analysis script on the preprocessed dataset from User Story 1 and verifying that: (1) the PSM step produces matched pairs with a standardized mean difference < 0.1 for all covariates, (2) the output JSON includes a regression table with coefficients, p-values, and confidence intervals for the `llm_adopted` variable, and (3) the script completes within the 6-hour CPU limit (asserting duration ≤ 6 hours).

**Acceptance Scenarios**:

1. **Given** a dataset with >100 PRs, **When** the regression model runs, **Then** the output must include a coefficient estimate and p-value for the `llm_adopted` predictor.
2. **Given** a dataset where `lines_of_code` varies significantly, **When** the model runs, **Then** `lines_of_code` must be included as a control variable in the regression equation.
3. **Given** a model that fails to converge (e.g., due to multicollinearity), **When** the script runs, **Then** it must automatically switch to Ridge Regression and log the switch, preventing the generation of invalid results.

---

### User Story 3 - Sensitivity Analysis and Reporting (Priority: P3)

The system must perform a sensitivity analysis by varying key thresholds (e.g., minimum PR size) and stratifying the analysis by programming language and repository age, generating a summary report visualizing how the effect size of LLM usage changes across these variations, ensuring the findings are robust.

**Why this priority**: This addresses the methodological soundness requirement for threshold justification and sensitivity. It ensures the results are not artifacts of arbitrary data choices or confounding variables, increasing the validity of the research.

**Independent Test**: Can be fully tested by running the sensitivity module with a predefined set of 3 alternative parameter values and verifying that the output includes a plot or table showing the variation in the primary effect size metric across language and age strata.

**Acceptance Scenarios**:

1. **Given** the primary regression result, **When** the sensitivity analysis runs with a ±10% variation in the `min_pr_lines` threshold, **Then** the output must report the new effect size for each variation.
2. **Given** the analysis results, **When** the report is generated, **Then** it must include a visual comparison (e.g., a line plot or table) of the primary coefficient across all tested sensitivity scenarios (including language and age strata).
3. **Given** a scenario where the effect size flips sign across thresholds, **When** the report is generated, **Then** it must flag this instability with a "High Sensitivity" warning in the summary.

### Edge Cases

- What happens if a repository's configuration file is ambiguous (e.g., mentions "AI" but not a specific LLM tool)? The system must default to `llm_adopted=false` and log the specific file content for manual review.
- How does the system handle repositories with < 10 PRs? The system must ingest them into the raw dataset but exclude them from the regression analysis to prevent statistical noise from dominating the results.
- What if the GitHub API rate limit is hit during data extraction? The system must implement a retry mechanism with exponential backoff (a limited number of attempts) before failing the specific repository fetch.
- What constitutes a 'revert'? A PR is counted as a revert if it was merged and subsequently reverted (merged a revert PR) within 7 days of the original merge.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download PR metadata from GitHub for a curated list of ≥ 50 repositories, extracting `comment_length`, `iteration_count`, and `revert_frequency` (See US-1).
- **FR-002**: The system MUST identify LLM adoption by scanning repository roots for `.cursorrules`, `copilot` config files, OR scanning PR commit messages and comments for case-insensitive keywords ('copilot', 'cursor', 'codium', 'tabnine'), assigning a binary `llm_adopted` flag (See US-1).
- **FR-003**: The system MUST execute a linear regression model with `llm_adopted` as the predictor and cognitive load proxies as outcomes, controlling for `lines_of_code`, `contributor_count`, and `domain_complexity` (defined as log10(lines_of_code) + log10(contributor_count) + 1) (See US-2).
- **FR-004**: The system MUST calculate and report 95% confidence intervals for all regression coefficients to assess statistical significance (See US-2).
- **FR-005**: The system MUST perform a sensitivity analysis sweeping at least 3 distinct values for data inclusion thresholds AND stratifying the analysis by the top 3 programming languages and repository age (median split), reporting the variation in the primary effect size (See US-3).
- **FR-006**: The system MUST perform Propensity Score Matching (PSM) to balance covariates between LLM-adopted and control groups before regression, ensuring a standardized mean difference < 0.1 for all covariates (See US-2).
- **FR-007**: The system MUST validate the theoretical link between proxies and cognitive load by reporting the correlation between `iteration_count` and `lines_of_code` to assess construct validity (See Assumptions).
- **FR-008**: The system MUST check Variance Inflation Factors (VIF) for all control variables; if any VIF ≥ 5, the system MUST automatically switch to Ridge Regression with alpha=1.0 and log the switch (See US-2).

### Key Entities

- **Repository**: Represents a GitHub project, attributes include `repo_id`, `llm_adopted` (binary), `lines_of_code`, `contributor_count`, `domain_complexity` (calculated).
- **PullRequest**: Represents a single PR, attributes include `pr_id`, `comment_length_chars`, `iteration_count`, `revert_frequency` (count of merged PRs reverted within 7 days), `repo_id` (foreign key), `exclude_from_analysis` (boolean).
- **AnalysisResult**: Represents the output of the statistical model, attributes include `coefficient`, `p_value`, `confidence_interval`, `sensitivity_flags`, `matching_quality_score`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The primary effect size (regression coefficient for `llm_adopted`) is measured against the null hypothesis value of 0.0 to determine statistical significance (See US-2).
- **SC-002**: The stability of the primary effect size is measured against the variation observed in the sensitivity analysis across multiple distinct threshold settings and language/age strata. (See US-3).
- **SC-003**: The computational feasibility is measured against the constraint of completing the full analysis (ingestion, PSM, regression, sensitivity) within 6 hours on a 2-core CPU runner (See US-2).
- **SC-004**: The data coverage is measured against the requirement to successfully process ≥ 80% of the target curated list (defined in `target_repos.json`) without critical errors (HTTP 4xx/5xx after 3 retries or timeout > 60s) (See US-1).
- **SC-005**: The validity of the matching process is measured against the requirement that the standardized mean difference for all covariates is < 0.1 after Propensity Score Matching (See US-2).

## Assumptions

- The public GitHub API rate limits are sufficient to extract the required metadata for the curated list within the 6-hour window.
- **Theoretical Framework**: The definition of "cognitive load" is proxied by code review metrics (comment length, iteration count, revert frequency) based on established Software Engineering research (e.g., iteration count as a proxy for review friction/effort). Self-report scales (NASA-TLX) and physiological proxies are out of scope for this public-data study.
- The presence of `.cursorrules`, `copilot` config files, OR commit messages containing specific LLM keywords is a reliable indicator of active LLM code completion usage in the professional workflow.
- The dataset fits within the RAM and disk constraints of the free-tier GitHub Actions runner without requiring chunking or external storage.
- The analysis is observational; therefore, all reported relationships will be framed as associational, not causal, despite the use of PSM to reduce selection bias.
- The 'target curated list' is defined in a separate `target_repos.json` file.
