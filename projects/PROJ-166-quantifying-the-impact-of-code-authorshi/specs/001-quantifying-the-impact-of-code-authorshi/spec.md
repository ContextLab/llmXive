# Feature Specification: Quantifying the Impact of Code Authorship Diversity on Software Security

**Feature Branch**: `001-quantify-authorship-diversity-security`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Code Authorship Diversity on Software Security"

## User Scenarios & Testing

### User Story 1 - Dataset Construction and Feature Extraction (Priority: P1)

The system MUST ingest a defined set of public GitHub repositories, extract commit metadata to calculate unique contributors, compute lines of code (KLOC), and retrieve associated vulnerability records from the NVD/CVE database to form the primary analysis dataset.

**Why this priority**: This is the foundational step; without a valid, reproducible dataset linking authorship metrics to vulnerability counts, no statistical analysis can occur. It delivers the core data artifact required for the research.

**Independent Test**: Can be fully tested by executing the data pipeline script on a small, fixed seed of repositories (defined as the first set of repositories sorted alphabetically by URL from the target list) and verifying that the output CSV contains non-null values for `unique_authors`, `kloc`, `cve_count`, and `primary_language` for all entries.

**Acceptance Scenarios**:

1. **Given** a list of 5 GitHub repository URLs, **When** the data extraction script runs, **Then** the output CSV contains exactly 5 rows with populated `kloc` and `cve_count` columns.
2. **Given** a repository with no CVEs in the NVD, **When** the script processes it, **Then** the `cve_count` field is explicitly set to 0 (not null).
3. **Given** a repository where `cloc` fails to parse a file type, **When** the script runs, **Then** the script logs the warning and continues, excluding only the unparseable files from the KLOC total.

---

### User Story 2 - Statistical Modeling and Inference (Priority: P2)

The system MUST fit a multivariate Poisson or Negative-Binomial GLM predicting vulnerability counts from author counts and control variables, using KLOC as an offset to account for project size, and output the coefficient estimates, p-values, and confidence intervals.

**Why this priority**: This delivers the primary scientific answer to the research question. It transforms the raw data into the hypothesis test results.

**Independent Test**: Can be fully tested by running the analysis script on a static, pre-generated CSV of representative rows and verifying that the output JSON includes an `author_count_coefficient` with a non-null standard error and a 95% confidence interval.

**Acceptance Scenarios**:

1. **Given** a processed dataset CSV, **When** the analysis script runs, **Then** it outputs a JSON file containing the regression coefficient for `author_count` and its 95% confidence interval.
2. **Given** a dataset where `kloc` is zero for a specific repo, **When** the script calculates density, **Then** that row is excluded from the regression to prevent division by zero, and the exclusion is logged.
3. **Given** a fitted model, **When** the script runs diagnostics, **Then** it reports the Variance Inflation Factor (VIF) for all predictors to assess collinearity.

---

### User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

The system MUST perform robustness checks including subsampling by programming language and a sensitivity analysis using an alternative diversity metric (Shannon entropy) to ensure findings are not artifacts of a single metric choice.

**Why this priority**: This validates the reliability of the results. It addresses potential confounding factors and ensures the observed relationship is robust to methodological variations.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces separate regression results for at least two distinct language subsamples (e.g., Python and JavaScript) and one alternative diversity metric.

**Acceptance Scenarios**:

1. **Given** the full dataset, **When** the robustness script runs, **Then** it outputs separate regression coefficients for the Python-only and JavaScript-only subsets.
2. **Given** the primary author count metric, **When** the sensitivity analysis runs, **Then** it recalculates the model using Shannon entropy of author contributions and reports the difference in the main coefficient.
3. **Given** a model with multiple hypothesis tests, **When** the script completes, **Then** it applies a Benjamini-Hochberg correction to the p-values and reports the adjusted values.

---

### Edge Cases

- What happens when a GitHub repository has been deleted or is private before the script runs? (System must skip and log, not crash).
- How does the system handle repositories where the NVD/CVE mapping is ambiguous (e.g., multiple projects share a similar name)? (System must use exact URL matching and flag ambiguous matches for manual review if count > 0).
- How does the system handle repositories with extremely high contributor counts but low activity (e.g., bot spam)? (System must filter out contributors with < 1 line of code committed to avoid skewing the author count).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract the total lines of code (raw_line_count) and unique commit author count from the git history of each target repository using the `cloc` tool and `git log` parsing. (See US-1)
- **FR-002**: The system MUST retrieve vulnerability counts by matching repository URLs against the NVD/CVE JSON feed, ensuring exact URL correspondence to avoid false positives. (See US-1)
- **FR-003**: The system MUST calculate `author_count` as the number of unique authors with ≥ 1 line of code committed, and `cve_count` as the number of matching CVEs. The system MUST calculate `kloc` as `raw_line_count / 1000`. (See US-1)
- **FR-004**: The system MUST fit a multivariate Poisson or Negative-Binomial GLM with `cve_count` as the response, `author_count` plus controls (project age, language, release count) as predictors, and `log(kloc)` as an offset to normalize for project size. (See US-2)
- **FR-005**: The system MUST perform a Variance Inflation Factor (VIF) diagnostic on the fitted model and flag any predictor with VIF > 5 as having potential multicollinearity. (See US-2)
- **FR-006**: The system MUST apply a multiple-comparison correction (Benjamini-Hochberg) to all p-values derived from the main model coefficients and all subsample tests. (See US-3)
- **FR-007**: The system MUST execute a sensitivity analysis recalculating the model using Shannon entropy of author contributions as the primary predictor and report the difference in the main coefficient. (See US-3)

### Key Entities

- **Repository**: Represents a target GitHub project, containing attributes for URL, language, star count, and age.
- **Metrics**: Represents derived values for a repository, including `unique_authors`, `raw_line_count`, `kloc`, `author_count`, `cve_count`.
- **ModelResult**: Represents the output of the statistical analysis, containing coefficients, standard errors, p-values, confidence intervals, and diagnostic metrics (VIF).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The dataset construction pipeline MUST successfully process ≥ 95% of the target repository list (defined as ≥ 500 repos) within the 6-hour CI window, with no critical failures. (See US-1)
- **SC-002**: The regression analysis MUST produce a 95% confidence interval for the `author_count` coefficient in the offset-adjusted model and flag if the model fails to converge. (See US-2)
- **SC-003**: The sensitivity analysis MUST output regression coefficients and p-values for the model using Shannon entropy as the primary predictor. (See US-3)
- **SC-004**: The VIF diagnostic MUST confirm that no predictor variable has a VIF > 5, ensuring that collinearity does not invalidate the interpretation of independent effects. (See US-2)
- **SC-005**: The multiple-comparison correction MUST be applied to all reported p-values, and the adjusted p-values MUST be included in the final output artifact. (See US-3)

## Assumptions

- The GitHub REST API rate limits (unauthenticated and authenticated tiers) will not prevent the download of commit logs for the target sample size within the 6-hour window.; if authentication tokens are unavailable, the sample size will be capped at a moderate level.
- The NVD/CVE database JSON feed provides a reliable mapping of CVEs to GitHub repository URLs; if the URL matching fails for a known vulnerable project, the vulnerability count will be underreported, but this bias is assumed to be random with respect to authorship diversity.
- The `cloc` tool is installed and available in the GitHub Actions runner environment; if missing, the KLOC calculation will fail for that specific repo, and the repo will be excluded.
- The relationship between authorship diversity and vulnerability density is linear (or log-linear for GLM) and additive; non-linear interactions (e.g., diversity only helps up to a point) are assumed to be negligible for the primary model.
- The dataset variables (KLOC, author count, CVE count) are sufficient to proxy for project size, complexity, and security posture; no unmeasured confounders (e.g., internal security team size) are assumed to be correlated with both diversity and vulnerability density in a way that would reverse the observed effect.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to process a dataset of up to 2 GB and run the statistical models without memory errors; if the dataset exceeds this, the sample will be randomly subsampled to fit. Note: The processing logic is designed to fit within ≤ 4 GB RAM as per the project idea constraints.
- The `author_count` metric (unique authors) is a valid proxy for "diversity of perspectives" when adjusted for project size via the KLOC offset; it does not account for the actual diversity of the authors (e.g., background, expertise), only their numerical count.