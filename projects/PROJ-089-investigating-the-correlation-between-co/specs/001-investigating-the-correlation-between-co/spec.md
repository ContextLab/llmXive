# Feature Specification: Investigating the Correlation Between Code Churn and Technical Debt

**Feature Branch**: `001-code-churn-technical-debt`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Code Churn and Technical Debt"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

The system must be able to automatically select a representative set of open-source repositories, clone them, and extract raw metrics for code churn (git history) and technical debt (static analysis) into a unified, queryable format.

**Why this priority**: This is the foundational step. Without reliable, normalized data from multiple projects, no correlation analysis can be performed. It validates the feasibility of the data pipeline on the CI runner.

**Independent Test**: Can be fully tested by running the data extraction script against a small, fixed set of public repositories and verifying that the output CSV contains non-null rows for both churn and debt metrics for every file.

**Acceptance Scenarios**:

1. **Given** a list of 50+ GitHub repository URLs with >500 stars and >2 years of history, **When** the data extraction pipeline runs, **Then** it successfully clones each repo, extracts commit counts and lines changed per file, runs the appropriate static analysis tool (Radon for Python, SonarQube for others), and outputs a single CSV with columns for `repo_id`, `file_path`, `churn_density`, `debt_score`, `avg_loc`, and `contributor_count`. Note: `commit_count` is logged as auxiliary metadata but is NOT used in the primary density calculation.
2. **Given** a repository with binary files or non-code assets, **When** the extraction pipeline runs, **Then** it filters out non-source-code files (e.g., images, binaries) based on file extension before calculating metrics, ensuring the CSV only contains valid code files.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The system must calculate the correlation between churn density and debt density across all files, controlling for confounding variables, and determine statistical significance.

**Why this priority**: This is the core research activity. It transforms the raw data from Story 1 into the primary research finding (the correlation coefficient and p-value).

**Independent Test**: Can be tested by feeding the pipeline a pre-generated CSV with known correlation properties (e.g., a synthetic dataset with a known r=0.5) and verifying the output reports a correlation coefficient within ±0.05 of the expected value and a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** a unified dataset of files with `churn_density` and `debt_density`, **When** the analysis script executes, **Then** it computes both Pearson and Spearman correlation coefficients and reports the p-value, flagging results where p < 0.05 as statistically significant.
2. **Given** a dataset where `project_age` or `language` varies significantly, **When** the analysis runs, **Then** it performs a partial correlation or regression analysis to control for these confounders, outputting an adjusted correlation coefficient that isolates the churn-debt relationship.

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

- **FR-001**: System MUST extract code churn metrics (commits, lines changed) per file for all files in repositories with >2 years of history (See US-1). The system MUST calculate churn density as (total lines changed in the last 2 years) / (average Lines of Code (LOC) over the 2-year period). The average LOC serves as the denominator to normalize churn against the file's typical size, avoiding spurious correlations with small files. Historical baseline LOC is not required as a separate input. Commit counts are logged as auxiliary metadata but are NOT used for the density calculation.
- **FR-002**: System MUST calculate technical debt density using a CPU-tractable static analysis tool (See US-1). The system MUST use `radon` version 2.4.0 for Python files and `sonar-scanner` CLI version 10.4 LTS with the 'SonarQube Community Rules' profile for multi-language support (including Java, JavaScript, TypeScript, C#, Go, Rust). The dataset MUST include repositories in these supported languages; files in unsupported languages are excluded. The `debt_score` is defined as: for Python, Sum of Cyclomatic Complexity (CC) + (100 - Maintainability Index); for other languages, Sum of Code Smells + Cyclomatic Complexity. The debt density is calculated as `debt_score` / (average LOC over the 2-year period). (See US-1).
- **FR-003**: System MUST perform both Pearson and Spearman correlation calculations to assess linear and monotonic relationships between churn density and debt density (See US-2).
- **FR-004**: System MUST control for confounding variables (project age, programming language, contributor count) by including them as covariates in a partial correlation or regression model (See US-2). 'Contributor count' is defined as the number of unique committers who modified the file within the last 2 years. The system MUST perform a Variance Inflation Factor (VIF) check on covariates; if VIF > 5 for any covariate, the system MUST log a warning and proceed with regularization or exclusion of the collinear variable.
- **FR-005**: System MUST generate a scatter plot visualization with a regression line and annotate it with the correlation coefficient (r) and p-value (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (Bonferroni) if aggregating p-values across >10 independent repositories to control family-wise error rate. This is required to control family-wise error rate when aggregating p-values across >10 independent hypothesis tests, as per standard statistical practice for multiple comparisons. (See US-2).
- **FR-007**: System MUST exclude files where the average LOC over the 2-year period is < 10 from the analysis. This threshold is chosen to avoid division-by-zero bias and ensure measurement validity of density metrics, consistent with standard practices in empirical software engineering (Kitchenham et al.). The threshold is parameterized to allow sensitivity analysis.
- **FR-008**: System MUST perform a sensitivity analysis on the file size exclusion threshold defined in FR-007. The system MUST re-run the correlation analysis with thresholds of varying average LOC and report how the correlation coefficient (r) and p-value vary across these thresholds to ensure the results are robust to the exclusion criteria.

### Key Entities

- **Repository**: An open-source project on GitHub identified by URL, containing metadata (stars, age, language).
- **FileMetric**: A record linking a specific file to its churn density (lines changed / avg LOC), debt density (debt_score / avg LOC), average LOC, and contributor count.
- **CorrelationResult**: A statistical output containing the correlation coefficient (r), p-value, and sample size (n) for a specific repository or the aggregate.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation coefficient (r) between churn density and debt density is measured against the hypothesis of a moderate positive correlation (|r| ≥ 0.3) (See FR-003, FR-004). The system MUST flag a correlation as 'moderate' if the absolute correlation coefficient |r| ≥ 0.3. This threshold aligns with Cohen's conventions for effect sizes in behavioral and social sciences, which are widely adopted in empirical software engineering studies (e.g., Kitchenham et al.) as a standard benchmark for moderate correlation. The null hypothesis is r=0; validation is performed against the *adjusted* correlation (controlling for LOC) to ensure non-triviality.
- **SC-002**: The statistical significance (p-value) is measured against the alpha level of 0.05 to confirm the relationship is not due to chance (See FR-003, FR-004).
- **SC-003**: The analysis pipeline completes within the 6-hour GitHub Actions time limit (See FR-001, FR-002).
- **SC-004**: The false-positive rate for significant correlations is measured against the family-wise error rate (controlled via Bonferroni or similar) when testing across multiple repositories (See FR-006).
- **SC-005**: The measurement validity of debt density is confirmed by verifying that the specific tool versions used (Radon 2.4.0, SonarQube 10.4 LTS) are validated against a documented validation study (Kitchenham et al. 2009, Meneely et al. 2009) or have >5,000 GitHub stars. The system MUST log the specific citation or star count found for each tool version used.

## Assumptions

- **Assumption about data**: The selected GitHub repositories (stars > 500) contain sufficient commit history (≥2 years) and are written in languages supported by the chosen CPU-tractable static analysis tool (e.g., Python, Java, JavaScript, Go, Rust).
- **Assumption about methodology**: Code churn (frequency of changes) is a valid proxy for code instability and that static analysis metrics (code smells, complexity) are valid proxies for technical debt, as supported by the related work citations.
- **Assumption about compute**: The total dataset size (a representative sample of repositories) and the chosen static analysis tools will fit within the 7GB RAM and 14GB disk constraints of the GitHub Actions free runner without requiring GPU acceleration.
- **Assumption about confounders**: Project age, programming language, and team size are the primary confounding variables that need to be controlled; other factors (e.g., developer experience, documentation quality) are assumed to be negligible or unmeasurable for this scope.
- **Assumption about threshold**: A correlation coefficient of r ≥ 0.3 is considered a "moderate" effect size sufficient to validate the hypothesis in this context, based on general statistical conventions in empirical software engineering.