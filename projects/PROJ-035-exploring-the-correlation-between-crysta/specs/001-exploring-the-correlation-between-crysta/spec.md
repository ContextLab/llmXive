# Feature Specification: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Feature Branch**: `001-crystal-thermal-correlation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion & Validation (Priority: P1)

The system fetches perovskite crystal structures from the Materials Project API and merges them with experimental thermal conductivity values from curated literature datasets. It validates that every entry contains both structural data and thermal conductivity measurements before proceeding.

**Why this priority**: Without clean, merged data containing both predictors (structure) and outcomes (thermal conductivity), no analysis can occur. This is the foundational step for the entire research workflow.

**Independent Test**: Can be fully tested by running the ingestion script against a mock API response and verifying that the output CSV contains exactly the expected columns and no rows with missing thermal values.

**Acceptance Scenarios**:

1. **Given** a list of perovskite material IDs, **When** the system queries the Materials Project API, **Then** it retrieves crystal structure data and filters for ABX₃ stoichiometry.
2. **Given** a merged dataset, **When** the system checks for missing values, **Then** it removes any entry where thermal conductivity or structural descriptors are null.
3. **Given** a data source with incomplete thermal coverage, **When** the system validates the dataset, **Then** it logs a warning and reports the percentage of retained entries.

---

### User Story 2 - Descriptor Computation & Correlation (Priority: P2)

The system calculates crystallographic distortion metrics (octahedral tilting angles, bond-length variance, tolerance factor) for each entry and performs statistical correlation analysis against thermal conductivity.

**Why this priority**: This step generates the primary scientific evidence (correlations) required to answer the research question. It depends on US-1 but is independent of the regression modeling.

**Independent Test**: Can be fully tested by running the descriptor calculation on a known structure file and verifying the output metrics match expected values within 0.01 tolerance, then confirming correlation coefficients are computed.

**Acceptance Scenarios**:

1. **Given** a valid crystal structure file, **When** the system computes descriptors, **Then** it outputs numerical values for tilting angle and bond-length variance.
2. **Given** a dataset of descriptors and thermal values, **When** the system runs correlation analysis, **Then** it outputs Pearson and Spearman coefficients for each descriptor.
3. **Given** multiple hypothesis tests, **When** the system evaluates significance, **Then** it applies Benjamini-Hochberg correction for False Discovery Rate (FDR) control.

---

### User Story 3 - Regression Modeling & Reporting (Priority: P3)

The system fits a multiple linear regression model to predict thermal conductivity from structural descriptors, evaluates performance using cross-validation, and generates a report with appropriate scientific framing.

**Why this priority**: This step synthesizes the findings into a predictive model and ensures the conclusions are methodologically sound (associational, sensitivity-checked). It depends on US-2.

**Independent Test**: Can be fully tested by running the model on a held-out test set and verifying the R² score, RMSE, and that the report text explicitly avoids causal language.

**Acceptance Scenarios**:

1. **Given** a training set of descriptors and thermal values, **When** the system fits the regression model using 5-fold cross-validation and a [deferred] held-out test set, **Then** it reports R² and RMSE on the held-out test set.
2. **Given** multiple predictors, **When** the system checks for collinearity, **Then** it calculates Variance Inflation Factors (VIF) and flags any predictor with VIF > 5.
3. **Given** a significance threshold, **When** the system generates the final report, **Then** it includes a sensitivity analysis sweeping the p-value cutoff over {0.01, 0.05, 0.1}.

---

### Edge Cases

- What happens when the Materials Project API returns rate-limit errors? The system MUST implement exponential backoff with a maximum of 3 retries per request.
- How does system handle entries with missing thermal conductivity? The system MUST exclude these entries from analysis and log the count of excluded entries.
- What happens when predictor collinearity is high? The system MUST flag the model as descriptive-only and refrain from claiming independent predictive effects for correlated variables.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch perovskite structures from the Materials Project API and filter for ABX₃ stoichiometry (See US-1).
- **FR-002**: System MUST remove any dataset entries where thermal conductivity or structural descriptors are missing (See US-1).
- **FR-003**: System MUST compute octahedral tilting angles, bond-length variance, tolerance factor, and unit cell volume using pymatgen (See US-2).
- **FR-004**: System MUST apply Benjamini-Hochberg correction for multiple comparisons across all tested descriptors (See US-2).
- **FR-005**: System MUST calculate Variance Inflation Factor (VIF) for all predictors; if VIF > 5, the system MUST flag the relationship as descriptive (See US-3).
- **FR-006**: System MUST frame all findings as associational rather than causal in the final report output; prohibited terms include 'cause', 'causes', 'effect', 'determines', 'deterministic'; required terms include 'associated with', 'correlated with', 'predicts' (See US-3).
- **FR-007**: System MUST sweep the p-value significance threshold over {0.01, 0.05, 0.1} and report variation in significant feature count (See US-3).
- **FR-008**: System MUST execute all analysis on CPU-only hardware without requiring CUDA or GPU acceleration (See US-3).
- **FR-009**: System MUST generate scatter plots with 95% confidence intervals for top-correlated features (See US-3).
- **FR-010**: System MUST report a power/sample-size justification analysis for the regression model (See US-3).

### Key Entities *(include if feature involves data)*

- **PerovskiteEntry**: Represents a single material record containing material_id, crystal_structure, thermal_conductivity, and computed_descriptors.
- **AnalysisResult**: Represents the output of the correlation/regression phase containing coefficients, p_values, R², and VIF_scores.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data retention rate is measured against the total initial query count (See US-1).
- **SC-002**: Correlation significance is measured against the corrected p-value threshold (See US-2).
- **SC-003**: Model predictive performance (R²) is measured against the [deferred] performance threshold (See US-3).
- **SC-004**: Sensitivity analysis coverage is measured against the defined p-value sweep set {0.01, 0.05, 0.1} (See US-3).

## Assumptions

- The Materials Project thermal properties endpoint primarily provides DFT-calculated thermal conductivity values (not experimental measurements); data availability and coverage must be verified during implementation ([deferred]).
- The total dataset size will fit within 7 GB of RAM after filtering, avoiding the need for chunked processing.
- All structural descriptors can be computed using standard pymatgen functions without requiring external DFT calculations.
- The GitHub Actions free‑tier runner, which provides modest CPU and memory resources, is sufficient for the entire analysis pipeline within the allocated runtime limit..
- The research design is observational; therefore, causal claims are out of scope regardless of statistical significance.
- The [deferred] minimum sample size for the regression analysis will be verified against the community-standard guideline of sufficient observations per predictor (4 predictors × 10 = 40 minimum, 4 predictors × 20 = 80 recommended) to ensure statistical power.