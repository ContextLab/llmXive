# Feature Specification: Statistical Analysis of GitHub Issue Resolution Times

**Feature Branch**: `001-github-issue-resolution`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Statistical analysis of publicly available GitHub issue resolution times"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Collection and Preprocessing Pipeline (Priority: P1)

A researcher can automatically collect closed issue data from multiple diverse GitHub repositories and produce a clean, analysis-ready dataset with computed resolution times and extracted features.

**Why this priority**: Without reliable data collection and preprocessing, no subsequent analysis is possible. This is the foundational step that enables all downstream statistical work.

**Independent Test**: Can be fully tested by running the collection pipeline on a fixed set of 5 repositories and verifying the output CSV contains ≥1000 issues with non-missing resolution times and all required feature columns.

**Acceptance Scenarios**:

1. **Given** a list of 5 valid GitHub repository paths, **When** the collection script executes, **Then** the output CSV contains ≥1000 closed issues with `created_at`, `closed_at`, `labels`, `assignee`, and `comments_count` columns populated
2. **Given** an issue with `closed_at` earlier than `created_at`, **When** the preprocessing script runs, **Then** that issue is flagged and excluded from the final dataset with a log entry
3. **Given** the GitHub API rate limit is reached during collection, **When** the script retries, **Then** the script waits ≥60 seconds before resuming and completes within the allocated CI budget

---

### User Story 2 - Descriptive Distribution Analysis (Priority: P2)

A researcher can generate empirical cumulative distribution plots and fit parametric distribution models (log-normal, Weibull) to understand the shape of resolution time distributions across repositories.

**Why this priority**: Understanding the distribution shape is essential before hypothesis testing; it determines whether parametric tests are valid and informs transformation choices (e.g., log-transform).

**Independent Test**: Can be fully tested by running the distribution analysis on the cleaned dataset and verifying that ECDF plots are generated and fit quality metrics are reported for both parametric families.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of ≥1000 issues, **When** the distribution analysis script runs, **Then** an ECDF plot is generated showing resolution time on the x-axis (log scale) and cumulative probability on the y-axis
2. **Given** the log-normal and Weibull candidate families, **When** maximum likelihood fitting is performed, **Then** fit quality metrics (KS statistic, p-value, AIC) are reported for both families regardless of threshold
3. **Given** resolution times with extreme outliers (>30 days), **When** the analysis runs, **Then** the script reports the number of outliers and their percentage of the total dataset

---

### User Story 3 - Hypothesis Testing and Regression Modeling (Priority: P3)

A researcher can execute ANOVA/Kruskal-Wallis tests for categorical predictors, apply Holm-Bonferroni correction for multiple comparisons, and fit a linear mixed-effects model with repository-level random intercepts to quantify variance explained by issue-level covariates.

**Why this priority**: This delivers the core research findings about which factors statistically explain resolution time differences; it is the primary scientific output of the project.

**Independent Test**: Can be fully tested by running the hypothesis testing suite on the cleaned dataset and verifying that hypothesis tests execute and report p-values with effect sizes and confidence intervals.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with ≥1000 issues across ≥20 repositories, **When** the Kruskal-Wallis test runs for programming language groups, **Then** a p-value is reported with Holm-Bonferroni adjusted α=0.05
2. **Given** the mixed-effects model with random intercepts for repository, **When** leave-one-repository-out cross-validation executes, **Then** MAE and R² metrics are reported with standard deviation across folds
3. **Given** any predictor with pairwise correlation |r|≥0.7, **When** the collinearity diagnostic runs, **Then** VIF is calculated from the full model design matrix and a VIF ≥5 is flagged (the model reports the joint relationship as descriptive rather than claiming independent effects)
4. **Given** decision cutoffs for significance or effect size, **When** the sensitivity analysis runs, **Then** cutoffs are swept over a range of thresholds and false-positive/false-negative rates are reported for each threshold

---

### Edge Cases

- What happens when a repository has <100 closed issues (insufficient sample for statistical power)?
- How does the system handle GitHub API authentication failures or token expiration mid-collection?
- What if resolution time is exactly zero (issue created and closed in the same second)?
- How are issues with multiple labels (e.g., both "bug" and "enhancement") categorized in label-group analyses?
- What if a repository's programming language cannot be inferred from repository metadata (null language field)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect closed issues from ≥100 repositories via GitHub REST API with `state=closed` and `since=2020-01-01` (See US-1)
- **FR-002**: System MUST compute resolution time as `closed_at - created_at` in hours and log-transform values for distribution fitting (See US-1, US-2)
- **FR-003**: System MUST exclude issues with resolution time <0 or missing timestamps from analysis (See US-1)
- **FR-004**: System MUST apply Holm-Bonferroni correction when conducting ≥3 hypothesis tests on the same outcome variable (See US-3)
- **FR-005**: System MUST fit a linear mixed-effects model with random intercepts for repository and fixed effects for issue-level covariates (See US-3)
- **FR-006**: System MUST calculate VIF from the full model design matrix after fitting and flag collinearity when VIF≥5; pairwise |r|≥0.7 triggers VIF calculation (See US-3)
- **FR-007**: System MUST perform sensitivity analysis sweeping any decision cutoffs over a range of low-probability thresholds. and report how false-positive/false-negative rates vary (See US-3)
- **FR-008**: System MUST include the phrase "associational" or "correlational" in all result text when describing relationships between variables (See US-3)
- **FR-009**: System MUST complete all data collection and analysis within ≤6 hours on a multi-core CPU, 7GB RAM GitHub Actions runner (implementation constraint for CI feasibility) (See US-1, US-2, US-3)
- **FR-010**: System MUST use only CPU-tractable methods (no GPU/CUDA, no low-bit quantization, no deep network training from scratch) (implementation constraint for CI feasibility) (See US-1, US-2, US-3)

### Key Entities *(include if feature involves data)*

- **Issue**: Represents a single GitHub issue with attributes `issue_id`, `repository`, `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, `resolution_time_hours`
- **Repository**: Represents a GitHub project with attributes `repo_id`, `language`, `star_count`, `contributor_count`, `created_at`
- **AnalysisResult**: Represents a statistical test outcome with attributes `test_type`, `predictor`, `p_value`, `effect_size`, `ci_lower`, `ci_upper`, `adjusted_p_value`

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset completeness is measured against GitHub API schema requirements (all required columns populated for ≥95% of collected issues) (See US-1)
- **SC-002**: Distribution goodness-of-fit is measured against Kolmogorov-Smirnov test p-value (reported for at least one parametric family) (See US-2)
- **SC-003**: Hypothesis test validity is measured against Holm-Bonferroni adjusted p-values (significant associations reported only when adjusted p<0.05) (See US-3)
- **SC-004**: Model predictive performance is measured against leave-one-repository-out cross-validation MAE and R² metrics (R² [deferred] expected ≥0.15 from prior literature) (See US-3)
- **SC-005**: Compute feasibility is measured against GitHub Actions free-tier constraints (total runtime ≤6h, memory ≤7GB, no GPU usage) (See US-1, US-2, US-3)

## Assumptions

- GitHub REST API rate limits allow collection of ≥100 repositories × ~500 issues each within 6 hours ([deferred] API calls with exponential backoff)
- The GitHub API provides all required variables: `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`, and repository `language` field
- Resolution times follow a right-skewed distribution (log-normal or Weibull) based on prior software engineering literature
- The GitHub API does not provide post-issue-closure metrics (e.g., user satisfaction); the study is limited to metadata available at closure time
- Mixed-effects modeling with `pymer4` or `statsmodels` can execute within 7GB RAM for the expected dataset size ([deferred] issues)
- Holm-Bonferroni correction is appropriate for the multiple comparison problem (family-wise error rate control across ≥3 hypothesis tests)
- Observational design means all reported associations are correlational; no causal claims will be made about label presence or contributor count effects
- The 100-repository sample will span ≥5 programming languages and ≥3 project size categories (measured by star count)