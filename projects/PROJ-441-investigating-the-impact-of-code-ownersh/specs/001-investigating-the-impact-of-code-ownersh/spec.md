# Feature Specification: Investigating the Impact of Code Ownership on LLM Code Understanding

**Feature Branch**: `001-code-ownership-llm-understanding`  
**Created**: 2026-07-02  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Code Ownership on LLM Code Understanding"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Socio-Technical Ownership Metrics (Priority: P1)

The research pipeline MUST successfully extract quantitative ownership metrics (e.g., Gini coefficient of commit distribution, developer turnover rates) from a curated set of open-source repositories (Java/Python) using git history analysis tools.

**Why this priority**: This is the foundational predictor variable generation. Without accurate ownership metrics, no correlation analysis with LLM performance is possible. It is the first independent step in the research workflow.

**Independent Test**: The system can be tested by running the extraction script on a known small repository and verifying the output JSON contains valid, non-null values for the Gini coefficient and commit counts, matching manual `git shortlog` verification.

**Acceptance Scenarios**:

1. **Given** a valid GitHub repository URL with complete git history, **When** the extraction script runs, **Then** it outputs a JSON file containing the calculated Gini coefficient for commit distribution and total unique developer count.
2. **Given** a repository where a single author contributes ≥ 90% of the total commits, **When** the script calculates the Gini coefficient, **Then** the result is ≥ 0.90.
3. **Given** a repository with a uniform distribution of commits across ≥ 10 authors (each holding ≤ 10% of commits), **When** the script calculates the Gini coefficient, **Then** the result is ≤ 0.20.

---

### User Story 2 - Compute Code Complexity and Documentation Controls (Priority: P2)

The research pipeline MUST calculate code complexity (cyclomatic complexity) and documentation density (comment-to-code ratio) for the same code snippets used in the ownership analysis to serve as control variables.

**Why this priority**: To isolate the effect of ownership, the model must statistically control for static code properties. If these controls are missing, the regression analysis cannot distinguish between ownership effects and general code complexity effects.

**Independent Test**: The system can be tested by running the complexity analyzer on a known code snippet and verifying the cyclomatic complexity score matches the output of the `radon` or `lizard` CLI tool.

**Acceptance Scenarios**:

1. **Given** a Python function with multiple nested loops and conditionals, **When** the complexity tool runs, **Then** the cyclomatic complexity score is ≥ 5.
2. **Given** a code file with 100 lines of code and 20 lines of comments, **When** the documentation density is calculated, **Then** the ratio is exactly 0.20.
3. **Given** a code file with zero comments, **When** the documentation density is calculated, **Then** the ratio is 0.0.

---

### User Story 3 - Execute LLM Inference and Statistical Correlation (Priority: P3)

The research pipeline MUST run a lightweight open-weight LLM (e.g., StarCoder2-3B, 4-bit quantized) on code snippets extracted from the original repositories of the CodeXGLUE dataset to generate comprehension scores (BLEU), and perform a multiple linear regression where the unit of analysis is the repository (n ≥ 30).

**Why this priority**: This is the core hypothesis test. It delivers the final research result (the regression coefficient) answering the primary research question.

**Independent Test**: The system can be tested by running the full pipeline on a representative subset of repositories and verifying that the output includes a regression summary table with p-values for the ownership coefficient.

**Acceptance Scenarios**:

1. **Given** a dataset of 30 repositories with associated ownership and complexity metrics, **When** the regression analysis runs, **Then** it outputs a p-value for the "Gini Coefficient" predictor.
2. **Given** a null hypothesis that ownership has no effect, **When** the p-value is < 0.05, **Then** the system flags the result as "Statistically Significant."
3. **Given** the memory constraint of the CI runner, **When** the full pipeline (inference + analysis) runs on the sampled dataset (30 repos, 5 snippets each), **Then** the process completes without OOM (Out of Memory) errors and finishes within 6 hours.

---

### Edge Cases

- **What happens when** a repository has no git history (e.g., initial commit only)? **Then** the ownership metrics are set to `null` and the repository is excluded from the regression analysis.
- **How does the system handle** a repository where the language is neither Java nor Python? **Then** the script skips the complexity calculation for that file and logs a warning, excluding it from the final dataset.
- **What happens when** the LLM inference times out or hangs? **Then** the system retries the inference up to 2 times; if it fails again, the specific sample is marked as "Failed Inference" and excluded from the statistical model.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract the Gini coefficient of commit distribution and unique developer count from git logs for each target repository (See US-1).
- **FR-002**: System MUST calculate cyclomatic complexity using `radon` or `lizard` and documentation density (comment lines / total lines) for every code snippet (See US-2).
- **FR-003**: System MUST execute inference on a CPU-tractable open-weight model (StarCoder2-3B, 4-bit quantized) on code snippets derived from CodeXGLUE-origin repositories, using the Code-to-Text task ground truth pairs for evaluation (See US-3).
- **FR-004**: System MUST perform a multiple linear regression where the dependent variable is LLM performance (BLEU score) and independent variables are repository-level ownership metrics, average snippet complexity, and average documentation density (See US-3).
- **FR-005**: System MUST filter out samples where the LLM inference fails or times out after 2 retries before running the statistical analysis (See US-3).
- **FR-006**: System MUST apply a Bonferroni correction or False Discovery Rate (FDR) adjustment if multiple hypothesis tests are run across different code languages or model variants (See US-3).
- **FR-007**: System MUST output a sensitivity analysis report sweeping the 'Gini aggregation window' (e.g., last 100 vs last 500 commits) over values {100, 500} to demonstrate result stability (See US-3).

### Key Entities

- **RepositorySnapshot**: Represents a specific version of a code repository, containing attributes: `repo_url`, `git_history_hash`, `language`.
- **OwnershipMetrics**: Represents the socio-technical properties of a snapshot, containing attributes: `gini_coefficient`, `developer_count`, `max_author_share`.
- **CodeSnippet**: Represents a unit of code analyzed, containing attributes: `file_path`, `cyclomatic_complexity`, `documentation_density`, `snippet_id`, `ground_truth_pair`.
- **PerformanceScore**: Represents the LLM evaluation result, containing attributes: `snippet_id`, `model_id`, `score` (e.g., BLEU, Accuracy), `ground_truth`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between ownership fragmentation and LLM error rates is measured against the null hypothesis of zero correlation using `scipy.stats` regression (See US-3).
- **SC-002**: The statistical significance (p-value) of the ownership metric in the regression model is measured against the standard alpha threshold of 0.05 (See US-3).
- **SC-003**: The stability of the regression coefficient is measured against the sensitivity analysis sweep of the 'Gini aggregation window' over the set {100, 500} (See US-3).
- **SC-004**: The computational feasibility is measured against the CI runner constraints: total runtime ≤ 6 hours, memory usage ≤ 7 GB, and zero GPU dependency (See US-3).
- **SC-005**: The validity of the control variables is measured by ensuring the variance inflation factor (VIF) for complexity and ownership metrics is < 5, indicating low collinearity (See US-3).

## Assumptions

- **Assumption about data source**: The selected open-source repositories (Java/Python) have complete, accessible git history that can be cloned via standard `git clone` commands without authentication tokens.
- **Assumption about model feasibility**: The StarCoder2-3B model (4-bit quantized) can perform inference on a 2-core CPU runner within 6 hours for a dataset of 30 repositories (max 5 snippets per repository, total 150 snippets).
- **Assumption about methodology**: The relationship between code ownership and LLM performance is primarily linear or monotonic, justifying the use of multiple linear regression as the primary analytical tool.
- **Assumption about CodeXGLUE**: The CodeXGLUE "Code-to-Text" ground truth dataset provides valid input/output pairs for the extracted code snippets from the original repositories, allowing for BLEU score calculation.
- **Assumption about measurement validity**: The Gini coefficient of commit distribution is a valid and accepted proxy for "ownership concentration" in the software engineering literature, as cited in the literature gap analysis.
- **Assumption about collinearity**: While ownership and complexity may be related, they are distinct enough that the Variance Inflation Factor (VIF) will remain below 5, allowing for independent coefficient estimation.
- **Assumption about unit of analysis**: The statistical power of the regression (n ≥ 30) is achieved by treating the Repository as the unit of analysis, not individual snippets.