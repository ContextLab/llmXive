# Feature Specification: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

**Feature Branch**: `001-analyzing-unmaintained-dependencies`  
**Created**: 2026-06-06  
**Status**: Draft  
**Input**: User description: "To what extent does the age of unmaintained dependencies in popular NPM packages correlate with exposure to unpatched security vulnerabilities in the JavaScript software supply chain?"

## User Scenarios & Testing

### User Story 1 - Data Collection and Variable Extraction (Priority: P1)

As a researcher, I need to programmatically retrieve the top [deferred] most-downloaded NPM packages, extract their direct and transitive dependency trees, and gather maintenance metadata (last commit/release date) and security metadata (CVE counts) for each unique dependency, so that I can construct the primary dataset for correlation analysis.

**Why this priority**: Without this data, no analysis can occur. This is the foundational step that defines the scope and validity of the entire study.

**Independent Test**: A script can be run that outputs a JSON/CSV file containing N rows of package data (where N matches the top-[N] query parameter), each with a list of dependencies, where each dependency has a `last_release_date`, `last_commit_date`, and `vulnerability_count`.

**Acceptance Scenarios**:

1. **Given** the NPM registry API is accessible, **When** the script queries for the top [deferred] packages by weekly downloads, **Then** the script successfully retrieves and stores the package names and download counts.
2. **Given** a list of package names, **When** the script recursively resolves dependencies, **Then** it produces a flattened list of unique dependencies with their version constraints.
3. **Given** a unique dependency, **When** the script queries GitHub and npm audit APIs, **Then** it records the timestamp of the last release and the count of unpatched vulnerabilities for that dependency.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

As a researcher, I need to compute the Spearman rank correlation coefficient between the "dependency age" (days since last release) and "vulnerability density" (number of unpatched CVEs) across the collected dataset, so that I can determine if there is a statistically significant relationship between maintenance status and security risk.

**Why this priority**: This is the core research question. It transforms the raw data into the primary finding (correlation vs. null result).

**Independent Test**: A script can take the dataset generated in US-1 and output a single correlation coefficient (r) and a p-value, along with a scatter plot visualization of age vs. vulnerability count. The test MUST verify that r is within [-1, 1] and the p-value is a float within [0, 1].

**Acceptance Scenarios**:

1. **Given** a dataset of dependencies with `age_in_days` and `vulnerability_count`, **When** the analysis script runs, **Then** it calculates and outputs the Spearman rank correlation coefficient and p-value.
2. **Given** the correlation result, **When** the script generates a visualization, **Then** it produces a scatter plot where the x-axis is dependency age and the y-axis is vulnerability count.
3. **Given** a p-value < 0.05, **When** the script determines significance, **Then** it flags the result as statistically significant in the output report.

---

### User Story 3 - Stratified Analysis and Reporting (Priority: P3)

As a researcher, I need to stratify the correlation analysis by package category (e.g., framework, utility, build tool) and generate a summary report of vulnerability density by category, so that I can identify if the risk profile varies across different types of software components.

**Why this priority**: This adds nuance to the findings, allowing for more targeted recommendations for dependency management tools, though the primary correlation (US-2) is the main deliverable.

**Independent Test**: A script can take the dataset and category metadata, output a table of correlation coefficients per category (only for categories with N ≥ 30 samples), and generate a histogram of unmaintained dependency percentages by category.

**Acceptance Scenarios**:

1. **Given** package metadata containing keywords, **When** the script assigns categories, **Then** it groups the dependencies into buckets like "framework," "utility," or "build tool."
2. **Given** grouped data, **When** the script runs the correlation analysis per group (excluding groups with N < 30), **Then** it outputs a distinct correlation coefficient and p-value for each valid category.
3. **Given** the grouped data, **When** the script generates a histogram, **Then** it displays the distribution of unmaintained dependency percentages across the defined categories.

### Edge Cases

- **What happens when a dependency has no GitHub repository?** The system MUST handle missing repository metadata by marking `last_commit_date` and `last_release_date` as null and excluding that dependency from the "age" calculation, while still counting its vulnerabilities.
- **How does the system handle rate-limiting from NPM/GitHub APIs?** The system MUST implement exponential backoff with a bounded maximum retry count per request before marking the specific data point as missing.
- **What happens if a dependency is a private package or not publicly accessible?** The system MUST skip the dependency and log a warning, ensuring the analysis only proceeds on public data available via the registry.

## Requirements

### Functional Requirements

- **FR-001**: System MUST query the NPM registry API to retrieve the top [deferred] packages by weekly download count and store their metadata. (See US-1)
- **FR-002**: System MUST recursively traverse the dependency tree of each top package to identify all unique direct and transitive dependencies. (See US-1)
- **FR-003**: System MUST query the GitHub API to determine the timestamp of the last commit and last release tag for each unique dependency. (See US-1)
- **FR-004**: System MUST query the npm audit API and security advisory database to retrieve the count of unpatched CVEs for each unique dependency. (See US-1)
- **FR-005**: System MUST calculate "dependency age" as the number of days elapsed since the last release date for each dependency. (See US-2)
- **FR-006**: System MUST compute the Spearman rank correlation coefficient and p-value between dependency age and vulnerability count across the entire dataset. (See US-2)
- **FR-007**: System MUST classify dependencies into categories (e.g., framework, utility) based on package metadata keywords (exploratory only) and perform stratified correlation analysis, falling back to dependency graph topology if keyword data is missing or noisy. (See US-3)
- **FR-008**: System MUST generate a scatter plot visualization of dependency age vs. vulnerability count and a histogram of unmaintained dependency percentages by category. (See US-2, US-3)
- **FR-009**: System MUST implement exponential backoff with a maximum of 3 retries for any failed API request to handle rate limiting. (See Edge Cases)
- **FR-010**: System MUST exclude dependencies with missing release metadata from the age calculation but include them in vulnerability counts. (See Edge Cases)

### Key Entities

- **Package**: Represents an NPM package, containing attributes: `name`, `weekly_downloads`, `category`, `dependencies_list`.
- **Dependency**: Represents a unique software component used by a package, containing attributes: `name`, `version`, `last_release_date`, `last_commit_date`, `vulnerability_count`, `age_in_days`, `category`.
- **AnalysisResult**: Represents the output of the statistical test, containing attributes: `correlation_coefficient`, `p_value`, `sample_size`, `methodology_notes`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman rank correlation coefficient between dependency age and vulnerability count is measured against the null hypothesis (rho=0) to determine statistical significance. (See US-2)
- **SC-002**: The proportion of dependencies with missing release metadata is measured against the total dataset size to assess data completeness and potential bias. (See FR-010)
- **SC-003**: The variance in correlation coefficients across package categories (for categories with N ≥ 30) is measured against the overall dataset correlation to determine if risk profiles differ by type. (See US-3)
- **SC-004**: The number of API requests successfully completed versus failed (after retries) is measured against the total required requests to verify data collection robustness. (See FR-009)
- **SC-005**: The computational runtime of the full analysis pipeline is measured against the 6-hour free-tier CI limit to ensure feasibility. (See Compute Feasibility)
- **SC-006**: The statistical power of the primary correlation test is measured against a target of ≥ 0.8 for detecting a moderate effect size (rho ≥ 0.2) at alpha = 0.05. (See Assumptions - Multiplicity & power)

## Assumptions

- **Dataset-variable fit**: It is assumed that the NPM registry API provides sufficient metadata to identify the "last release date" for all public packages, and that the GitHub API provides repository metadata for the majority of dependencies. If a dependency lacks a GitHub repository, it is assumed that the `last_release_date` from NPM metadata is the primary indicator of maintenance status.
- **Inference framing**: The study is observational; therefore, all findings regarding the relationship between age and vulnerabilities will be framed as **associational** correlations, not causal claims. The analysis does not assume that lack of maintenance *causes* vulnerabilities, only that they are correlated.
- **Multiplicity & power**: The analysis involves a single primary hypothesis test (Spearman correlation). While stratified tests are performed, the primary success criterion relies on the aggregate correlation. A formal power analysis for the sample size (N=[deferred] packages, [deferred]+ dependencies) is deferred, but the sample size is assumed to be sufficient for detecting moderate effect sizes (rho ≥ 0.2) given the high variability expected in the data, targeting a power of ≥ 0.8.
- **Threshold justification**: No arbitrary decision cutoffs (e.g., "packages older than X days are unmaintained") are introduced for the primary correlation analysis. The "age" variable is continuous. If a binary classification of "unmaintained" is used for visualization only, a threshold of **180 days** (6 months) since last release will be used, justified by common industry practices for defining "stale" dependencies, and a sensitivity analysis will sweep this threshold over a range of days to ensure the headline rates (vulnerability density) are robust to this choice.
- **Measurement validity**: The "vulnerability count" metric is assumed to be a valid proxy for "exposure to unpatched security vulnerabilities" based on the npm audit database, which is the standard industry source for such data.
- **Predictor collinearity**: "Last commit date" and "last release date" are highly correlated. The primary predictor will be "last release date" as it is a more direct indicator of active maintenance for consumers. "Last commit date" is strictly an exploratory secondary metric; it will not be used as a primary predictor to avoid multiple testing issues. If both are used in exploratory analysis, a collinearity diagnostic (VIF) will be required to ensure independent effects are not claimed.
- **Compute feasibility**: The entire analysis (API scraping, data processing, statistical testing, and visualization) is assumed to fit within the GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 hours). The dataset size is small enough to fit in memory, and the statistical methods (Spearman correlation) are computationally trivial. No GPU or large-model inference is required.
- **API Rate Limits**: It is assumed that the NPM and GitHub APIs will not permanently block the CI runner, and that the implemented exponential backoff (FR-009) is sufficient to navigate rate limits without exceeding the 6-hour time budget.
- **Data Availability**: It is assumed that the top [deferred] packages by download count are publicly accessible and that their dependency trees do not contain private or inaccessible packages that would halt the recursion.