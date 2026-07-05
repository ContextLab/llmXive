# Feature Specification: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

**Feature Branch**: `001-predicting-oxidation-resistance`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Alloying on High-Temperature Oxidation Resistance"

## User Scenarios & Testing

### User Story 1 - Composition-Only Predictive Screening (Priority: P1)

A materials scientist uploads a list of candidate nickel-based superalloy compositions and receives an immediate prediction of their high-temperature oxidation weight gain (in mg/cm²) based solely on elemental composition and derived thermodynamic descriptors.

**Why this priority**: This is the core value proposition: accelerating the initial screening phase by filtering out poor candidates before expensive physical testing. It directly addresses the "bottleneck in alloy development" mentioned in the motivation.

**Independent Test**: This can be fully tested by providing a CSV of 10 known alloy compositions (excluding microstructural data) and verifying that the system outputs a numerical prediction with a confidence interval, without requiring any microstructural input files.

**Acceptance Scenarios**:

1. **Given** a CSV file containing 50 alloy rows with columns for Ni, Cr, Al, Co, Ti (wt%) and no microstructural data, **When** the user uploads the file and runs the "Composition-Only Prediction" pipeline, **Then** the system outputs a CSV with an additional column `predicted_weight_gain` and `prediction_uncertainty` for every row.
2. **Given** a single alloy composition with [deferred] Aluminum (a known failure case for alumina scale formation), **When** the model predicts, **Then** the predicted weight gain value is within the top [deferred] of the training distribution (indicating high oxidation), consistent with known materials science principles.
3. **Given** a dataset of 500 samples, **When** the 5-fold cross-validation completes, **Then** the system reports an R² score ≥ 0.5 and RMSE ≤ 15 mg/cm² (based on the idea's expected results).

---

### User Story 2 - Microstructural Gap Quantification (Priority: P2)

A researcher identifies specific alloys where the composition-only model fails by comparing the model's error against a subset of samples that include microstructural annotations (grain size, precipitate volume fraction).

**Why this priority**: This addresses the specific research gap: quantifying *where* and *why* composition-only models fail. It transforms a standard prediction task into a scientific inquiry about the limits of compositional data.

**Independent Test**: This can be tested by running the "Gap Analysis" mode on a dataset containing a mix of "composition-only" and "composition+microstructure" samples, verifying that the system calculates the error reduction (ΔRMSE) specifically for the annotated subset.

**Acceptance Scenarios**:

1. **Given** a dataset where [deferred] of samples have `grain_size` and `precipitate_fraction` columns populated, **When** the "Gap Analysis" is executed, **Then** the system outputs a report comparing `RMSE_composition_only` vs `RMSE_composition_plus_microstructure`, highlighting the error reduction percentage.
2. **Given** an alloy with a known fine grain size but average composition, **When** the model predicts, **Then** the residual error (Actual - Predicted) for this specific sample is flagged as "High Microstructural Sensitivity" if the error exceeds 2x the global median absolute error.
3. **Given** the results of the gap analysis, **When** the user requests a summary, **Then** the system identifies the top 3 alloys with the largest prediction residuals and lists their specific microstructural annotations.

---

### User Story 3 - Interpretability and Feature Importance (Priority: P3)

A domain expert reviews the model's decision logic to understand which elemental or thermodynamic factors (e.g., Aluminum content, oxide formation enthalpy) drive the oxidation predictions, ensuring the model aligns with known physical mechanisms.

**Why this priority**: In materials science, "black box" predictions are often rejected. Interpretability builds trust and validates that the model is learning physical relationships (e.g., Alumina scale formation) rather than spurious correlations.

**Independent Test**: This can be tested by generating SHAP summary plots and feature importance tables, verifying that Chromium and Aluminum are ranked as the top positive/negative predictors consistent with the literature.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** the "Generate Interpretability Report" function is called, **Then** the system outputs a SHAP summary plot and a table of top 10 features with their mean absolute SHAP values.
2. **Given** the feature importance table, **When** the user reviews the top predictors, **Then** "Aluminum (wt%)" and "Oxide Formation Enthalpy (Al)" appear in the top 3 most influential features.
3. **Given** a specific prediction for a high-chromium alloy, **When** the user requests a local explanation, **Then** the system provides a waterfall plot showing how the high Chromium content specifically reduced the predicted weight gain compared to the baseline.

### Edge Cases

- **Missing Elements**: What happens when an alloy contains an element not in the training set (e.g., a trace rare earth)? The system must flag the row with a `[NEEDS CLARIFICATION: unknown element detected]` warning and exclude it from the prediction or impute using a periodic table average with a high uncertainty flag.
- **Zero Variance**: How does the system handle a dataset where a key element (e.g., Aluminum) is constant across all samples? The system must detect zero-variance features, exclude them from the model, and log a warning to prevent division-by-zero errors in thermodynamic calculations.
- **Data Scarcity**: What happens if the public dataset contains fewer than 50 samples with microstructural annotations? The system must still run the composition-only model but report the gap analysis as "Inconclusive due to insufficient microstructural data (< 50 samples)" rather than failing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse tabular alloy data from the NIST Materials Data Repository and Zenodo, filtering for entries containing Nickel, Chromium, and Aluminum weight percentages and oxidation weight gain measurements (See US-1).
- **FR-002**: System MUST calculate thermodynamic descriptors (oxide formation enthalpies) for the primary alloying elements using a CPU-efficient lookup table or simplified calculation, ensuring no external GPU-dependent libraries are invoked (See US-1).
- **FR-003**: System MUST train at least three distinct regression models (Random Forest, Gradient Boosting, Gaussian Process) using `scikit-learn` with 5-fold cross-validation to select the best-performing model for composition-only prediction (See US-1).
- **FR-004**: System MUST perform a comparative error analysis between the composition-only model and a model augmented with microstructural features (grain size, precipitate fraction) for any samples where these annotations exist (See US-2).
- **FR-005**: System MUST generate SHAP (SHapley Additive exPlanations) plots and feature importance tables to identify the contribution of each elemental and thermodynamic descriptor to the predicted oxidation weight gain (See US-3).
- **FR-006**: System MUST enforce a hard memory limit of 7 GB and a runtime limit of 6 hours, automatically downsampling the dataset to ≤500 rows if the initial fetch exceeds this threshold (See Assumptions).
- **FR-007**: System MUST explicitly frame all reported correlations as associational and not causal, unless the input data explicitly includes randomized experimental conditions (See Methodological Soundness).

### Key Entities

- **AlloySample**: Represents a single material entry; attributes include `elemental_composition` (dict), `thermodynamic_descriptors` (dict), `microstructural_features` (optional dict), and `observed_weight_gain` (float).
- **PredictionResult**: Represents the output of a model run; attributes include `predicted_weight_gain` (float), `confidence_interval` (tuple), `model_type` (string), and `feature_contributions` (dict).
- **GapAnalysisReport**: Represents the comparative study; attributes include `composition_only_rmse` (float), `augmented_rmse` (float), `error_reduction_pct` (float), and `sensitive_samples` (list of IDs).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive accuracy (R²) of the composition-only model is measured against the baseline of random guessing and the expected range of 0.5–0.7 derived from the literature review (See US-1).
- **SC-002**: The reduction in prediction error (RMSE) when adding microstructural features is measured against the composition-only baseline to quantify the "microstructural effect gap" (See US-2).
- **SC-003**: The top predictive features identified by SHAP analysis are measured against established materials science principles (specifically the dominance of Al and Cr for scale formation) to validate physical consistency (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of running end-to-end on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM) within 6 hours (See FR-006).
- **SC-005**: The validity of the dataset is measured by confirming that all required predictor variables (composition, thermodynamics) are present in the source data, or explicitly flagging `[NEEDS CLARIFICATION]` if missing (See Methodological Soundness).

## Assumptions

- **Dataset Availability**: We assume the NIST Materials Data Repository and Zenodo contain at least 300–500 entries with explicit elemental weight percentages and corresponding high-temperature oxidation weight gain measurements. If fewer than 100 samples are found, the statistical power will be insufficient to detect microstructural effects, and the project scope will be limited to composition-only correlation.
- **Thermodynamic Data**: We assume that oxide formation enthalpies for the relevant elements (Ni, Cr, Al, Co, Ti) can be approximated using standard reference values (e.g., NIST-JANAF or Materials Project) without requiring real-time, GPU-accelerated quantum chemistry calculations.
- **Linearity of Microstructural Effects**: We assume that the impact of microstructural features (grain size, precipitates) on oxidation weight gain can be captured by standard tree-based or Gaussian process regressors without requiring deep learning architectures or complex physics-informed neural networks.
- **No GPU Dependency**: We assume that `scikit-learn` and `SHAP` libraries can perform all necessary computations (including cross-validation and feature importance) on CPU-only hardware within the 6-hour limit, provided the dataset is capped at 500 samples.
- **Associational Framing**: We assume that the public datasets provided are observational (non-randomized), and therefore all model outputs will be framed strictly as associational predictions rather than causal claims of elemental influence.
- **Threshold Justification**: We assume that the decision to cap the dataset at 500 samples is a defensible standard for CPU-only feasibility on free-tier runners, and that a sensitivity analysis will sweep this cap (e.g., 200, 500, 1000) to verify stability, as required by the methodological soundness guidelines.
