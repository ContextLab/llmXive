# Feature Specification: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

**Feature Branch**: `[###-ductility-prediction]`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Which process parameters (laser power, scan speed, hatch spacing, energy density) most strongly influence the ductility of additively manufactured nickel-based superalloys, and what is the magnitude and direction of their effects?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Curated Dataset Acquisition (Priority: P1) *(US-1)*

A materials scientist needs a ready‑to‑use dataset that pairs laser‑based process parameters with experimentally measured ductility for a diverse set of nickel‑based superalloy builds.

**Why this priority**: Without reliable data the entire analysis pipeline cannot proceed; this is the foundation for all downstream modeling.

**Independent Test**: Execute the data‑ingestion script and verify that a CSV file with ≥ 250 rows and all required columns (laser power, scan speed, hatch spacing, layer thickness, ductility, alloy composition) is produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** the Materials Project API and the HuggingFace “additive‑manufacturing‑superalloy” collection are reachable, **when** the acquisition script runs, **then** it downloads all publicly available records, merges supplementary tables from the four cited papers, and outputs a combined dataset meeting the size and column criteria.  
2. **Given** a record missing any required field, **when** the cleaning step runs, **then** that record is excluded and a log entry reports the omission.

---

### User Story 2 – Quantify Parameter Influence via Mixed‑Effects Modeling (Priority: P2) *(US-2)*

A researcher wants to determine which process parameters most strongly affect ductility, expressed as standardized coefficients with confidence intervals, while accounting for alloy‑family random effects.

**Why this priority**: This delivers the core scientific insight required to answer the research question and guides process optimization.

**Independent Test**: Run the mixed‑effects analysis on the curated dataset and confirm that the output table contains standardized coefficients, 95 % confidence intervals, and p‑values for each fixed effect, and that the model’s partial R² ≥ 0.50.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with all predictors, **when** the linear mixed‑effects model is fit, **then** the model converges, reports standardized coefficients for laser power, scan speed, hatch spacing, and volumetric energy density, and includes a random intercept for each alloy family.  
2. **Given** multicollinearity diagnostics, **when** any predictor has a variance‑inflation factor > 5, **then** the pipeline automatically drops or combines that predictor before model fitting.

---

### User Story 3 – Deploy a Predictive Ductility Model for What‑If Exploration (Priority: P3) *(US-3)*

A practitioner wants a fast, CPU‑only predictive model that estimates ductility from process parameters, with documented performance metrics and feature‑importance rankings.

**Why this priority**: Enables rapid virtual testing of new process settings without costly experiments, directly supporting engineering decisions.

**Independent Test**: Train the XGBoost regressor on the training split, evaluate on the held‑out test split, and verify that test‑set R² ≥ 0.60 and that permutation importance highlights the same top three parameters identified by the mixed‑effects model.

**Acceptance Scenarios**:

1. **Given** the training ([deferred]) and validation ([deferred]) splits stratified by alloy family, **when** hyper‑parameter tuning via 5‑fold CV completes, **then** the best model is saved and its test‑set R² meets the target.
2. **Given** the fitted model, **when** a user supplies a new set of process parameters, **then** the system returns a ductility prediction within 0.1 % of the model’s internal prediction time (< 2 seconds on a free‑tier CI runner).

---

### Edge Cases

- What happens when the source API returns fewer than 100 build records?  
- How does the system handle a predictor whose VIF exceeds 10 after initial engineering?  
- What if the mixed‑effects model fails to converge due to singularity?  
- How are missing units (e.g., power reported in kW) resolved?  
- What if the test‑set R² falls below 0.60 after hyper‑parameter search?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST query the Materials Project API and the HuggingFace “additive‑manufacturing‑superalloy” collection, download all records containing the required variables, and merge supplementary tables from the four cited papers. *(See US-1)*
- **FR-002**: System MUST remove any entry with missing ductility or incomplete process specifications, and log each exclusion with a clear reason. *(See US-1)*
- **FR-003**: System MUST convert all raw units to SI (W, mm s⁻¹, µm, etc.) and store the cleaned data in a version‑controlled CSV file. *(See US-1)*
- **FR-004**: System MUST compute volumetric energy density \(E_v = P/(v·h·t)\) for every record and encode alloy composition as binary categorical flags for the presence of Cr, Al, Ti, etc. *(See US-1)*
- **FR-005**: System MUST calculate variance‑inflation factors for all fixed‑effect predictors and automatically drop or combine any predictor with VIF > 5, recording the action in the analysis log. *(See US-2)*
- **FR-006**: System MUST fit a linear mixed‑effects model with fixed effects for laser power, scan speed, hatch spacing, and volumetric energy density, and a random intercept for alloy family, returning standardized coefficients, 95 % confidence intervals, and p‑values. *(See US-2)*
- **FR-007**: System MUST compute the model’s partial R² and enforce a minimum threshold of 0.50; if the threshold is not met, the pipeline aborts and logs a diagnostic report. *(See US-2)*
- **FR-008**: System MUST perform a likelihood‑ratio test against a null intercept‑only model at α = 0.05 and record the test statistic and p‑value. *(See US-2)*
- **FR-009**: System MUST conduct a sensitivity analysis by repeating the mixed‑effects fit across a range of conventional significance thresholds (e.g., stringent, typical, and relaxed levels) and report how standardized coefficients and partial R² vary. *(See US-2)*
- **FR-010**: System MUST train a gradient‑boosting regressor (XGBoost) on [deferred] of the data, validate via 5‑fold CV, and test on a [deferred] hold‑out set stratified by alloy family, using CPU‑only execution. *(See US-3)*
- **FR-011**: System MUST evaluate the predictive model on the test set and require R² ≥ 0.60; if unmet, it retries hyper‑parameter search up to three additional times before aborting. *(See US-3)*
- **FR-012**: System MUST compute permutation feature importance for the final predictive model and verify that the top three features match those with the largest absolute standardized coefficients from the mixed‑effects model. *(See US-3)*
- **FR-013**: System MUST generate a final report containing (a) a table of standardized coefficients with confidence intervals, (b) partial dependence plots for the three most influential parameters, (c) predictive model metrics (R², MAE, RMSE), and (d) results of the sensitivity and VIF analyses. *(See US-2 & US-3)*

### Key Entities *(include if feature involves data)*

- **BuildRecord**: Represents a single additive‑manufacturing build; key attributes – `laser_power_W`, `scan_speed_mm_per_s`, `hatch_spacing_um`, `layer_thickness_um`, `energy_density_J_per_mm3`, `ductility_percent`, `alloy_family`, binary flags for elemental presence (e.g., `has_Cr`).  
- **MixedEffectsResult**: Stores fixed‑effect standardized coefficients, confidence intervals, p‑values, partial R², and random‑effect estimates.  
- **PredictiveModelArtifact**: Serialized XGBoost model file, hyper‑parameter settings, and performance metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The linear mixed‑effects model achieves a partial R² ≥ 0.50 and all reported fixed‑effect p‑values are evaluated at α = 0.05 (standard significance level). *(See US-2)*
- **SC-002**: The XGBoost predictive model reaches a test‑set R² ≥ 0.60, with MAE ≤ 5 % of the mean ductility and RMSE ≤ 3 % of the mean ductility. *(See US-3)*
- **SC-003**: Sensitivity analysis across α ∈ {0.01, 0.05, 0.10} shows that the ranking of the top three influential parameters does not change, and the variation in partial R² is ≤ 0.05 across thresholds. *(See US-2)*
- **SC-004**: Post‑VIF filtering yields a maximum VIF ≤ 5 for all retained predictors, confirming acceptable multicollinearity. *(See US-2)*
- **SC-005**: The final report is generated automatically, passes validation (all required sections present), and can be rendered as a PDF within 30 seconds on a free‑tier CI runner. *(See US-3)*

## Assumptions

- The Materials Project API and the HuggingFace dataset contain **all** required variables (laser power, scan speed, hatch spacing, layer thickness, ductility, and elemental composition). **[NEEDS CLARIFICATION: does the Materials Project API expose measured ductility for AM builds?]**
- Supplementary tables from the four cited papers are freely downloadable and contain compatible variable names that can be harmonized with the primary dataset.
- Alloy composition is available at the level of elemental presence/absence; detailed weight percentages are not required for the primary analysis.
- CPU‑only XGBoost (tree‑method = “hist”) will converge on ≤ 250 records within the 6‑hour CI time budget.
- Standard statistical thresholds (α = 0.05, VIF ≤ 5) are acceptable community defaults for materials‑science regression analyses.
