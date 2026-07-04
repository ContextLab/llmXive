# Specification: Code Ownership Analysis

## User Stories

### US1: Repository Data Collection
As a researcher, I want to clone repositories and parse commit history so that I can calculate ownership and bug counts.
- **Acceptance Criteria**:
 - Repos cloned with depth 1000 (or full history if <1000).
 - Intermediate CSVs generated for commits and issues.
 - Path normalization applied for bug linking.

### US2: Metric Calculation
As an analyst, I want to calculate Gini, churn, complexity, and bug density so that I can prepare data for correlation.
- **Acceptance Criteria**:
 - Gini coefficient calculated per module.
 - Bug density normalized by KLOC.
 - Cyclomatic complexity calculated for Python files.
 - Modules deleted between T and T+1 are excluded.

### US3: Statistical Analysis
As a stakeholder, I want to see correlation coefficients and sensitivity analysis so that I can understand the robustness of the findings.
- **Acceptance Criteria**:
 - Spearman correlation reported with p-values.
 - VIF calculated for all predictors.
 - Non-linearity tested via quadratic model.
 - Sensitivity sweeps for p-values and rho cutoffs.

## Functional Requirements
- **FR-009**: Path normalization (lowercase, strip extensions).
- **FR-013**: VIF calculation for multicollinearity.
- **FR-016**: Non-linearity test via LRT and t-test on Gini².

## Sensitivity Constraints
- **SC-008**: P-value sweep set {0.01, 0.05, 0.1}.
- **SC-011**: Correlation magnitude sweep set {0.2, 0.3, 0.4}.
