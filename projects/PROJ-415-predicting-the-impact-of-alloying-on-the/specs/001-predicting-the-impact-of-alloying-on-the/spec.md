# Feature Specification: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Feature Branch**: `001-predict-alloy-diffusion`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Curation (Priority: P1)

A materials scientist needs to load raw diffusion datasets from public repositories (Materials Project, NIST) and filter them to ensure only valid FCC self-diffusion data points are included in the analysis.

**Why this priority**: Without a clean, validated dataset restricted to FCC structures and self-diffusion modes, any subsequent modeling is scientifically invalid. This is the foundational step that enables all other features.

**Independent Test**: Can be fully tested by running the data ingestion script against a mock dataset containing mixed crystal structures (FCC, BCC, HCP) and verifying that the output CSV contains *only* the FCC self-diffusion entries with standardized units (eV/atom, at.%).

**Acceptance Scenarios**:

1. **Given** a raw CSV containing 500 entries of mixed crystal structures and diffusion modes, **When** the ingestion script is executed, **Then** the output file contains exactly the subset of entries where `crystal_structure == "FCC"` and `diffusion_mode == "self"`, with all activation energies converted to eV/atom.
2. **Given** a dataset with missing values for solute concentration, **When** the curation step is executed, **Then** those specific rows are excluded, and a log file records the count of excluded rows with a reason code "MISSING_CONCENTRATION".

---

### User Story 2 - Feature Engineering and Model Training (Priority: P2)

A researcher needs to compute atomic descriptors (radius mismatch, electronegativity difference) for each solute and train both a Random Forest and a Gradient Boosting regressor to predict activation energy shifts. Additionally, a Linear Regression model must be trained specifically to extract and test the statistical significance of the `size_mismatch` coefficient.

**Why this priority**: This is the core analytical engine. It transforms raw atomic properties into predictive relationships. The inclusion of multiple models (RF, GB, Linear) allows for both high-accuracy prediction and interpretable statistical validation of the hypothesized geometric driver.

**Independent Test**: Can be tested by feeding a small, known dataset of FCC alloys into the feature engineering pipeline and verifying that the calculated "size mismatch" (Δr/r_host) matches manual calculations, followed by confirming that all three model types (RF, GB, Linear) train without CUDA errors and output their respective performance metrics and coefficients.

**Acceptance Scenarios**:

1. **Given** a curated dataset of 50 FCC alloys with solute atomic radii and host radii, **When** the feature engineering module runs, **Then** it generates a `size_mismatch` column where every value is calculated as `(solute_radius - host_radius) / host_radius` and the column contains no nulls.
2. **Given** the engineered dataset, **When** the Random Forest and Gradient Boosting models are trained with `max_depth` ∈ [3, 10] and `n_estimators` ∈ [50, 200] (selected via Grid Search maximizing R²), **Then** the training completes within 15 minutes on a 2-core CPU runner, and the model objects are saved to `models/final_rf.pkl` and `models/final_gb.pkl` respectively.
3. **Given** the engineered dataset, **When** the Linear Regression model is trained, **Then** it outputs a `size_mismatch` coefficient with an associated standard error and p-value, saved to `models/linear_coef.json`.

---

### User Story 3 - Statistical Validation and Threshold Sensitivity Analysis (Priority: P3)

A peer reviewer needs to verify that the model's performance is statistically significant and that any decision thresholds used (e.g., for classifying "high" vs. "low" diffusion barriers) are robust to small variations.

**Why this priority**: Scientific rigor requires proving that the results are not due to chance and that conclusions are not artifacts of arbitrary cutoff choices. This ensures the methodology is defensible.

**Independent Test**: Can be tested by executing the validation script on the held-out test set, generating a report that includes R², RMSE, and a sensitivity plot showing how the "high barrier" classification rate changes when the threshold is swept from 0.45 eV to 0.55 eV in 0.01 eV steps.

**Acceptance Scenarios**:

1. **Given** a trained Linear Regression model and a held-out test set, **When** the validation script runs, **Then** it outputs a JSON report confirming the `size_mismatch` coefficient is statistically significant (p < 0.05) with a 95% bootstrap confidence interval.
2. **Given** a default classification threshold of 0.5 eV for "significant diffusion slowing" (defined as ΔE > threshold relative to pure host), **When** the sensitivity analysis runs, **Then** it re-evaluates the classification at thresholds 0.45, 0.46, ..., 0.55 eV and reports the variation in classification stability (measured as the standard deviation of the classification rate relative to the model's RMSE), confirming stability is within ±5% across this sweep.

---

### Edge Cases

- **What happens when** the dataset contains only one host metal (e.g., only Nickel)?
  - The stratified split logic must handle this by falling back to a standard random split and logging a warning that "Stratification by host metal was not possible due to single-class data."
- **How does the system handle** solutes where the atomic radius is not available in the standard periodic table database?
  - The feature engineering step must flag these rows, exclude them from training, and append a record to `errors/missing_atomic_data.csv` with the solute symbol and the missing attribute.
- **What happens if** the random forest hyperparameter grid search results in a model with `R² < 0.1`?
  - The pipeline must not crash; it must complete, save the model, and flag the result in the final report as "Low Predictive Power - Null Result Hypothesis Supported."

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest diffusion data from specified CSV sources and filter rows to include ONLY those where `crystal_structure` is "FCC" and `diffusion_mode` is "self" (See US-1).
- **FR-002**: System MUST calculate the `size_mismatch` feature as `(solute_radius - host_radius) / host_radius` for every valid data point, using atomic radii from a standard periodic table database (See US-2).
- **FR-003**: System MUST train a Random Forest regressor AND a Gradient Boosting regressor using scikit-learn on CPU-only hardware. Hyperparameters `max_depth` (range 3–10) and `n_estimators` (range 50–200) MUST be selected via Grid Search with 5-fold cross-validation maximizing R² (See US-2).
- **FR-004**: System MUST perform 5-fold cross-validation on the training set to tune hyperparameters, AND separately compute R², RMSE, and MAE metrics on the held-out test set for both the Random Forest and Gradient Boosting models (See US-2).
- **FR-005**: System MUST train a Linear Regression model to extract the `size_mismatch` coefficient and compute its p-value and 95% bootstrap confidence interval. Additionally, the system MUST execute a sensitivity analysis sweeping the classification threshold for "significant activation energy shift" (relative to pure host) across the continuous range 0.45 eV to 0.55 eV in 0.01 eV increments, reporting the variation in classification stability (See US-3).
- **FR-006**: System MUST define the baseline for "significant activation energy shift" as the difference between the predicted activation energy of a solute and the activation energy of the pure host metal at 0 at.% solute concentration (See US-3).

### Key Entities

- **DiffusionRecord**: Represents a single data point containing host metal ID, solute ID, concentration (at.%), activation energy (eV), and crystal structure.
- **AtomicDescriptor**: Represents the computed features for a solute, including atomic radius, electronegativity, valence electron count, and calculated size mismatch.
- **ModelArtifact**: Represents the trained regression model (RF, GB, or Linear), its hyperparameters, and the associated performance metrics or coefficients.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The predictive performance (R² score) of the regression models (RF and GB) is measured against the baseline of a simple mean-predictor on the held-out test set to confirm the models add value (See US-2).
- **SC-002**: The statistical significance of the `size_mismatch` coefficient is measured against the p-value and 95% bootstrap confidence interval derived from the Linear Regression model to verify the relationship is not due to random chance (See US-3).
- **SC-003**: The stability of the "significant shift" classification is measured against the variation in classification rates across the threshold sweep {0.45, 0.46, ..., 0.55} eV to ensure robustness (See US-3).
- **SC-004**: The computational resource usage is measured against the GitHub Actions free-tier limits (≤6 hours, ≤7 GB RAM) to confirm feasibility (See US-2).

## Assumptions

- **Assumption about data availability**: Public repositories (Materials Project, NIST) contain sufficient data points (≥50) for FCC self-diffusion with known solute concentrations to support a train/test split.
- **Assumption about atomic properties**: Standard periodic table values for atomic radius and electronegativity are sufficient proxies for the electronic environment effects in FCC alloys, and no quantum-mechanical calculations are required for feature generation.
- **Assumption about linearity**: The relationship between size mismatch and activation energy shift can be adequately captured by a Random Forest regressor without requiring deep neural networks or GPU acceleration. The Linear Regression model is used solely for statistical inference of the geometric descriptor's significance, acknowledging it is a proxy for complex electronic effects.
- **Assumption about threshold justification**: A threshold of 0.5 eV is used as an arbitrary exploratory baseline for sensitivity analysis. There is no universally accepted community-standard threshold for "significant" activation energy shifts in this context; the sweep (0.45–0.55 eV) is designed to validate that conclusions are robust to this arbitrary choice rather than relying on a single fixed value.
- **Assumption about inference framing**: Since the dataset is observational (experimental/simulation data without random assignment of solutes), all conclusions regarding the relationship between alloying and diffusion will be framed as associational, not causal.
- **Assumption about ground truth**: The "ground truth" for the sensitivity analysis is defined relative to the model's own prediction stability (RMSE) rather than an external physical standard, as no universal physical threshold exists for "significant" shifts in this domain.