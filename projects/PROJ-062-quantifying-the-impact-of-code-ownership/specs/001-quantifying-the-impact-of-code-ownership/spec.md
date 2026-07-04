# Feature Specification: Quantifying the Impact of Code Ownership on Software Quality

**Feature Branch**: `001-code-ownership-analysis`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Code Ownership on Software Quality - Does higher code ownership concentration (fewer owners per module) correlate with lower bug density and code churn in large-scale open-source software projects?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repository Data Collection and Processing (Priority: P1)

The system MUST download Git repositories for multiple high-activity open-source projects, parse commit logs to identify file-level ownership from shallow history (depth 1000) up to the analysis cutoff, and extract bug counts using a path-based proximity heuristic for time window T for ownership and T+1 for bugs.

**Why this priority**: Without baseline data collection, no subsequent analysis can occur. This is the foundational step that enables all research outcomes.

**Independent Test**: Can be fully tested by verifying that 10 valid repositories (those meeting the ≥1000 commit threshold) are successfully cloned with shallow history (depth 1000) up to the analysis cutoff, commit logs are parsed into ownership data, and bug metadata is retrieved via the path-based proximity heuristic for issues reported in time window T+1 for at least 8 repositories (≥80% success rate calculated as: successful_repos / 10 ≥ 0.8, where the denominator is the target of 10 valid repositories).

**Acceptance Scenarios**:

1. **Given** a list of 10 GitHub repository URLs, **When** the system executes `git clone --depth 1000` (up to cutoff T), **Then** each repository must complete within 30 minutes and store raw commit data to disk
2. **Given** parsed commit data, **When** the system applies the Bug-File Proximity Heuristic (path-only matching) to link issues to modules, **Then** at least 8 repositories must return linked bug metadata (fallback to path-only if API fails)
3. **Given** intermediate CSVs, **When** disk space is monitored, **Then** total storage must remain ≤14 GB across all repositories

---

### User Story 2 - Ownership and Quality Metric Calculation (Priority: P2)

The system MUST calculate ownership concentration (Gini coefficient for commit distribution per module) using shallow history (depth 1000) up to time T, code churn (lines added/deleted) as a control variable, cyclomatic complexity using `radon`, and normalize metrics per module (bugs per KLOC) for time window T+1. Modules deleted between T and T+1 are excluded from BOTH the predictor (ownership concentration) and outcome (bug density) calculations to prevent survivorship bias.

**Why this priority**: This enables the core analytical relationship between ownership concentration and quality outcomes. Without these metrics, correlation analysis cannot proceed.

**Independent Test**: Can be fully tested by verifying that Gini coefficients are computed for all modules using shallow history, code churn values are calculated for ≥90% of modules, and normalized bug density (bugs per KLOC) is available for statistical analysis.

**Acceptance Scenarios**:

1. **Given** commit distribution per module, **When** Gini coefficient is calculated, **Then** the value must be ∈ [0.0, 1.0] with at least 3 decimal precision
2. **Given** file-level code changes, **When** cyclomatic complexity is computed via `radon`, **Then** ≥95% of modules must have valid complexity scores (defined as non-null, non-NaN, and ≥0)
3. **Given** bug counts and lines of code, **When** normalized bug density is computed, **Then** the result must be bugs per KLOC with ≥2 decimal precision

---

### User Story 3 - Statistical Correlation Analysis and Visualization (Priority: P3)

The system MUST perform Spearman rank correlation analysis between ownership Gini coefficient and normalized bug density, validate statistical significance with confidence intervals, perform collinearity diagnostics (VIF) and report framing if VIF ≥5, apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg), test for non-linearity (quadratic regression), and visualize results with scatter plots and regression lines.

**Why this priority**: This delivers the research outcome and enables hypothesis validation. It is the final analytical step that produces publishable results.

**Independent Test**: Can be fully tested by verifying that correlation coefficients are computed with p-values reported, confidence intervals are calculated, VIF is reported, multiple-comparison correction is applied, non-linearity is tested, and scatter plots with regression lines are generated for all 10 repositories.

**Acceptance Scenarios**:

1. **Given** paired ownership and bug density data, **When** Spearman correlation is computed via `scipy.stats`, **Then** the correlation coefficient must be ∈ [-1.0, 1.0] and the p-value must be reported (regardless of magnitude)
2. **Given** correlation results, **When** collinearity diagnostics are calculated, **Then** the VIF for each predictor (Gini, Gini², Size, Age) must be reported; if VIF ≥5, the report must explicitly state that independent effects are not claimed
3. **Given** multiple hypothesis tests, **When** correction is applied, **Then** adjusted p-values or a corrected threshold must be reported using Bonferroni or Benjamini-Hochberg
4. **Given** analysis results, **When** non-linearity is tested, **Then** a quadratic regression model (Gini + Gini²) must be fitted and the significance of the Gini² term reported
5. **Given** analysis results, **When** visualization is generated, **Then** scatter plots with regression lines must be saved as PNG files (≥300 DPI) for at least 8 repositories

---

### Edge Cases

- What happens when a repository has <1000 commits (insufficient data for Gini coefficient calculation)? → System must skip that repository and log a warning, continuing with ≥8 valid repositories (target is 10 valid, not 10 attempted)
- How does system handle GitHub API rate limiting (unauthenticated request limits)? → System must implement exponential backoff with ≤3 retries per endpoint, with ≥60-second delay between retries
- What happens when a module has 0 lines of code (division by zero in KLOC normalization)? → System must exclude that module from normalized bug density calculations and log it as a data quality issue
- How does system handle repositories that exceed significant RAM capacity when loading full history? → System must process one repository at a time, clearing memory between each, with disk-based intermediate storage

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download 10 valid GitHub repositories (those with ≥1000 commits) using `git clone --depth 1000` (up to analysis cutoff T) (See US-1)
- **FR-002**: System MUST calculate Gini coefficient for commit distribution per module using shallow history (depth 1000) up to time T with precision ≥3 decimal places; modules deleted between T and T+1 are excluded from both predictor and outcome (See US-2)
- **FR-003**: System MUST compute cyclomatic complexity using `radon` library on the latest snapshot for ≥95% of modules (See US-2)
- **FR-004**: System MUST perform Spearman rank correlation analysis using `scipy.stats` and output a JSON summary containing the correlation coefficient, p-value, and 95% confidence interval (See US-3)
- **FR-005**: System MUST generate scatter plots with regression lines using `matplotlib` saved as PNG files (≥300 DPI) for ≥8 repositories (See US-3)
- **FR-006**: System MUST implement exponential backoff for GitHub API rate limiting with ≤3 retries and ≥60-second delay between attempts (See US-1)
- **FR-007**: System MUST store intermediate CSVs to disk to avoid memory accumulation, ensuring peak RAM usage ≤7 GB at any point (See US-1)
- **FR-008**: System MUST enforce temporal separation: Ownership metrics calculated on commits from time window T (defined as T-6 months to T, where T is the date of the latest commit), and Bug counts extracted from issues reported in time window T+1 (defined as the 6 months following T). Modules deleted between T and T+1 are excluded from both predictor and outcome calculations (See US-2)
- **FR-009**: System MUST link bugs to modules using a Bug-File Proximity Heuristic defined as: (1) exact match of the full filename (case-insensitive, path-normalized) of the issue title/description against the file path. Path-normalization is defined as: lowercase, remove trailing .bak/.pyc/.min.js/.lock, and normalize slashes to '/'. If the issue text contains 'src/main.py', it must match 'src/main.py' exactly (word-boundary match). Condition (2) (assignee match) is REMOVED to prevent circular validation. (See US-1)
- **FR-010**: System MUST frame all statistical findings as associational rather than causal, explicitly noting the observational nature of the study in the final report (See US-3)
- **FR-011**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) when testing >1 hypothesis to control family-wise error rate (See US-3)
- **FR-012**: System MUST perform a sensitivity analysis on the statistical significance threshold (p-value) by sweeping values over a set of low learning rates and report how the count of significant findings varies across these cutoffs (See US-3)
- **FR-013**: System MUST calculate Variance Inflation Factor (VIF) for predictors (Gini, Gini², Size, Age) and flag if VIF ≥5, requiring a descriptive framing of the joint relationship rather than independent effect claims. Gini² is defined as the square of the Gini coefficient (See US-3)
- **FR-014**: System MUST validate dataset-variable fit by confirming commit history contains all required variables (committers, timestamps, file paths, line counts); if missing, the repository is skipped and logged (See US-1)
- **FR-015**: System MUST perform a sensitivity analysis on the correlation magnitude threshold (|ρ|) by sweeping values over the set {0.2, 0.3, 0.4} and report how the count of significant findings varies across these cutoffs (See US-3)
- **FR-016**: System MUST test for non-linearity by fitting a quadratic regression model (Outcome ~ Gini + Gini² + Size + Age) and report if the Gini² term is statistically significant (p < 0.05) (See US-3)

### Non-Functional Requirements

- **NFR-001**: Total execution time must be ≤6 hours on the GitHub Actions free-tier runner. This is a performance target for the CI environment and is not a deterministic functional test (See US-1)

### Key Entities

- **Repository**: A GitHub project containing Git history, with attributes including URL, clone depth, commit count, and file modules
- **Module**: A code file or directory within a repository, with attributes including ownership distribution (commits per developer), lines of code (Size), age (months since creation), and complexity metrics
- **Bug**: A GitHub Issue linked to specific file paths via path-based proximity heuristic, with attributes including issue ID, creation date, and associated file/module
- **Metric**: A calculated value (Gini coefficient, bug density, code churn, complexity) with attributes including module reference, value, and timestamp
- **Gini² (Quadratic Ownership Term)**: The square of the Gini coefficient, used as a predictor to test for non-linear (U-shaped) relationships
- **Size**: Lines of Code (KLOC) for a module
- **Age**: Time in months since the module's first commit

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Spearman correlation coefficient between ownership Gini and bug density is measured against the null hypothesis (ρ=0), with p-value and 95% confidence interval reported in JSON output (See US-3)
- **SC-002**: Peak RAM usage is measured against the 7 GB RAM constraint throughout repository processing, with peak usage ≤7 GB (See US-1)
- **SC-003**: Repository processing success rate is measured against the target of 10 valid repositories, with ≥80% success (≥8 valid repositories) (See US-1)
- **SC-004**: Correlation coefficient and p-value are measured and reported; statistical significance is defined as p < 0.05, and effect size is reported as |ρ| regardless of magnitude (See US-3)
- **SC-005**: Total execution time is measured against the 6-hour GitHub Actions free-tier limit, with total runtime ≤6 hours (See US-1)
- **SC-006**: Code churn correlation with bug density is measured and reported as a secondary outcome (See US-2)
- **SC-007**: Bug-File linkage rate is measured against the total number of issues reported in time window T+1 that mention at least one file path in the repository, calculated as a global aggregate across all included repositories, and reported as a percentage (See US-1)
- **SC-008**: The sensitivity analysis of the p-value threshold is measured by the variance in the count of significant findings across the sweep {0.01, 0.05, 0.1} (See US-3)
- **SC-009**: The collinearity diagnostic is measured by the maximum VIF value among predictors; if VIF ≥5, the report must explicitly state that independent effects are not claimed (See US-3)
- **SC-010**: The multiple-comparison correction is measured by the presence of adjusted p-values or a corrected significance threshold in the final statistical output (See US-3)
- **SC-011**: The sensitivity analysis of the correlation magnitude threshold is measured by the variance in the count of significant findings across the sweep {0.2, 0.3, 0.4} (See US-3)
- **SC-012**: The non-linearity test is measured by the p-value of the Gini² term in the quadratic regression model (See US-3)

## Assumptions

- GitHub repository URLs are publicly accessible without authentication for `git clone --depth 1000`
- GitHub Issues API returns issue metadata (title, description) for at least 8 of the 10 sampled repositories; if API fails, path-only matching is used
- The 10 selected repositories (e.g., `apache/httpd`, `apache/stratos`) contain sufficient commit history (≥1000 commits) for Gini coefficient calculation
- `radon` library successfully parses Python files for cyclomatic complexity in all repositories; other languages are excluded from complexity analysis
- The analysis is observational (no random assignment), so all findings are framed as associational rather than causal
- Multiple-comparison correction is applied when testing >1 hypothesis (e.g., Bonferroni or Benjamini-Hochberg) to control family-wise error rate
- Any threshold introduced (e.g., p <0.05, |ρ| >0.3) carries a community-standard basis (standard significance level in empirical software engineering) and requires sensitivity analysis sweeping the threshold over {0.01, 0.05, 0.1} for p-value and {0.2, 0.3, 0.4} for correlation magnitude
- If two predictors are definitionally related (e.g., Gini coefficient and Gini²), the analysis frames their joint relationship descriptively and requires a collinearity diagnostic (VIF ≥5 indicates problematic collinearity); Gini² is a quadratic transformation of the sole ownership metric, not a separate variable
- No GPU/CUDA accelerators are required; all computation runs on CPU-only GitHub Actions free-tier runner
- Intermediate CSVs are written to disk rather than retained in memory to stay within 7 GB RAM / 14 GB disk constraints
- The job time limit is sufficient for sequential processing of multiple repositories with shallow history (depth 1000)
- API latency may exceed 60 seconds; the system must handle this gracefully without failing the test unless the total execution time exceeds 6 hours
- Gini coefficient is the sole linear metric for ownership concentration; 'commit concentration' is not a separate variable to avoid tautological analysis; Gini² is a quadratic transformation used for non-linearity testing
- Dataset-variable fit is validated: each repository's commit history must contain all required variables; if a repository is missing required variables, it is skipped and a warning is logged (See US-1)
- Path normalization in FR-009 is defined as: lowercase, remove trailing .bak/.pyc/.min.js/.lock, normalize slashes to '/'
- Exact match in FR-009 means the full filename must match (e.g., 'main.py' matches 'main.py' but not 'main.py.bak' or 'src/main.py' unless the path is also included)