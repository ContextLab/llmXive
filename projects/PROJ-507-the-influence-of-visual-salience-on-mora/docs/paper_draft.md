# The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## 1. Introduction
(Content from previous sections)

## 2. Related Work
(Content from previous sections)

## 3. Methods
(Content from T038a - see Section 3.1 for CLMM specification, data cleaning, and ordinal post-hoc corrections)

### 3.1 Methods
(Detailed description of CLMM model specification, data cleaning procedures, and ordinal post-hoc corrections)

## 4. Results

### 4.1 Results

**Table 1: Cumulative Link Mixed Model (CLMM) Results**
| Predictor | Estimate (β) | SE | 95% CI | Odds Ratio | p-value |
|-----------|--------------|----|--------|------------|---------|
| Salience (Medium) | [VALUE] | [VALUE] | [LOWER, UPPER] | [VALUE] | [VALUE] |
| Salience (High) | [VALUE] | [VALUE] | [LOWER, UPPER] | [VALUE] | [VALUE] |
| (Intercept 1) | [VALUE] | [VALUE] | - | - | - |
| (Intercept 2) | [VALUE] | [VALUE] | - | - | - |
| (Intercept 3) | [VALUE] | [VALUE] | - | - | - |

*Note: Reference level for Salience is Low. Random intercepts included for Participant and Scenario.*

**Table 2: Ordinal Post-Hoc Pairwise Comparisons (Tukey-adjusted)**
| Comparison | Estimate | SE | 95% CI | Odds Ratio | Adjusted p-value |
|------------|----------|----|--------|------------|------------------|
| Medium vs Low | [VALUE] | [VALUE] | [LOWER, UPPER] | [VALUE] | [VALUE] |
| High vs Low | [VALUE] | [VALUE] | [LOWER, UPPER] | [VALUE] | [VALUE] |
| High vs Medium | [VALUE] | [VALUE] | [LOWER, UPPER] | [VALUE] | [VALUE] |

**Table 3: Model Fit and Precision Metrics**
| Metric | Value |
|--------|-------|
| Convergence Status | [CONVERGED/FAILED] |
| AIC | [VALUE] |
| BIC | [VALUE] |
| Log-Likelihood | [VALUE] |
| CI Width (Primary Coefficient) | [VALUE] |
| Precision Adequate (CI Width < 0.1) | [TRUE/FALSE] |
| Power Adequate (Power ≥ 0.80) | [TRUE/FALSE] |
| Estimated Power | [VALUE] |

**Summary of Findings:**
- The primary analysis using Cumulative Link Mixed Models (CLMM) [indicated/revealed] a [significant/non-significant] effect of visual salience on moral blame ratings.
- The confidence interval width for the primary salience coefficient was [VALUE], which [met/did not meet] the precision threshold of 0.1.
- Post-hoc power analysis indicated [adequate/inadequate] statistical power (Power = [VALUE]).
- [If fallback was used]: The primary CLMM model failed to converge; results are based on the [LMM with Cluster-Robust SE / Non-parametric Bootstrap CLMM] fallback model.

## 5. Discussion
(Content from previous sections)

## 6. Conclusion
(Content from previous sections)

## References
(Content from previous sections)

## Appendices
### Appendix A: Stimulus Manifest
(Link to data/processed/stimulus_manifest.json)

### Appendix B: Data Cleaning Code
(Link to code/data_cleaning.py)

### Appendix C: Analysis Code
(Link to code/analysis.py)