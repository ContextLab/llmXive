# Feature Specification: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Feature Branch**: `001-sensitivity-regression-coefficients`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Violation Profiling (Priority: P1)

The researcher MUST be able to ingest up to 10 numerical datasets from UCI or HuggingFace, automatically detect and quantify OLS assumption violations (heteroscedasticity via Breusch-Pagan, outliers via Cook's Distance), and compute the design matrix condition number for collinearity.

**Why this priority**: This is the foundational step. Without accurate profiling of the input data's violation severity and collinearity, the subsequent stability analysis lacks the independent variables required to test the research hypothesis. It validates that the dataset contains the necessary numerical features to perform OLS.

**Independent Test**: Can be fully tested by running the ingestion script on a single known dataset (e.g., `Auto` from UCI) and verifying that the output JSON contains valid, non-null values for `breusch_pagan_stat`, `max_cooks_distance`, and `condition_number`, and that the data fits within the 7GB RAM limit.

**Acceptance Scenarios**:

1. **Given** a CSV dataset from the UCI repository containing at least 5 numerical predictors and 1 numerical outcome, **When** the ingestion script processes it, **Then** the system calculates and records the Breusch-Pagan test statistic and Cook's distance, flagging the dataset's violation severity level (Low/Medium/High).
2. **Given** a dataset with perfect multicollinearity (condition number > 30), **When** processed, **Then** the system correctly identifies the high collinearity and records the condition number without crashing due to singular matrix errors.
3. **Given** a dataset that exceeds 100,000 rows AND is estimated to exceed 7GB RAM, **When** processed, **Then** the system automatically subsamples the data to ≤ 100,000 rows to ensure CPU feasibility and memory compliance (linked to the 6-hour CPU time limit in the project idea), logging the reduction ratio and verifying that the Breusch-Pagan statistic deviation between original and subsampled data is < 5%.

---

### User Story 2 - Subset Resampling and Stability Estimation (Priority: P2)

The researcher MUST be able to generate multiple random observation subsets per dataset across 5 distinct sample size tiers ([deferred], [deferred], [deferred], [deferred], [deferred] of N) and fit OLS models to each to derive the empirical standard deviation of coefficients.

**Why this priority**: This constitutes the core experimental engine. It generates the dependent variable (empirical coefficient variance) needed to correlate with the violation metrics. It directly addresses the "subset selection" aspect of the research question.

**Independent Test**: Can be tested by running the resampling module on a small, fixed dataset (N=500) with a fixed random seed, verifying that a sufficient number of subsets are generated across the five tiers, OLS fits complete without GPU requirements, and the resulting coefficient variance is a single positive float value.

**Acceptance Scenarios**:

1. **Given** a pre-profiled dataset with N=1000 rows, **When** the resampling module executes, **Then** it generates exactly 1000 subsets (200 per sample size tier: [deferred], [deferred], [deferred], [deferred], [deferred]) and fits an OLS model to each within 15 minutes on a 2-core CPU (derived from the global 6-hour budget: 6h/10 datasets = 36m, with 15m as a safety margin).
2. **Given** a subset size that is < 10 × number of predictors, **When** the OLS fit is attempted, **Then** the system skips that specific subset, logs a warning, and ensures the total count of valid fits remains ≥ 190 per tier.
3. **Given** the full set of coefficient estimates from the 200 subsets per tier, **When** aggregated, **Then** the system calculates and outputs the empirical standard deviation for each predictor coefficient, stored in a structured format (e.g., CSV/JSON) for downstream regression.

---

### User Story 3 - Interaction Analysis and Sensitivity Visualization (Priority: P3)

The researcher MUST be able to run a multiple regression analysis where the outcome is empirical coefficient variance, with predictors including condition number, violation severity, and their interaction terms, and visualize the interaction effects.

**Why this priority**: This delivers the final scientific answer. It tests the hypothesis that violations *modify* the relationship between collinearity and stability. It transforms raw simulation data into the "Expected Results" described in the idea.

**Independent Test**: Can be tested by running the analysis script on the aggregated results from US-2, verifying that a linear model is fitted, the interaction term p-value is reported regardless of significance, and a plot is generated showing the divergence of stability curves across violation levels.

**Acceptance Scenarios**:

1. **Given** the aggregated results from US-2 containing variance estimates, condition numbers, and violation metrics, **When** the analysis script runs, **Then** it performs a multiple regression with an interaction term (Condition Number × Violation Severity) and reports the coefficient and p-value for this interaction, regardless of whether p < 0.05.
2. **Given** a significant interaction effect, **When** the visualization module runs, **Then** it generates a plot showing three distinct curves (Low, Medium, High violation) demonstrating how coefficient variance scales with collinearity differently for each.
3. **Given** the final regression output, **When** the report is generated, **Then** it explicitly states whether the empirical variance correlates more strongly with the interaction term or the main effects, confirming or refuting the research hypothesis.

### Edge Cases

- What happens when a random subset results in a singular design matrix (perfect collinearity within the subset)? The system must detect the singularity, skip the fit, and log the incident without halting the entire 200-iteration loop.
- How does the system handle datasets where the Breusch-Pagan test fails to converge? The system must default the violation severity to "Unknown" and exclude that dataset from the interaction analysis, logging the exclusion reason.
- What occurs if the 6-hour CPU time limit is approached during the resampling phase? The system must implement a checkpoint mechanism, saving intermediate results at regular intervals, allowing the job to resume or report partial results rather than timing out abruptly.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess up to 10 numerical datasets from UCI/HuggingFace, standardizing predictors and calculating condition numbers, ensuring all data fits within 7GB RAM (See US-1).
- **FR-002**: System MUST quantify OLS assumption violations by computing Breusch-Pagan test statistics for heteroscedasticity and Cook's Distance for outliers for every dataset on the FULL dataset to serve as theoretical predictors of stability (See US-1).
- **FR-003**: System MUST generate multiple random observation subsets per dataset across 5 sample size tiers ([deferred], [deferred], [deferred], [deferred], [deferred]) and fit OLS models using `statsmodels` on a CPU-only environment, ensuring subset size ≥ 10 × number of predictors (See US-2).
- **FR-004**: System MUST calculate the empirical standard deviation of regression coefficients across multiple subsets per tier to serve as the stability metric (See US-2).
- **FR-005**: System MUST perform a multiple regression analysis with empirical coefficient variance as the outcome, and condition number, violation severity, and their interaction as predictors (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis for the "High/Medium/Low" violation thresholds by sweeping the cutoff values (e.g., Breusch-Pagan p-value across conventional significance thresholds) and reporting the variance in classification rates (See US-3).
- **FR-007**: System MUST frame all findings as associational, explicitly avoiding causal claims regarding the effect of violations on stability, as the design is observational (See US-3).

### Key Entities

- **DatasetProfile**: Represents a single input dataset, containing attributes: `dataset_id`, `n_rows`, `n_predictors`, `condition_number`, `bp_statistic`, `max_cooks_distance`, `violation_severity`.
- **StabilityResult**: Represents the outcome of the resampling phase, containing attributes: `dataset_id`, `sample_size_percent`, `coefficient_std_dev` (per predictor), `n_valid_fits`.
- **InteractionModel**: Represents the final regression output, containing attributes: `interaction_coefficient`, `interaction_p_value`, `r_squared`, `sensitivity_sweep_results`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The empirical coefficient variance (stability metric) is measured against the theoretical variance predicted by the condition number alone (using the standard homoscedastic OLS formula), to determine if violations amplify instability beyond this baseline (See FR-005).
- **SC-002**: The significance of the interaction term (Condition Number × Violation Severity) is measured against a conventional significance threshold to confirm the hypothesis that violations modify the collinearity-stability relationship (See FR-005).
- **SC-003**: The robustness of the "High/Medium/Low" violation classification is measured by sweeping the Breusch-Pagan p-value cutoff over a range of conventional significance thresholds and reporting the variation in the proportion of datasets classified as "High" (See FR-006).
- **SC-004**: The computational feasibility is measured by ensuring the total execution time for 10 datasets and 1000 total subset fits remains ≤ 6 hours on a 2-core CPU runner (See FR-003).
- **SC-005**: The validity of the stability metric is measured by checking that the standard deviation of coefficients across subsets converges (standard error of the SD < 5%) when increasing from an initial set of subsets to a larger, expanded set of subsets (See FR-004).

## Assumptions

- The UCI Machine Learning Repository and HuggingFace Datasets provide at least 10 numerical datasets with sufficient sample sizes (N ≥ 100) to support the generation of meaningful subsets without immediate singularity.
- The `statsmodels` library is sufficient for fitting OLS models on CPU without requiring GPU acceleration or specialized quantization libraries.
- The Breusch-Pagan test and Cook's Distance are valid and robust proxies for "heteroscedasticity severity" and "outlier severity" in the context of the selected public datasets.
- The relationship between collinearity and coefficient stability is linear enough within the sampled range to be captured by the interaction term in the multiple regression model.
- A resampling count provides a stable estimate of the coefficient variance distribution. without requiring a computationally prohibitive number of iterations.
- No dataset will contain missing values that prevent standardization or matrix inversion after the initial preprocessing step; imputation is handled as a pre-processing assumption.
- Using full-dataset violation metrics as predictors for subset-level instability is a test of whether global data properties predict local instability, not a tautology; the correlation is the hypothesis being tested.