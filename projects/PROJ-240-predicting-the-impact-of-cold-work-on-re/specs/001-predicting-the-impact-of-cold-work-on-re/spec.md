# Feature Specification: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Feature Branch**: `001-cold-work-recrystallization`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Variable Validation (Priority: P1)

As a materials researcher, I want to ingest experimental data from public repositories (NIST, HuggingFace) and automatically validate that all required variables (cold work %, alloy composition, annealing temperature, time-to-peak softening) are present and within physical bounds, so that I can proceed with analysis without manual data scrubbing.

**Why this priority**: Without valid, complete input data, no modeling or kinetic analysis can occur. This is the foundational step that ensures the dataset-variable fit required for the study.

**Independent Test**: The system can be tested by feeding a raw CSV file containing the required columns; it must output a cleaned dataset and a validation report listing any missing variables or out-of-bounds values (e.g., negative cold work, >100% deformation) without requiring any model training.

**Acceptance Scenarios**:

1. **Given** a dataset with missing "time-to-peak softening" values for [deferred] of entries, **When** the ingestion script runs, **Then** the system flags these rows for exclusion and reports the count of excluded samples in the validation log.
2. **Given** a dataset where "cold work percentage" contains a value of -5%, **When** the ingestion script runs, **Then** the system rejects this row as physically impossible and logs a warning with the specific row ID and value.
3. **Given** a dataset with alloy composition columns (Mg, Si, Cu) but no "alloy series" identifier, **When** the ingestion script runs, **Then** the system attempts to derive the series only if the composition falls strictly within a defined boundary for a series (e.g., Mg > 2.5% for 5xxx); if the composition is ambiguous or falls between boundaries, the system flags the record as 'Unresolved Series' for exclusion. The system prioritizes continuous solute variables over nominal series labels for downstream modeling.

---

### User Story 2 - Kinetic Model Training and Feature Importance (Priority: P2)

As a process engineer, I want to train a CPU-tractable Random Forest Regressor to predict time-to-peak softening based on cold work and composition, and receive a ranked list of feature importances, so that I can identify whether deformation level or specific solute content drives the kinetic variance.

**Why this priority**: This is the core analytical engine of the project. It directly addresses the research question regarding the "non-linear relationship" and the "modifier effect" of alloy composition.

**Independent Test**: The system can be tested by running the training script on a pre-processed dataset; it must output a trained model artifact and a JSON report of feature importances, with execution completing within 60 minutes on a 2-CPU runner.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] rows with normalized composition and cold work features, **When** the training script executes, **Then** the model converges and outputs a ranked list of feature importances with confidence intervals for each feature.
2. **Given** a dataset where "annealing temperature" varies but is controlled for in the model training, **When** the model is trained, **Then** the system correctly identifies and reports the interaction effect between "cold work percentage" and "annealing temperature" on the target variance.
3. **Given** a dataset with collinear predictors (e.g., total solute content vs. individual elements), **When** the model is trained, **Then** the system logs a collinearity diagnostic warning and reports the variance inflation factor (VIF) for the top correlated features.

---

### User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

As a quality assurance specialist, I want to evaluate the model on a held-out test set and perform a sensitivity analysis on the prediction confidence intervals, so that I can quantify the model's generalization error and ensure the results are robust to minor parameter variations.

**Why this priority**: This validates the scientific rigor (methodological soundness) of the findings, ensuring the results are not overfitted and that the "saturation at high deformation" hypothesis is supported by robust statistics.

**Independent Test**: The system can be tested by running the validation script on a separate test set; it must output R² and MAE metrics, plus a sensitivity report showing how error rates change when the prediction confidence interval is varied.

**Acceptance Scenarios**:

1. **Given** a held-out test set of 500 experimental points, **When** the validation script runs, **Then** the system calculates an R² score and reports it; if the R² is below a configurable threshold, the system flags the result as "Below Target Threshold" for scientific review without halting execution.
2. **Given** a prediction confidence interval for "time-to-peak" defined as ±10%, **When** the sensitivity analysis runs, **Then** the system sweeps the interval across {[deferred], [deferred], [deferred]} and reports the variation in MAE and R² of the underlying regression model.
3. **Given** an observational dataset (no randomization), **When** the results are generated, **Then** the system automatically appends a disclaimer to the output stating that findings are "associational, not causal" as per the inference framing requirement.

### Edge Cases

- What happens when the public dataset contains no entries for a specific alloy series (e.g., 6xxx) required for the analysis? The system must flag the missing series and exclude it from the "feature importance" ranking for that specific group.
- How does the system handle datasets where the "time-to-peak softening" is recorded in seconds instead of minutes? The system must detect the unit (via heuristic or metadata) and normalize to minutes, or flag a unit mismatch error.
- How does the system handle a scenario where the Random Forest model fails to converge due to extreme multicollinearity? The system must fall back to a linear regression with regularization (Ridge) and log the switch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest data from NIST Materials Data Repository and HuggingFace Datasets, parsing CSV/text to extract cold work %, alloy composition (Mg, Si, Cu, Mn), annealing temperature, and time-to-peak softening (See US-1).
- **FR-002**: System MUST validate all input variables against physical bounds (e.g., 0 ≤ cold work ≤ 100%, positive time-to-peak) and exclude invalid rows before modeling (See US-1).
- **FR-003**: System MUST train a Random Forest Regressor (Scikit-learn) using only CPU resources, limiting the dataset to <5,000 rows to ensure completion within 60 minutes on a 2-core runner with 7 GB RAM (See US-2).
- **FR-004**: System MUST output a feature importance ranking that explicitly quantifies the contribution of "cold work percentage" versus specific solute elements to the variance in time-to-peak softening (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis on the prediction confidence interval by sweeping the interval over {[deferred], [deferred], [deferred]} and reporting the resulting change in MAE and R² (See US-3).
- **FR-006**: System MUST detect and log collinearity diagnostics (e.g., VIF) for any predictors that are definitionally related (e.g., total solute vs. individual elements) and MUST NOT include both derived categorical Alloy Series and raw elemental weights simultaneously in the model input vector (See US-2).
- **FR-007**: System MUST calculate permutation-based feature importance scores with 95% confidence intervals if the feature importance test involves more than 5 features (See US-2).

### Key Entities

- **ExperimentalRecord**: Represents a single data point containing processing history (cold work, temperature) and kinetic outcome (time-to-peak).
- **AlloyComposition**: Represents the chemical makeup of the sample, including wt% of major solutes. Note: Derived Alloy Series labels are stored for metadata but are excluded from the model input vector to prevent masking.
- **KineticModel**: The trained regression model object mapping input features to predicted time-to-peak.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The model's predictive performance (R²) is measured against the held-out experimental test set to determine if the variance is explained by the combined factors (See US-3).
- **SC-002**: The robustness of the prediction is measured against the sensitivity sweep results across a representative range of confidence interval thresholds (See US-3).
- **SC-003**: The statistical validity of the feature importance claims is measured against the collinearity diagnostics and permutation-based confidence intervals (See US-2).
- **SC-004**: The computational feasibility is measured against a fixed wall-clock time limit and RAM constraint on the standard GitHub Actions runner (See US-2).
- **SC-005**: The data completeness is measured against the requirement that all variables needed for the regression (cold work, composition, temperature, time-to-peak) are present in the final dataset (See US-1).

## Assumptions

- The public datasets (NIST, HuggingFace) contain sufficient rows (>1,000) with the specific combination of cold work percentage and time-to-peak softening measurements to train a meaningful regression model.
- The "time-to-peak softening" variable is recorded in a consistent unit (minutes) across all source datasets, or can be reliably normalized via metadata parsing.
- The relationship between cold work and recrystallization kinetics is non-linear but can be adequately approximated by a Random Forest Regressor without requiring deep learning or GPU acceleration.
- The "alloy series" (e.g., 5xxx, 6xxx) can be derived from the chemical composition (Mg, Si, Cu ratios) if not explicitly provided in the source data, but derived series labels will not be used as primary inputs for the kinetic model.
- The observational nature of the data means the model will identify associations, not causal mechanisms; the results will be framed as "predictive of kinetics" rather than "causing kinetics."
- The dataset size will naturally fall below a substantial threshold.; if it exceeds this, the system will randomly sample to fit the memory constraints without introducing significant bias.