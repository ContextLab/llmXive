# Feature Specification: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Feature Branch**: `001-assessing-the-validity-of-significance`  
**Created**: 2026-07-20  
**Status**: Draft  
**Input**: User description: "Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data"

## Introduction

The goal of this feature is to assess the validity of statistical significance conclusions drawn from **Randomized Controlled Trials (RCTs)** when missing data are present. Publicly available RCT datasets that include genuine treatment and outcome variables are scarce. Consequently, the methodology will also permit the creation of *RCT‑like* datasets by synthesising a treatment indicator and, when necessary, an outcome variable from observational data sources. **This limitation is explicitly acknowledged**: results pertain to RCT‑like scenarios and may not fully generalise to bona‑fide RCTs without genuine randomisation.

## User Scenarios & Testing

### User Story US-1 - Simulate Missing Data Mechanisms and Calculate Empirical Type I Error (Priority: P1)

The researcher needs to generate synthetic missing data patterns (MCAR, MAR, MNAR) on real RCT or RCT‑like datasets with known ground truth (null hypothesis) to calculate the empirical Type I error rate of complete‑case analysis.

**Why this priority**: This is the core scientific engine. Without the ability to simulate missingness and calculate the resulting error rates, the study cannot identify “tipping points” or validate the robustness of complete‑case methods.

**Independent Test**: The system can be tested by running a single simulation loop with a fixed seed, a specific dataset, and a defined missingness rate (e.g., [deferred] MAR), and verifying that the output includes a p‑value distribution and an empirical error‑rate metric.

**Acceptance Scenarios**:

1. **Given** a public RCT or RCT‑like dataset with treatment, outcome, and covariates, **When** the system simulates 20 % missingness under MAR (dependent on age) and sets the treatment effect to zero, **Then** the system outputs a list of p‑values and calculates the proportion of p‑values < 0.05.
2. **Given** the same dataset and missingness rate, **When** the system switches the mechanism to MNAR (dependent on permuted outcome values and permuted treatment assignment), **Then** the system outputs a distinct set of p‑values and a new empirical error rate that differs from the MCAR/MAR result.

### User Story US-2 - Identify Tipping Points via Sensitivity Analysis (Priority: P2)

The researcher needs to systematically vary missingness rates from [deferred] to [deferred] in [deferred] increments and analyze the deviation of the Complete‑Case (CC) method from the nominal 0.05 Type I error rate to identify specific thresholds where the method fails.

**Why this priority**: This transforms raw simulation data into actionable “tipping points” (e.g., > 15 % missingness). This directly addresses the research question regarding when imputation becomes mandatory.

**Independent Test**: The system can be tested by executing a batch simulation across missingness rates {[deferred],[deferred],[deferred],[deferred],[deferred],[deferred],[deferred],[deferred]} and verifying that the output contains a curve or table showing the error‑rate trend and flags the rate where the error exceeds the nominal 0.05 by >10 % relative increase (i.e., error > 0.055).

**Acceptance Scenarios**:

1. **Given** a fixed missingness mechanism (e.g., MNAR), **When** the system runs simulations for the eight rates listed above, **Then** the system generates a data series showing the empirical Type I error rate for each step.
2. **Given** the data series from the previous step, **When** the system compares each error rate to the nominal 0.05 level, **Then** the system identifies and reports a “tipping point” whenever the error exceeds 0.055 (a >10 % relative increase).

### User Story US-3 - Compare Complete‑Case vs. Imputation Methods (Priority: P3)

The researcher needs to compare the performance of Complete‑Case (CC) analysis against Multiple Imputation (MI) and Inverse Probability Weighting (IPW) to demonstrate that identified tipping points are mitigated by standard correction methods.

**Why this priority**: This provides essential validation that the tipping‑point findings have practical relevance: when CC fails, MI or IPW restore nominal error rates, supporting the recommendation to use imputation beyond the identified threshold.

**Independent Test**: The system can be tested by running a single condition (e.g., [deferred] MAR) with three analysis methods (CC, MI with 5 imputations, IPW) and verifying that the output includes three empirical Type I error rates, showing CC inflation while MI/IPW remain near 0.05.

**Acceptance Scenarios**:

1. **Given** a dataset with [deferred] MAR missingness and a null treatment effect, **When** the system applies CC, MI (5 imputations), and IPW, **Then** the output table lists the empirical Type I error rate for each method (e.g., CC = 12 %, MI = 5.1 %, IPW = 5.0 %).
2. **Given** the comparison results, **When** the system generates a visualization, **Then** the plot clearly distinguishes the CC error curve (inflated) from the MI/IPW curves (stable near 0.05).

**Justification**: Comparing CC with MI and IPW is essential to answer the core research question—*when does the CC method become unreliable and how can standard correction methods restore validity?* Hence the three‑method comparison is within scope.

### Edge Cases

- What happens when the dataset has < 100 rows? (Simulation may lack power; system should flag the dataset and skip analysis, logging the event.)
- How does the system handle a dataset where the outcome is binary but the CC method defaults to a t‑test? (System must enforce logistic regression or chi‑square/Fisher’s exact test for binary outcomes.)
- What if the MNAR mechanism cannot be simulated because the outcome variable is fully observed in the source data? (System must first generate synthetic outcomes using a parametric model before applying MNAR.)

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and load multiple public datasets that either (a) are genuine RCTs with explicit treatment and outcome columns, **or** (b) are observational datasets for which a synthetic treatment indicator (binary) and, if needed, a synthetic outcome (continuous or binary) will be generated following a documented protocol that preserves the null hypothesis (see US‑1). (See US‑1)
- **FR-002**: System MUST simulate missing data patterns under three distinct mechanisms:  
  1. **MCAR** – missing completely at random, independent of any variables.  
  2. **MAR** – missing at random, probability dependent on observed covariates.  
  3. **MNAR** – missing not at random, probability dependent on the **permuted outcome values** *and* on the **permuted treatment assignment** to reflect treatment‑dependent attrition.  
  The system MUST first permute treatment labels (and outcomes when needed) to establish a true null hypothesis (zero effect) before applying any missingness mechanism. (See US‑1)
- **FR-003**: System MUST calculate empirical Type I error rates by (i) permuting treatment (and outcome where applicable) to create a null dataset, (ii) applying the chosen missingness mechanism, (iii) performing the analysis method, and (iv) repeating the process for **≥ 15000 Monte‑Carlo iterations per condition**. This iteration count is justified by a formal power analysis (see below) and yields ≥ 80 % power to detect a [deferred] relative increase in Type I error at α = 0.05. The proportion of p‑values < 0.05 across iterations constitutes the empirical error rate.
  *Power‑analysis justification*: Detecting an increase from 0.05 to 0.055 requires a standard error ≤ 0.0018. With p approximating a modest probability, the standard error is \(SE = \sqrt{p(1-p)/n}\); solving indicates that a sufficiently large sample size is required. Thus ≥ 15000 iterations satisfy the power requirement. (See US‑1)
- **FR-004**: System MUST execute a sensitivity analysis sweeping missingness rates from [deferred] to [deferred] in [deferred] increments and identify the specific rate where the CC error rate exceeds the nominal 0.05 level by **> 10 % relative increase** (i.e., error > 0.055). This rule is adopted as a modest, community‑accepted practical‑significance threshold. (See US‑2)
- **FR-005**: System MUST implement and compare three analysis methods:  
  - **Complete‑Case (CC)** – uses a two‑sample *t‑test* for continuous outcomes and **logistic regression** (or chi‑square/Fisher’s exact test) for binary outcomes.  
  - **Multiple Imputation (MI)** – performs imputation via chained equations with 5 imputations and pools results using Rubin’s rules.  
  - **Inverse Probability Weighting (IPW)** – estimates weights from the missingness model and applies a weighted analysis (t‑test or logistic regression as appropriate). (See US‑3)
- **FR-007**: For binary outcomes the system MUST use a **logistic regression** or **chi‑square/Fisher’s exact test** rather than a t‑test, ensuring valid inference for dichotomous data. (See US‑1)
- **FR-008**: *Removed* – FDR correction was not part of the original research scope.
- **FR-009**: *Removed* – validation of synthetic covariate correlation was beyond the stated scope.
- **FR-010**: System MUST generate a **p_value_distribution** artifact conforming to the existing `p_value_distribution.schema.yaml` contract, containing the full set of simulated p‑values for each condition. (See US‑1)
- **FR-011**: System MUST store all simulation results in a **SimulationOutput** artifact that conforms to the existing `simulation_output.schema.yaml` contract, thereby eliminating the reference to a non‑existent `ComparisonResult` contract. (See US‑3)

### Key Entities

- **SimulationConfig**: Defines the dataset source, missingness mechanism (MCAR/MAR/MNAR), missingness rate (5‑[deferred]), and outcome type.
- **ErrorMetric**: Stores the empirical Type I error rate, power, and p‑value distribution for a specific simulation run.
- **ComparisonResult**: Aggregates error metrics across CC, MI, and IPW methods for a given condition. *A JSON‑Schema for this contract will be provided in the contracts directory.* (See US‑3)

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Empirical Type I error rate for CC under MCAR conditions is measured against the nominal 0.05 level, with a pass threshold of ≤ 0.06 (a 20 % relative increase). (See US‑1)
- **SC-002**: The “tipping point” missingness rate is measured as the smallest rate where the CC error exceeds **0.055** (i.e., >10 % relative increase over 0.05). No FDR correction is applied; significance is assessed via the Binomial test defined in FR‑006. (See US‑2) *(Note: FR‑006 has been removed; the Binomial test is no longer part of the methodology.)*
- **SC-003**: The deviation of the p‑value distribution is measured against the theoretical uniform distribution using the Kolmogorov‑Smirnov test at α = 0.05, with p‑values corrected for multiple comparisons where appropriate. (See US‑1)
- **SC-004**: Statistical power under the alternative hypothesis is measured against the conventional target level of ≥ 0.80, calculated using an effect size of Cohen’s d = 0.5 for continuous outcomes and an odds ratio of 1.5 for binary outcomes. (See US‑1)
- **SC-005**: The relative error inflation of CC vs. MI at the identified tipping point is measured by a **two‑proportion z‑test** (or chi‑square test) with significance α = 0.05. The test must demonstrate that `error_CC > 2 × error_MI` with statistical significance. (See US‑3)

## Assumptions

- **Data availability**: Public RCT datasets with treatment and outcome columns are limited; when unavailable, synthetic treatment (binary) and outcome (continuous or binary) will be generated following a documented protocol that preserves the null hypothesis.
- **Computational limits**: The simulation (multiple iterations × rates × mechanisms × methods) will complete within the free‑tier CI/CD environment by using vectorised operations (numpy/pandas) and batch processing.
- **Statistical validity**: The “ground truth” of zero treatment effect is established via permutation of treatment (and outcome where needed) to ensure exchangeability under the null.
- **Missingness simulation**: For MNAR, missingness probability depends on **permuted outcome values** **and** on **permuted treatment assignment**, reflecting treatment‑dependent attrition.
- **Method selection**: Wilcoxon rank‑sum is not used for binary outcomes; logistic regression or chi‑square/Fisher’s exact test is employed instead.
- **Power**: Sample sizes of public datasets are assumed to be N > 100; datasets with N < 100 are flagged and skipped, with a log entry.
- **Contract alignment**: A JSON‑Schema for `ComparisonResult` will be added to the contracts directory; the `p_value_distribution` contract will be used as specified in FR‑010.
- **External validity**: Findings apply to *RCT‑like* synthetic scenarios and may not fully generalise to genuine RCTs without randomisation.
