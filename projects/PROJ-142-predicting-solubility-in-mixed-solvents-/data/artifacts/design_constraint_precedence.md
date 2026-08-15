# Design Constraint Precedence: Constitution vs. Specification

## Document Purpose
This document formally records the design decision regarding the statistical testing methodology for User Story 2 (Model Training and Baseline Comparison). It establishes the hierarchy of authority when conflicts arise between the project's governing "Constitution" and the functional requirements in the `spec.md`.

## The Conflict
- **Spec FR-005**: Originally mandated the use of the **Wilcoxon signed-rank test** for comparing model performance (XGBoost vs. Abraham baseline). This non-parametric test is typically chosen when data distributions are unknown or non-normal.
- **Constitution Principle VII**: Mandates the use of the **Paired t-test** for statistical significance testing in this research context.

## The Decision
**Constitution Principle VII (Paired t-test) takes precedence over Spec FR-005 (Wilcoxon).**

### Rationale
1. **Governing Authority**: The "Constitution" represents the foundational research principles and methodological constraints established at the project's inception. It supersedes specific functional requirements (FRs) derived during the specification phase.
2. **Statistical Power**: For the expected sample sizes in this solubility dataset (post-filtering), the Paired t-test offers higher statistical power than the Wilcoxon test, provided the differences in absolute errors are approximately normally distributed.
3. **Research Consistency**: The project's research goals (US2) align with standard practices in computational chemistry where paired t-tests are the standard for comparing regression model errors on the same test set.

## Implementation Impact
- **Task T024**: The implementation in `code/04_evaluation.py` **must** use `scipy.stats.ttest_rel` (Paired t-test).
- **Task T024**: Any references to Wilcoxon logic in `code/04_evaluation.py` are hereby invalidated.
- **Output**: The file `data/artifacts/statistical_test_results.json` will contain the t-statistic and p-value derived from the paired t-test.

## Verification
The execution of `code/04_evaluation.py` will be validated by:
1. Confirming the import of `ttest_rel` from `scipy.stats`.
2. Confirming the absence of `wilcoxon` imports or calls in the statistical comparison block.
3. Verifying that `data/artifacts/statistical_test_results.json` contains keys `t_statistic` and `p_value`.

## Status
**Active / Enforced**
*Date: 2023-10-27*
*Authority: Constitution Principle VII*