# Feature Specification: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Feature Branch**: `001-chess-elo-deviation-analysis`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

As a data analyst, I want to download a subset of ≤100,000 public chess games from the Lichess database and extract specific game features (opening code, move times, material imbalance) so that I have a clean, structured dataset ready for statistical modeling.

**Why this priority**: Without a valid, parsed dataset containing the required predictors and outcomes, no statistical analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample of [deferred] games and verifying the output CSV contains ≥99% non-null values for all defined feature columns and the calculated outcome deviation.

**Acceptance Scenarios**:

1. **Given** the Lichess PGN database is accessible, **When** the ingestion script runs on a sample of [deferred] games, **Then** the output file contains [deferred] rows with columns for `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move_10`, and `outcome_deviation`.
2. **Given** a game file with missing move-time metadata, **When** the parser processes it, **Then** the row is either excluded or marked with the value 'NaN', and the script logs the exclusion count without crashing.
3. **Given** the dataset is limited to ≤100,000 games, **When** the full ingestion completes, **Then** the resulting CSV file size is ≤ 500 MB, ensuring it fits within the 7 GB RAM limit of the CI runner.

---

### User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

As a researcher, I want to fit multiple regression models (linear, ridge) using the extracted game features to predict outcome deviations, validate against an external engine-evaluation proxy, and perform statistical significance tests on the coefficients so that I can determine if specific game features systematically bias Elo predictions.

**Why this priority**: This is the core scientific inquiry. It transforms raw data into statistical evidence regarding the research question (do features correlate with deviations?) while mitigating circular validation risks.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that the output includes a summary table of coefficients, p-values, R², and an engine-evaluation comparison report.

**Acceptance Scenarios**:

1. **Given** a clean dataset of [deferred] games, **When** the linear regression model is fitted, **Then** the output includes a coefficient table where every predictor has an associated p-value and standard error.
2. **Given** the fitted model, **When** the cross-validation (k=5) is executed, **Then** the system reports the mean R² and standard deviation across the 5 folds, ensuring R² > 0.05.
3. **Given** a model with multiple predictors, **When** the variance inflation factor (VIF) is calculated, **Then** the system reports VIF scores for each predictor, specifically checking the correlation between move time and material imbalance.

---

### User Story 3 - Diagnostic Visualization and Reporting (Priority: P3)

As a stakeholder, I want to generate diagnostic plots (residuals, feature importance, predicted vs. actual) and a summary report so that I can visually inspect model validity and communicate the findings regarding Elo system biases.

**Why this priority**: While the statistical tests provide the numbers, visualizations are essential for validating assumptions (e.g., normality of residuals) and communicating the magnitude of deviations to non-technical audiences.

**Independent Test**: Can be fully tested by running the reporting script and verifying that the output directory contains at least three distinct plot images (residual plot, scatter plot, bar chart) and a text summary file.

**Acceptance Scenarios**:

1. **Given** a fitted model, **When** the diagnostic script runs, **Then** a residual plot is generated showing residuals on the y-axis and predicted values on the x-axis.
2. **Given** the model coefficients, **When** the feature importance chart is generated, **Then** the chart displays the magnitude of each feature's effect on the outcome deviation.
3. **Given** the analysis results, **When** the summary report is generated, **Then** it explicitly states whether the p-value for the overall model fit is < 0.01, lists the top 3 features with significant coefficients, and reports the R² value.

### Edge Cases

- **What happens when** the Lichess API or database download fails due to network timeout?
  - The system MUST retry the download up to 3 times with a 10-second backoff before failing the job.
- **How does the system handle** games where the material imbalance cannot be calculated (e.g., incomplete games ending before move 10)?
  - The system MUST exclude these games from the analysis *before* feature extraction and log the count of excluded games to ensure the sample size remains accurate.
- **What happens when** a specific opening code (ECO) has fewer than 100 occurrences in the 100k sample?
  - The system MUST either group these rare codes into an "Other" category or exclude them to prevent unstable coefficient estimates in the regression.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse a subset of ≤100,000 chess games from the Lichess public database, extracting ECO codes, move times, and material imbalance at move 10. Games ending before move 10 MUST be excluded prior to extraction. (See US-1)
- **FR-002**: The system MUST calculate the expected win probability for White using the standard Elo logistic formula: $P = 1 / (1 + 10^{(R_{black} - R_{white})/400})$, where $R_{white}$ is White's rating and $R_{black}$ is Black's rating. (See US-2)
- **FR-003**: The system MUST compute the outcome deviation as the difference between the actual result for White (1 for win, 0.5 for draw, 0 for loss) and the expected win probability $P$ calculated in FR-002. (See US-2)
- **FR-004**: The system MUST fit at least two regression models (Linear and Ridge) using the extracted features as predictors and outcome deviation as the target variable. (See US-2)
- **FR-005**: The system MUST perform 5-fold cross-validation on the fitted models and report the mean R² and standard deviation. (See US-2)
- **FR-006**: The system MUST calculate and report Variance Inflation Factors (VIF) for all predictors to assess collinearity. (See US-2)
- **FR-007**: The system MUST generate a residual plot, a predicted-vs-actual scatter plot, and a feature importance bar chart. (See US-3)
- **FR-008**: The system MUST apply a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when testing the significance of multiple regression coefficients. (See US-2)
- **FR-009**: The system MUST report 95% confidence intervals for the Elo expectation calculation and perform a sensitivity analysis on the expectation formula parameters (e.g., varying the K-factor or rating difference scaling) to validate robustness. (See US-2)
- **FR-010**: The system MUST perform a power analysis demonstrating that the sample size ([deferred] games) is sufficient to detect a deviation magnitude of effect size ≥ 0.1 with power ≥ 0.8. (See US-2)
- **FR-011**: The system MUST validate the 'outcome deviation' findings against an external ground truth proxy, specifically the difference in engine evaluation (in centipawns) at move 20, to ensure findings are not purely circular residuals. (See US-2)
- **FR-012**: The system MUST explicitly test for and report the correlation between `avg_move_time` and `material_imbalance`, and exclude or adjust for high collinearity (VIF > 5.0) between these specific predictors before interpreting coefficients. (See US-2)
- **FR-013**: The system MUST include a 'rating_difference' binning feature or interaction term in the model to explicitly account for and distinguish 'regression to the mean' artifacts from genuine Elo biases. (See US-2)

### Key Entities

- **GameRecord**: Represents a single chess game. Attributes include `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move_10`, `actual_result_white`, `expected_probability_white`, `outcome_deviation`.
- **ModelFit**: Represents the result of a regression analysis. Attributes include `model_type` (e.g., "Linear", "Ridge"), `coefficients`, `p_values`, `r_squared`, `aic`, `vif_scores`, `confidence_intervals`.
- **DiagnosticPlot**: Represents a visual output. Attributes include `plot_type` (e.g., "Residuals", "Scatter"), `file_path`, `generation_timestamp`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The dataset validity is measured against the requirement that ≥99% of included games have non-null values for `eco_code`, `avg_move_time`, and `material_imbalance_move_10`, based on the [deferred] game limit defined in FR-001. (See US-1)
- **SC-002**: The model generalizability is measured against the requirement that the 5-fold cross-validation R² standard deviation is ≤ 0.05. (See US-2)
- **SC-003**: The statistical significance is measured against the requirement that the model explains a significant proportion of variance (R² > 0.05) AND at least one predictor has a p-value < 0.01 after applying the multiple-comparison correction. (See US-2)
- **SC-004**: The collinearity risk is measured against the requirement that no predictor has a Variance Inflation Factor (VIF) > 5.0, specifically including the pair `avg_move_time` and `material_imbalance`. (See US-2)
- **SC-005**: The compute feasibility is measured against the requirement that the entire analysis (ingestion, modeling, plotting) completes within 6 hours on a CPU-only runner with ≤ 7 GB RAM usage. (See US-1, US-2, US-3)
- **SC-006**: The constitutional rigor is measured against the requirement that the sensitivity analysis for the Elo expectation covers a parameter sweep range of ±10% and reports the variance in outcome deviation. (See US-2, FR-009)
- **SC-007**: The sample size justification is measured against the requirement that the power analysis confirms a detectable effect size of ≥ 0.1 with power ≥ 0.8 for the [deferred] game sample. (See US-2, FR-010)

## Assumptions

- **Dataset-variable fit**: It is assumed that the Lichess public PGN database contains accurate move-time data and game-ending results for the selected [deferred] games. If the source data lacks precise move times for a significant portion of games, the sample size may need to be reduced, which is recorded as a limitation.
- **Inference framing**: The analysis is framed as **associational**; findings will identify correlations between game features and Elo deviations, not causal effects of those features on player performance, as the data is observational (no random assignment of game features).
- **Threshold justification**: A significance threshold of **p < 0.01** is used for declaring statistical significance, consistent with standard practices in sports statistics to reduce false positives. A sensitivity analysis will sweep this threshold over **{0.005, 0.01, 0.05}** to report how the count of significant features varies.
- **Compute constraints**: The analysis assumes that the [deferred] game dataset (approx. 500 MB CSV) fits entirely in RAM (~7 GB limit) and that standard Python libraries (`pandas`, `scikit-learn`, `statsmodels`) can process this volume on a 2-core CPU within the 6-hour job limit.
- **Measurement validity**: The Elo formula used ($P = 1 / (1 + 10^{(R_{black} - R_{white})/400})$) is assumed to be the standard definition for expected win probability in the context of the Lichess rating system.
- **Predictor collinearity**: It is assumed that `avg_move_time` and `material_imbalance` are not definitionally related; however, if high collinearity is detected (VIF > 5), the interpretation of independent effects will be restricted to descriptive joint relationships, as mandated by FR-012.
- **Sample Size Justification**: The [deferred] game sample size is selected to satisfy the power analysis requirement (FR-010) for detecting an effect size of ≥ 0.1, ensuring the study is not underpowered.