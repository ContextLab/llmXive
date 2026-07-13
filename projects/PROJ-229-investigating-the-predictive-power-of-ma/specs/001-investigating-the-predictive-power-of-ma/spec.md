# Feature Specification: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Feature Branch**: `001-phase-change-predictive-power`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials"

## User Scenarios & Testing

### User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1)

A researcher needs to download a curated subset of the Materials Project dataset containing compounds with melting points and heat capacity data, then compute elemental and structural descriptors (atomic number, electronegativity, radius, and crystal graph representations) to prepare a dataset for model training.

**Why this priority**: Without a clean, feature-rich dataset, no modeling or analysis can occur. This is the foundational data engineering step required for all subsequent machine learning tasks.

**Independent Test**: Can be fully tested by executing the data retrieval script and verifying that the output CSV contains at least 5,000 compounds with non-null values for melting point, latent heat (where available), and the computed feature columns, all fitting within the 7 GB RAM constraint.

**Acceptance Scenarios**:

1. **Given** the Materials Project API credentials and a valid query for phase-change relevant compounds, **When** the data retrieval script runs, **Then** a local dataset is generated with ≥ 5,000 rows and ≤ 7 GB memory footprint.
2. **Given** the raw crystal structures, **When** the feature extraction module runs, **Then** the output includes both elemental descriptors and graph-based representations without memory errors on a standard multi-core CPU.
3. **Given** the requirement for NIST latent heat data, **When** the data integration step runs, **Then** the system reports the imputation rate and validates the proxy correlation against the NIST subset. If the NIST overlap is < 500 compounds, the system falls back to using melting point and heat capacity as primary predictors and flags the limitation.

---

### User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

A researcher needs to train Random Forest and Gradient Boosting baselines alongside interpretable models (SHAP-analyzed trees and symbolic regression via PySR) to predict phase-change suitability, ensuring all training completes on CPU within a feasible time limit.

**Why this priority**: This delivers the core analytical capability. The distinction between black-box baselines and interpretable models is central to the research question of identifying governing factors.

**Independent Test**: Can be fully tested by running the training pipeline and verifying that models achieve an R² > 0.0 on the validation set and that the symbolic regression process terminates within 4 hours on the free-tier runner.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the baseline models (Random Forest, Gradient Boosting) train, **Then** they complete within 2 hours and output an R² score and feature importance ranking.
2. **Given** the validation set, **When** the symbolic regression model (PySR) runs, **Then** it outputs at least one explicit mathematical formula within a fixed computational time budget.
3. **Given** the trained tree ensemble, **When** SHAP analysis is performed, **Then** a ranked list of feature importances is generated without requiring GPU acceleration.

---

### User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

A researcher needs to validate the derived symbolic rules against a held-out set of known PCMs from literature and perform a sensitivity analysis on any decision thresholds (e.g., correlation cutoffs) to ensure robustness.

**Why this priority**: This confirms the scientific validity of the findings and addresses the methodological requirement for sensitivity analysis, distinguishing genuine physical insights from dataset artifacts.

**Independent Test**: Can be fully tested by applying the derived rules to the external validation set and verifying that the performance drop is ≤ 10% compared to the test set, and that the sensitivity analysis report is generated.

**Acceptance Scenarios**:

1. **Given** the symbolic rules derived from the training set, **When** applied to an external set of literature PCMs ranked by measured latent heat, **Then** the rules correctly rank ≥ 60% of the top [deferred] highest-heat PCMs.
2. **Given** a specific feature importance threshold used to select "governing factors," **When** the sensitivity analysis sweeps the threshold over a range of low values, **Then** a report is generated showing the variation in false-positive/false-negative rates.
3. **Given** the correlation analysis results, **When** the predictor collinearity diagnostic runs, **Then** any definitional dependencies (e.g., atomic radius vs. ionic radius, coordination number vs. bond density) are flagged and the interpretation is adjusted to be descriptive rather than causal.

### Edge Cases

- What happens when the The Materials Project API returns a limited subset of compounds with complete melting point and latent heat data.? (System must switch to a fallback strategy or raise a critical error).
- How does the system handle compounds with undefined crystal structures or missing elemental properties in the graph representation? (System must impute or exclude with a log).
- What happens if the symbolic regression fails to converge to a formula with R² > 0.0 within the time limit? (System must default to the SHAP analysis results and flag the limitation).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve and parse Materials Project data for compounds with documented melting points and heat capacity, ensuring the dataset fits within 7 GB RAM (See US-1).
- **FR-002**: System MUST compute two distinct feature sets: (1) elemental descriptors (atomic number, electronegativity, radius) and (2) crystal graph representations using pymatgen's StructureGraph module (See US-1).
- **FR-003**: System MUST train baseline black-box models (Random Forest, Gradient Boosting) and interpretable models (SHAP-analyzed trees, PySR symbolic regression) within a 6-hour CPU-only execution window (See US-2).
- **FR-004**: System MUST perform a sensitivity analysis on any decision thresholds (e.g., feature importance cutoffs) by sweeping values over a range of small magnitudes and reporting the variation in consistency rates (See US-3).
- **FR-005**: System MUST validate derived symbolic rules against an independent set of known PCMs from literature to ensure generalization beyond the training distribution (See US-3).
- **FR-006**: System MUST flag and adjust interpretation for any predictor collinearity where one variable is definitionally derived from another (e.g., atomic radius vs. ionic radius, coordination number vs. bond density), framing joint relationships descriptively (See US-3).
- **FR-007**: System MUST output explicit mathematical formulas or ranked feature lists that differ significantly from opaque deep learning weights, framing findings as associational due to the observational nature of the data (See US-2).

### Key Entities

- **MaterialCompound**: Represents a chemical compound with attributes for elemental composition, crystal structure, melting point, and latent heat.
- **DescriptorSet**: A collection of computed features including elemental properties (atomic number, radius) and structural representations (graph adjacency, symmetry).
- **ModelResult**: Contains the trained model parameters, performance metrics (R², accuracy), and derived rules or feature rankings.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The correlation between identified structural features and phase-change suitability is measured against the Pearson correlation coefficient (value [deferred]) (See US-2).
- **SC-002**: The predictive power of interpretable models is measured against the R² performance of the black-box baselines using a paired t-test, with success defined as |R²_interpretable - R²_baseline| ≤ 0.05 (See US-2).
- **SC-003**: The generalization capability of derived rules is measured against the ranking accuracy on an independent set of literature PCMs, with success defined as ≥ 60% accuracy on the top [deferred] (See US-3).
- **SC-004**: The robustness of decision thresholds is measured against the variation in false-positive rates across the sensitivity sweep (See US-3).
- **SC-005**: The computational feasibility is measured against a defined time limit and memory constraint on a multi-core CPU runner (See US-2).

## Assumptions

- The Materials Project API provides sufficient access to download the required subset of compounds with melting point and heat capacity data without hitting rate limits that exceed the 6-hour job window.
- The NIST PCM dataset contains latent heat values for a significant overlap with the Materials Project compounds; if not, the project will proceed with a proxy metric or a reduced dataset.
- The PySR library can be installed and run efficiently on the GitHub Actions free-tier environment without requiring proprietary dependencies or GPU acceleration.
- The "governing factors" identified are primarily structural and compositional; kinetic factors or synthesis conditions are assumed to be secondary or out of scope for this specific analysis.
- The 50 known PCMs from literature can be mapped to the Materials Project database IDs or have equivalent structural data available for validation.
- The observational nature of the dataset precludes causal claims; all findings will be framed as associational relationships.
- Latent heat of fusion is not a deterministic function of melting point alone; any imputation strategy introduces noise, and the identified 'governing factors' may be confounded by the imputation model. This bias will be assessed via the sensitivity analysis (FR-004).
- The validation of the imputation model uses a disjoint set (NIST) from the training set (Materials Project) to ensure independence and avoid circular validation.