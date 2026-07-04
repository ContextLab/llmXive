# Research and Methodology Documentation

**Project**: Statistical Analysis of Publicly Available Election Poll Aggregates (PROJ-206)
**Version**: 1.0
**Date**: 2023-10-27

## 1. Overview

This document details the mathematical formulations, implementation strategies, and architectural decisions for the statistical analysis pipeline. It explicitly addresses the three primary forecasting methods implemented: Simple Averaging, Accuracy-Weighted Averaging, and Bayesian Hierarchical Modeling (Random Walk). It also documents specific "Sanctioned Architectural Exceptions" where the implementation deviates from the initial project plan to align with feature specifications or hypothesis testing requirements.

## 2. Data Sources and Harmonization

### 2.1 Primary Data Sources
- **FiveThirtyEight Poll Data**: Raw polling data is ingested from the FiveThirtyEight public repository (`https://projects.fivethirtyeight.com/polls/`). This dataset provides granular polling information including sample sizes, margins of error, and pollster identifiers.
- **Election Outcomes**: Ground truth data is sourced from the MIT Election Data and Science Lab (MEDSL) or the Federal Election Commission (FEC) to validate forecast accuracy. [UNRESOLVED-CLAIM: c_d91d886c — status=not_enough_info]

### 2.2 Data Harmonization
- **Date Unification**: All dates are parsed and normalized to ISO 8601 format.
- **Temporal Binning**: Data is aggregated into weekly bins to reduce noise and align with the temporal resolution of the Bayesian model.
- **Missing Data Handling**: Polls with missing sample sizes or vote shares are excluded prior to analysis.

## 3. Methodological Formulations

### 3.1 Simple Unweighted Averaging
The simplest baseline method, serving as a control for more complex models.

**Formulation**:
For a given election cycle $E$ and time $t$, the forecast $\hat{y}_{t}$ is the arithmetic mean of all available polls $P$ within the current weekly bin:

$$ \hat{y}_{t} = \frac{1}{N} \sum_{i=1}^{N} p_{i,t} $$

Where:
- $p_{i,t}$ is the vote share reported by poll $i$ at time $t$.
- $N$ is the total number of polls in the bin.

**Assumptions**: All polls are equally reliable; systematic biases are uncorrelated or cancel out.

### 3.2 Accuracy-Weighted Averaging
This method assigns weights to polls based on the historical performance of the pollster.

**Formulation**:
The forecast is a weighted sum:

$$ \hat{y}_{t} = \sum_{i=1}^{N} w_{i} \cdot p_{i,t} $$

Where the weight $w_{i}$ for pollster $j$ is derived from the inverse of their historical Root Mean Square Error (RMSE):

$$ w_{j} = \frac{1 / \text{RMSE}_{j}}{\sum_{k=1}^{M} (1 / \text{RMSE}_{k})} $$

**Historical RMSE Calculation**:
$$ \text{RMSE}_{j} = \sqrt{\frac{1}{K} \sum_{k=1}^{K} (p_{j, k} - y_{k})^2} $$
- Calculated using an out-of-sample temporal split (weights for cycle $T$ use only cycles $< T$).
- A default median weight is assigned to pollsters with no historical data to prevent division by zero.

### 3.3 Bayesian Hierarchical Model (Random Walk)
A dynamic model that captures temporal evolution of voter preference.

**Formulation**:
Let $\theta_t$ be the latent true preference at week $t$. The model assumes a Random Walk process:

$$ \theta_t \sim \mathcal{N}(\theta_{t-1}, \sigma_{\text{rw}}^2) $$

Where $\sigma_{\text{rw}}$ is the volatility parameter.

**Observation Model**:
Each poll $i$ at time $t$ is an observation of the latent state with noise:

$$ p_{i,t} \sim \mathcal{N}(\theta_t, \tau_i^2 + \sigma_{\text{obs}}^2) $$

Where:
- $\tau_i^2$ is the poll-specific variance (often derived from sample size).
- $\sigma_{\text{obs}}^2$ is the global observation noise.

**Inference**:
- **Sampler**: No-U-Turn Sampler (NUTS) via PyMC.
- **Execution**: CPU-only, constrained RAM.
- **Convergence**: Monitored via $\hat{R}$ (R-hat) statistic. The pipeline halts if $\hat{R} > 1.05$.

## 4. Evaluation Metrics

### 4.1 Predictive Accuracy
- **RMSE**: $\sqrt{\frac{1}{n}\sum(\hat{y}_i - y_i)^2}$
- **MAE**: $\frac{1}{n}\sum|\hat{y}_i - y_i|$

### 4.2 Coverage Reliability
- **Credible Interval Coverage**: The proportion of actual election outcomes falling within the predicted 95% credible intervals.
- **Binomial Test**: A hypothesis test ($H_0: p = 0.95$) is performed with $\alpha=0.05$ to verify if the observed coverage rate is statistically consistent with the nominal level.

### 4.3 Model Comparison
- **Diebold-Mariano (DM) Test**: A pairwise test to determine if the predictive accuracy of two forecasts is significantly different.
- **Loss Differential**: $d_t = L(e_{1,t}) - L(e_{2,t})$.
- **Correction**: Westfall-Young step-down max-t correction is applied to account for multiple comparisons (1000 permutations).

## 5. Sanctioned Architectural Exceptions

The following deviations from the initial Project Plan were implemented to satisfy Feature Specifications (Spec) or to conduct specific hypothesis tests. These are documented here as sanctioned exceptions.

### 5.1 Exclusion of RealClearPolitics (RCP) Data
- **Spec Requirement**: FR-001 deviation.
- **Plan Constraint**: The Plan excluded RCP based on the "Verified Accuracy" principle due to historical concerns about aggregation methodology.
- **Implementation**: The `download.py` module explicitly excludes RCP sources.
- **Documentation**: A "Source Excluded" warning is logged during execution, citing the Plan's principle. This is a deliberate architectural choice to maintain data integrity standards defined in the Plan, even though the Spec mentions RCP in passing. The exclusion is enforced to prevent potential bias from unverified aggregation methods.

### 5.2 Bayesian Random Walk vs. Static Parameter
- **Spec Requirement**: FR-005 mandates a Random Walk hierarchical model.
- **Plan Constraint**: The Plan initially preferred a "Static Parameter" model for simplicity and computational efficiency.
- **Exception**: The implementation adopts the **Random Walk** structure ($\theta_t \sim \mathcal{N}(\theta_{t-1}, \sigma^2)$) as required by the Spec.
- **Rationale**: This is treated as a hypothesis test. The Random Walk model is expected to better capture dynamic shifts in voter sentiment closer to election day compared to a static model. The deviation is documented to track the performance difference between the Spec-mandated dynamic approach and the Plan's preferred static approach.

### 5.3 Diebold-Mariano Test Implementation
- **Spec Requirement**: FR-006 requires pairwise DM tests with Westfall-Young correction.
- **Plan Constraint**: The Plan rejected the DM test for static forecasts, arguing it was unnecessary for the proposed scope.
- **Exception**: The implementation includes the full **Diebold-Mariano test** with **Westfall-Young correction** (1000 permutations, step-down max-t).
- **Rationale**: The Spec mandates rigorous statistical comparison (SC-003). Even though the Plan questioned its necessity, the implementation proceeds to provide a robust, statistically significant comparison of predictive accuracy between the Simple, Weighted, and Bayesian methods. This serves as the sole implementation of SC-003.

## 6. Conclusion

This pipeline integrates three distinct forecasting methodologies, each grounded in established statistical theory. By adhering to the Spec's requirements while documenting deviations from the Plan as "Sanctioned Architectural Exceptions," the project ensures both compliance with user stories and transparency regarding architectural trade-offs. The results will provide a comprehensive comparison of static averaging, accuracy-weighted methods, and dynamic Bayesian inference in the context of election polling.