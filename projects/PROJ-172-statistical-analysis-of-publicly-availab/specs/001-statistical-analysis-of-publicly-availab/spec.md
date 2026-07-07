# Feature Specification: Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

**Feature Branch**: `001-sports-prediction`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Sports Data for Predictive Modeling"

## User Scenarios & Testing

### User Story 1 - Reproducible Data Pipeline and Feature Engineering (Priority: P1)

As a data analyst, I need a fully automated pipeline that ingests raw play-by-play and season data from Retrosheet and Baseball-Reference, cleans it, and engineers both traditional and advanced metrics (e.g., wOBA, BABIP) so that I have a clean, temporally-split dataset ready for modeling without manual intervention.

**Why this priority**: Without a reliable, reproducible data foundation, no modeling or statistical comparison can occur. This is the prerequisite for all downstream analysis.

**Independent Test**: The pipeline can be executed end-to-end on a fresh environment; it produces a single CSV file containing the final training and testing sets with all required columns (traditional stats, advanced stats, labels) and verifies that no data leakage exists between the training (≤2018) and testing (2019-2022) periods.

**Acceptance Scenarios**:
1. **Given** raw CSV files from Retrosheet and Baseball-Reference for the years 2000-2022, **When** the data ingestion script is executed, **Then** the output dataset contains exactly one row per game with resolved team/player IDs and handles missing entries by imputation or exclusion as defined.
2. **Given** a dataset containing play-by-play events, **When** the feature engineering module runs, **Then** advanced metrics (wOBA, BABIP, park-adjusted run expectancy) are calculated for every team in every game, and these values are mathematically consistent with the underlying play data.
3. **Given** the full dataset spanning 2000-2022, **When** the chronological split is applied, **Then** the training set contains only games from 2000-2018 and the test set contains only games from 2019-2022, with zero overlap in dates.

---

### User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

As a researcher, I need to train three distinct models (Logistic Regression, Random Forest, Gradient Boosting) on the engineered dataset using time-series cross-validation so that I can objectively compare the predictive power of advanced metrics against traditional statistics.

**Why this priority**: This is the core experimental engine. It allows us to quantify the "material improvement" hypothesis by comparing model performance metrics (ROC-AUC, log-loss) between the baseline (traditional stats) and the experimental (advanced stats) feature sets.

**Independent Test**: The training script can be run independently to produce a JSON report containing ROC-AUC, log-loss, and Brier scores for both feature sets across all three algorithms, including the results of the hyperparameter tuning process.

**Acceptance Scenarios**:
1. **Given** the prepared training dataset, **When** the model training pipeline executes, **Then** three models (Logistic Regression, Random Forest, Gradient Boosting) are trained using 5-fold time-series cross-validation with hyperparameter tuning to optimize performance.
2. **Given** the trained models, **When** evaluation is performed on the held-out test set (2019-2022), **Then** the system outputs ROC-AUC, log-loss, and Brier scores for both the "Traditional Metrics" feature set and the "Advanced Metrics" feature set.
3. **Given** the evaluation results, **When** the system compares the "Advanced Metrics" model performance against the "Traditional Metrics" baseline, **Then** it identifies the specific model and feature combination that achieves the highest ROC-AUC.

---

### User Story 3 - Statistical Significance and Methodological Validation (Priority: P3)

As a methodologist, I need the system to perform a paired-sample statistical test (t-test or Wilcoxon) on the cross-validated scores and conduct a sensitivity analysis on any decision thresholds to confirm that observed performance gains are statistically significant and robust.

**Why this priority**: A performance difference alone is not scientific proof; statistical significance and robustness checks are required to validate the research hypothesis and ensure the findings are not due to random chance or arbitrary parameter choices.

**Independent Test**: The analysis script can be run to produce a final report containing p-values for the paired comparisons, a sensitivity analysis plot/table showing performance variance across threshold sweeps, and a statement on the methodological validity (e.g., associational framing).

**Acceptance Scenarios**:
1. **Given** the cross-validated ROC-AUC scores for the baseline and advanced models, **When** the statistical comparison module runs, **Then** it performs a Diebold-Mariano test or corrected resampled t-test (to account for temporal dependence) and reports a p-value to determine if the improvement is significant at α = 0.05.
2. **Given** any decision thresholds used in the analysis (e.g., classification cutoffs), **When** the sensitivity analysis runs, **Then** it sweeps the threshold over the full range [0.0, 1.0] with a step size of 0.01 and reports how the false-positive and false-negative rates vary, confirming robustness.
3. **Given** the observational nature of the data, **When** the final report is generated, **Then** it explicitly frames all findings as "associational" rather than "causal" to maintain methodological integrity.

### Edge Cases

- What happens when a specific season (e.g., 2020) has significantly fewer games due to external factors (e.g., pandemic)? The system must handle this by excluding the season or down-weighting it if it skews the temporal distribution, without breaking the chronological split logic.
- How does the system handle missing data for advanced metrics (e.g., wOBA cannot be calculated for a team with no at-bats in a game)? The system must impute these values with a neutral baseline (e.g., league average for that year) or exclude the game if the missingness is systemic.
- What if the test set (2019-2022) yields a lower ROC-AUC than the training set due to overfitting or a shift in league dynamics? The system must flag this as a "generalization gap" in the report rather than failing silently.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw CSV files from Retrosheet and Baseball-Reference, parse game IDs, and resolve team/player identifiers to create a unified dataset covering 2000-2022. (See US-1)
- **FR-002**: System MUST compute advanced metrics (wOBA, BABIP, park-adjusted run expectancy) and traditional metrics (batting average, ERA) for every team per game, ensuring no data leakage across the 2018/2019 temporal split. (See US-1)
- **FR-003**: System MUST train three distinct models (Logistic Regression, Random Forest, Gradient Boosting) using 5-fold time-series cross-validation with hyperparameter tuning on the training set. (See US-2)
- **FR-004**: System MUST evaluate all models on the held-out test set (2019-2022) and output ROC-AUC, log-loss, and Brier scores for both traditional and advanced feature sets. (See US-2)
- **FR-005**: System MUST perform a Diebold-Mariano test or corrected resampled t-test on the cross-validated ROC-AUC scores to determine if the performance difference is statistically significant at α = 0.05, accounting for temporal dependence. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis on classification thresholds by sweeping values across the full range [0.0, 1.0] with a step size of 0.01, explicitly defining a utility function or cost matrix to justify the analysis, and reporting the resulting variance in false-positive and false-negative rates. (See US-3)

### Key Entities

- **GameRecord**: Represents a single MLB game, containing attributes for date, home/away teams, final score, weather conditions, and the binary outcome (home_win).
- **TeamMetrics**: Represents the aggregated statistics for a team in a specific game, including both traditional (AVG, ERA) and advanced (wOBA, BABIP) features.
- **ModelResult**: Represents the output of a single model training run, containing hyperparameters, cross-validation scores, and test set performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive accuracy (ROC-AUC) of the model using advanced metrics is measured against the baseline model using only traditional metrics to determine the observed magnitude of improvement and statistical significance (p < 0.05). (See US-2)
- **SC-002**: The statistical significance of the performance difference is measured against the p-value threshold of 0.05 using a Diebold-Mariano test or corrected resampled t-test on cross-validated scores. (See US-3)
- **SC-003**: The robustness of the model's decision boundary is measured against the sensitivity analysis results to report the full variance profile of false-positive and false-negative rates across the threshold range. (See US-3)
- **SC-005**: The data validity is measured against a completeness rate of ≥ 95% for all required variables (predictors, outcomes, covariates) in the source datasets. (See US-1)

## Assumptions

- **Assumption about data availability**: The public datasets from Retrosheet and Baseball-Reference contain all necessary variables for computing wOBA, BABIP, and park factors for the years -2022. If specific weather data is missing, the system will default to a neutral "no weather impact" assumption or exclude games with missing weather if the feature is critical.
- **Assumption about temporal stability**: The relationship between advanced metrics and game outcomes remains relatively stable between the training period (2000-2018) and the test period (2019-2022), allowing for valid generalization without major regime shifts.
- **Assumption about compute resources**: The entire dataset (play-by-play and season stats for 23 years) fits within 7 GB of RAM when loaded into pandas DataFrames, and the training of XGBoost with hyperparameter tuning on 2 CPU cores completes within 6 hours on a CPU-only GitHub Actions runner.
- **Assumption about methodological framing**: Since the data is observational and lacks random assignment, all conclusions drawn regarding the "impact" of advanced metrics are strictly framed as associational correlations, not causal effects.
- **Assumption about metric definitions**: The definitions of "advanced metrics" (wOBA, BABIP) used in this study align with the standard community definitions provided by FanGraphs and Baseball-Reference, specifically using the standard wOBA formulas with annual league-average weights as defined by FanGraphs for the specific season year, ensuring comparability with existing literature.