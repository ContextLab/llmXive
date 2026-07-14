# Feature Specification: Predicting Molecular Dipole Moments with Graph Neural Networks

**Feature Branch**: `001-predicting-molecular-dipole-moments`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "To what extent does 3D conformational geometry provide independent predictive information for molecular dipole moments beyond 2D connectivity and atom types?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Preparation and Baseline Feature Extraction (Priority: P1)

A researcher can download the QM9 dataset, filter to a random subset, and extract both 3D coordinates and 2D descriptors (Morgan fingerprints, Coulomb matrices) for baseline comparison.

**Why this priority**: This is the foundational step without which no modeling can occur. It delivers immediate value by establishing the data infrastructure and confirming the dataset is accessible and preprocessed correctly.

**Independent Test**: Can be fully tested by verifying data files exist, the subset is of a substantial size, and both 3D and 2D feature matrices are generated with no missing values.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset is available at the specified DOI, **When** the researcher runs the preprocessing script, **Then** A subset is created with extracted 3D coordinates, atom types, bond connectivity, and 2D descriptors
2. **Given** the preprocessing script has completed, **When** the researcher validates the output files, **Then** The dataset comprises a substantial collection of molecules, each characterized by complete feature vectors free of NaN values.
3. **Given** the QM9 subset contains molecules with missing 3D coordinates, **When** the preprocessing script processes them, **Then** molecules are flagged and excluded with a report of excluded count (edge case acceptance criteria)

---

### User Story 2 - Model Training and Evaluation Pipeline (Priority: P2)

A researcher can train a lightweight SchNet-style GNN and Random Forest baseline on the same train/test splits, then evaluate both on a held-out test set using MAE and RMSE for dipole moments with 50 epochs and early stopping.

**Why this priority**: This delivers the core comparative analysis. Without it, the research question cannot be answered. It builds on the data preparation from Story 1.

**Independent Test**: Can be fully tested by running training with 50 epochs and early stopping (patience=10), then verifying both models produce MAE and RMSE scores on the test set with confidence intervals.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset from Story 1, **When** the researcher trains both the GNN and Random Forest models with 5 random seeds, **Then** each model produces a test set MAE and RMSE score with confidence intervals
2. **Given** both models have completed training, **When** the researcher compares their performance, **Then** the RMSE distributions are saved for statistical comparison and RMSE variance across seeds is < 10%

---

### User Story 3 - Feature Attribution and Statistical Significance Analysis (Priority: P3)

A researcher can apply permutation importance to the Random Forest and saliency mapping to GNN embeddings, then perform paired t-tests to confirm statistical significance of the performance delta.

**Why this priority**: This provides the interpretability and scientific rigor needed to answer the research question. It depends on both Story 1 (data) and Story 2 (model outputs).

**Independent Test**: Can be fully tested by verifying feature importance rankings are generated and t-test p-values are computed across multiple random seeds.

**Acceptance Scenarios**:

1. **Given** trained models from Story 2, **When** the researcher runs the attribution analysis, **Then** structural contributions are ranked (e.g., electronegative atom placement, local bond angles)
2. **Given** RMSE distributions from 5 random seeds, **When** paired t-tests are performed (α=0.05), **Then** statistical significance of the GNN vs baseline delta is reported

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and cache the QM9 dataset (DOI: 10.1038/sdata.2014.22) with integrity verification
- **FR-002**: System MUST extract 3D coordinates, atom types, and bond connectivity from the dataset
- **FR-003**: System MUST generate 2D descriptors (Morgan fingerprints, Coulomb matrices) for baseline comparison
- **FR-004**: System MUST implement a lightweight SchNet-style GNN using PyTorch Geometric in CPU-only mode
- **FR-005**: System MUST train and evaluate both GNN and Random Forest models with identical train/test splits across multiple random seeds, using 50 epochs with early stopping (patience=10)
- **FR-006**: System MUST compute MAE and RMSE metrics for dipole moment predictions on a held-out test set
- **FR-007**: System MUST apply permutation importance to Random Forest features and saliency mapping to GNN node embeddings (2 methods total)
- **FR-008**: System MUST perform paired t-tests (α=0.05) comparing RMSE distributions between GNN and baseline
- **FR-009**: System MUST visualize feature importance maps on representative molecules to correlate with chemical intuition
- **FR-010**: System MUST complete execution within 6h on 2 CPU cores (constraint applies to entire pipeline from data download through final visualization)
- **FR-011**: System MUST validate predictions against QM9 quantum calculation reference data (physical experimental measurements are out of scope for this computational feature; Dipole moments from a benchmark molecular dataset are derived from DFT calculations at the BLYP/-31G(2df,p) level per the dataset specification)
- **FR-012**: System MUST report confidence intervals for both MAE and RMSE (95% CI computed across 5 random seeds)
- **FR-013**: System MUST operate within 8GB memory footprint throughout entire pipeline execution

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: GNN model achieves lower MAE than Random Forest baseline on held-out test set with 95% confidence intervals for both MAE and RMSE (statistically significant at α=0.05)
- **SC-002**: Feature attribution analysis identifies at least 3 structural features contributing to predictive variance (e.g., electronegative atom placement, local bond angles)
- **SC-003**: All experiments complete within 6h runtime on 2 CPU cores (constraint applies to entire pipeline from data download through final visualization)
- **SC-004**: Paired t-tests confirm performance delta between 3D GNN and 2D baseline across all 5 random seeds
- **SC-005**: Reproducibility achieved with consistent results across the 5 random seeds (RMSE variance < 10%)

## Assumptions

- The QM9 dataset is accessible via the specified DOI and contains dipole moment reference values
- PyTorch Geometric is available in the execution environment with CPU-only mode support
- A random subset of QM9 is representative of the full dataset for dipole moment prediction.
- **Hydration state limitation**: QM9 molecules are gas-phase DFT calculations without explicit solvent; hydration effects are out-of-scope for this feature and documented as a known limitation
- **Conformational ensembles**: Single lowest-energy conformer per molecule from QM9 is used; ensemble sampling is documented as future work in research.md
- Physical measurement validation is out of scope for this computational feature; validation will use QM9 quantum calculation reference data as the ground truth standard (experimental validation is a downstream research requirement, not a feature requirement)
- The 6h execution time limit on 2 CPU cores is a hard constraint that cannot be exceeded and applies to the entire pipeline execution
- All cited literature URLs from the idea markdown are valid and accessible for reference validation (validated by T053 in tasks.md)
- Computational efficiency requirements (6h on 2 CPU cores, 8GB memory) are hard constraints documented in FR-010, FR-013, SC-003

## Edge Cases

- What happens when the QM9 dataset DOI link is inaccessible or the download fails? (handled by T021)
- How does the system handle molecules with missing 3D coordinates in the QM9 subset? (handled by T019 with acceptance criteria in User Story 1)
- What happens when the 6h CPU time limit is exceeded during model training? (handled by T049 with 2 CPU cores constraint enforced by T050)