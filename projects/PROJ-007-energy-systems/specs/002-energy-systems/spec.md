# Feature Specification: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-29  
**Status**: Draft  
**Input**: User description: "Developing Novel Solutions to Address Energy Inequity in Low-Income Communities"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Cohort Definition (Priority: P1)

The system MUST ingest public microdata (EIA RECS and ACS), filter for low-income census tracts, and construct a binary treatment variable indicating clean-energy adoption (solar/microgrid) alongside outcome variables (energy cost burden, disposable income, and socioeconomic proxies such as home value appreciation).

**Why this priority**: Without a clean, matched dataset including all required outcome variables, no causal inference can be performed. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by running the data pipeline on a sample subset and verifying that the resulting dataset contains exactly the required columns (including socioeconomic proxies), correct binary treatment flags, and that low-income filtering criteria are applied as defined (income < 150% of federal poverty line).

**Acceptance Scenarios**:

1. **Given** the EIA RECS and ACS raw CSV files, **When** the ingestion script runs with the low-income filter enabled, **Then** the output dataset contains only households in census tracts with median income below the specified threshold.
2. **Given** a household record with reported solar installation, **When** the treatment variable is constructed, **Then** the `treatment` column is set to `1`; otherwise, it is `0`.
3. **Given** the merged dataset, **When** checking for missing values in key outcome variables (energy cost, income, home value), **Then** records with missing critical outcomes are either imputed via the specified method or flagged for exclusion, ensuring no silent data loss.

---

### User Story 2 - Propensity Score Matching and Balance Validation (Priority: P2)

The system MUST implement a Propensity Score Matching (PSM) algorithm to create a control group of non-adopting households that are statistically similar to adopters based on pre-treatment covariates (income, housing type, location), validate the balance of these covariates, and perform a placebo test on pre-treatment outcomes to assess the validity of the unconfoundedness assumption.

**Why this priority**: PSM is the core causal identification strategy. Without a balanced control group and validation of the unconfoundedness assumption, the estimated treatment effect is biased and the research question cannot be answered validly.

**Independent Test**: Can be fully tested by running the PSM algorithm on the ingested dataset, extracting the matched pairs, and calculating the standardized mean difference (SMD) for all covariates. A pass is achieved if all SMDs are <= 0.1. Additionally, a placebo test on a pre-treatment outcome must yield a non-significant difference between treatment and control groups.

**Acceptance Scenarios**:

1. **Given** the full dataset with covariates, **When** the PSM algorithm runs with a caliper of 0.05, **Then** a matched control group is generated where each adopter has at least one non-adopter match.
2. **Given** the matched sample, **When** calculating the standardized mean difference for income, housing type, and location, **Then** all resulting SMD values are <= 0.1, indicating successful balance.
3. **Given** a failed balance check (SMD > 0.1 for any covariate) OR a significant result in the placebo test, **When** the system executes, **Then** it logs a warning and attempts to adjust the caliper or covariate set, or triggers the fallback Difference-in-Differences (DiD) strategy if balance cannot be achieved.

---

### User Story 3 - Causal Effect Estimation and Sensitivity Analysis (Priority: P3)

The system MUST estimate the Average Treatment Effect on the Treated (ATT) for energy cost burden, disposable income, and socioeconomic proxies using OLS regression with clustered standard errors on the matched sample. If PSM fails, the system MUST fall back to a Difference-in-Differences (DiD) estimation. The system MUST also perform a sensitivity analysis by varying the propensity score caliper (e.g., 0.01, 0.05, 0.1) to test the robustness of the results.

**Why this priority**: This delivers the primary answer to the research question and satisfies the methodological requirement for threshold justification and sensitivity analysis, ensuring the findings are not artifacts of a single arbitrary parameter choice. The fallback mechanism ensures the analysis proceeds even if PSM assumptions are violated.

**Independent Test**: Can be fully tested by executing the regression (or DiD) and sensitivity sweep, then verifying that the output includes the ATT estimate, p-values, confidence intervals, and a table showing how the ATT changes across the different caliper values. The test passes if the system outputs a valid estimate regardless of statistical significance.

**Acceptance Scenarios**:

1. **Given** the balanced matched sample, **When** the OLS regression runs with robust, cluster-robust standard errors (clustered by matched pair), **Then** the system outputs the ATT estimate for energy cost burden along with its p-value and 95% confidence interval.
2. **Given** the sensitivity analysis loop, **When** the caliper is swept across {0.01, 0.05, 0.1}, **Then** the system generates a report showing the variation in the ATT estimate and whether the direction and significance of the effect remain consistent across the tested caliper range.
3. **Given** a failure in PSM balance or common support, **When** the system executes, **Then** it automatically switches to the Difference-in-Differences (DiD) estimation strategy (if pre/post data is available) and reports the DiD estimate instead of halting.

---

### Edge Cases

- What happens when the low-income filter results in a sample size too small for PSM (e.g., < 50 adopters)? The system must halt and report a power limitation, deferring the analysis to a broader geographic definition or acknowledging the limitation in the final report.
- How does the system handle households with zero energy costs (potential outliers or data errors)? The system must apply a log-transformation or winsorization at the 1st/99th percentile before regression to prevent skewing the ATT.
- What if the propensity score distribution is too extreme (near 0 or 1) for some households? The system must implement a common support check and exclude units outside the overlap region before matching.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and merge EIA RECS and ACS data, filtering for households in low-income census tracts (See US-1).
- **FR-002**: System MUST construct a binary treatment variable for clean-energy adoption and calculate energy cost burden (energy cost / income), disposable income, and socioeconomic proxies (e.g., home value appreciation) as continuous outcomes (See US-1).
- **FR-003**: System MUST implement a Propensity Score Matching algorithm with a default caliper of 0.05 to balance covariates between adopters and non-adopters (See US-2).
- **FR-004**: System MUST validate covariate balance by calculating the standardized mean difference (SMD) for all matching variables and ensuring SMD <= 0.1 (See US-2).
- **FR-005**: System MUST estimate the Average Treatment Effect on the Treated (ATT) using OLS regression with cluster-robust standard errors (clustered by matched pair) on the matched sample (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the propensity score caliper over the set {0.01, 0.05, 0.1} and reporting the variation in the ATT estimate (See US-3).
- **FR-007**: System MUST flag and exclude observations outside the common support region of the propensity score distribution before matching (See US-2).
- **FR-008**: System MUST implement a fallback Difference-in-Differences (DiD) estimation strategy if PSM fails balance checks or common support requirements (See US-3).
- **FR-009**: System MUST perform a placebo test on a pre-treatment outcome variable to validate the unconfoundedness assumption (See US-2).

### Key Entities

- **Household**: Represents a single residential unit with attributes: `income`, `energy_cost`, `housing_type`, `location`, `treatment_status` (binary), `propensity_score`, `home_value_change`.
- **MatchedPair**: Represents a linkage between an adopter and a non-adopter, containing references to both household IDs and the calculated difference in covariates.
- **AnalysisResult**: Represents the output of the causal inference, containing `att_estimate`, `p_value`, `confidence_interval`, `methodology_used` (PSM or DiD), and `sensitivity_sweep_data`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Covariate balance is measured against the threshold of standardized mean difference (SMD) <= 0.1 for all matching variables (See US-2).
- **SC-002**: The statistical significance of the ATT is measured against the successful calculation and reporting of the p-value and confidence interval (See US-3).
- **SC-003**: The robustness of the causal estimate is measured against the variation in the ATT estimate across the sensitivity sweep (calipers 0.01, 0.05, 0.1) (See US-3).
- **SC-004**: The sample size after matching is measured against the minimum power requirement (at least 50 adopters with matches) to ensure statistical validity (See US-2).
- **SC-005**: The validity of the unconfoundedness assumption is measured against the result of the placebo test on pre-treatment outcomes (See US-2).

## Assumptions

- The EIA RECS and ACS datasets contain the necessary variables (income, energy costs, housing type, location, self-reported solar/microgrid installation, and home value changes) for the analysis.
- The causal identification strategy relies on the assumption of "unconfoundedness" (selection on observables), meaning that after controlling for observed covariates, there are no unobserved confounders affecting both adoption and outcomes.
- The analysis is observational; therefore, findings will be framed as associational or causal estimates based on the PSM/DiD methodology, not as results from a randomized controlled trial.
- The dataset size (after filtering for low-income tracts) will fit within the 7 GB RAM limit of the free-tier CI runner, allowing for in-memory processing without chunking.
- The propensity score model will converge successfully; if not, the system will default to a simpler matching algorithm or report a failure.
- The sensitivity analysis thresholds (calipers 0.01, 0.05, 0.1) are based on community standards for PSM robustness checks in social science literature.
- The research design is limited to the US context due to data availability; international low-income energy inequity is out of scope for this specific feature.
- If PSM fails, sufficient longitudinal data exists to perform a Difference-in-Differences analysis.