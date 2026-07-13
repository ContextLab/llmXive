# Feature Specification: Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

**Feature Branch**: `001-statistical-chess-elo-analysis`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

**As a** data analyst, **I want** to download a subset of public Lichess PGN games and parse them to extract specific game features (opening codes, move times, material imbalance) and calculate Elo-based expected win probabilities, **so that** I have a clean, structured dataset ready for statistical modeling.

**Why this priority**: This is the foundational step. Without a validated dataset containing the predictors and the target variable (outcome deviation), no analysis can occur. It must function independently to ensure data integrity before modeling begins.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small sample (e.g., 100 games) and verifying that the output collection of GameRecord entities contains the expected columns (ECO code, avg_move_time, material_imbalance_move10, elo_expected_prob, outcome_deviation) with no null values in critical fields.

**Acceptance Scenarios**:

1. **Given** a valid Lichess PGN file URL and a request for [deferred] games, **When** the ingestion script executes, **Then** the output collection of GameRecord entities contains [deferred] records with calculated `outcome_deviation` values and no missing data in the predictor columns.
2. **Given** a PGN file with malformed move lists, **When** the parser encounters an error, **Then** the specific game is skipped, logged, and the process continues without crashing, ensuring the final dataset size is within ±1% of the requested target.

---

### User Story 2 - Regression Modeling and Significance Testing (Priority: P2)

**As a** researcher, **I want** to fit multiple regression models (Beta, Ridge) using the extracted features to predict outcome deviations, apply multiple-comparison correction (Benjamini-Hochberg FDR) to p-values, and perform statistical significance tests, **so that** I can identify which game features systematically correlate with Elo prediction errors.

**Why this priority**: This is the core analytical engine. It directly addresses the research question by quantifying the relationship between features and deviations. It relies on the output of Story 1 but is independently testable as a statistical pipeline.

**Independent Test**: The system can be tested by running the modeling script on the generated dataset and verifying that the output includes coefficient tables with p-values, R² scores, and AIC values for all specified models, with p-values corrected for multiple comparisons.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] games with calculated deviations, **When** the regression module runs, **Then** it outputs a summary table where every coefficient has an associated p-value (corrected for multiple comparisons) and the model fit statistics (R², AIC) are recorded for each model type.
2. **Given** a fitted model, **When** the significance test module runs, **Then** it correctly identifies coefficients with p < 0.01 (after correction) as statistically significant and flags them in the final report.
3. **Given** a set of one-hot encoded ECO codes, **When** the feature preparation step runs, **Then** the system collapses ECO codes into broader opening families to reduce multicollinearity before fitting the regression model.

---

### User Story 3 - Cross-Validation and Diagnostic Reporting (Priority: P3)

**As a** reviewer, **I want** to see the results of 5-fold cross-validation and diagnostic plots (residuals, feature importance, predicted vs. actual) to ensure the model generalizes and to visualize the nature of the Elo biases, **so that** I can validate the robustness of the findings before publication.

**Why this priority**: This adds rigor to the findings by preventing overfitting and providing visual evidence. It depends on the models from Story 2 but serves as a distinct validation step.

**Independent Test**: The system can be tested by executing the validation script and verifying that the output includes a confusion matrix or residual plot and a report of the mean squared error (MSE) across the 5 folds.

**Acceptance Scenarios**:

1. **Given** a trained regression model, **When** the cross-validation routine executes, **Then** it produces a report showing the variation in R² and MSE across the 5 folds, confirming the model's stability.
2. **Given** the final model results, **When** the diagnostic generator runs, **Then** it produces a scatter plot of predicted vs. actual deviation and a residual plot that can be saved as a PNG file for the final report.

---

### Edge Cases

- **What happens when** the Lichess API is temporarily unavailable or rate-limited? The system must implement an exponential backoff retry strategy with a configurable maximum number of retries. and exit gracefully with a clear error message if the download fails after retries.
- **How does the system handle** games where the rating difference is so extreme that the expected probability is effectively 0 or 1 (causing numerical instability in log-odds)? The system must cap expected probabilities within a bounded range away from the theoretical extremes. to prevent division-by-zero or log-of-zero errors during deviation calculation.
- **What happens when** a game lacks move-time metadata? The system must exclude that specific game from the analysis rather than imputing a value, as imputation could bias the "move time" predictor.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a subset of [deferred] games from the Lichess database (or a verified mirror) containing complete rating and move-time data (See US-1).
- **FR-002**: System MUST parse PGN files to extract opening ECO codes, average move times per player, and material_imbalance_move10 (See US-1).
- **FR-003**: System MUST calculate the expected win probability using the standard Elo logistic formula: P = 1 / (1 + 10^((R2-R1)/400)) for every game (See US-1).
- **FR-004**: System MUST compute the outcome deviation as (actual_result - expected_probability) where actual_result is 1 (win), 0.5 (draw), or 0 (loss) (See US-1).
- **FR-005**: System MUST fit at least two regression models (Beta Regression, Ridge Regression) using the extracted features as predictors and outcome deviation as the target (See US-2).
- **FR-006**: System MUST perform k-fold cross-validation (k=5) on all models to assess generalizability and prevent overfitting (See US-3).
- **FR-007**: System MUST perform significance tests (t-tests on coefficients, F-test for model fit) and report p-values for all predictors (See US-2).
- **FR-008**: System MUST generate diagnostic plots including residual plots, feature importance rankings, and predicted vs. actual deviation scatterplots (See US-3).
- **FR-009**: System MUST apply the Benjamini-Hochberg False Discovery Rate (FDR) correction to p-values when reporting significant predictors to control the false discovery rate, specifically accounting for correlated predictors (See US-2).
- **FR-010**: System MUST perform a sensitivity analysis on the decision threshold for "statistical significance" (e.g., p < 0.01) by sweeping the threshold over {0.005, 0.01, 0.05} and reporting the variation in the number of significant predictors (See US-2).
- **FR-011**: System MUST collapse one-hot encoded ECO codes into broader opening families (e.g., King's Pawn, Queen's Gambit) before significance testing to reduce multicollinearity (See US-2).

### Key Entities

- **GameRecord**: Represents a single chess game. Attributes: `game_id`, `white_rating`, `black_rating`, `eco_code`, `avg_move_time_white`, `avg_move_time_black`, `material_imbalance_move10`, `outcome`, `elo_expected_prob`, `outcome_deviation`.
- **RegressionModel**: Represents a fitted statistical model. Attributes: `model_type` (beta/ridge), `coefficients`, `p_values`, `r_squared`, `aic`, `cross_validation_scores`.
- **DiagnosticReport**: Represents the output of the validation step. Attributes: `residual_plot_path`, `feature_importance_ranking`, `predicted_vs_actual_plot_path`, `cross_validation_summary`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of games successfully parsed and included in the dataset is measured against the number of valid PGN files in the requested subset (target ≥ 95% inclusion rate) (See US-1).
- **SC-002**: The statistical significance of the regression coefficients is measured against the corrected p-value threshold (p < 0.01 after Benjamini-Hochberg FDR correction) to determine if systematic biases exist (See US-2).
- **SC-003**: The model generalizability is measured against the variance in R² scores (scale [0.0, 1.0]) across the 5 cross-validation folds (target: standard deviation of R² < 0.05) (See US-3).
- **SC-004**: The robustness of the findings is measured against the sensitivity analysis sweep (target: the set of "significant" predictors remains stable with a Jaccard index ≥ 0.8 across the {0.005, 0.01, 0.05} threshold range) (See US-2).
- **SC-005**: The computational feasibility is measured against the GitHub Actions free-tier constraints (target: total job runtime ≤ 6 hours, RAM usage ≤ 7 GB, no GPU errors) (See US-1).

## Assumptions

- The Lichess database (or a verified mirror) contains the necessary variables (move times, ratings, ECO codes) for the selected subset of [deferred] games; if move time data is missing for a significant portion, the analysis scope will be limited to games with complete data.
- The analysis is observational; therefore, all findings regarding "correlations" and "biases" are framed as associational, not causal, as there is no random assignment of game features.
- The dataset size will fit within the RAM limit of the GitHub Actions runner. after loading into a pandas DataFrame; if memory pressure occurs, the sample size will be reduced.
- The standard Elo logistic formula (P = 1 / (1 + 10^((R2-R1)/400))) is the accepted baseline for expected win probability in this context.
- The `python-chess` library and `statsmodels` package are sufficient for parsing PGNs and performing the required regression analyses on a CPU-only environment.
- The "material_imbalance_move10" is a valid proxy for early-game strategic complexity, assuming the move 10 state is representative of the opening phase.
- **Methodological Rigor Justification**: The requirement for multiple-comparison correction (FR-009) and sensitivity analysis (FR-010) is included as essential methodological rigor to ensure valid inference and robust findings, preventing false positives in the presence of multiple predictors and threshold sensitivity.
- **Feature Selection Justification**: The exclusion of "pawn structure complexity" and "number of captures" from FR-002 is based on the lack of a defined metric in the original idea, ensuring all requirements are verifiable and testable.