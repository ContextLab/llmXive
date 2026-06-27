# Feature Specification: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Feature Branch**: `[001-impurity-clustering-segregation]`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Impurity Clustering on Grain Boundary Segregation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Pipeline and Clustering Descriptor Computation (Priority: P1)

The researcher MUST be able to download atomistic simulation datasets from public repositories (Materials Project, OQMD), extract bulk configurations with impurity concentrations and grain boundary structures, and compute clustering descriptors (radial distribution function peaks, pair correlation statistics, Voronoi-based neighbor counts) for impurity species.

**Why this priority**: This is the foundational data layer; without clustering descriptors and segregation energy labels, no model training is possible. All downstream analysis depends on this pipeline functioning correctly.

**Independent Test**: Can be fully tested by executing the data pipeline script on a representative sample of bulk configurations and verifying that clustering descriptors (RDF peak positions, coordination numbers) are computed and saved to disk with non-empty values.

**Acceptance Scenarios**:

1. **Given** Materials Project/OQMD datasets are accessible via `wget`/`curl`, **When** the data pipeline script is executed, **Then** bulk configurations with impurity concentrations are downloaded and stored locally within 30 minutes of wall-clock time
2. **Given** a bulk configuration file is loaded, **When** clustering descriptors are computed, **Then** at least 3 descriptor types (RDF peaks, pair correlations, Voronoi neighbor counts) are output with numeric values for each impurity species
3. **Given** a grain boundary structure file is available, **When** segregation energy data is extracted from supplementary databases, **Then** at least 50 segregation energy measurements are collected with associated cluster metadata

---

### User Story 2 - Regression Model Training and Cross-Validation (Priority: P2)

The researcher MUST be able to train a lightweight regression model (RandomForest or linear regression) using cluster descriptors as predictors and segregation energy as target, then perform 5-fold cross-validation to report R², RMSE, and coefficient p-values.

**Why this priority**: This delivers the core predictive capability. The model quantifies the cluster-segregation coupling relationship and enables hypothesis testing about clustering effects on segregation thermodynamics.

**Independent Test**: Can be fully tested by running the training script on a held-out test set of samples and verifying that R², RMSE, and p-values are computed and saved with valid numeric outputs.

**Acceptance Scenarios**:

1. **Given** a training dataset with ≥100 samples containing clustering descriptors and segregation energies, **When** the regression model is trained with 5-fold cross-validation, **Then** R², RMSE, and coefficient p-values are computed for each fold within 6 hours of wall-clock time on CPU-only hardware
2. **Given** the trained model, **When** predictions are generated on a test set of ≥20 held-out samples, **Then** predicted segregation energies are output with confidence intervals (95%) for each prediction
3. **Given** multiple alloy systems are in the dataset, **When** the model is evaluated per-system, **Then** R² values are reported for each system separately with ≥2 systems in the test set

---

### User Story 3 - Threshold Sensitivity Analysis and Validation Reporting (Priority: P3)

The researcher MUST be able to perform a sensitivity analysis on any decision thresholds (e.g., cluster size cutoffs, correlation significance levels) by sweeping over a concrete set of values and report how false-positive/false-negative rates or inconsistency rates vary across the sweep.

**Why this priority**: This ensures methodological soundness per the Spec Kit requirements. Without threshold sensitivity analysis, any cutoff-based conclusions would be rejected by the methodology panel.

**Independent Test**: Can be fully tested by executing the sensitivity analysis script on a sample of predictions and verifying that at least 3 threshold values are swept and corresponding rate changes are logged.

**Acceptance Scenarios**:

1. **Given** a decision threshold (e.g., cluster size ≥ N atoms), **When** the sensitivity analysis is executed, **Then** at least 3 threshold values from the set {0.01, 0.05, 0.1} or equivalent concrete values are swept and corresponding false-positive/false-negative rates are reported
2. **Given** multiple hypothesis tests are performed (e.g., testing each predictor coefficient), **When** the analysis completes, **Then** multiple-comparison correction (e.g., Bonferroni or FDR) is applied and adjusted p-values are reported
3. **Given** the full analysis pipeline, **When** validation on held-out alloy systems is performed, **Then** at least 2 alloy systems from the test set are validated and R² ≥ 0.5 is achieved or null results are documented with p-values

---

### Edge Cases

- What happens when the atomistic simulation datasets are unavailable or rate-limited by the public repository? The pipeline MUST implement retry logic with at most 3 failed attempts before marking the dataset as inaccessible and logging a `[DATA_UNAVAILABLE]` error
- How does the system handle bulk configurations with zero impurity atoms (no clusters)? These cases MUST be filtered out and excluded from the regression training set with a count logged in the preprocessing report
- What happens when clustering descriptors are collinear (e.g., cluster size and density are definitionally related)? The system MUST detect collinearity (VIF ≥ 10) and report joint relationships descriptively rather than claiming independent predictive effects
- How does the system handle grain boundary structures with missing segregation energy data? These entries MUST be excluded from the training set with a count logged, and the exclusion rate MUST be ≤15% of total samples to maintain statistical power

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download bulk configuration files and grain boundary structure files from Materials Project and OQMD using `wget`/`curl` with at most 3 failed attempts before marking the dataset as inaccessible (See US-1)
- **FR-002**: System MUST compute at least 3 clustering descriptor types (radial distribution function peaks, pair correlation statistics, Voronoi-based neighbor counts) for each impurity species in the bulk configuration (See US-1)
- **FR-003**: System MUST extract at least 50 segregation energy measurements from published simulation records and supplementary databases with associated cluster metadata (See US-1)
- **FR-004**: System MUST train a lightweight regression model (RandomForest or linear regression) with 5-fold cross-validation and compute R², RMSE, and coefficient p-values for each fold (See US-2)
- **FR-005**: System MUST perform multiple-comparison correction (e.g., Bonferroni or FDR) when >1 hypothesis test is run and report adjusted p-values (See US-3)
- **FR-006**: System MUST perform a threshold sensitivity analysis sweeping over at least 3 concrete values (e.g., {0.01, 0.05, 0.1}) and report how false-positive/false-negative rates vary across the sweep (See US-3)
- **FR-007**: System MUST detect predictor collinearity (VIF ≥ 10) and frame joint relationships descriptively rather than claiming independent predictive effects for definitionally-related predictors (See US-2)

### Key Entities *(include if feature involves data)*

- **BulkConfiguration**: Represents a bulk lattice structure with impurity atoms; key attributes include impurity species, concentration, atomic coordinates, and crystal structure type
- **GrainBoundaryStructure**: Represents a grain boundary configuration; key attributes include boundary plane orientation, misorientation angle, and associated segregation energy measurements
- **ClusteringDescriptor**: Represents a computed clustering metric; key attributes include descriptor type (RDF peak, pair correlation, Voronoi count), numeric value, and associated impurity species
- **SegregationEnergy**: Represents the thermodynamic driving force for segregation; key attributes include energy value (eV), grain boundary identifier, and impurity species

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Coefficient of determination (R²) is measured against the test set of ≥2 held-out alloy systems to quantify predictive utility (See US-2)
- **SC-002**: Root mean square error (RMSE) is measured against the held-out test set predictions to quantify prediction accuracy (See US-2)
- **SC-003**: False-positive/false-negative rates are measured across at least 3 threshold values from the sensitivity analysis sweep to quantify threshold robustness (See US-3)
- **SC-004**: Multiple-comparison correction is measured against the unadjusted p-values to quantify family-wise error rate control (See US-3)
- **SC-005**: Collinearity diagnostics (VIF scores) are measured against the threshold VIF ≥ 10 to quantify predictor independence (See US-2)

---

## Assumptions

- Public atomistic simulation datasets (Materials Project, OQMD, supplementary data from arXiv/NCBI papers) are accessible via standard HTTP/HTTPS protocols without authentication requirements
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, CPU-only) is sufficient for training RandomForest or linear regression models on a sampled dataset of ≤1000 configurations
- Segregation energy data from published atomistic simulation records uses consistent units (eV) and reference states across all sources
- Impurity clustering descriptors (RDF peaks, pair correlations, Voronoi counts) computed from bulk configurations are representative of the clustering behavior at the grain boundary interface
- The 5-fold cross-validation procedure provides adequate statistical power for evaluating model performance on the available sample size
- RandomForest or linear regression methods are appropriate for capturing the cluster-segregation relationship without requiring deep learning architectures or GPU acceleration
- The dataset contains sufficient samples (≥100) with both clustering descriptors and segregation energy measurements to support 5-fold cross-validation with ≥20 samples per fold
