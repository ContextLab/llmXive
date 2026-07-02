# Feature Specification: Evaluating the Impact of Code Comment Style on Maintainability

**Feature Branch**: `101-eval-comment-maintainability`  
**Created**: 2024-05-24  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Comment Style on Maintainability"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition & Preprocessing (Priority: P1)

The system MUST identify a representative sample of high-star Python repositories and fetch their full git history locally for analysis. This forms the foundational dataset for all subsequent metric calculations.

**Why this priority**: Without a valid, complete dataset of repositories with accessible version history, no analysis can occur. This is the prerequisite for all downstream features.

**Independent Test**: Can be fully tested by verifying that 500 unique repositories exist in the local workspace with accessible `git log` history, independent of metric calculation logic.

**Acceptance Scenarios**:

1. **Given** the HuggingFace `codeparrot/github-code` dataset is accessible, **When** the system queries for Python repositories with ≥100 stars, **Then** a list of candidate repository identifiers is returned to reach a target of 500 valid clones.
2. **Given** a repository identifier, **When** the system clones the repository, **Then** the full git history is available locally without errors.

---

### User Story 2 - Metric Computation (Priority: P2)

The system MUST compute comment quality metrics (readability, sentiment, density) and maintainability metrics (churn, bug fix rate) for every repository in the dataset.

**Why this priority**: These metrics are the core variables for the research question. They must be accurate and consistent to allow for valid statistical comparison.

**Independent Test**: Can be fully tested by running the metric pipeline on a known small subset of repositories and verifying the calculated values match manual inspection of the source code and git logs.

**Acceptance Scenarios**:

1. **Given** a repository with source files containing comments, **When** the system parses the code, **Then** comment density is calculated as (lines of comment / lines of code) with a precision of at least 2 decimal places. Specifically, given the comment string "This is a simple test." (6 words, 1 sentence, 20 chars), the Flesch-Kincaid readability score MUST be 65.3 ± 0.1.
2. **Given** a repository's git history, **When** the system analyzes commit messages and static analysis warnings, **Then** the bug fix rate is calculated as (commits introducing `pylint` error-level warnings / total commits) with a precision of at least 2 decimal places. This metric is validated against a manually labeled subset of 50 commits from a reference repository to ensure accuracy ≥ 95%.

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

The system MUST perform correlation and regression analysis to determine the relationship between comment metrics and maintainability, producing a report with statistical significance values.

**Why this priority**: This delivers the final research output. It synthesizes the data and metrics into the answer to the research question.

**Independent Test**: Can be fully tested by running the analysis script on a pre-computed CSV of metrics and verifying the output report contains p-values and correlation coefficients within expected ranges.

**Acceptance Scenarios**:

1. **Given** a dataset of computed metrics, **When** the system runs the regression model, **Then** the output report includes p-values for all predictor variables, and the model achieves either an R² ≥ 0.05 or a p-value < 0.1 for at least one predictor.
2. **Given** a significance threshold of p < 0.05, **When** the system evaluates the results, **Then** the output JSON contains a boolean field `is_significant` set to true for any correlation meeting the corrected p-value threshold.

---

### Edge Cases

- What happens when a repository has zero comments? (System MUST assign a default readability/sentiment score of 0 and density of 0, logging the event).
- How does system handle git clone failures? (System MUST skip the repository, log the error, and query additional candidates from the HuggingFace index until the target of 500 valid repositories is reached).
- How does system handle repositories with no git history? (System MUST exclude the repository from the dataset and log the exclusion).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch a target of 500 unique Python repositories using identifiers from the HuggingFace `codeparrot/github-code` dataset and clone their full git history locally from GitHub (See US-1).
- **FR-002**: System MUST extract comments using `tree-sitter` to ensure accurate AST navigation and avoid false positives from string literals (See US-1).
- **FR-003**: System MUST compute Flesch-Kincaid readability scores using the `textstat` library for all extracted comments (See US-2).
- **FR-004**: System MUST compute sentiment polarity using `TextBlob` for all extracted comments (See US-2).
- **FR-005**: System MUST calculate code churn as total lines changed per commit using `git log` analysis (See US-2).
- **FR-006**: System MUST calculate bug fix rate as the ratio of commits introducing at least one `pylint` error-level warning to total commits, validated against a labeled subset (See US-2).
- **FR-007**: System MUST perform Negative Binomial regression (for count data) or Beta regression (for bounded ratios) modeling maintainability as a function of comment metrics, controlling for project age and contributor count (See US-3).
- **FR-008**: System MUST frame all findings as associational correlations, NOT causal effects, in all generated reports (See US-3).
- **FR-009**: System MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg FDR) to p-values when testing >1 hypothesis (See US-3).
- **FR-010**: System MUST perform a sensitivity analysis sweeping the significance threshold over {0.01, 0.05, 0.1} and report how headline rates vary (See US-3).
- **FR-011**: System MUST enforce a memory limit of ≤7 GB RAM during execution to fit CI constraints (See US-1).
- **FR-012**: System MUST complete the full pipeline within 6 hours on a 2 CPU core runner (See US-3).
- **FR-013**: System MUST process repositories in batches of no more than 10 concurrent clones to guarantee the memory limit (≤7 GB) is not exceeded during AST parsing and history loading (See US-1).
- **FR-014**: System MUST include code complexity (average cyclomatic complexity per function) as a control variable in the regression model to prevent spurious correlations (See US-3).

### Key Entities *(include if feature involves data)*

- **Repository**: A software project identified by a unique URL, containing source files and git history.
- **Comment**: A text block within source code, distinct from executable statements, used for documentation.
- **Metric**: A quantitative value derived from a Repository or Comment (e.g., Readability Score, Churn Rate).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against the target of 500 valid repositories with full git history (See US-1).
- **SC-002**: Metric calculation accuracy is measured against manual spot-checks with a threshold of ≥ 95% accuracy on a validation set of N=50 samples (See US-2).
- **SC-003**: Statistical significance is measured against the threshold of p < 0.05 with multiple-comparison correction (See US-3).
- **SC-004**: Execution runtime is measured against the 6-hour limit on the GitHub Actions free-tier runner (See US-3).
- **SC-005**: Memory usage is measured against the 7 GB RAM limit during peak processing (See US-3).

## Assumptions

- The HuggingFace `codeparrot/github-code` dataset provides valid repository identifiers sufficient to clone full git history from GitHub, but the dataset itself is used *only* for identifier selection, not for fetching git history.
- The GitHub Actions free-tier runner environment includes `git` CLI, Python 3.9+, and network access to GitHub and HuggingFace.
- The `codeparrot/github-code` dataset does not contain the full git history itself, requiring cloning from the source repository for churn analysis.
- All repositories will be accessible via public GitHub URLs without authentication requirements.
- The `textstat` and `TextBlob` libraries are compatible with the CPU-only environment without requiring CUDA or GPU acceleration.
- The analysis treats comment metrics and maintainability metrics as associational variables, avoiding causal claims due to the observational nature of the data.
- Sample size power is sufficient for detecting medium effect sizes given a large-scale repository constraint, though specific power calculations are deferred to the analysis phase.
- Network bandwidth will not exceed hours total download time for a representative set of repositories.
- The HuggingFace `codeparrot/github-code` dataset index provides stable repository identifiers (owner/repo format) but does not guarantee the persistence of the raw git history objects required for churn analysis. Therefore, the system MUST NOT rely on the dataset for git history. Instead, the system MUST use the stable identifiers to fetch the full git history directly from the public GitHub API via `git clone https://github.com/<owner>/<repo>.git`. This approach ensures access to the complete commit history required for FR-005 and FR-006, assuming the repositories remain public and accessible.
- The `pylint` error-level warnings provide a sufficient proxy for "bug-fix" intent in the absence of direct issue tracker linkage, validated against a manual sample.