# Constitution Amendment 001: Statistical Methodology Update

**Date**: 2023-10-27
**Status**: DRAFT FOR RATIFICATION
**Affects**: Principle VII (Statistical Rigor)
**Related FR**: FR-006 (Bayesian Hierarchical Modeling)

## 1. Preamble

The current Constitution Principle VII mandates the use of "repeated-measures ANOVA" for analyzing within-subject effects in experimental designs. This amendment proposes replacing this mandate with "Bayesian Hierarchical Modeling (BHM)" for the specific context of the **Quantization Robustness of Multi-Effect LoRA Adapters** study (Project PROJ-892).

## 2. Scientific Justification

### 2.1 The Failure of ANOVA in Small-N Designs
The study design involves a limited number of distinct "effects" (N=10) acting as the repeated measure units. A standard repeated-measures ANOVA assumes:
1. **Normality of Residuals**: With N=10, the Central Limit Theorem does not guarantee normality of the sampling distribution of the mean, making F-tests highly sensitive to non-normality.
2. **Sphericity**: The assumption that variances of differences between all pairs of within-subject conditions are equal is statistically impossible to verify or robustly correct for with such a low degrees of freedom (df = 9).
3. **Power**: With N=10, the power to detect anything but massive effect sizes is negligible. The "N=5" reduction scenario (mentioned in the convergence panel concern) renders ANOVA completely non-functional (df=4), leading to a guaranteed Type II error or undefined F-statistics.

### 2.2 Validity of Bayesian Hierarchical Modeling (BHM)
BHM is not merely a "fallback" but a superior method for this specific design because it addresses the "double failure" concern by leveraging **partial pooling**:

1. **Shrinkage Estimation**: BHM models the effects of quantization on each LoRA adapter as draws from a common population distribution. Instead of estimating 10 independent means (which is unstable with low N), it shrinks extreme estimates toward the global mean. This reduces variance in the estimates without introducing the bias of a fixed-effects model.
2. **Explicit Uncertainty Quantification**: Unlike ANOVA's binary p-value (significant/not significant), BHM provides a full posterior distribution for the effect size. This allows us to explicitly state: "There is a 95% probability that the concept bleeding increases by between X and Y units." This is scientifically more informative when N is small.
3. **Robustness to Non-Normality**: By using appropriate likelihood functions (e.g., Student-t) and priors, BHM is robust to the non-normality that plagues ANOVA in small samples.
4. **Handling Hierarchical Structure**: The data structure (measurements nested within prompts, nested within effects) is naturally encoded in the model hierarchy, avoiding the "pseudoreplication" errors common in ANOVA when the hierarchy is ignored.

## 3. The Amendment

**Principle VII** is hereby amended to read:

> "Statistical analysis for experiments with low sample sizes (N < 30) or complex hierarchical structures shall prioritize **Bayesian Hierarchical Modeling (BHM)** over frequentist repeated-measures ANOVA. BHM must be used to estimate effect sizes with full posterior distributions, explicitly quantifying uncertainty via credible intervals. ANOVA may only be used if the sample size is sufficient to satisfy sphericity and normality assumptions with adequate power (N ≥ 30)."

## 4. Implementation Plan for PROJ-892

1. **Model Specification**: Define a BHM where `concept_bleeding ~ quantization_level + (1 | effect_prompt)`.
2. **Prior Selection**: Use weakly informative priors (e.g., `Normal(0, 1)`) for fixed effects and `HalfNormal(0.5)` for group-level standard deviations to prevent overfitting.
3. **Validation**: Perform posterior predictive checks to ensure the model fits the observed data distribution.
4. **Reporting**: Report the 95% Highest Density Interval (HDI) for the quantization effect. If the HDI excludes zero, the effect is considered statistically significant.

## 5. Conclusion

Replacing ANOVA with BHM resolves the "double failure" risk. While ANOVA fails due to lack of power and assumption violations, BHM succeeds by borrowing strength across the 10 effects, providing a valid, interpretable, and scientifically rigorous answer to the research question even with a small N.
