# Deviation Log: Statistical Test Implementation

## Spec Requirement
**FR-006**: Perform a paired t-test to compare error distributions between Group 13 and Conventional ligands.

## Implemented Logic
**Task T035**: Implemented an **unpaired Welch's t-test** to compare error distributions between Group 13 and Conventional ligands.

## Statistical Justification
The original specification (FR-006) requested a **paired t-test**, which assumes that each observation in Group 13 has a corresponding, naturally paired observation in the Conventional group. However, in the context of transition state catalysis:

1. **Independent Groups**: Each reaction sample in the QM9-TS dataset belongs to exactly one ligand class (either Group 13 or Conventional). There is no natural pairing mechanism between individual samples in the two groups.

2. **Different Sample Sizes**: The number of reactions involving Group 13 ligands and Conventional ligands are likely different, which violates the fundamental assumption of paired tests (equal sample sizes with 1:1 correspondence).

3. **Unequal Variances**: Welch's t-test is specifically designed to handle cases where the two groups may have different variances, which is a common scenario in real-world data.

**Conclusion**: An unpaired Welch's t-test is the statistically appropriate choice for comparing two independent groups with potentially unequal variances and sample sizes. The paired t-test would be invalid in this context.

## Spec Update Request
**Request**: Update FR-006 in `spec.md` to reflect the correct statistical methodology:

**Original**: "Perform a paired t-test to compare error distributions between Group 13 and Conventional ligands."

**Proposed Update**: "Perform an unpaired Welch's t-test to compare error distributions between Group 13 and Conventional ligands. This test is appropriate because the two ligand classes represent independent groups with potentially different sample sizes and variances."

## Implementation Details
- **Test**: Welch's t-test (unpaired, unequal variance)
- **Null Hypothesis**: The mean error for Group 13 ligands equals the mean error for Conventional ligands.
- **Alternative Hypothesis**: The mean errors are different.
- **Significance Level**: α = 0.05
- **Output**: `data/results/statistical_tests.json` containing t-statistic, p-value, confidence intervals, and effect size.

## References
- Welch, B. L. (1947). The generalization of Student's problem when several different population variances are involved. *Biometrika*, 34(1-2), 28-35.
- Ruxton, G. D. (2006). The unequal variance t-test is an underused alternative to Student's t-test and the Mann–Whitney U test. *Behavioral Ecology*, 17(4), 688-690.
