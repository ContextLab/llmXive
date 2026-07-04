# Research Documentation: Statistical Analysis of Publicly Available Election Poll Aggregates

## Overview

This document details the mathematical formulations for the three forecasting methods implemented in the llmXive project (PROJ-206) and explicitly records the **Sanctioned Architectural Exceptions** where the project's implementation deviates from the initial `plan.md` to satisfy the `spec.md` requirements.

## 1. Mathematical Formulations

### 1.1 Simple Unweighted Averaging (Frequentist)

The simple average forecast for a given week $t$ and candidate $c$ is the arithmetic mean of all available polls $i$ for that week:

$$ \hat{y}_{t,c}^{simple} = \frac{1}{N_t} \sum_{i=1}^{N_t} y_{i,c} $$

Where:
- $N_t$ is the number of polls in week $t$.
- $y_{i,c}$ is the vote share reported by pollster $i$ for candidate $c$.

**Assumption**: All polls are of equal quality.

### 1.2 Accuracy-Weighted Averaging (Frequentist)

The weighted average forecast assigns weights $w_i$ inversely proportional to the pollster's historical Root Mean Squared Error (RMSE):

$$ w_i = \frac{1 / \text{RMSE}_i}{\sum_{j=1}^{N} (1 / \text{RMSE}_j)} $$

$$ \hat{y}_{t,c}^{weighted} = \sum_{i=1}^{N_t} w_i y_{i,c} $$

Where $\text{RMSE}_i$ is calculated using out-of-sample data from previous election cycles (strict temporal split).

**Assumption**: Past accuracy is a reliable predictor of future accuracy.

### 1.3 Bayesian Hierarchical Random Walk Model

The project implements a **Random Walk** hierarchical model, where the latent preference $\theta_t$ for a candidate at time $t$ evolves as:

$$ \theta_t = \theta_{t-1} + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, \sigma_t^2) $$

The observation model for poll $i$ at time $t_i$ is:

$$ y_i = \theta_{t_i} + \nu_i, \quad \nu_i \sim \mathcal{N}(0, \tau_i^2) $$

Where $\tau_i^2$ is the known sampling variance (derived from sample size) plus an overdispersion parameter to account for house effects.

**Inference**: Performed using PyMC's NUTS sampler on CPU.

## 2. Meta-Analysis and Model Comparison

### 2.1 Diebold-Mariano (DM) Test

To compare the predictive accuracy of two forecasts $A$ and $B$, we use the Diebold-Mariano test statistic:

$$ DM = \frac{\bar{d}}{\sqrt{\hat{V}(\bar{d})}} $$

Where $d_t = L(e_{A,t}) - L(e_{B,t})$ is the loss differential series, and $\hat{V}(\bar{d})$ is the long-run variance of $d_t$.

**Loss Function**: Squared Error Loss $L(e) = e^2$.

### 2.2 Westfall-Young Correction

To control the Family-Wise Error Rate (FWER) across multiple pairwise comparisons, we apply the **Westfall-Young step-down max-t permutation correction**.

**Procedure**:
1. Calculate observed DM statistics for all pairs.
2. Permute the loss differential series (via sign flipping) $B=1000$ times.
3. For each permutation, compute the maximum absolute DM statistic.
4. The adjusted p-value for a hypothesis is the proportion of permutations where the max statistic exceeds the observed statistic for that hypothesis.
5. Apply the step-down procedure to ensure monotonicity of adjusted p-values.

## 3. Sanctioned Architectural Exceptions

The following deviations from the `plan.md` were implemented to satisfy specific requirements in `spec.md`. These are documented as "Sanctioned Exceptions" to maintain traceability.

### 3.1 Exception: Random Walk Model (T021)

- **Plan Decision**: The `plan.md` specified a "Static Parameter" model.
- **Spec Requirement**: `spec.md` (FR-005) mandates a "Random Walk" hierarchical model.
- **Action**: Implemented the Random Walk model as per `spec.md`.
- **Justification**: The Random Walk model is more appropriate for election polling where public opinion shifts over time. The static model assumption is too restrictive for the temporal nature of the data.
- **Documentation**: This deviation is recorded here as a hypothesis test (Random Walk vs. Static) and the Spec's requirement takes precedence.

### 3.2 Exception: Diebold-Mariano Test (T026)

- **Plan Decision**: The `plan.md` rejected the Diebold-Mariano test for static forecasts.
- **Spec Requirement**: `spec.md` (FR-006, SC-003) mandates pairwise DM tests with Westfall-Young correction.
- **Action**: Implemented the DM test with Westfall-Young correction.
- **Justification**: The DM test is a standard tool for comparing predictive accuracy of time-series forecasts, even if the underlying models are "static" in parameter estimation but dynamic in application (weekly bins). The Spec's requirement for rigorous statistical comparison overrides the Plan's heuristic rejection.
- **Documentation**: This is the sole implementation of SC-003. The Plan's concern regarding "static" nature is addressed by the fact that the forecasts themselves are time-varying (weekly bins), making the DM test applicable.

### 3.3 Exception: Data Source Exclusion (T009b)

- **Plan Decision**: The `plan.md` mentioned "Verified Accuracy" which excluded certain sources.
- **Spec Requirement**: `spec.md` (FR-001) requires specific data sources but allows for exclusions based on accuracy verification.
- **Action**: Excluded RealClearPolitics (RCP) data.
- **Justification**: RCP data was excluded due to concerns about its accuracy verification process compared to FiveThirtyEight and MEDSL.
- **Documentation**: Documented in `research.md` as a sanctioned architectural exception.

## 4. Conclusion

This project prioritizes the `spec.md` requirements for statistical rigor and methodological completeness. Where the `plan.md` made heuristic decisions that conflicted with these requirements, the Spec's mandates were implemented, with the deviations clearly documented as "Sanctioned Architectural Exceptions". This approach ensures that the final product meets the highest standards of scientific analysis while maintaining transparency about architectural decisions.
