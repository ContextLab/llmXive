# Feature Specification: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Feature Branch**: `001-unveiling-hidden-correlations`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys"

## User Scenarios & Testing

### User Story US-1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

A researcher uploads or downloads a raw public AM alloy dataset and receives a clean, normalized CSV ready for modeling, with missing values handled and categorical variables encoded.

**Why this priority**: Without clean, structured data, no modeling or analysis can occur. This is the foundational step that enables all subsequent user stories.

**Independent Test**: Can be fully tested by running the preprocessing script on a known raw dataset file and verifying the output CSV contains normalized numeric columns, one-hot encoded alloy types, and no missing values, with a log file confirming the imputation and normalization steps.

**Acceptance Scenarios**:

1. **Given** a raw CSV with missing values in "Laser Power" and "Yield Strength", **When** the preprocessing script runs, **Then** the output CSV has these values replaced by the column median, and a log entry records the imputation count.
2. **Given** a dataset with alloy types "Ti-6Al-4V" and "Inconel 718", **When** the script runs, **Then** the output CSV contains binary columns "is_Ti-6Al-4V" and "is_Inconel_718" with values 0 or 1, and the original "alloy_type" column is removed.
3. **Given** a dataset where "Laser Power" ranges from 100-500W, **When** normalization runs, **Then** the "Laser Power_norm" column values are strictly between the minimum possible normalized value and 1.0.

---

### User Story US-2 - Gaussian Process Regression Model Training and Validation (Priority: P2)

A researcher trains a Gaussian Process Regression model to predict mechanical properties from processing parameters and receives performance metrics (R², RMSE) documenting the model's predictive capability.

**Why this priority**: This delivers the core scientific value: quantifying the non-linear relationships. It depends on US-1 but is the primary mechanism for answering the research question.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed data, verifying the model object is saved, and checking a results JSON file for R² and RMSE values that are reported (without arbitrary pass/fail thresholds).

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with a substantial number of samples, **When** the GPR training script executes with 5-fold cross-validation, **Then** the output JSON contains an `r2_score` value (regardless of magnitude) to document the relationship strength.
2. **Given** a target property range spanning the lower end up to 1000 MPa for Yield Strength, **When** the model predicts on the test set, **Then** the `rmse` value in the results JSON is reported as a percentage of the observed range in the test set.
3. **Given** a random seed of 42, **When** the training is repeated, **Then** the resulting model artifacts and performance metrics are identical, ensuring reproducibility.

---

### User Story US-3 - Uncertainty Quantification and Visualization (Priority: P3)

A researcher views contour plots of predicted mechanical properties overlaid with uncertainty heatmaps to identify parameter regimes with high prediction confidence versus those requiring further experimentation.

**Why this priority**: This provides the "uncertainty-aware" aspect of the methodology, guiding future experimental design. It is a value-add on top of the core prediction model.

**Independent Test**: Can be fully tested by running the visualization script, confirming PNG files are generated, and verifying that regions with high predicted standard deviation (σ) are correctly highlighted in red on the uncertainty heatmap.

**Acceptance Scenarios**:

1. **Given** a trained GPR model and test data, **When** the visualization script runs, **Then** a contour plot of predicted Yield Strength vs. Laser Power and Scan Speed is generated as a PNG file ≤5MB.
2. **Given** a test point with a predicted standard deviation (σ) greater than 2× the median σ, **When** the uncertainty heatmap is generated, **Then** that region is colored red to indicate high uncertainty.
3. **Given** the top few most influential parameters identified by permutation importance, **When** partial dependence plots are generated, **Then** three separate PNG files are produced, each showing the relationship between one parameter and the predicted property.

### Edge Cases

- What happens when the input dataset has fewer than 50 samples? The system MUST halt execution and log an error: "Insufficient data for GPR training; minimum 50 samples required."
- How does the system handle a dataset where all values for a specific feature (e.g., "Layer Thickness") are identical? The system MUST detect zero variance, log a warning, and exclude that feature from the model to prevent singularity.
- What happens if the public dataset download fails due to network issues? The system MUST retry the download a limited number of times with a backoff interval, then fail gracefully with a clear error message directing the user to manual download instructions.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse public AM alloy datasets (Zenodo, HuggingFace, UCI) and validate that the loaded dataset **contains exactly the required columns** `laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, and `ductility` (or a recognized synonym) **with at least 50 samples** (See US-1). If any required column is missing or renamed, the system MUST abort and log a descriptive error.
- **FR-002**: System MUST perform median imputation for missing values and min-max normalization for all numeric features to the [0,1] range (See US-1).
- **FR-003**: System MUST implement Gaussian Process Regression with an RBF kernel and optimize hyperparameters via 5-fold cross-validation to maximize log marginal likelihood (See US-2).
- **FR-004**: System MUST calculate and output R², RMSE, and MAE metrics on a held-out test set in a JSON results file (See US-2).
- **FR-005**: System MUST generate contour plots of predicted properties and uncertainty heatmaps overlaying the parameter space (See US-3).
- **FR-006**: System MUST perform permutation importance analysis to rank the influence of processing parameters on predicted outcomes (See US-3).
- **FR-007**: System MUST identify parameter regions where predictive uncertainty (σ) exceeds 2× the median uncertainty and flag them as high-priority for future data collection (See US-3).
- **FR-008**: System MUST incorporate alloy composition as a categorical feature in the GPR model and optionally perform stratified analysis or include it as a covariate to control for confounding effects (See US-2).
- **FR-009**: System MUST explicitly detect and control for latent confounding variables (e.g., alloy composition, documented microstructural state) by (a) including them as covariates in the GPR model, (b) reporting variance‑inflation factors or correlation diagnostics, and (c) providing a stratified performance report per alloy type to demonstrate that inferred process‑property relationships are not driven by composition alone (See US-2).

### Key Entities

- **Dataset Record**: A single experimental observation containing processing parameters (power, speed, thickness), alloy composition, and resulting mechanical properties.
- **Model Artifact**: A serialized GPR model object including hyperparameters, training data references, and performance metrics.
- **Uncertainty Map**: A 2D representation of the parameter space where each cell contains a predicted value and a standard deviation estimate.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The model's R² score on the test set is measured against the R² score of a linear regression baseline to confirm non-linear relationships are captured (See US-2).
- **SC-002**: The Root Mean Square Error (RMSE) is measured as a percentage of the observed range of the target property in the test set to validate prediction accuracy (See US-2).
- **SC-003**: The percentage of test samples falling into "high uncertainty" regions (σ > 2× median) is measured to assess the model's ability to identify data-sparse regimes (See US-3).
- **SC-004**: The correlation between permutation importance rankings and an independent reference ranking sourced from prior literature or separate experiments (not derived from the same training data) is measured to validate the identified predictive drivers (See US-3).
- **SC-005**: The total runtime for data preprocessing, training, and visualization is measured against the free-tier CI runner time limit to ensure compute feasibility (See US-2).
- **SC-006**: After preprocessing, verify that the resulting CSV contains no missing values and includes all required columns (laser power, scan speed, layer thickness, alloy composition, yield strength, ductility) (See US-1).
- **SC-007**: Report subgroup R² scores for each alloy type and compare to the overall R² to assess potential confounding by alloy composition (See US-2).
- **SC-008**: Demonstrate that controlling for alloy composition (and any available microstructural covariates) changes the model’s predictive performance by reporting (i) the R² and RMSE with composition covariates and (ii) the same metrics without them; the difference must be ≥ 0.02 R² or ≥ 5 % RMSE to confirm confound impact (See US-2).

## Assumptions

- The public datasets (Zenodo AM-Machine-Learning, HuggingFace Materials Project, UCI Alloy Properties) contain the specific variables required: laser power, scan speed, layer thickness, alloy composition, yield strength, and ductility.
- **Dataset-variable fit**: If the chosen dataset lacks "fatigue life" data, the analysis will be restricted to "yield strength" and "ductility" only, and this scope reduction will be documented in the final report.
- The dataset size (N ≥ 50) is sufficient for training a GPR model with an RBF kernel without overfitting on a CPU‑only environment.
- The relationships between processing parameters and mechanical properties are non-linear and continuous, justifying the use of Gaussian Process Regression over linear models.
- The "free CPU" CI runner (2 cores, ~7 GB RAM) can handle the memory footprint of a GPR model trained on 50‑500 samples with standard precision (no 8‑bit quantization or GPU acceleration required).
- All mechanical property values in the dataset are positive and physically plausible (e.g., yield strength > 0), requiring no complex outlier removal beyond standard variance checks.
- The "uncertainty" quantified by the GPR model (predictive variance) is a valid proxy for **epistemic uncertainty** (lack of training data in that region) but does **not** capture **aleatoric uncertainty** (inherent noise in the physical measurement process). In AM, mechanical properties have high intrinsic variance due to microstructural defects; the model identifies data‑sparse regimes, not necessarily regimes with high physical noise.