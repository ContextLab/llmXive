# Feature Specification: Statistical Analysis of Publicly Available Election Poll Aggregates

**Feature Branch**: `001-statistical-poll-aggregation`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Compare simple averaging, accuracy-weighted averaging, and Bayesian hierarchical aggregation for U.S. election forecasts derived from publicly available poll aggregates."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Harmonization (Priority: P1)

The system MUST ingest raw poll data from FiveThirtyEight and RealClearPolitics repositories, harmonize dates to weekly bins, and compute pollster-specific historical RMSE weights.

**Why this priority**: This is the foundational data layer. Without clean, harmonized input data with calculated weights, no aggregation models can run.

**Independent Test**: Can be fully tested by verifying the output of the preprocessing script produces a single CSV with columns `date`, `pollster`, `vote_share`, `sample_size`, `historical_rmse` for the historical election period.

**Acceptance Scenarios**:

1. **Given** raw CSV files from FiveThirtyEight and RCP archives, **When** the preprocessing script executes, **Then** a unified `poll_data_cleaned.csv` is generated with no duplicate dates for the same pollster.
2. **Given** a pollster with no prior election history in the dataset, **When** the script calculates `historical_rmse`, **Then** a default weight (median of all pollsters) is assigned to prevent division by zero.

---

### User Story 2 - Frequentist Aggregation Execution (Priority: P2)

The system MUST compute point forecasts for each election week using (1) Simple Unweighted Averaging and (2) Accuracy-Weighted Averaging based on historical RMSE.

**Why this priority**: These are the baseline methods. They establish the benchmark for predictive accuracy against which the Bayesian model will be compared.

**Independent Test**: Can be fully tested by running the aggregation scripts on `poll_data_cleaned.csv` and verifying the output contains `simple_avg_forecast` and `weighted_avg_forecast` columns matching the election outcomes across multiple cycles within expected variance.

**Acceptance Scenarios**:

1. **Given** the cleaned poll data for the 2020 election cycle, **When** the Simple Average method is applied, **Then** the forecast value equals the arithmetic mean of all available polls for that week.
2. **Given** the cleaned poll data for the 2020 election cycle, **When** the Weighted Average method is applied, **Then** the forecast value is calculated using inverse-RMSE weighting where weights are normalized to sum to 1.0, and high-performing pollsters contribute proportionally more to the aggregate based on their normalized weights.

---

### User Story 3 - Bayesian Hierarchical Modeling and Evaluation (Priority: P3)

The system MUST fit a Bayesian hierarchical model using PyMC (NUTS sampler) to generate posterior distributions, credible intervals, and perform Diebold-Mariano significance testing against the frequentist baselines.

**Why this priority**: This is the advanced methodological contribution. It provides uncertainty quantification and rigorous statistical comparison.

**Independent Test**: Can be fully tested by verifying the MCMC sampler completes without divergence, produces a 95% credible interval that covers the actual election outcome at a rate ≥90%, and outputs a Diebold-Mariano p-value matrix.

**Acceptance Scenarios**:

1. **Given** the cleaned poll data, **When** the PyMC model runs, **Then** the sampler completes without divergences and produces a trace with R-hat ≤ 1.05.
2. **Given** the posterior samples, **When** the 95% credible intervals are evaluated against actual outcomes, **Then** the observed coverage rate is ≥90% and a binomial test against the [deferred] null hypothesis fails to reject the null (p ≥ 0.05).
3. **Given** the error metrics from all three methods, **When** pairwise Diebold-Mariano tests are run, **Then** p-values are adjusted for multiple comparisons using a method accounting for error correlation (e.g., Westfall-Young) and reported.

---

### Edge Cases

- What happens when a specific election cycle has fewer than 10 polls available (low data density)?
- How does the system handle MCMC non-convergence (R-hat > 1.05)?
- How does the system handle missing final election outcome data for a specific state or year?

## Non-Functional Requirements

- **NFR-001**: The full analysis pipeline MUST complete within 4 hours on a standard 2-core CPU-only runner (Intel Xeon or equivalent with ≥2.0 GHz clock speed) without GPU acceleration, processing up to 10 election cycles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse poll data from `https://projects.fivethirtyeight.com/polls/` and ` into a unified format (See US-1)
- **FR-002**: System MUST compute pollster-specific historical RMSE for weighting factors based on past elections (See US-1)
- **FR-003**: System MUST calculate simple arithmetic mean of vote shares for each weekly bin (See US-2)
- **FR-004**: System MUST calculate inverse-RMSE weighted mean of vote shares for each weekly bin, normalizing weights to sum to 1.0 (See US-2)
- **FR-005**: System MUST fit Bayesian hierarchical model with latent weekly preference θₜ ~ Normal(θₜ₋₁, σₜ²) and observation noise τᵢ² (See US-3)
- **FR-006**: System MUST apply a correlation-aware multiple comparison correction (e.g., Westfall-Young or Benjamini-Hochberg) to pairwise Diebold-Mariano tests (See US-3)
- **FR-007**: System MUST frame findings as predictive accuracy and associational uncertainty, not causal voter influence (See US-3)
- **FR-008**: System MUST perform a qualitative data sufficiency check on temporal density and recency; if data is deemed insufficient for hierarchical shrinkage (defined as <5 polls within 30 days or <3 distinct election cycles), the system MUST halt and issue a warning (See US-1)
- **FR-009**: System MUST report 95% credible interval coverage rate against actual election outcomes and perform a binomial test against the [deferred] null hypothesis (See US-3)
- **FR-010**: System MUST halt and report an error if the total poll count across the target period is <500 (See US-1)

### Key Entities

- **PollRecord**: Represents a single poll entry with attributes `date`, `pollster`, `sample_size`, `vote_share`, `margin_of_error`.
- **AggregationForecast**: Represents the output of a method for a specific week with attributes `method_type`, `point_estimate`, `uncertainty_interval`.
- **ElectionOutcome**: Represents the ground truth final vote share for a specific election year.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: RMSE and MAE are calculated for Simple, Weighted, and Bayesian methods against actual election outcomes (See US-2)
- **SC-002**: Calibration reliability achieves ≥90% coverage of actual outcomes within the 95% credible interval, validated by a binomial test (See US-3)
- **SC-003**: Statistical significance of method differences is measured via Diebold-Mariano test statistics with correlation-aware multiplicity correction (See US-3)

## Assumptions

- FiveThirtyEight public repository contains complete CSV data for presidential polls covering multiple election cycles through recent years.
- GitHub Actions free-tier runner provides sufficient CPU stability for PyMC NUTS sampling, subject to the NFR-001 time limit.
- RealClearPolitics archived data may be partial for the early 21st-century period; the system will ingest available data and flag missing cycles.
- Election final popular vote outcomes are available from official federal election commission records for all target years.
- PyMC v5 is compatible with the default CPU-only environment without requiring CUDA libraries.
- Poll sample sizes and margins of error are reported consistently across all included pollsters.
- No GPU hardware is available or required for this analysis.