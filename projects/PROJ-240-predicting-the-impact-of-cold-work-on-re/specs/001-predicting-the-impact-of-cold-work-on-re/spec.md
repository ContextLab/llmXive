# Feature Specification: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Feature Branch**: `001-predict-cold-work-kinetics`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Construction (Priority: P1)

A materials scientist needs to ingest raw experimental data from public repositories (NIST, HuggingFace) and transform it into a structured dataset containing cold work percentages, alloy compositions (Mg, Si, Cu, Mn), annealing temperatures, and time-to-peak softening, while engineering interaction features to capture pinning effects.

**Why this priority**: Without a clean, engineered dataset containing the necessary interaction terms (e.g., `cold_work * Mn_content`) and temperature-normalized kinetics, no predictive modeling can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: The system can be tested by running the data pipeline on a provided sample CSV and verifying the output DataFrame contains the required columns, calculated interaction features, and Arrhenius-normalized time variables without errors.

**Acceptance Scenarios**:

1. **Given** a raw CSV file from the NIST repository containing cold work and annealing data, **When** the ingestion script is executed, **Then** the output is a pandas DataFrame with normalized composition variables, engineered interaction features (e.g., `cold_work * Mn_content`), and time-to-peak values normalized to a reference temperature (e.g., 450K).
2. **Given** a dataset with missing alloy composition values for specific rows, **When** the cleaning step runs, **Then** those rows are either imputed using a defined strategy (e.g., mean of series) or flagged for exclusion, ensuring the final dataset has no null values in predictor columns.

---

### User Story 2 - Predictive Model Training and Validation (Priority: P2)

A researcher needs to train a Random Forest Regressor to predict time-to-peak softening using the engineered features and validate its performance using 5-fold cross-validation and a held-out test set to ensure generalization.

**Why this priority**: This delivers the core predictive capability. It moves beyond simple data preparation to generate the quantitative model that addresses the research question regarding the influence of cold work and composition.

**Independent Test**: The system can be tested by training the model on the full dataset (excluding the hold-out set) using a fixed random seed (seed=42) and an 80/20 stratified split, verifying that the cross-validation score is calculated and the model predicts values for the hold-out set with a Mean Absolute Error (MAE) below the threshold defined in SC-006.

**Acceptance Scenarios**:

1. **Given** the cleaned and engineered dataset split into training and test sets (80/20, seed=42), **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the system outputs the mean cross-validation R² score and standard deviation.
2. **Given** a held-out test set not used during training, **When** the trained model predicts time-to-peak softening, **Then** the Mean Absolute Error (MAE) is calculated and reported, demonstrating the model's ability to generalize to unseen alloy compositions and deformation levels.

---

### User Story 3 - Statistical Significance and Interaction Analysis (Priority: P3)

A metallurgist needs to statistically verify that including alloy composition interaction terms significantly improves prediction accuracy compared to a baseline model using only cold work and additive composition effects, and identify which factors drive the variance.

**Why this priority**: This addresses the "research gap" by quantifying the *additional* explanatory power of interaction terms, moving beyond empirical heuristics to a statistically validated understanding of the mechanisms.

**Independent Test**: The system can be tested by running a Likelihood Ratio Test (or equivalent permutation importance test) comparing the error distributions of the additive model and the interaction model, and verifying that feature importance scores are generated.

**Acceptance Scenarios**:

1. **Given** two models (one additive: cold work + composition, one interaction: cold work + composition + interactions), **When** a Likelihood Ratio Test is performed on their prediction errors, **Then** the system reports a p-value indicating whether the interaction model's improvement is statistically significant (p < 0.05).
2. **Given** the trained Random Forest model, **When** feature importance is extracted, **Then** the output lists the top 5 features (including interaction terms) ranked by their contribution to reducing variance, allowing the researcher to identify key pinning mechanisms.

### Edge Cases

- What happens when the dataset contains only pure aluminum (no alloying elements)? The system must handle zero variance in composition columns without crashing and flag that the "interaction effect" cannot be computed for this subset.
- How does the system handle outliers in time-to-peak softening (e.g., > 1000 hours)? The system must cap or clip extreme values to prevent skewing the Random Forest training **before** any statistical testing is performed, logging any clipped values for review.
- What occurs if the dataset size is < 50 rows? The system must halt training and return an error indicating insufficient data for meaningful 5-fold cross-validation, as a minimum of 50 samples is required to ensure statistical power in the validation split.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw CSV/JSON data from specified URLs and parse it into a structured tabular format with columns for cold work (%), alloy composition (wt%), annealing temperature (K), and time-to-peak softening. (See US-1)
- **FR-002**: System MUST engineer interaction features by multiplying cold work percentage with specific alloying element concentrations (e.g., `cold_work * Mn_content`) AND MUST normalize time-to-peak softening values to a reference temperature (e.g., 450K) using Arrhenius kinetics to account for temperature dependence. (See US-1)
- **FR-003**: System MUST train a Random Forest Regressor using CPU-only execution. If the input dataset exceeds a predefined threshold, the system MUST truncate the dataset to a manageable subset of entries. The system MUST complete execution within the allocated CI runner timeout and available memory limits. (See US-2)
- **FR-004**: System MUST perform 5-fold cross-validation and evaluate performance on a held-out test set (80/20 split, random seed=42) to calculate R² and Mean Absolute Error (MAE). (See US-2)
- **FR-005**: System MUST execute a Likelihood Ratio Test (or equivalent statistical test) comparing the error distributions of an Additive Model (cold work + composition) and an Interaction Model (cold work + composition + interactions) to determine if the interaction terms provide statistically significant improvement (p < 0.05). (See US-3)
- **FR-006**: System MUST output feature importance rankings to identify which alloying elements and interaction terms most significantly explain the variance in softening time. (See US-3)
- **FR-007**: System MUST perform outlier clipping on the target variable (time-to-peak softening) prior to calculating any error metrics or performing statistical significance tests to ensure the tests are based on cleaned data. (See Edge Cases)

### Key Entities

- **ExperimentRecord**: Represents a single experimental data point containing cold work percentage, alloy composition (Mg, Si, Cu, Mn), annealing temperature, and observed time-to-peak softening.
- **EngineeredFeatureSet**: A derived entity containing normalized composition variables, Arrhenius-normalized time variables, and calculated interaction terms (e.g., `cold_work * Mn_content`) used as inputs for the regression model.
- **ModelPerformanceMetrics**: A record containing R², MAE, and p-values derived from cross-validation, held-out testing, and statistical significance comparisons.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The R² score of the full model on the held-out test set (fixed seed=42, 80/20 split) is measured against the target of > 0.6 to determine if the model successfully explains the variance in softening time. (See FR-004)
- **SC-002**: The p-value from the Likelihood Ratio Test comparing the Additive Model and the Interaction Model is measured against the significance threshold of 0.05 to confirm that interaction terms provide a statistically significant improvement beyond additive effects. (See FR-005)
- **SC-003**: The statistical significance of the interaction term is measured via permutation importance (must be > 0.05) OR via the p-value of the Likelihood Ratio Test (must be < 0.05) to validate the pinning hypothesis, rather than relying on feature rank. (See FR-006)
- **SC-004**: The total runtime of the analysis pipeline is measured against the allocated CI runner timeout to verify compute feasibility. (See FR-003)
- **SC-005**: The memory usage during model training is measured against the available CI memory to ensure the dataset and model fit within the free-tier CI constraints. (See FR-003)
- **SC-006**: The Mean Absolute Error (MAE) of the full model on the held-out test set is measured against a target of < 15% of the mean time-to-peak softening to ensure prediction accuracy. (See FR-004)

## Assumptions

- The NIST Materials Data Repository and HuggingFace Datasets contain sufficient public records (≥ 100 valid entries) with explicit values for cold work percentage, specific alloying elements (Mg, Si, Cu, Mn), and time-to-peak softening.
- The relationship between cold work and recrystallization is primarily associative in this observational dataset; no causal claims will be made regarding the mechanism of pinning without randomized controlled trials.
- The Random Forest algorithm, when configured with default parameters and a modest number of trees (e.g., 100), will complete training within the allocated CI timeout for datasets ≤ 10,000 rows.
- The "time-to-peak softening" variable is consistently reported in minutes or hours across all sources and can be normalized to a single unit (minutes) and then Arrhenius-normalized to a reference temperature (e.g., 450K) without loss of precision, assuming activation energies are available or estimated from literature.
- Missing values in alloy composition columns are rare (< 5% of rows) and can be imputed using the mean value of the specific alloy series without introducing significant bias.
- The dataset does not contain duplicate entries for the same experimental condition; if duplicates exist, they are treated as independent measurements of the same process.
- Outliers in time-to-peak softening (> 1000 hours) are due to measurement error or non-representative conditions and can be safely clipped without invalidating the statistical analysis.