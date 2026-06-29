# Feature Specification: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Feature Branch**: `001-code-complexity-bug-prediction`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Code Complexity Metrics and Bug Prediction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing (Priority: P1)

A researcher downloads open-source Java projects from GHTorrent, extracts commit history and issue tracker data to label bug-fix occurrences, computes code complexity metrics using lizard, and produces a clean, stratified dataset ready for analysis.

**Why this priority**: This is the foundational data pipeline; without a valid, labeled dataset, no statistical analysis can proceed. It delivers the essential input for all downstream modeling.

**Independent Test**: Can be fully tested by verifying the output dataset contains ≥10,000 code units with complete bug labels and all required complexity metrics, and that stratified train/test splits ([deferred]/30%) are reproducible.

**Acceptance Scenarios**:

1. **Given** a list of 10+ open-source Java projects from GHTorrent, **When** the data acquisition pipeline runs, **Then** the output dataset contains ≥10,000 code units (files or functions) with binary bug labels and at least 5 complexity metrics per unit.
2. **Given** a dataset with missing values in <5% of rows, **When** preprocessing completes, **Then** missing values are imputed or removed and all numeric metrics are log-transformed if skewness >2.
3. **Given** the full dataset, **When** the stratified split executes, **Then** the training set contains [deferred] of samples and the test set contains [deferred], with project-level stratification preventing data leakage.

---

### User Story 2 - Statistical Modeling and Metric Selection (Priority: P2)

A researcher fits at least one predictive model (e.g., logistic regression with L1 regularisation, random forest, or other supervised classifier) to identify the most predictive complexity metrics, runs additional models as robustness checks, and produces variable importance rankings.

**Why this priority**: This delivers the core analytical output—identifying which metrics predict bugs. It builds on the data pipeline and enables interpretation and threshold setting.

**Independent Test**: Can be fully tested by verifying the primary model converges, returns at least one non-zero coefficient or feature importance score, and alternative models produce comparable ROC-AUC (within ±0.05) on the held-out test set.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with ≥5 complexity metrics, **When** the primary predictive model fits, **Then** the model converges within 100 iterations and identifies at least one metric with non-zero coefficient or feature importance.
2. **Given** the same training data, **When** an alternative model trains (e.g., random forest with 100 trees, max depth 10), **Then** it achieves ROC-AUC within ±0.05 of the primary model on the held-out test set.
3. **Given** fitted models, **When** variable importance is extracted, **Then** the top-ranked metrics are documented and compared across models.

---

### User Story 3 - Evaluation, Inference, and Reporting (Priority: P3)

A researcher evaluates model performance on the held-out test set, generates partial dependence plots for top metrics, and documents practical thresholds for developers.

**Why this priority**: This delivers the final scientific output—validated associations and actionable thresholds. It depends on both data acquisition and modeling.

**Independent Test**: Can be fully tested by verifying the test set ROC-AUC is computed, partial dependence plots are generated for the top 3 metrics, and threshold documentation is produced.

**Acceptance Scenarios**:

1. **Given** a fitted predictive model, **When** evaluation runs on the [deferred] test set, **Then** ROC-AUC and precision-recall AUC are computed and documented.
2. **Given** fitted models with at least 2 metrics showing predictive signal, **When** multiple hypothesis testing correction is applied, **Then** the false discovery rate is controlled at α=0.05 using an appropriate method for the model type.
3. **Given** the top 3 metrics by coefficient magnitude or feature importance, **When** partial dependence plots generate, **Then** each plot documents the observed relationship between metric value and predicted bug probability.

---

### Edge Cases

- What happens when a project has <100 bug-fix commits (insufficient positive samples for stratified split)?
- How does the system handle metrics that are highly collinear (e.g., lines of code and token count)?
- What happens when lizard fails to parse a file (syntax errors, unsupported Java version)?
- How does the system handle imbalanced outcomes (e.g., [deferred] non-buggy, [deferred] buggy files)?
- What happens when the dataset exceeds available RAM on the execution environment?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download ≥10 open-source Java projects from GHTorrent, extract commit history and issue tracker data to label code units as bug-fix or non-bug-fix, and produce a dataset with ≥10,000 code units (See US-1)
- **FR-002**: System MUST compute ≥5 complexity metrics per code unit using lizard (cyclomatic complexity, lines of code, token count, nesting depth, Halstead volume) at the file level, with optional function-level breakdown (See US-1)
- **FR-003**: System MUST log-transform metrics with skewness >2 and impute or remove rows where missing values constitute <5% of total rows (See US-1)
- **FR-004**: System MUST split the dataset into training ([deferred]) and test ([deferred]) sets with project-level stratification to prevent data leakage (See US-1)
- **FR-005**: System MUST fit at least one predictive model (e.g., logistic regression with L1 regularisation, random forest, or other supervised classifier) that converges and identifies at least one metric with predictive signal (See US-2)
- **FR-006**: System MUST train at least one alternative model (e.g., random forest with 100 trees, max depth 10 if logistic regression is primary) and compare variable importance across models (See US-2)
- **FR-007**: System MUST evaluate model performance on the held-out test set and compute ROC-AUC, precision-recall AUC, and calibration plots (See US-3)
- **FR-008**: System MUST apply multiple hypothesis testing correction to regression p-values using an appropriate method for the model type (e.g., selective inference for regularized models, or Benjamini–Hochberg for unregularized models) (See US-3)
- **FR-009**: System MUST generate partial dependence plots for the top 3 metrics and document practical thresholds in tabular format with metric name, threshold value, and justification (See US-3)

### Key Entities *(include if file involves data)*

- **CodeUnit**: Represents a file in the source code (with optional function-level breakdown); key attributes include project_id, file_path, line_count, and bug_label
- **ComplexityMetrics**: Represents computed code metrics; key attributes include cyclomatic_complexity, lines_of_code, token_count, nesting_depth, halstead_volume
- **BugLabel**: Represents the binary outcome variable; key attributes include code_unit_id, is_bug_fix (boolean), and source (commit message / issue tracker)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Test set ROC-AUC is measured against the baseline of random prediction (AUC=0.50) to validate predictive power (See US-3)
- **SC-002**: False discovery rate is measured against the α=0.05 threshold using an appropriate correction method for the model type to validate statistical inference (See US-3)
- **SC-003**: Variable importance rankings are measured across models using Spearman rank correlation ≥0.7 to validate metric stability (See US-2)

## Assumptions

- GHTorrent provides sufficient Java project data with accessible commit history and issue tracker metadata for ≥10 projects
- The lizard tool can parse all target Java files without syntax errors or unsupported language features
- Bug-fix labels derived from commit messages and issue tracker keywords are sufficiently accurate (≥85% precision) for statistical analysis
- The dataset of ≥10,000 code units with 5+ complexity metrics will fit within available RAM on the execution environment
- The analysis is observational (no random assignment), so all findings will be framed as associational, not causal
- Cyclomatic complexity and nesting depth are primary metrics of interest based on prior defect-prediction literature, but their ranking is exploratory
- If multiple hypothesis tests are run, family-wise error correction will control the false discovery rate using an appropriate method for the model type
- Any decision thresholds (e.g., p<0.05, ROC-AUC≥0.70) are justified by community standards in software defect prediction research
- If two predictors are definitionally related (e.g., lines of code and token count), collinearity diagnostics will be required and independent effects will not be claimed
- L1-regularized logistic regression does not produce valid standard p-values; p-value inference requires either unregularized models or specialized selective inference methods