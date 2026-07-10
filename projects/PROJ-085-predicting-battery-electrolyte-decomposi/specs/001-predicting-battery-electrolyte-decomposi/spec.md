# Feature Specification: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and Feature Engineering Pipeline (Priority: P1)

The system must ingest pre-computed DFT data from public repositories (Materials Project, NOMAD), filter for relevant electrolyte species (e.g., EC, DMC, LiPF), and construct a feature matrix containing ground-state descriptors (HOMO/LUMO, bond lengths) and synthetic labels derived from applied potentials.

**Why this priority**: Without a clean, non-leaking dataset where features are strictly ground-state properties and labels are correctly calculated as $E_{decomp} = E_{products} - E_{reactants} - nF\phi$, no model training can occur. This is the foundational data layer.

**Independent Test**: The pipeline can be tested by running the ingestion script on a small, static subset of the Materials Project API and verifying that the resulting CSV contains exactly the expected columns (HOMO, LUMO, bond lengths, potential-adjusted energy) with zero NaN values in the feature set.

**Acceptance Scenarios**:

1. **Given** a raw download of DFT entries for EC and DMC from Materials Project, **When** the ingestion script runs, **Then** the output CSV contains only entries with valid ground-state electronic properties and calculated decomposition energies for at least 3 distinct potential levels.
2. **Given** the feature matrix, **When** a collinearity diagnostic is run, **Then** the system writes a warning to the log and adds a column to the output CSV for any pair of definitionally related predictors (e.g., bond length vs. bond order) with a Variance Inflation Factor (VIF) ≥ 10, flagging them for joint descriptive analysis rather than independent causal claims.
3. **Given** the dataset, **When** the system checks for variable fit, **Then** it confirms that every predictor (HOMO, LUMO) and outcome variable exists in the source data; if a required variable (e.g., specific solvation energy) is missing from the source, the system logs an error and halts the pipeline.

---

### User Story 2 - CPU-Constrained Model Training and Interpretability (Priority: P2)

The system must train a Random Forest Regressor on the curated dataset using only CPU resources (≤7GB RAM, 2 cores) to predict decomposition energies, and extract permutation importance scores to identify the dominant physical determinants at each potential level.

**Why this priority**: This delivers the core scientific insight (the shift in determinants) while strictly adhering to the compute constraints of the free-tier CI runner.

**Independent Test**: The training script can be tested by executing it on a local machine with resource limits mimicking the CI runner (e.g., `cgroup` limits) and verifying that the process completes without OOM errors and outputs a JSON file of feature importances within the defined time budget.

**Acceptance Scenarios**:

1. **Given** the curated dataset, **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the training process completes within ≤ 6 hours on a 2-core CPU without utilizing any GPU or CUDA libraries.
2. **Given** the trained model, **When** permutation importance is calculated, **Then** the output includes a ranked list of descriptors for each potential level, explicitly noting if the top descriptor shifts from HOMO/LUMO at low potentials to bond dissociation energies at high potentials.
3. **Given** the model configuration, **When** hyperparameter tuning is performed via GridSearchCV, **Then** the system validates that no GPU-accelerated libraries (e.g., `bitsandbytes`, `load_in_8bit`) are invoked, and the memory usage remains below a defined threshold.

---

### User Story 3 - Experimental Validation and Sensitivity Analysis (Priority: P3)

The system must evaluate the model against held-out experimental decomposition onset potentials from literature and perform a sensitivity analysis on the decision thresholds used to define "stable" vs. "unstable" regimes.

**Why this priority**: This validates the scientific claim against reality and ensures the robustness of the findings, addressing the methodological requirement for threshold justification.

**Independent Test**: The validation module can be tested by providing a static JSON of experimental CV data and verifying that the model's predictions are compared against these values, calculating R² and generating a sensitivity report for at least 3 threshold variations.

**Acceptance Scenarios**:

1. **Given** a held-out set of experimental decomposition onset potentials from cyclic voltammetry literature, **When** the model predicts values for these molecules (after applying bias correction), **Then** the system calculates the R² score and reports the improvement over a mean-prediction baseline, acknowledging the physics gap between thermodynamic stability and kinetic onset.
2. **Given** a specific threshold for defining decomposition instability (e.g., energy < 0.0 eV), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold across a concrete set (e.g., negative, zero, and positive values in eV) and reports how the false-positive rate varies across these values.
3. **Given** the observational nature of the data (no random assignment), **When** the results are summarized, **Then** all claims regarding descriptor influence are framed as "associational" or "predictive" rather than "causal," unless the input data explicitly includes randomized potential assignment.

### Edge Cases

- What happens when the source dataset (Materials Project) returns entries with missing HOMO/LUMO values? The system must drop these rows and log a count of excluded entries, ensuring the feature matrix is complete.
- How does the system handle a scenario where the Random Forest model achieves R² < 0.5 on the validation set? The system must flag this as a "null result" indicating ground-state descriptors are insufficient, rather than failing silently or overfitting.
- What occurs if the experimental validation data contains molecules not present in the training distribution? The system must report the prediction error specifically for these out-of-distribution samples to assess generalization limits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest DFT data from Materials Project and NOMAD, filtering for ground-state electronic properties (HOMO, LUMO, band gap) and geometric features, ensuring no leakage of target decomposition energies into the feature set (See US-1).
- **FR-002**: System MUST calculate synthetic decomposition energy labels using the formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ for a user-defined range of electrochemical potentials $\phi$ (See US-1).
- **FR-003**: System MUST train a Random Forest Regressor using Scikit-learn, constrained to CPU-only execution with a maximum memory footprint of 7 GB and a runtime limit of ≤ 6 hours (See US-2).
- **FR-004**: System MUST perform 5-fold cross-validation stratified by discrete potential levels (e.g., 0V, 1V, 2V) to ensure the model generalizes across different electrochemical conditions (See US-2).
- **FR-005**: System MUST extract and output permutation importance scores for all molecular descriptors at each potential level to identify the "tipping point" of governing mechanisms (See US-2).
- **FR-006**: System MUST validate model performance against a held-out set of experimentally measured decomposition onset potentials sourced from cyclic voltammetry literature as a proxy correlation study, distinct from the training data, provided a bias correction is applied (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on any decision threshold (e.g., stability boundary), sweeping the threshold over a concrete set (e.g., negative, zero, and positive values) and reporting the variation in false-positive/negative rates (See US-3).
- **FR-008**: System MUST frame all findings as associational rather than causal when the data is observational, unless randomization is explicitly present in the input design (See US-3).
- **FR-009**: System MUST apply a systematic bias correction (e.g., linear offset regression) when comparing synthetic DFT labels to experimental values to account for the inherent DFT error relative to experiment (See US-3).
- **FR-010**: System MUST perform a partial correlation analysis between feature sources (eigenvalues) and target sources (total energies) to ensure no mathematical identity leakage exists, rejecting features with partial correlation > 0.9 (See US-1).
- **FR-011**: System MUST explicitly state in all output reports that the model predicts "thermodynamic stability" and that validation against "kinetic onset" is a proxy correlation study acknowledging the physics gap (See US-3).

### Key Entities

- **Molecule**: Represents a specific electrolyte species (e.g., EC, DMC) with attributes for HOMO, LUMO, bond lengths, and calculated decomposition energy.
- **PotentialLevel**: Represents a specific applied electrochemical potential ($\phi$) used to generate synthetic labels and stratify validation.
- **ExperimentalMeasurement**: Represents an independent, literature-sourced decomposition onset potential used for final validation, distinct from DFT calculations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The R² score is calculated, and the improvement over a mean-prediction baseline is measured as a trend correlation study acknowledging the physics gap between thermodynamic stability and kinetic onset (See US-3).
- **SC-002**: The shift in dominant feature importance (e.g., from HOMO to bond dissociation energy) is measured against the potential range to identify the specific voltage "tipping point" (See US-2).
- **SC-003**: The false-positive and false-negative rates for stability classification are measured against the swept threshold set ({-0.05, 0.0, +0.05} eV) to assess the robustness of the decision boundary (See US-3).
- **SC-004**: The memory usage and runtime of the training pipeline are measured against the constraints of a fixed RAM limit and a defined time budget to ensure feasibility on free-tier CI (See US-2).
- **SC-005**: The Variance Inflation Factor (VIF) for definitionally related predictors must be < 10 to confirm that collinearity diagnostics are applied and independent causal claims are avoided (See US-1).

## Assumptions

- The Materials Project and NOMAD repositories contain sufficient entries for common electrolytes (EC, DMC, LiPF6) with the required ground-state electronic properties (HOMO, LUMO) and geometric features to construct a training set of at least 100 unique molecules.
- The experimental decomposition onset potentials sourced from cyclic voltammetry literature are available in a machine-readable format or can be reliably extracted from the cited papers without requiring manual entry.
- The "synthetic" labels generated via the formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ are a valid proxy for the training target, acknowledging that they approximate the experimental onset potential rather than replicating the full dynamic solvation environment.
- The Random Forest algorithm is sufficient to capture the non-linear relationships between ground-state descriptors and decomposition energies without requiring deep learning architectures that would violate the CPU-only constraint.
- The dataset does not contain hidden confounders (e.g., unreported solvent effects) that would invalidate the associational claims, or if they exist, they are acknowledged as a limitation in the final report.
- The "sensitivity analysis" threshold sweep (e.g., {-0.05, 0.0, +0.05} eV) is computationally trivial and does not significantly impact the total runtime budget.