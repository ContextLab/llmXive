# Feature Specification: Predicting Avian Song Variation with Climatic and Geographic Factors

**Feature Branch**: `001-predicting-avian-song-variation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Avian Song Variation with Climatic and Geographic Factors"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Variable Alignment (Priority: P1)

As a researcher, I want to ingest the avian acoustic dataset and align it with corresponding climate (temperature, precipitation) and geographic (latitude, longitude, elevation) variables so that I have a single, clean analysis-ready table.

**Why this priority**: Without a unified dataset where every song recording has matched environmental predictors, no modeling or analysis can proceed. This is the foundational step.

**Independent Test**: The pipeline can be tested by loading the raw acoustic CSV and the raw climate CSVs, joining them by species and location ID, and outputting a single CSV with no missing rows for the core variables.

**Acceptance Scenarios**:

1. **Given** raw acoustic recordings with species and location IDs, **When** the ingestion script runs against the climate and geographic datasets, **Then** the output dataset contains a row for every recording with matched temperature, precipitation, latitude, longitude, and elevation values.
2. **Given** a location ID in the acoustic dataset that has no corresponding entry in the climate dataset, **When** the script runs, **Then** that record is flagged or removed, and a log is generated listing the missing matches.

---

### User Story 2 - Exploratory Data Analysis and Correlation Matrix (Priority: P2)

As a researcher, I want to generate a correlation matrix and scatterplot matrix of the song variation metrics against the environmental predictors so that I can visually inspect potential relationships and multicollinearity before modeling.

**Why this priority**: This step is critical for hypothesis generation and diagnosing predictor collinearity (e.g., latitude and temperature often correlate). It informs the modeling strategy but is not the final result.

**Independent Test**: The script produces a PDF report containing a correlation heatmap and a grid of scatterplots with no runtime errors.

**Acceptance Scenarios**:

1. **Given** the aligned dataset from User Story 1, **When** the EDA script executes, **Then** it outputs a PDF containing a correlation matrix of all continuous variables and scatterplots of each song metric against each climate variable.
2. **Given** two predictors that are definitionally related (e.g., derived from the same source) with a correlation coefficient |r| > 0.8, **When** the EDA script executes, **Then** the system automatically applies dimensionality reduction (PCA) or regularization (Ridge/Lasso) to the predictor set and documents the method used in the report, rather than merely flagging for manual review.

---

### User Story 3 - Associational Modeling and Sensitivity Analysis (Priority: P3)

As a researcher, I want to run a linear regression model to quantify the association between environmental factors and song variation, and perform a sensitivity analysis on the model's inclusion threshold to ensure robustness.

**Why this priority**: This delivers the core scientific insight (the association) and addresses the methodological requirement for threshold justification and sensitivity analysis.

**Independent Test**: The model runs successfully on the CPU, produces coefficient estimates, and the sensitivity analysis loop completes, outputting a table of results across different thresholds.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset, **When** the regression model runs, **Then** it outputs a summary table of coefficients, p-values, and R-squared values for the association between climate/geography and song metrics.
2. **Given** a decision threshold for variable inclusion (e.g., p < 0.05), **When** the sensitivity analysis runs, **Then** it re-runs the model with thresholds swept across {0.01, 0.05, 0.1} and reports the change in the number of significant predictors and model fit metrics.
3. **Given** the trained model, **When** evaluated on the hold-out validation set, **Then** the system reports the predictive stability (R² difference) between training and validation sets.

---

### Edge Cases

- What happens when the acoustic dataset contains multiple recordings for the exact same location and species but with different timestamps, and the climate data is aggregated daily? (System must aggregate or select the closest match).
- How does the system handle species with extremely low sample sizes (e.g., < 5 recordings) in the dataset? (These should be flagged or excluded from the regression to prevent model instability).
- What occurs if the climate dataset has missing values for a specific coordinate? (The record is dropped, and the count of dropped records is logged).
- What happens if the song variation metric is not normally distributed? (System switches to a Generalized Linear Model (GLM) with an appropriate link function).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the avian acoustic dataset and merge it with climate (temperature, precipitation) and geographic (lat, lon, elevation) data based on species and location identifiers (See US-1).
- **FR-002**: System MUST generate a correlation matrix and scatterplot matrix to visualize relationships and detect multicollinearity among predictors; if |r| > 0.8, the system MUST automatically apply dimensionality reduction (PCA) or regularization (Ridge/Lasso) and document the method (See US-2).
- **FR-003**: System MUST fit a linear regression model to quantify the associational relationship between environmental predictors and song variation metrics, framing results as associations rather than causal effects; ALL result headers MUST include the phrase "Associational Analysis" (See US-3).
- **FR-004**: System MUST perform a sensitivity analysis by sweeping the statistical significance threshold (p-value) across {0.01, 0.05, 0.1} and reporting the variation in model outcomes (See US-3).
- **FR-005**: System MUST output all results (datasets, plots, model summaries) in a format compatible with standard CSV/PDF viewers without requiring GPU acceleration (See US-1, US-2, US-3).
- **FR-006**: System MUST log the number of records dropped due to missing data or insufficient sample size per species (See US-1).
- **FR-007**: System MUST partition the dataset into a training set ([deferred]) and a hold-out validation set ([deferred]) BEFORE modeling, and evaluate the final model on the hold-out set to validate robustness against artifacts (See US-3).
- **FR-008**: System MUST explicitly model confounding structure by including habitat covariates or using phylogenetic generalized least squares (PGLS) if phylogenetic data is available; if not, the system MUST include geographic coordinates as proxies and report the variance explained by these confounders (See US-3).
- **FR-009**: System MUST perform distributional assumption checks (Shapiro-Wilk test) on the residuals; if the null hypothesis is rejected (p < 0.05), the system MUST switch to a Generalized Linear Model (GLM) with a distribution appropriate for the data (e.g., Gamma, Poisson) and report the selected family (See Edge Cases).

### Key Entities

- **SongRecord**: Represents a single acoustic recording, containing attributes: species, location_id, song_metric_1, song_metric_2, timestamp.
- **EnvironmentRecord**: Represents the environmental context for a location, containing attributes: location_id, avg_temp, total_precip, latitude, longitude, elevation.
- **ModelResult**: Represents the output of the regression analysis, containing attributes: predictor_name, coefficient, p_value, r_squared, model_family.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data alignment success rate is measured against the total number of raw acoustic records; the system MUST achieve a success rate of ≥ 95% (See US-1).
- **SC-002**: Model convergence rate is measured against the total number of species subsets attempted; the system MUST achieve a convergence rate of ≥ 90% (See US-3).
- **SC-003**: Sensitivity analysis coverage is measured against the specified threshold set {0.01, 0.05, 0.1} (See US-3).
- **SC-004**: Runtime duration is measured against the time limit of the GitHub Actions free-tier runner (6 hours); the system MUST complete within 4.8 hours ([deferred] of the limit) (See US-3).
- **SC-005**: Memory usage is measured against the RAM limit of the CI environment (7 GB); the system MUST not exceed a specified memory capacity threshold (a defined percentage of the limit) during execution. (See US-1, US-3).
- **SC-006**: Predictive stability is measured as the absolute difference in R² between training and hold-out validation sets; the system MUST report this value and ensure it is < 0.10 (See US-3, FR-007).
- **SC-007**: Confounder variance explanation is measured as the proportion of total variance in the response explained by the confounding structure (habitat/phylogeny/coordinates) versus the climate predictors; the system MUST report this partition (See US-3, FR-008).
- **SC-008**: Model family selection is measured by the distributional assumption check; the system MUST report whether OLS or a GLM was used and the specific family/link function if GLM was selected (See FR-009).

## Assumptions

- The avian acoustic dataset provided contains the necessary song variation metrics (e.g., frequency, duration, entropy) and location identifiers.
- The climate and geographic datasets cover the spatial and temporal range of the acoustic recordings; if gaps exist, they will result in dropped records rather than imputation.
- The analysis is strictly observational; therefore, all findings regarding climate and geography will be framed as associational, not causal.
- The dataset size fits within the ~7 GB RAM limit of the free-tier runner; if the full dataset is too large, a random sample of records will be used for the initial analysis.
- The "song variation" metric is a continuous variable suitable for linear regression; if the data is not normally distributed, the system will automatically switch to a GLM as defined in FR-009.
- No GPU is available; all statistical computations will use CPU-optimized libraries (e.g., `scikit-learn`, `statsmodels`) in default precision.
- Phylogenetic data may not be available; if missing, geographic coordinates will serve as a proxy for phylogenetic/habitat structure as per FR-008.