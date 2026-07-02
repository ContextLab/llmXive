# Feature Specification: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Feature Branch**: `001-evaluating-the-impact-of-llm-based-code-completion`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and LLM Adoption Classification (Priority: P1)

The system must identify a corpus of GitHub repositories with documented LLM code completion tool usage and extract their pull request metadata to establish the independent variable (LLM adoption) and dependent variables (cognitive load proxies).

**Why this priority**: Without a validated dataset linking specific repositories to LLM tool usage and their corresponding review metrics, no analysis can be performed. This is the foundational data layer for the entire study.

**Independent Test**: The system can be tested by running the ingestion script against a known subset of repositories (some with `.cursorrules` or copilot configs, others without) and verifying that the output CSV correctly flags the LLM adoption status and contains non-empty rows for review comment length, iteration counts, review thread depth, and revert frequencies.

**Acceptance Scenarios**:

1. **Given** a list of 50 target repositories with public access, **When** the ingestion script executes, **Then** it produces a master dataset where every row includes a binary `llm_adoption_flag`, `avg_comment_length`, `iteration_count`, `review_thread_depth`, and `revert_frequency`.
2. **Given** a repository with a `.cursorrules` file in the root directory, **When** the ingestion script processes it, **Then** the `llm_adoption_flag` is set to `1` (True).
3. **Given** a repository with no LLM configuration files or documentation mentions, **When** the ingestion script processes it, **Then** the `llm_adoption_flag` is set to `0` (False).
4. **Given** a repository where ≥5% of commit messages contain "Copilot" or "LLM", **When** the ingestion script processes it, **Then** the `llm_adoption_flag` is set to `1` (True) to capture IDE plugin usage without config files.

### User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

The system must compute regression models to test the association between LLM adoption and cognitive load proxies, controlling for project size, team size, and domain complexity, while applying multiple-comparison corrections.

**Why this priority**: This transforms the raw data into the research findings. It directly addresses the research question by quantifying the relationship between the predictor and outcomes.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the correlation between `llm_adoption_flag` and `avg_comment_length` is hardcoded to a known value (e.g., 0.5). The output must report a statistically significant coefficient matching the synthetic input within a 95% confidence interval.

**Acceptance Scenarios**:

1. **Given** the master dataset with ≥ 40 valid repository entries, **When** the analysis script runs, **Then** it outputs a regression table showing coefficients, standard errors, and p-values for the `llm_adoption_flag` predictor across all cognitive load proxies (comment length, iteration count, thread depth, revert frequency).
2. **Given** that four hypothesis tests are performed (one for each proxy), **When** the analysis script completes, **Then** it applies a Bonferroni correction (or equivalent family-wise error rate control) and reports adjusted p-values.
3. **Given** a regression model, **When** the script executes, **Then** it outputs a sensitivity analysis report showing how the headline effect size varies when the `iteration_count` threshold is swept across values {1, 2, 3}.

### User Story 3 - Visualization and Reporting (Priority: P3)

The system must generate publication-ready visualizations (effect size plots with 95% confidence intervals) and a summary report detailing the findings, limitations, and sensitivity analysis results.

**Why this priority**: This delivers the final artifact for the research community, making the results interpretable and transparent regarding the study's constraints and robustness.

**Independent Test**: The system can be tested by verifying that the generated PDF/HTML report contains a forest plot of effect sizes and that the text explicitly states the null hypothesis rejection status for each proxy based on the corrected p-values.

**Acceptance Scenarios**:

1. **Given** the statistical analysis results, **When** the reporting module runs, **Then** it generates a figure showing the effect size of LLM adoption on `avg_comment_length` with error bars representing the 95% confidence interval.
2. **Given** the sensitivity analysis data, **When** the reporting module runs, **Then** it includes a table or plot demonstrating the variation in false-positive rates or effect estimates across the tested threshold sweep.
3. **Given** the final dataset, **When** the report is generated, **Then** it explicitly frames all findings as "associational" rather than causal, citing the observational nature of the data.

### Edge Cases

- **What happens when** a repository has LLM configuration files but no pull requests in the last 12 months? The system must exclude such repositories from the analysis to avoid zero-variance outcomes in the dependent variables.
- **How does the system handle** repositories where the LLM configuration is ambiguous (e.g., a generic `config.json` without clear tool naming)? The system must default to `llm_adoption_flag = 0` and log the repository ID for manual review, ensuring no false positives inflate the treatment group.
- **What happens when** the GitHub API rate limit is hit during data ingestion? The system must implement a retry mechanism with exponential backoff, attempting up to 5 retries with a 60-second delay between attempts before failing the job.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST identify repositories with LLM code completion tools by parsing configuration files (e.g., `.cursorrules`, `copilot` config) and explicit documentation mentions. A mention is defined as a string match for "Copilot" or "LLM" within 500 characters of the phrase in `README.md` or `CONTRIBUTING.md`. Additionally, if ≥5% of commit messages in the last 12 months contain "Copilot" or "LLM", the system MUST classify the repository as `1` (adopted) to capture IDE plugin usage without config files. Otherwise, it classifies as `0` (See User Story 1).
- **FR-002**: The system MUST extract pull request metadata including comment length (characters), review thread depth (max nested comments), revert frequency, and iteration count. The `iteration_count` is derived as the count of push events between PR open and merge, EXCLUDING any push event where the commit message contains "Copilot" OR the diff size is < 100 lines (to exclude auto-generated/accept-only updates). This ensures the metric captures human review iterations distinct from LLM output (See User Story 1).
- **FR-003**: The system MUST perform linear regression analysis with `llm_adoption_flag` as the independent variable and the cognitive load proxies (comment length, iteration count, review thread depth, revert frequency) as dependent variables. The model MUST control for project size (lines of code), team size (contributor count), and domain complexity. Domain complexity is defined as the sum of unique programming languages detected in the repo and the count of top-level dependencies (from `package.json`, `requirements.txt`, `go.mod`, etc.; default to 0 if no manifest exists) (See User Story 2).
- **FR-004**: The system MUST apply a multiple-comparison correction (e.g., Bonferroni) to the p-values of the hypothesis tests to control the family-wise error rate (See User Story 2).
- **FR-005**: The system MUST execute a sensitivity analysis sweeping the `iteration_count` definition threshold over the set {1, 2, 3} and report the resulting variation in effect estimates (See User Story 2).
- **FR-006**: The system MUST generate a final report containing effect size plots with 95% confidence intervals and a textual summary explicitly framing findings as associational (See User Story 3).

### Key Entities

- **Repository**: Represents a GitHub project, characterized by `repo_id`, `llm_adoption_flag`, `lines_of_code`, `contributor_count`, and `domain_complexity`.
- **PullRequest**: Represents a single pull request within a repository, characterized by `pr_id`, `comment_length`, `iteration_count`, `review_thread_depth`, and `reverted` (boolean).
- **AnalysisResult**: Represents the output of the statistical test, characterized by `coefficient`, `standard_error`, `p_value`, `adjusted_p_value`, and `confidence_interval`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The dataset validity is measured against the requirement that every included repository has ≥ 10 pull requests in the last 12 months relative to the data ingestion date to ensure statistical power for proxy calculation (See User Story 1).
- **SC-002**: The statistical validity is measured against the requirement that the regression model includes control variables for project size, team size, and domain complexity (defined as unique languages + dependency count) to isolate the effect of LLM adoption (See User Story 2).
- **SC-003**: The methodological rigor is measured against the requirement that a multiple-comparison correction is applied to the p-values of the hypothesis tests to prevent Type I error inflation (See User Story 2).
- **SC-004**: The robustness is measured against the requirement that the sensitivity analysis sweeps the `iteration_count` threshold over at least 3 distinct values and reports the variation in effect size (See User Story 2).
- **SC-005**: The interpretability is measured against the requirement that the final report explicitly states that findings are associational and not causal, referencing the observational study design (See User Story 3).

## Assumptions

- **Dataset-variable fit**: The GitHub API public data contains sufficient metadata (comment text, update timestamps, merge/revert status) to derive the required cognitive load proxies (comment length, iteration count, review thread depth, revert frequency). If a repository lacks sufficient PR history, it will be excluded.
- **Inference framing**: Since the study relies on observational data (no random assignment of LLM tools), all conclusions regarding the relationship between LLM adoption and cognitive load proxies will be framed strictly as associational, not causal.
- **Compute feasibility**: The analysis will run on a CPU-only environment (GitHub Actions free tier) using Python's `scikit-learn` and `statsmodels` libraries on a sampled dataset of ≤ 50 repositories, ensuring the total runtime does not exceed 6 hours and memory usage stays within 7 GB.
- **Threshold justification**: The `iteration_count` threshold (defining what constitutes an "iteration") is set to a default of 1 update cycle for the primary analysis, justified by the standard definition of a PR update in GitHub's event model (See GitHub PR Event Documentation). A sensitivity analysis will sweep this value to {2, 3} to test robustness.
- **Measurement validity**: The proxies (comment length, iteration count, review thread depth, revert frequency) are assumed to be valid operationalizations of "cognitive load" in professional workflows, based on the theoretical bridge that "review friction" and "iteration patterns" reflect the cognitive effort required to process and integrate code changes. This acknowledges that self-report scales (e.g., NASA-TLX) are not available in public metadata, and these proxies serve as observable behavioral correlates of cognitive load.
- **Predictor collinearity**: The control variables (lines of code, contributor count) are assumed to be distinct from the LLM adoption flag, but a collinearity diagnostic (Variance Inflation Factor) will be computed to ensure no definitionally related predictors distort the regression coefficients.