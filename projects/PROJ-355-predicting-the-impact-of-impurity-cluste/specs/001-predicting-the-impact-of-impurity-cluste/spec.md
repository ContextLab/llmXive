# Feature Specification: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Feature Branch**: `[001-impurity-clustering-segregation]`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Impurity Clustering on Grain Boundary Segregation"

## User Scenarios & Testing *(mandatory)*

### User Story US-1 - Data Pipeline and Clustering Descriptor Computation (Priority: P1)

The researcher MUST be able to download bulk configuration files from public repositories (Materials Project, OQMD), generate grain boundary (GB) supercell structures by inserting impurities at the interface, compute clustering descriptors (radial distribution function peaks, pair correlation statistics, Voronoi-based neighbor counts) specifically within the interface region of the GB supercell, and extract segregation energy measurements from published atomistic simulation records for each configuration.

**Why this priority**: This is the foundational data layer; without clustering descriptors and reliable segregation‑energy labels derived from existing literature, no model training is possible. All downstream analysis depends on this pipeline functioning correctly.

**Independent Test**: Can be fully tested by executing the data pipeline script on a representative sample of bulk configurations, verifying that GB supercells are constructed, impurities are inserted at the interface, descriptors are computed from the interface region, and segregation energies are successfully extracted from literature sources, with non‑empty values saved to disk.

**Acceptance Scenarios**:

1. **Given** Materials Project/OQMD datasets are accessible via `wget`/`curl`, **When** the data pipeline script is executed, **Then** bulk configurations are downloaded and stored locally within 30 minutes of wall‑clock time.
2. **Given** a bulk configuration file is loaded, **When** clustering descriptors are computed, **Then** at least 3 descriptor types (RDF peaks, pair correlations, Voronoi neighbor counts) are output with numeric values for each impurity species, computed from the GB interface region.
3. **Given** a literature database of segregation energies, **When** the extraction routine runs, **Then** segregation energy values for at least 200 configurations are retrieved and linked to their corresponding clustering descriptors.

---

### User Story US-2 - Regression Model Training and Cross‑Validation (Priority: P2)

The researcher MUST be able to train a regression model (Linear Regression *or* RandomForest) using the clustering descriptors as predictors and segregation energy as target, then perform 5‑fold cross‑validation (or LOOCV if N < 5) to report R², RMSE, and, when Linear Regression is used, coefficient p‑values.

**Why this priority**: This delivers the core predictive capability. The model quantifies the cluster‑segregation coupling relationship and enables hypothesis testing about clustering effects on segregation thermodynamics.

**Independent Test**: Can be fully tested by running the training script on a held‑out test set of samples and verifying that R², RMSE, and (when applicable) p‑values are computed and saved with valid numeric outputs.

**Acceptance Scenarios**:

1. **Given** a training dataset with at least 200 samples containing clustering descriptors and segregation energies, **When** the regression model is trained with 5‑fold cross‑validation (or LOOCV if N < 5), **Then** R², RMSE, and (for Linear Regression) coefficient p‑values are computed for each fold within 6 hours of wall‑clock time on CPU‑only hardware.
2. **Given** the trained model, **When** predictions are generated on a test set of at least 50 held‑out samples, **Then** Predicted segregation energies are output with confidence intervals reflecting a high level of confidence for each prediction.
3. **Given** multiple alloy systems are in the dataset, **When** the model is evaluated per‑system, **Then** R² values are reported for each system separately with at least 3 systems represented in the test set.

---

### User Story US-3 - Hypothesis Testing and Reporting (Priority: P3)

The researcher MUST be able to perform hypothesis testing on the regression coefficients, apply a multiple‑comparison correction (Bonferroni or FDR), and generate a concise report summarizing statistical significance, adjusted p‑values, and any changes in significance status.

**Why this priority**: This ensures methodological soundness per the Spec Kit requirements. Proper statistical inference prevents false‑positive claims about clustering‑segregation relationships.

**Independent Test**: Can be fully tested by executing the hypothesis‑testing script on the regression results and verifying that adjusted p‑values are reported, that a count of hypotheses whose significance changes after correction is provided, and that a brief textual summary is generated.

**Acceptance Scenarios**:

1. **Given** a set of regression coefficients, **When** hypothesis testing is executed, **Then** raw p‑values for each predictor are computed.
2. **Given** more than one hypothesis, **When** multiple‑comparison correction is applied, **Then** adjusted p‑values are reported and the number of predictors whose significance (α = 0.05) changes after correction is logged.
3. **Given** the corrected results, **When** the final report is generated, **Then** a JSON file listing each predictor, its raw and adjusted p‑values, and a free‑text summary of the overall statistical conclusions is produced.

---

### Edge Cases

- What happens when the atomistic simulation datasets are unavailable or rate‑limited by the public repository? The pipeline MUST implement retry logic with at most 3 failed attempts before marking the dataset as inaccessible and logging a `[DATA_UNAVAILABLE]` error.
- How does the system handle bulk configurations with zero impurity atoms (no clusters)? These cases MUST be filtered out and excluded from the regression training set with a count logged in the preprocessing report.
- What happens when clustering descriptors are collinear (e.g., cluster size and density are linearly dependent by construction)? The system MUST detect collinearity (VIF ≥ 10) **before** any dimensionality reduction and produce a JSON report (see FR‑007) listing the offending predictor groups.
- How does the system handle grain boundary structures with missing segregation‑energy data? These entries MUST be excluded from the training set with a count logged; if the exclusion rate exceeds 5 % a warning is issued.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download bulk configuration files from Materials Project and OQMD using `wget`/`curl` with at most 3 failed attempts before marking the dataset as inaccessible (See US‑1).
- **FR-002**: System MUST compute at least 3 clustering descriptor types (radial distribution function peaks, pair correlation statistics, Voronoi‑based neighbor counts) for each impurity species specifically within the interface region of the GB supercell (See US‑1).
- **FR-003**: System MUST extract segregation‑energy measurements from published atomistic simulation records for at least 200 configurations, linking each energy to its corresponding clustering descriptor set (See US‑1).
- **FR-004a**: System MUST train a Linear Regression model with 5‑fold cross‑validation (or LOOCV if N < 5) and compute coefficient p‑values for each predictor (See US‑2).
- **FR-004b**: System MUST train a RandomForest model with 5‑fold cross‑validation (or LOOCV if N < 5); p‑values are not required for this model (See US‑2).
- **FR-005**: System MUST perform multiple‑comparison correction (Bonferroni or FDR) when >1 hypothesis test is run and report adjusted p‑values (See US‑3).
- **FR-006**: *Removed* (sensitivity‑sweep over regularization strength was out of scope).
- **FR-007**: System MUST detect predictor collinearity (VIF ≥ 10) **before** any PCA or dimensionality reduction, and output a JSON report listing each predictor group with VIF ≥ 10 together with a one‑sentence descriptive summary (See US‑2).
- **FR-008**: System MUST conduct a power analysis targeting statistical power ≥ 0.80, significance level α = 0.05, and effect size f² = 0.15 (medium per Cohen, 1992). The analysis must report the required minimum sample size and confirm that the available dataset meets or exceeds this size (See US‑2).
- **FR-009**: System MUST generate a plot of cluster‑size vs. segregation‑energy with confidence intervals for each alloy system, saved as a high‑resolution PNG (See US‑3).
- **FR-010**: System MUST perform exploratory linearity assessment (scatter plots of each descriptor vs. segregation energy, residual analysis) and document whether the relationship appears linear; if non‑linear, RandomForest may be used (See US‑2).
- **FR-011**: System MUST validate EAM‑derived segregation‑energy labels against a DFT benchmark set of at least 30 samples; the mean absolute error must be ≤ 0.1 eV, justified by typical EAM‑DFT discrepancies in alloy segregation studies (≈0.08–0.12 eV) (See US‑1).
- **FR-012**: System MUST report VIF values for the original three descriptors and ensure any VIF ≥ 10 triggers the JSON collinearity report required by FR‑007 (See US‑2).

### Key Entities *(include if feature involves data)*

- **BulkConfiguration**: Represents a bulk lattice structure with impurity atoms; key attributes include impurity species, concentration, atomic coordinates, and crystal structure type.
- **GrainBoundaryStructure**: Represents a grain boundary configuration; key attributes include boundary plane orientation, misorientation angle, and associated segregation‑energy measurements.
- **ClusteringDescriptor**: Represents a computed clustering metric; key attributes include descriptor type (RDF peak, pair correlation, Voronoi count), numeric value, and associated impurity species.
- **SegregationEnergy**: Represents the thermodynamic driving force for segregation; key attributes include energy value (eV), grain boundary identifier, and impurity species.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Coefficient of determination (R²) is measured on the held‑out test set of at least 3 alloy systems; statistical significance is determined via permutation testing (See US‑2). Power analysis (FR‑008) must confirm that the sample size yields ≥ 0.80 power.
- **SC-002**: Root mean square error (RMSE) is measured on the held‑out test set predictions to quantify prediction accuracy (See US‑2).
- **SC-003**: Multiple‑comparison correction is measured by reporting adjusted p‑values and the count of hypotheses whose significance (α = 0.05) changes after correction (See US‑3).
- **SC-004**: Collinearity diagnostics (VIF scores) are measured against the threshold VIF ≥ 10; a JSON report listing all predictors exceeding this threshold must be produced (See US‑2).
- **SC-005**: The visualization of cluster‑size vs. segregation‑energy with confidence intervals is generated for each alloy system and saved as a PNG file (See US‑3).
- **SC-006**: Validation of EAM‑derived segregation energies against the DFT benchmark set yields MAE ≤ 0.1 eV (See FR‑011).

## Assumptions

- Public atomistic simulation datasets (Materials Project, OQMD) are accessible via standard HTTP/HTTPS protocols without authentication requirements for bulk structures.
- Segregation‑energy data are available in published literature or curated databases; no new GB supercell simulations are required.
- The GitHub Actions free‑tier runner (multiple CPU cores, ~7 GB RAM, ~14 GB disk, CPU‑only) is sufficient for training RandomForest or Linear Regression models on a sampled dataset of ≤ 1000 configurations.
- Segregation‑energy values extracted from literature use consistent units (eV) and reference states.
- Impurity clustering descriptors (RDF peaks, pair correlations, Voronoi counts) computed from the GB interface region are representative of the clustering behavior driving segregation.
- The 5‑fold cross‑validation (or LOOCV) procedure provides adequate statistical power for evaluating model performance on the available sample size, as confirmed by FR‑008.
- Linear regression is selected only when exploratory analysis (FR‑010) indicates an approximately linear relationship; otherwise RandomForest is employed.
- The dataset contains sufficient samples (≥ 200) with both clustering descriptors and segregation‑energy measurements to support cross‑validation and power analysis.
- VIF diagnostics are performed on the original three descriptors before any dimensionality reduction, adhering to the collinearity threshold VIF ≥ 10 (source: 2005.02245, https://arxiv.org/abs/2005.02245).
