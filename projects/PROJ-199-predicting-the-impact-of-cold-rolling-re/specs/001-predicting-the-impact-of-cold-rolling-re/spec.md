# Feature Specification: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Feature Branch**: `001-predicting-cold-rolling-texture`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

A materials scientist needs to automatically download, filter, and standardize EBSD datasets for Aluminum, Copper, and Nickel across specific cold-rolling reductions ([deferred], [deferred], [deferred], [deferred], [deferred]) to ensure the analysis is based on high-quality, crystallographically consistent data.

**Why this priority**: Without a reliable, automated ingestion pipeline that handles low-confidence data points and symmetry re-indexing, any subsequent modeling will be built on noisy or inconsistent inputs, rendering the predictive results invalid. This is the foundational step for the entire research.

**Independent Test**: The pipeline can be tested by running the data acquisition script against the specified public repositories and verifying that the output is a tidy CSV/Parquet file containing only valid orientations with confidence indices ≥ 0.1, properly re-indexed to FCC symmetry.

**Acceptance Scenarios**:

1. **Given** the Materials Project and MTData repositories contain EBSD files for Al, Cu, and Ni, **When** the acquisition script executes, **Then** it successfully downloads files for reduction levels at [deferred], [deferred], [deferred], [deferred], and [deferred] and outputs a consolidated dataset.
2. **Given** a downloaded EBSD file contains points with a confidence index < 0.1, **When** the pre-processing step runs, **Then** those points are filtered out, and the remaining data is re-indexed to the correct FCC crystal symmetry without errors.
3. **Given** the input files are missing a specific reduction level for a specific metal (e.g., [deferred] for Nickel), **When** the script runs, **Then** it logs a warning for the missing data point but continues processing available data for other levels and metals.

### User Story 2 - Texture Quantification and Descriptor Extraction (Priority: P2)

A researcher needs to convert raw orientation data into specific, quantifiable texture descriptors (Texture Index, Volume Fractions of Brass, Copper, S, and Goss components) to enable statistical modeling of texture evolution.

**Why this priority**: Raw EBSD data is high-dimensional and not directly usable for regression. This step transforms the data into the specific scalar metrics required by the research question to establish the relationship between reduction percentage and texture.

**Independent Test**: The quantification module can be tested by processing a known benchmark dataset (e.g., from Rosenstock et al., 2018) and verifying that the calculated volume fractions and texture indices match the published values within a tolerance of ±0.05.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of orientations for a specific reduction level, **When** the quantification script runs, **Then** it calculates and outputs the Texture Index and volume fractions for Brass, Copper, S, and Goss components using the MTEX-style search algorithm.
2. **Given** the calculated volume fractions, **When** the system aggregates them, **Then** the sum of the major components plus the "random" fraction equals 1.0 ± 0.01, ensuring mass balance.
3. **Given** a benchmark dataset from Rosenstock et al. (2018) with known texture descriptors, **When** the script processes this data, **Then** the output matches the published values within ±0.05 volume fraction.

### User Story 3 - Predictive Modeling and Validation (Priority: P3)

A process engineer needs a predictive model that estimates texture descriptors based on cold-rolling reduction with high accuracy (R² ≥ 0.85) to support rapid process design decisions without new experiments.

**Why this priority**: This is the ultimate value proposition of the project. It delivers the "predictive relationship" mentioned in the motivation, allowing users to forecast material properties from processing inputs.

**Independent Test**: The model training and validation pipeline can be tested by splitting the dataset into training and test sets, training the regression/GP models, and verifying that the R² on the held-out test set meets the 0.85 threshold for all metals.

**Acceptance Scenarios**:

1. **Given** the tidy dataset of (material, reduction, texture metrics), **When** the Gaussian Process or polynomial regression model is trained with 5-fold cross-validation, **Then** the model achieves an R² ≥ 0.85 on the held-out test data for all three metals (Al, Cu, Ni) and each texture descriptor.
2. **Given** a new reduction percentage (e.g., [deferred]) not explicitly in the training set, **When** the model predicts the texture descriptors, **Then** the predicted values fall within the confidence intervals established by the cross-validation RMSE.
3. **Given** the model predictions, **When** they are compared against known qualitative trends (e.g., increasing Brass with higher reduction), **Then** the model reproduces these trends without requiring manual intervention.

### User Story 4 - Model Robustness and Extrapolation Bounds (Priority: P4)

A researcher needs to ensure that the predictive model remains stable and reliable even when data is sparse or when interpolating between reduction levels, specifically quantifying the impact of missing microstructural variables.

**Why this priority**: Texture evolution is complex and influenced by factors beyond just reduction percentage (e.g., stacking fault energy). This step validates that the model's predictions do not fluctuate wildly due to minor data gaps and explicitly quantifies the error introduced by the single-variable assumption.

**Independent Test**: The robustness module can be tested by running the sensitivity analysis on interpolation tolerance and verifying that the R² variation remains within the defined stability threshold (≤ 0.02).

**Acceptance Scenarios**:

1. **Given** a dataset with missing reduction levels (e.g., [deferred] and [deferred] missing), **When** the model predicts texture descriptors using linear interpolation, **Then** the prediction error remains within the confidence intervals established by the cross-validation RMSE.
2. **Given** the sensitivity analysis sweeping the reduction interpolation tolerance over {0.01, 0.05, 0.1}, **When** the model re-evaluates, **Then** the R² value varies by no more than 0.02 across the swept tolerances.
3. **Given** the model predictions, **When** the system calculates the residual variance, **Then** it reports the portion of variance attributable to missing microstructural variables (e.g., grain size) as a percentage of total variance.

### Edge Cases

- What happens when the EBSD data for a specific metal/reduction combination is completely missing or corrupted? The system must skip that entry, log the error, and proceed with available data rather than crashing.
- How does the system handle metals where the texture evolution does not follow the standard FCC trend (e.g., anomalous behavior in a specific alloy)? The model must flag these outliers during validation rather than forcing a fit that degrades overall R².
- What if the confidence index filtering removes >50% of the data points for a specific sample? The system must flag this sample as "low reliability" and exclude it from the final training set to prevent bias.
- What happens when the system attempts to extrapolate beyond the 0-80% reduction range? The system must explicitly flag the prediction as "extrapolated" and apply a penalty factor to the confidence interval, rather than silently returning a value.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download EBSD datasets for Al, Cu, and Ni from the Materials Project and MTData repositories covering a range of reduction levels from no reduction to significant deformation. (See US-1)
- **FR-002**: The system MUST filter out EBSD points with a confidence index < 0.1 and re-index all orientations to FCC crystal symmetry using the `orix` package. (See US-1)
- **FR-003**: The system MUST compute scalar texture metrics including the Texture Index and volume fractions of Brass, Copper, S, and Goss components for every valid sample. (See US-2)
- **FR-004**: The system MUST fit separate regression models (polynomial up to a low degree) and a joint Gaussian Process model to predict texture metrics from reduction percentage. (See US-3)
- **FR-005**: The system MUST perform k-fold cross-validation and output RMSE and R² metrics for each material and texture descriptor. (See US-3)
- **FR-006**: The system MUST explicitly frame all findings as associational relationships, avoiding causal claims unless the dataset includes randomized assignment (which is not the case here). (See US-3)
- **FR-007**: The system MUST implement a sensitivity analysis sweeping the reduction interpolation tolerance (defined as the maximum absolute difference in reduction percentage between a query point and the nearest available data point) over {0.01, 0.05, 0.1} to verify model stability, where stability is defined as an R² variation ≤ 0.02. (See US-4)
- **FR-008**: The system MUST include 'Material Type' as a categorical feature in the joint model and report the residual variance attributed to missing microstructural variables (e.g., grain size, stacking fault energy) as a percentage of total variance. (See US-4)
- **FR-009**: The system MUST flag any prediction made at reduction levels outside the lower-bound threshold as "extrapolated" and apply a confidence penalty factor of 2.0 to the standard error. (See US-4)

### Key Entities

- **EBSD Sample**: Represents a specific material specimen at a specific cold-rolling reduction, containing raw orientation data and metadata (material type, reduction %, confidence index).
- **Texture Descriptor**: A scalar value derived from an EBSD Sample, representing a specific crystallographic feature (e.g., Brass Volume Fraction, Texture Index).
- **Predictive Model**: A statistical function mapping (Material, Reduction %) to a set of Texture Descriptors, trained on the dataset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The data acquisition pipeline MUST successfully retrieve and process at least 90% of the available EBSD files across the three metals and five reduction levels, measured against the total available files in the source repositories. (See US-1)
- **SC-002**: The extracted texture descriptors MUST match the benchmark dataset (Rosenstock et al., 2018) within ±0.05 volume fraction for Brass, Copper, S, and Goss components, measured against the published values. (See US-2)
- **SC-003**: The predictive model MUST achieve an R² ≥ 0.85 on held-out test data for each of the three FCC metals (Al, Cu, Ni) and each texture descriptor, measured against the 5-fold cross-validation results. (See US-3)
- **SC-004**: The sensitivity analysis MUST demonstrate that the model's R² value varies by no more than 0.02 when the interpolation tolerance is swept over {0.01, 0.05, 0.1}, measured against the stability threshold. (See US-4)

## Assumptions

- The Materials Project and MTData repositories contain sufficient EBSD data for Al, Cu, and Ni across the full 0-80% reduction range; if data is missing for a specific point, the model will interpolate or exclude that specific point rather than halting.
- The `orix` Python package and its dependencies can be installed and executed within the GitHub Actions free-tier runner constraints (2 CPU, ~7 GB RAM) without exceeding the 6-hour time limit.
- The crystallographic symmetry for all samples is strictly FCC; any samples with mixed phases or non-FCC structures will be excluded from the analysis.
- The "cold-rolling reduction" percentage provided in the metadata is accurate and corresponds to the true plastic strain applied; no independent verification of the reduction percentage is performed.
- The Gaussian Process regression model, when applied to the sampled dataset, will not require GPU acceleration and will converge within the CPU time limits.
- The dataset variable "reduction percentage" is sufficient to predict texture evolution without needing additional microstructural variables (e.g., grain size, dislocation density) which are not available in the source data; any missing physical mechanisms are treated as unobserved confounders, and the model explicitly quantifies the residual variance attributed to these factors (see FR-008).
- The "Brass", "Copper", "S", and "Goss" components are defined using standard MTEX-style orientation ranges, and the search algorithm in `orix` correctly identifies these components without manual tuning.
- The "Material Type" feature acts as a sufficient proxy for differences in stacking fault energy (SFE) between Al, Cu, and Ni to allow the joint model to generalize across metals.