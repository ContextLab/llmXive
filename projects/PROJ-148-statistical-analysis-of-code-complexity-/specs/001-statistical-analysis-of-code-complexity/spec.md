# Specification: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Project ID**: PROJ-148
**Status**: Active
**Last Updated**: 2023-10-27

## 1. Executive Summary

This project aims to investigate the relationship between static code complexity metrics and the likelihood of a code unit (function/method) containing a bug. We will analyze a dataset of Java projects extracted from GHTorrent, compute standard complexity metrics (Cyclomatic Complexity, LOC, Halstead, etc.), and train predictive models to identify bug-prone code. The ultimate goal is to provide actionable thresholds for developers and verify statistical significance of the findings.

## 2. Research Questions & Hypotheses

- **RQ1**: Do code complexity metrics significantly predict the presence of bugs in Java code?
 - *H1*: Higher values of complexity metrics (CC, LOC, Halstead Volume) are positively correlated with bug occurrence.
- **RQ2**: Can a simple L1-regularized logistic regression model achieve comparable predictive performance to a Random Forest model?
 - *H2*: The L1 model will achieve ROC-AUC within ±0.05 of the Random Forest model while providing more interpretable coefficients.
- **RQ3**: What are the practical threshold values for complexity metrics that indicate a high probability of bugs?
 - *H3*: Specific thresholds (e.g., CC > 10) will be identified that correspond to a predicted bug probability ≥ 0.5.

## 3. Data Source & Acquisition

- **Source**: GHTorrent (GitHub Archive).
- **Target**: Java projects with active issue trackers and commit histories.
- **Minimum Sample**: 10 distinct Java projects.
- **Extraction**:
 - Download project archives.
 - Extract Java source files (`.java`).
 - Extract commit metadata (hash, message, files changed).
 - Link commits to issues (bug labels) via regex matching in commit messages (e.g., "Fixes #123").

## 4. Data Model

The primary dataset will be a tabular structure (CSV) with the following columns:

| Column Name | Type | Description |
|:--- |:--- |:--- |
| `file_path` | String | Relative path to the source file. |
| `function_name` | String | Name of the function/method. |
| `start_line` | Integer | Starting line number. |
| `end_line` | Integer | Ending line number. |
| `cyclomatic_complexity` | Integer | Cyclomatic complexity (M). |
| `loc` | Integer | Lines of Code. |
| `token_count` | Integer | Total token count. |
| `nesting_depth` | Integer | Maximum nesting depth. |
| `halstead_volume` | Float | Halstead Volume. |
| `bug_label` | Integer | 1 if the function was modified in a bug-fix commit, 0 otherwise. |
| `project_id` | String | Identifier for the source project (for stratification). |

## 5. Methodology

### 5.1. Preprocessing
- **Missing Data**: Impute missing values if < 5% of rows are affected; otherwise, drop the row.
- **Transformation**: Apply log-transformation to metrics with skewness > 2 to normalize distributions.
- **Outliers**: Remove rows with > 5% missing values across all features.

### 5.2. Train/Test Split
- **Strategy**: Project-level stratified split to prevent data leakage (a project must not appear in both sets).
- **Proportions**: 70% Train / 30% Test.
- **Validation**: Ensure each project appears in exactly one split.

### 5.3. Modeling
- **Primary Model**: L1-Regularized Logistic Regression (max 100 iterations).
 - *Constraint*: Must converge and have at least one non-zero coefficient.
- **Alternative Model**: Random Forest Classifier (100 trees, max depth 10).
- **Collinearity**: Perform VIF analysis; drop features with VIF > 10 before modeling.

### 5.4. Evaluation
- **Metrics**: ROC-AUC, PR-AUC, Calibration plots.
- **Baseline**: ROC-AUC ≥ 0.50 (random chance).
- **Significance**: Apply Benjamini-Hochberg correction for multiple hypothesis testing.
 - *Constraint*: False Discovery Rate (FDR) must be ≤ 0.05.

## 6. Deliverables

1. **Cleaned Dataset**: `data/processed/bug_complexity_dataset.csv`
2. **Train/Test Splits**: `data/processed/train_split.csv`, `data/processed/test_split.csv`
3. **Model Artifacts**: `data/model/primary.pkl`, `data/model/alternative.pkl`
4. **Evaluation Reports**:
 - `data/model/corrected_pvalues.csv`
 - `data/model/thresholds.csv`
 - `figures/pdp_top3.png` (Partial Dependence Plots)
5. **Research Report**: `reports/final_report.pdf`

## 7. Implementation Strategy

The implementation follows a phased approach:

- **Phase 0**: Contracts & Schemas (Define data structures and validation rules).
- **Phase 1**: Setup (Project initialization, dependencies).
- **Phase 2**: Foundational (Logging, config, utility functions).
- **Phase 3**: User Story 1 (Data Acquisition & Preprocessing).
 - Download data, extract metrics, label bugs, preprocess, split dataset.
- **Phase 4**: User Story 2 (Statistical Modeling).
 - Collinearity check, train primary/alternative models, compare performance.
- **Phase 5**: User Story 3 (Evaluation & Reporting).
 - Evaluate models, correct p-values, generate PDPs, thresholds, and final report.
- **Phase N**: Polish (Linting, testing, documentation).

## 8. Constraints & Assumptions

- **Language**: Python 3.11.
- **Dependencies**: pandas, scikit-learn, lizard, statsmodels, matplotlib, seaborn, pymer4.
- **Reproducibility**: All random seeds must be fixed via `code/utils/config.py`.
- **Data Integrity**: Checksums must be verified for all downloaded archives.
- **Memory**: Processing must be chunked to handle large repositories within modest RAM limits.

## 9. Risk Management

- **Risk**: Low bug-label reliability.
 - *Mitigation*: Validate labels with precision ≥ 85% before modeling; fallback to manual review if needed.
- **Risk**: Model non-convergence.
 - *Mitigation*: Increase iterations or adjust regularization strength; log warnings.
- **Risk**: Data leakage in split.
 - *Mitigation*: Enforce project-level stratification with strict assertions.