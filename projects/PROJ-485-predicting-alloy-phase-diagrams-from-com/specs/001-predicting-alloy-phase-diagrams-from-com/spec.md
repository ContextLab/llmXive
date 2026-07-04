# Feature Specification: Predicting Alloy Phase Diagrams from Compositional Data

**Feature Branch**: `001-predict-alloy-phase-diagrams`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Alloy Phase Diagrams from Compositional Data with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1)

A materials researcher needs to ingest raw binary and ternary alloy phase data from the **NIST-JANAF Thermochemical Tables and SGTE databases** (or verified local CSVs) and automatically generate compositional descriptors (e.g., mean atomic radius, electronegativity variance, valence electron concentration) to create a training-ready dataset.

**Why this priority**: Without a clean, feature-engineered dataset derived from experimental ground truth, no predictive modeling can occur. This is the foundational data pipeline step.

**Independent Test**: This can be fully tested by running the data extraction script against a small, hardcoded subset of the NIST-JANAF/SGTE data (or a local mock file) and verifying the output CSV contains the correct number of rows and the specific derived feature columns with valid numeric ranges.

**Acceptance Scenarios**:

1. **Given** a valid access to the NIST-JANAF/SGTE database or a local CSV file, **When** the data extraction script runs, **Then** it retrieves phase boundary coordinates (temperature vs. composition) and filters for entries with valid temperature values.
2. **Given** a retrieved binary alloy composition (e.g., a hardcoded record for Cu-Al), **When** the descriptor generator runs, **Then** it calculates and appends at least four elemental descriptors (mean atomic radius, electronegativity variance, valence electron count, Hume-Rothery electron concentration) to the record.
3. **Given** a dataset entry with missing temperature data, **When** the pipeline processes the row, **Then** the row is excluded from the final training dataset with a logged warning.

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

A data scientist needs to train a Random Forest Regressor on the generated descriptors to predict phase transition temperatures and evaluate performance using Leave-One-System-Out (LOSO) cross-validation on unseen alloy systems, ensuring the test set contains only elements present in the training set.

**Why this priority**: This implements the core research hypothesis: determining if composition alone predicts phase boundaries. It validates the methodological approach.

**Independent Test**: This can be fully tested by executing the training script on a fixed random seed; the output must include a LOSO cross-validation report with Mean Absolute Error (MAE) and R² scores, a power analysis report, and the model file must be saved to disk.

**Acceptance Scenarios**:

1. **Given** a processed dataset of binary alloys, **When** the training script executes with Leave-One-System-Out (LOSO) cross-validation, **Then** it outputs a summary table showing the MAE and R² for each fold (where each fold excludes one unique alloy system) and the aggregate mean.
2. **Given** a held-out test set of a specific binary system (e.g., Al-Cu) which IS the excluded system in the current LOSO fold and containing only elements present in the training set, **When** the model predicts phase boundaries, **Then** it generates a set of predicted temperatures for a grid of compositions.
3. **Given** a single CPU core execution environment with <7 GB RAM, **When** the model training completes, **Then** the process finishes within 4 hours without memory errors.
4. **Given** the trained model and a null model baseline (predicting the global mean experimental temperature), **When** performance is compared, **Then** the Random Forest model must demonstrate a statistically significant reduction in MAE (p < 0.05) compared to the baseline and report the percentage improvement.
5. **Given** a power analysis result indicating statistical power < 0.8 (at α ≤ 0.05), **When** the pipeline completes, **Then** the system halts and reports the error code `INSUFFICIENT_POWER` instead of proceeding to final model evaluation.

### User Story 3 - Visualization and Fidelity Assessment (Priority: P3)

A domain expert needs to visualize the predicted phase diagrams alongside ground-truth data for representative **simple binary systems (e.g., Cu-Zn, Al-Cu)** to qualitatively assess the model's ability to reconstruct phase fields. Complex systems with metastable phases (e.g., Fe-C) are out of scope for this iteration.

**Why this priority**: While the model produces numbers, the scientific value lies in the visual reconstruction of phase fields to confirm physical plausibility for systems where the hypothesis holds.

**Independent Test**: This can be fully tested by running the visualization script on a specific binary system (e.g., Cu-Zn) and verifying that a plot file (PNG/SVG) is generated containing both the experimental ground-truth lines and the model-predicted lines.

**Acceptance Scenarios**:

1. **Given** a trained model and a selected binary system (e.g., Cu-Zn), **When** the visualization script runs, **Then** it generates a plot where the X-axis represents composition (0-100%) and the Y-axis represents temperature.
2. **Given** the generated plot, **When** a user inspects it, **Then** the experimental phase boundary lines are clearly distinguishable (e.g., solid line) from the model predictions (e.g., dashed line).
3. **Given** a system where the model fails to capture a critical phase transition, **When** the plot is generated, **Then** the discrepancy is flagged if the Mean Absolute Error (MAE) between predicted and experimental lines (derived from NIST-JANAF/SGTE) exceeds 50K.

### Edge Cases

- What happens when the dataset contains a ternary system where the NIST-JANAF/SGTE data lacks temperature-composition coordinates? The system must skip these entries and log a specific error code `MISSING_TEMP_COORDS` rather than crashing.
- How does the system handle a binary system with extremely low data density? The system must report error code `LOW_DATA_DENSITY` if the sample size is < 5 OR if the standard deviation of the prediction error exceeds 50K (Kelvin).
- What happens if the NIST-JANAF/SGTE API (or local file access) fails during bulk download? The system must implement an exponential backoff strategy with a maximum of 3 retries before failing gracefully with an `API_RATE_LIMIT_EXCEEDED` error.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve binary and ternary phase stability data from the **NIST-JANAF Thermochemical Tables and SGTE databases**, specifically filtering for records containing **experimental** phase boundary coordinates (See US-1). The system MUST validate the retrieved data schema to ensure it contains phase boundary coordinates; if the schema does not match, the system must fail gracefully with an `INVALID_DATA_SCHEMA` error.
- **FR-002**: System MUST generate at least four compositional descriptors (mean atomic radius, electronegativity variance, valence electron count, Hume-Rothery electron concentration) for every unique alloy composition in the dataset (See US-1).
- **FR-003**: System MUST train a Random Forest Regressor using scikit-learn with a Leave-One-System-Out (LOSO) cross-validation strategy to predict phase transition temperatures, ensuring the test set contains only elements present in the training set (See US-2).
- **FR-004**: System MUST calculate and report Mean Absolute Error (MAE) and R² scores for each cross-validation fold and the aggregate dataset (See US-2).
- **FR-005**: System MUST generate visualization plots comparing predicted phase boundaries against ground-truth data for at least two representative **simple binary systems (e.g., Cu-Zn, Al-Cu)**; complex systems with metastable phases (e.g., Fe-C) are excluded (See US-3).
- **FR-006**: System MUST execute the entire analysis pipeline on a **single CPU core** environment without requiring GPU acceleration or CUDA libraries (See US-2).
- **FR-007**: System MUST handle API rate limits by implementing an exponential backoff strategy with a maximum of 3 retries before failing gracefully (See Edge Cases).
- **FR-008**: System MUST log specific error codes (`MISSING_TEMP_COORDS`, `LOW_DATA_DENSITY`) for data quality issues to ensure traceability; `LOW_DATA_DENSITY` is triggered if sample size < 5 OR if the standard deviation of prediction error > 50K (Kelvin) (See Edge Cases).
- **FR-009**: System MUST compare the Random Forest model performance against a null model baseline (global mean experimental temperature) and report the percentage improvement, ensuring the baseline is derived from experimental data distinct from any computational assessment (See US-2).
- **FR-010**: System MUST validate that no "new element" exists in the test fold of the LOSO cross-validation before training; if a new element is detected, the fold is skipped or the system halts (See US-2).
- **FR-011**: System MUST perform a statistical power analysis (target power ≥ 0.8, α ≤ 0.05) on the dataset before training to justify the sample size (See US-2).
- **FR-012**: System MUST implement a fallback mechanism to load local CSVs of literature-curated experimental phase data if the primary NIST-JANAF/SGTE source is unavailable (See US-1).
- **FR-013**: System MUST calculate the standard deviation of prediction errors per system to evaluate data density (See FR-008).
- **FR-014**: System MUST halt the pipeline and report `INSUFFICIENT_POWER` if the power analysis indicates the dataset is too small to detect the effect size (See US-2).
- **FR-015**: System MUST include Hume-Rothery derived features (e.g., valence electron concentration) in the descriptor set to improve physical validity (See FR-002).

### Key Entities

- **AlloyComposition**: Represents a specific mixture of elements, defined by elemental fractions and derived descriptors (atomic radius, electronegativity, valence electron concentration).
- **PhaseBoundary**: Represents a point on a phase diagram, defined by composition (x-axis) and temperature (y-axis), linked to a specific AlloyComposition.
- **ModelMetrics**: Stores the performance results (MAE, R²) of the regression model, linked to a specific cross-validation fold or test set.
- **PowerAnalysisResult**: Stores the calculated statistical power, effect size, and sample size justification.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The prediction error (MAE) for phase transition temperatures is measured against the ground-truth experimental data for the held-out test set (See US-2).
- **SC-002**: The generalization capability (R² score) is measured against the performance on the Leave-One-System-Out (LOSO) test sets to ensure independence from training chemistry (See US-2).
- **SC-003**: The computational feasibility is measured against the constraint of completing the full pipeline within 4 hours on a **single CPU core** with <7 GB RAM (See US-2).
- **SC-004**: The visual fidelity of the reconstructed phase diagrams is measured against the **Mean Absolute Error (MAE)** of the predicted boundary lines compared to experimental ground truth, with a target MAE ≤ 50K for representative systems (See US-3).
- **SC-005**: The descriptor generation logic is validated against known physical constants (e.g., atomic radius of Cu) with ≤ 1% deviation, and derived values (e.g., valence electron concentration) are validated against calculated values from constituent elements (See US-1).
- **SC-006**: The statistical power analysis is reported with a calculated power value ≥ 0.8 (at α ≤ 0.05); if power < 0.8, the project halts (See US-2).
- **SC-007**: The generated descriptors (mean atomic radius, electronegativity, etc.) are validated against a reference dataset of known physical constants with ≤ 1% deviation (See US-1).
- **SC-008**: The model performance improvement over the null baseline is measured as a percentage reduction in MAE, with a target of statistically significant improvement (p < 0.05) (See US-2).
- **SC-009**: The standard deviation of prediction errors is measured against a threshold of 50K (Kelvin) to trigger the `LOW_DATA_DENSITY` error condition (See Edge Cases).

## Assumptions

- **Hypothesis**: The compositional descriptors (mean atomic radius, electronegativity variance, valence electron concentration, Hume-Rothery electron concentration) **may** contain sufficient information to approximate phase stability boundaries for simple binary systems without explicit thermodynamic simulation inputs. This is a hypothesis to be tested, not a fixed assumption.
- **Data Source**: The NIST-JANAF Thermochemical Tables and SGTE databases provide sufficient **experimental** temperature-composition phase boundary data for a statistically significant sample of binary systems to train a Random Forest model.
- **Fallback Data**: A local CSV of literature-curated experimental phase data is available in the repository if the primary API access fails.
- **Algorithm Capability**: The Random Forest algorithm, as implemented in scikit-learn, is capable of capturing the non-linear relationships between elemental properties and phase transition temperatures within the memory constraints of a single CPU core.
- **Data Quality**: The dataset does not require complex imputation for missing temperature values; entries lacking phase boundary coordinates can be safely excluded without introducing significant selection bias.
- **Scope Boundary**: The "phase stability boundaries" refer specifically to the liquidus and solidus lines where sufficient experimental data exists, excluding more complex invariant reactions (e.g., eutectic, peritectic) and metastable phases (e.g., cementite in Fe-C) that may lack clear coordinate definitions or are kinetically controlled.
- **Baseline Validity**: A null model based on the global mean experimental temperature provides a valid baseline for establishing the non-triviality of the machine learning model's predictions.
- **Generalization Scope**: The model is expected to generalize to "new systems" (interpolation of known elements) but **not** to "new elements" (elements not seen in training).
- **Descriptor Sufficiency**: The selected descriptors (mean atomic radius, electronegativity, valence electron concentration, Hume-Rothery electron concentration) are sufficient to capture the primary thermodynamic drivers for simple binary systems, though they may not capture complex kinetic effects in systems like Fe-C.