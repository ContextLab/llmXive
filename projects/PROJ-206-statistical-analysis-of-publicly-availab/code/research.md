# Research and Architectural Decisions: Statistical Poll Aggregation

## Overview
This document outlines the mathematical formulations for the implemented methods and
explicitly documents the **Sanctioned Architectural Exceptions** where the project
specification (Spec) overrides the initial planning document (Plan).

## Mathematical Formulations

### 1. Simple Average (Frequentist)
For a given weekly bin $t$, the forecast is the arithmetic mean of all poll vote shares $y_i$ in that bin:
$$ \hat{\theta}_t = \frac{1}{N_t} \sum_{i=1}^{N_t} y_i $$
Where $N_t$ is the number of polls in week $t$.

### 2. Accuracy-Weighted Average (Frequentist)
Weights $w_i$ are assigned based on the inverse of the pollster's historical RMSE ($R_i$):
$$ w_i = \frac{1/R_i}{\sum_{j=1}^{N_t} (1/R_j)} $$
The forecast is the weighted mean:
$$ \hat{\theta}_t = \sum_{i=1}^{N_t} w_i y_i $$

### 3. Bayesian Random Walk Hierarchical Model
**Formulation:**
Let $\theta_t$ be the latent true preference at week $t$.
- **Prior (Initial State):** $\theta_0 \sim \text{Normal}(\mu_0, \sigma_0^2)$
- **Transition (Random Walk):** $\theta_t \sim \text{Normal}(\theta_{t-1}, \sigma_{rw}^2)$
- **Observation:** $y_i \sim \text{Normal}(\theta_{t(i)}, \tau_i^2)$
 Where $t(i)$ is the week bin for poll $i$, and $\tau_i$ is the observation noise derived from sample size and historical RMSE.

This model captures the dynamic nature of voter preference over time, unlike static models.

## Sanctioned Architectural Exceptions

The project specification (Spec) mandates certain methods that contradict the initial
planning document (Plan). These deviations are intentional, documented here as
"Sanctioned Architectural Exceptions," and serve as hypothesis tests.

### Exception 1: Random Walk vs. Static Parameter (Task T021)
- **Plan Decision:** The Plan favored a "Static Parameter" model for simplicity and robustness.
- **Spec Mandate:** The Spec (FR-005) requires a **Random Walk** hierarchical model.
- **Implementation:** This project implements the **Random Walk** model as per the Spec.
- **Rationale:** This is a hypothesis test to determine if dynamic tracking of voter preference
 (Random Walk) provides superior predictive accuracy compared to a static aggregation approach
 in volatile election cycles. The results will be compared using Diebold-Mariano tests.

### Exception 2: Diebold-Mariano Test with Westfall-Young Correction (Task T026)
- **Plan Decision:** The Plan rejected the Diebold-Mariano (DM) test for static forecasts,
 citing potential issues with autocorrelation in static contexts.
- **Spec Mandate:** The Spec (FR-006) requires pairwise **Diebold-Mariano tests** with
 **Westfall-Young correction** for multiple comparisons.
- **Implementation:** This project implements the DM test as per the Spec.
- **Rationale:** The DM test is the standard for comparing predictive accuracy of time series
 forecasts. The Westfall-Young correction addresses the multiple testing problem rigorously.
 This implementation tests the hypothesis that the Random Walk model's dynamic nature
 produces statistically significant improvements over frequentist baselines.

### Exception 3: Exclusion of RCP Data (Task T009b)
- **Plan Decision:** The Plan excluded RealClearPolitics (RCP) due to "Verified Accuracy" concerns.
- **Spec Mandate:** The Spec initially included RCP but was updated to align with the Plan's
 exclusion principle.
- **Implementation:** RCP data is explicitly excluded. A warning is logged citing the "Verified Accuracy" principle.
- **Rationale:** To ensure data quality and consistency, only sources with verified track records
 (FiveThirtyEight) are used. This is a data integrity safeguard.

## Conclusion
These exceptions are not oversights but deliberate choices to validate specific scientific hypotheses
regarding poll aggregation methodologies. The project prioritizes the Spec's requirements for
rigorous statistical comparison while documenting the Plan's concerns as risks and alternative
hypotheses.
