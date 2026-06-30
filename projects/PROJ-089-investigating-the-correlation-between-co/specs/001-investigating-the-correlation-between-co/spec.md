# Feature Specification: Investigating the Correlation Between Code Churn and Technical Debt

**Feature Branch**: `001-code-churn-technical-debt`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Code Churn and Technical Debt"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system must be able to automatically select a representative set of open-source repositories, clone them, and extract raw metrics for code churn (git history) and technical debt (static analysis) into a unified, queryable format.

**Why this priority**: This is the foundational step. Without reliable, normalized data from multiple projects, no correlation analysis can be performed. It validates the feasibility of the data pipeline on the CI runner.

**Independent Test**: Can be fully tested by running the data extraction script against a small, fixed set of 3 public repositories and verifying that the output CSV contains non-null rows for both churn and debt metrics for every file.

**Acceptance Scenarios**:

1. **Given** a list of 50+ GitHub repository URLs with >500 stars and >2 years of history, **When** the data extraction pipeline runs, **Then** it successfully clones each repo, extracts commit counts/lines changed per file, runs a static analysis tool (e.g., `radon` or `sonar-scanner` in CLI mode), and outputs a single CSV with columns for `repo_id`, `file_path`, `churn_count`, `debt_score`, and `loc`.
2. **Given** a repository with binary files or non-code assets, **When** the extraction pipeline runs, **Then** it filters out non-source-code files (e.g., images, binaries) based on file extension before calculating metrics, ensuring the CSV only contains valid code files.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The system must calculate the correlation between churn density and debt density across all files, controlling for confounding variables, and determine statistical significance.

**Why this priority**: This is the core research activity. It transforms the raw data from Story 1 into the primary research finding (the correlation coefficient and p-value).

**Independent Test**: Can be tested by feeding the pipeline a pre-generated CSV with known correlation properties (e.g., a synthetic dataset with a known r=0.5) and verifying the output reports a correlation coefficient within ±0.05 of the expected value and a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** a unified dataset of files with `churn_density` and `debt_density`, **When** the analysis script executes, **Then** it computes both Pearson and Spearman correlation coefficients and reports the p-value, flagging results where p < 0.05 as statistically significant.
2. **Given** a dataset where `project_age` or `language` varies significantly, **When** the analysis runs, **Then** it performs a partial correlation or regression analysis to control for these confounders, outputting a adjusted correlation coefficient that isolates the churn-debt relationship.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system must generate scatter plots with regression lines and a summary report summarizing the findings across all analyzed repositories.

**Why this priority**: This delivers the final interpretability of the research, allowing stakeholders to visually verify the relationship and understand the aggregate results.

**Independent Test**: Can be tested by running the analysis on a sample dataset and verifying that the output directory contains a PNG file for the scatter plot and a text/CSV summary file with the headline statistics.

**Acceptance Scenarios**:

1. **Given** the results of the correlation analysis, **When** the reporting module runs, **Then** it generates a scatter plot where the X-axis is churn density, the Y-axis is debt density, and a regression line is overlaid with the correlation coefficient (r) and p-value annotated on the chart.
2. **Given** multiple repositories analyzed, **When** the summary report is generated, **Then** it lists the correlation strength (weak/moderate/strong) and significance for each repository individually and provides an aggregate weighted average across the entire dataset.

### Edge Cases

- **What happens when** a repository has no commit history in the last 2 years? (System must skip or flag it as invalid per the >2 years filter).
- **How does the system handle** a repository where the static analysis tool fails (e.g., due to unsupported language)? (System must log the error, exclude the specific repo from the correlation calculation, and continue processing others without crashing).
- **What happens when** a file has zero lines of code (LOC)? (System must exclude it from density calculations to avoid division-by-zero errors).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract code churn metrics (commits, lines changed) per file for all files in repositories with >2 years of history (See US-1) [NEEDS CLARIFICATION: Does the dataset contain a specific "lines of code" baseline for the start of the 2-year window, or should we use the current LOC as the denominator?].
- **FR-002**: System MUST calculate technical debt density (code smells/complexity per line of code) using a CPU-tractable static analysis tool (See US-1) [NEEDS CLARIFICATION: Should we use `radon` (Python-only) or a language-agnostic tool like `SonarQube` CLI, and does the dataset contain all target languages supported by the chosen tool?].
- **FR-003**: System MUST perform both Pearson and Spearman correlation calculations to assess linear and monotonic relationships between churn density and debt density (See US-2).
- **FR-004**: System MUST control for confounding variables (project age, programming language, contributor count) by including them as covariates in a partial correlation or regression model (See US-2).
- **FR-005**: System MUST generate a scatter plot visualization with a regression line and annotate it with the correlation coefficient (r) and p-value (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) if aggregating p-values across >10 independent repositories to control family-wise error rate (See US-2).
- **FR-007**: System MUST exclude files with <10 lines of code from the analysis to ensure measurement validity of density metrics (See US-1).

### Key Entities

- **Repository**: An open-source project on GitHub identified by URL, containing metadata (stars, age, language).
- **FileMetric**: A record linking a specific file to its churn density (commits/LOC) and debt density (smells/LOC).
- **CorrelationResult**: A statistical output containing the correlation coefficient (r), p-value, and sample size (n) for a specific repository or the aggregate.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation coefficient (r) between churn density and debt density is measured against the hypothesis of a moderate positive correlation (r ≥ 0.3) (See FR-003, FR-004) [NEEDS CLARIFICATION: Is the threshold r ≥ 0.3 considered "moderate" for this specific domain, or should we reference a standard software engineering benchmark?].
- **SC-002**: The statistical significance (p-value) is measured against the alpha level of 0.05 to confirm the relationship is not due to chance (See FR-003, FR-004).
- **SC-003**: The analysis pipeline completes within the 6-hour GitHub Actions free-tier time limit on a CPU-only runner with ≤7GB RAM (See FR-001, FR-002).
- **SC-004**: The false-positive rate for significant correlations is measured against the family-wise error rate (controlled via Bonferroni or similar) when testing across multiple repositories (See FR-006).
- **SC-005**: The measurement validity of debt density is confirmed by verifying that the static analysis tool used has a documented validation study or is a widely accepted industry standard (See FR-002).

## Assumptions

- **Assumption about data**: The selected GitHub repositories (stars > 500) contain sufficient commit history (≥2 years) and are written in languages supported by the chosen CPU-tractable static analysis tool (e.g., Python, Java, JavaScript).
- **Assumption about methodology**: Code churn (frequency of changes) is a valid proxy for code instability and that static analysis metrics (code smells, complexity) are valid proxies for technical debt, as supported by the related work citations.
- **Assumption about compute**: The total dataset size (50-100 repos) and the chosen static analysis tools will fit within the 7GB RAM and 14GB disk constraints of the GitHub Actions free runner without requiring GPU acceleration.
- **Assumption about confounders**: Project age, programming language, and team size are the primary confounding variables that need to be controlled; other factors (e.g., developer experience, documentation quality) are assumed to be negligible or unmeasurable for this scope.
- **Assumption about threshold**: A correlation coefficient of r ≥ 0.3 is considered a "moderate" effect size sufficient to validate the hypothesis in this context, based on general statistical conventions in empirical software engineering.
