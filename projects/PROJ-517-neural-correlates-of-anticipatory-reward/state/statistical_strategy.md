# Statistical Strategy Definition

## Parameters

- **Alpha Level**: 0.05
- **Permutation Iterations**: 1000
- **Dispersion Formula**: LRT/AIC (Likelihood Ratio Test / Akaike Information Criterion)

## Methodology

1. **Model Selection**:
 - Calculate dispersion (deviance / degrees of freedom).
 - If dispersion > 1.1, select Negative Binomial model.
 - If dispersion <= 1.1, select Poisson model.

2. **Significance Testing**:
 - Perform Freedman-Lane permutation test.
 - Iterations: 1000.
 - Null hypothesis: No correlation between reward magnitude and firing rate.

3. **Robustness Checks**:
 - Likelihood Ratio Test (LRT) for categorical vs linear reward models.
 - Cross-validation (k-fold) for predictive performance.

## Traceability

- Plan.md Phase 0 Step 3
- SC-001 (Permutation Test Parameters)
