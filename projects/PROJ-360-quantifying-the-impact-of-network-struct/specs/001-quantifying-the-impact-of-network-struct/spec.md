# Feature Specification: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

**Feature Branch**: `001-network-structure-thermal-conductivity`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How does the topological structure of atomic networks in crystalline solids correlate with their thermal conductivity? Specifically, do network metrics such as node degree, path length, and clustering coefficient predict thermal transport efficiency across different crystal structures?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Construct Atomic Networks from Materials Project (Priority: P1)

The researcher downloads crystallographic data (CIF files) for ≥50 materials from Materials Project and constructs atomic networks where nodes represent atoms and edges represent bonds defined by covalent radii (with fallback distance cutoffs).

**Why this priority**: This is the foundational data pipeline. Without successfully downloading crystallographic data and constructing atomic networks, no subsequent analysis can proceed. This represents the minimum viable research step.

**Independent Test**: Can be fully tested by verifying that ≥50 CIF files are downloaded and parsed, and that corresponding atomic network graphs are constructed with ≥2 nodes and ≥1 edge per material (or explicitly skipped with a log entry), delivering a validated network dataset.

**Acceptance Scenarios**:

1. **Given** Materials Project API access is available, **When** the download script queries for materials with known thermal conductivity values, **Then** ≥50 CIF files are successfully downloaded and stored in `data/raw/cif/` within A fixed time interval.
2. **Given** CIF files exist in `data/raw/cif/`, **When** the network construction script processes each file using covalent-radius-based bond detection (sum of radii + a small tolerance), **Then** ≥50 atomic network graphs are created in `data/processed/networks/` with node counts matching atom counts in the original crystals.
3. **Given** a network graph exists, **When** the system validates graph structure, **Then** each graph has ≥2 nodes, ≥1 edge, or is explicitly skipped with a log entry if no bonds are found after fallback attempts (4.0 Å, 4.5 Å).

---

### User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

The researcher computes network metrics (node degree distribution, average shortest path length on the largest connected component, clustering coefficient) and performs correlation analysis with thermal conductivity values (scalarized as the mean of principal components).

**Why this priority**: This delivers the core scientific analysis. Without correlation analysis, the research question remains unanswered. This depends on successful network construction from P1.

**Independent Test**: Can be fully tested by verifying that ≥3 independent network metrics are computed for each material and that correlation coefficients (Pearson and Spearman) are calculated between each metric and thermal conductivity, delivering quantified relationships.

**Acceptance Scenarios**:

1. **Given** ≥50 atomic network graphs exist, **When** the metrics computation script runs, **Then** ≥3 metrics (average degree, average path length on LCC, clustering coefficient) are computed for each material and stored in `data/processed/metrics.csv`. Network density is computed as a derived diagnostic only.
2. **Given** network metrics and thermal conductivity values exist, **When** correlation analysis runs, **Then** Pearson and Spearman correlation coefficients with p-values are computed for all 3 metric-conductivity pairs and stored in `results/correlations.json`.
3. **Given** multiple hypothesis tests are performed, **When** statistical significance is evaluated, **Then** Bonferroni-corrected p-values are computed to control family-wise error rate at α ≤ 0.05 across all 3 correlation tests.

---

### User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

The researcher trains a linear regression model using network metrics as features (after VIF-based collinearity filtering) to predict thermal conductivity and evaluates performance using -fold cross-validation.

**Why this priority**: This extends the analysis beyond simple correlations to predictive modeling, providing additional validation of the relationship. This is valuable but secondary to establishing the correlations themselves.

**Independent Test**: Can be fully tested by verifying that a regression model is trained, K-fold cross-validation is performed, and R² and RMSE metrics are computed on held-out test folds, delivering validated predictive performance estimates.

**Acceptance Scenarios**:

1. **Given** network metrics and thermal conductivity values exist, **When** the regression model trains, **Then** a linear regression model with features filtered by VIF < 5 is created and stored in `models/thermal_predictor.pkl`.
2. **Given** a trained model exists, **When** k-fold cross-validation

The specific value to remove/generalize: 'k'

Rewritten passage:
k-fold cross-validation runs on CPU-only hardware, **Then** R² and RMSE metrics are computed for each fold and aggregated (mean ± standard deviation) in `results/model_performance.json`.
3. **Given** cross-validation results exist, **When** model performance is evaluated, **Then** the mean R² is computed and documented regardless of value, with a specific interpretation provided for values < 0.30 (e.g., "weak predictive power, consistent with null hypothesis").

---

### Edge Cases

- **API Rate Limiting**: If the Materials Project API returns a 429 or 503 error, the system MUST retry up to 3 times with exponential backoff (1s, 2s, 4s). If all retries fail, the material is skipped and logged with the error code.
- **Missing Thermal Conductivity**: If a CIF file lacks a thermal conductivity value in the metadata, the material is skipped and logged.
- **Isolated Atoms (No Bonds)**: If no bonds are found within the covalent-radius tolerance, the system attempts a fallback distance cutoff at progressively larger distances. If still no edges exist, the material is skipped and logged as "Disconnected/No Bonds".
- **Identical Metrics**: Materials with identical network metrics but different thermal conductivity are retained; the regression model will treat them as noise or unexplained variance.
- **Small Dataset**: If A subset of materials remains after filtering, the system proceeds with n < 50 but logs a warning in `results/power_analysis.log` and adjusts the Bonferroni correction accordingly.
- **Disconnection**: If a graph is fully disconnected (no edges), the average shortest path length is reported as NaN.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download ≥50 CIF files from Materials Project API for materials with documented thermal conductivity values within 30 minutes. If the API is rate-limited or unavailable, the system MUST retry up to 3 times with exponential backoff (1s, 2s, 4s) before skipping the material and logging the failure (See US-1)
- **FR-002**: System MUST construct atomic network graphs where nodes represent atoms and edges represent bonds defined by the sum of covalent radii of the atom pair plus a small tolerance. If no bonds are found, the system MUST attempt fallback distance cutoffs of increasing magnitude sequentially. If no edges are found after fallbacks, the material MUST be skipped and logged (See US-1)
- **FR-003**: System MUST compute ≥3 independent network metrics (average degree, average shortest path length on the largest connected component, clustering coefficient) for each atomic network. If a graph is fully disconnected, average shortest path length MUST be reported as NaN. Network density is computed as a derived diagnostic only (See US-2)
- **FR-004**: System MUST perform Pearson and Spearman correlation analysis between each network metric and thermal conductivity. Thermal conductivity MUST be scalarized as the arithmetic mean of the principal components (k_x, k_y, k_z) of the thermal conductivity tensor. P-values MUST be computed for all tests (See US-2)
- **FR-005**: System MUST apply Bonferroni correction for multiple-comparison adjustment across all correlation tests to control family-wise error rate at α ≤ 0.05 (See US-2)
- **FR-006**: System MUST train a linear regression model using network metrics as features to predict thermal conductivity values. Features MUST be filtered to exclude those with Variance Inflation Factor (VIF) ≥ 5 (See US-3)
- **FR-007**: System MUST evaluate model performance using k-fold cross-validation with R² and RMSE metrics computed for each fold (See US-3)
- **FR-008**: The final report MUST contain a section titled "Limitations" that explicitly states: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." (See US-2)
- **FR-009**: System MUST perform collinearity diagnostics (Variance Inflation Factor) when network metrics are used as features. If VIF ≥ 5 for any feature, that feature MUST be excluded from the regression model and logged (See US-2)
- **FR-010**: System MUST document sample-size and power considerations, or explicitly acknowledge power limitations if n < 50 (See US-2)

### Key Entities

- **MaterialRecord**: Represents a single crystalline material from Materials Project, key attributes include material_id, cif_file_path, thermal_conductivity_tensor (k_x, k_y, k_z), network_graph_id, skip_reason (if applicable)
- **NetworkGraph**: Represents an atomic network constructed from crystallography, key attributes include material_id, node_count, edge_count, average_degree, average_path_length (LCC only), clustering_coefficient, is_connected (boolean)
- **CorrelationResult**: Represents statistical analysis between a network metric and thermal conductivity, key attributes include metric_name, correlation_coefficient, p_value, bonferroni_adjusted_p, significance_flag, vif_value (if applicable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation analysis is measured against the requirement that Pearson and Spearman coefficients with p-values are computed and reported for all 3 independent metrics for every material in the dataset (See US-2)
- **SC-002**: Model predictive performance (R²) is measured against cross-validation results on held-out test folds with stratified cross-validation. (See US-3)
- **SC-003**: Dataset-variable fit is measured against the requirement that Materials Project contains all required variables (crystallography, thermal conductivity tensor, bond connectivity) for ≥50 materials (See US-1)
- **SC-004**: Multiplicity control is measured against the requirement that all 3 correlation tests undergo Bonferroni correction with family-wise error rate controlled at α ≤ 0.05 (See US-2)
- **SC-005**: Compute feasibility is measured against the constraint that full analysis completes within 6 hours on CPU-only hardware (2 cores, ≤7 GB RAM, ≤GB disk) (See US-3)
- **SC-006**: Limitations reporting is measured against the requirement that the "Limitations" section exists in the final report and contains the mandatory text defined in FR-008 (See US-2)

## Assumptions

- Materials Project API provides programmatic access to CIF files and thermal conductivity tensor values (k_x, k_y, k_z) without requiring institutional authentication or paid API keys.
- Thermal conductivity values in Materials Project include both experimental measurements and high-fidelity DFT-calculated values that are scientifically valid for correlation analysis.
- A covalent-radius-based bond detection method (sum of radii plus a small tolerance) is sufficient to capture relevant atomic interactions for network construction across diverse crystal structures. If radii are missing, a fallback distance cutoff is used.
- Network metrics (degree, path length on LCC, clustering) are computed using standard graph-theoretic definitions available in NetworkX or equivalent CPU-tractable libraries.
- The Materials Project database contains ≥50 materials with both complete crystallographic data and documented thermal conductivity tensor values after filtering.
- All analysis runs on GitHub Actions free-tier runners (CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU) with ≤6 hour job timeout.
- Pearson and Spearman correlation methods are appropriate for the data distribution (or transformations are applied as needed).
- Linear regression is an acceptable baseline model; more complex models are out of scope for this research phase.
- The observational study design means all findings will be framed as associational relationships, not causal claims, as explicitly stated in the "Limitations" section.
- The arithmetic mean of principal components is an acceptable scalar reduction for the thermal conductivity tensor in this exploratory phase.