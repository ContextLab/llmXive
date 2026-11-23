# Analysis Plan: Missing Data and Imputation Strategies

## Missing Data Assessment
- **Pattern**: Evaluate if missingness is MCAR, MAR, or MNAR using Little's test
- **Extent**: Report percentage of missing data per variable
- **Thresholds**:
 - ≤5%: Complete-case analysis acceptable
 - 5-20%: Multiple imputation recommended
 - >20%: Sensitivity analysis required; consider excluding variable

## Imputation Strategies

### Multiple Imputation (MI)
- **Method**: Predictive Mean Matching (PMM)
- **Imputations**: m = 20
- **Variables**: All variables with >5% missingness
- **Software**: `statsmodels` or `sklearn.impute.IterativeImputer`

### Complete-Case Analysis
- Used if ≤5% missing or if MI fails convergence
- Report number of excluded studies

### Sensitivity Analysis
- **Worst-case**: Impute missing outcomes as no effect
- **Best-case**: Impute missing outcomes as maximum effect
- Compare pooled estimates across scenarios

## Heterogeneity Handling
- **I² > 50%**: Use random-effects model (DerSimonian-Laird or REML)
- **I² ≤ 50%**: Fixed-effects model acceptable
- **Subgroup Analysis**: If heterogeneity persists, explore moderators:
 - Mindfulness component
 - Delivery format
 - Social skill domain
 - Follow-up duration

## Publication Bias
- **Funnel Plot**: Only if N ≥ 10
- **Egger's Test**: Only if N ≥ 10
- **Trim-and-Fill**: If asymmetry detected, report adjusted estimate

## Reporting
- **PRISMA Flow Diagram**: Study selection process
- **Table of Study Characteristics**: Sample sizes, interventions, outcomes
- **Forest Plot**: Individual and pooled effect sizes
- **Heterogeneity Statistics**: I², Q, p-value
- **Publication Bias Assessment**: Funnel plot, Egger's test results
