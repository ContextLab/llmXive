# Feature Specification: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

**Feature Branch**: `001-battery-electrolyte-decomposition`  
**Created**: 2026-07-02  
**Status**: Draft  
**Input**: User description: "Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Extraction (Priority: P1)

The system must successfully ingest pre-computed DFT structures and energies from public repositories (Materials Project, NOMAD), filter for relevant electrolyte species (EC, DMC, LiPF6, etc.), and extract a standardized set of ground-state molecular descriptors (HOMO, LUMO, band gap, bond lengths, angles) using `pymatgen` and `RDKit`.

**Why this priority**: Without a clean, reproducible dataset of features and targets, no modeling or analysis can occur. This is the foundational data pipeline required for any downstream scientific insight.

**Independent Test**: This can be fully tested by running the data extraction script on a small, fixed subset of known entries and verifying that the output CSV contains the expected columns, no missing values in the feature matrix, and that the calculated target variable (decomposition energy) matches the manual formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ within a tolerance of 0.01 eV, validating the calculation pipeline implementation.

**Acceptance Scenarios**:

1. **Given** a valid Materials Project ID for an electrolyte molecule, **When** the ingestion script runs, **Then** the system extracts HOMO, LUMO, and geometric features and calculates the decomposition energy for at least 3 distinct electrochemical potentials (0V, 2V, 4V vs Li/Li+).
2. **Given** a dataset entry with missing geometric data, **When** the extraction script runs, **Then** the system logs a warning and excludes the entry from the final feature matrix without crashing the pipeline.

---

### User Story 2 - Model Training and Feature Importance Ranking (Priority: P2)

The system must train a Random Forest Regressor on the extracted dataset to predict decomposition energies and generate a ranked list of molecular descriptors based on permutation importance, specifically analyzing how this ranking shifts across different electrochemical potential bins (defined as low-potential 0-2V and high-potential 3-5V).

**Why this priority**: This addresses the core research question: identifying *which* descriptors govern stability and *how* their importance shifts. It transforms raw data into the primary scientific finding.

**Independent Test**: This can be fully tested by training the model on an 80/20 split, calculating the R² score on the test set, and generating a heatmap showing the top 5 features at low (0-2V) vs. high (3-5V) potentials. The test passes if the model outputs an R² score and the heatmap visually demonstrates the feature ranking.

**Acceptance Scenarios**:

1. **Given** a filtered dataset of 500+ electrolyte entries, **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the system outputs an R² score and a permutation importance list for each potential bin.
2. **Given** a trained model, **When** the user requests a comparison of feature importance between 1V and 4V, **Then** the system identifies at least one descriptor that enters the top 3 at 4V but is absent from the top 3 at 1V.

---

### User Story 3 - Experimental Validation and Sensitivity Analysis (Priority: P3)

The system must validate the model's predictions against independent experimental onset potentials from literature and perform a sensitivity analysis on the decomposition energy threshold to ensure the findings are robust to small variations in the cutoff.

**Why this priority**: This ensures the model predicts physical reality, not just DFT artifacts, and satisfies the methodological requirement for threshold justification and sensitivity analysis, which is critical for scientific defensibility.

**Independent Test**: This can be fully tested by comparing the model's predicted onset potentials for a held-out set of available known electrolytes against experimental values, calculating the Mean Absolute Error (MAE), and re-running the importance analysis with the energy threshold shifted by ±0.05 eV to verify that the top 3 descriptors remain consistent. The predicted onset potential is derived from the predicted energy via the transformation $V_{onset} = E_{decomp} / nF$.

**Acceptance Scenarios**:

1. **Given** a set of up to N available experimental onset potentials from literature (where N is the count of found data points), **When** the model predicts values for these molecules, **Then** the Mean Absolute Error (MAE) is calculated and reported.
2. **Given** a baseline decomposition threshold of 0.5 eV, **When** the threshold is swept to {0.45, 0.50, 0.55} eV, **Then** the top 3 feature importance rankings change by no more than 1 position, confirming robustness.

---

### Edge Cases

- What happens when the DFT dataset contains duplicate entries for the same molecule at different potentials? (System must deduplicate based on molecule ID and potential).
- How does the system handle molecules where the HOMO/LUMO gap is effectively zero or negative (metallic behavior)? (System must flag these as outliers and exclude them from the regression to prevent skewing).
- What if the experimental validation set is smaller than a sufficient threshold for robust analysis? (System must proceed with available data but flag the statistical power limitation in the report).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and parse DFT energy data and molecular structures from Materials Project and NOMAD, filtering for entries containing EC, DMC, or LiPF6 species (See US-1).
- **FR-002**: System MUST calculate the decomposition energy target variable using the formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ for a fixed set of potentials $\phi$ spanning a representative range, where $n$ is the number of electrons transferred and $F$ is the Faraday constant. (See US-1).
- **FR-003**: System MUST extract ground-state descriptors including HOMO, LUMO, band gap, and at least 5 geometric features (specifically bond lengths, bond angles, and dihedral angles) using `pymatgen` and `RDKit` (See US-1).
- **FR-004**: System MUST train a Random Forest Regressor with hyperparameter tuning via 5-fold cross-validation to predict decomposition energies (See US-2).
- **FR-005**: System MUST generate permutation importance scores for all descriptors stratified by electrochemical potential ranges (See US-2).
- **FR-006**: System MUST validate predictions against an external experimental dataset and calculate MAE and R² metrics (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the decomposition energy threshold by sweeping the cutoff over $\{0.45, 0.50, 0.55\}$ eV and reporting rank stability (See US-3).
- **FR-008**: System MUST determine reaction stoichiometry and electron count (n) for each molecule using a defined reaction database or heuristic to ensure the target variable is well-defined (See US-1).

### Key Entities

- **ElectrolyteMolecule**: Represents a chemical species with attributes: `smiles`, `dft_id`, `formation_energy`, `homo`, `lumo`, `band_gap`, `bond_lengths`.
- **DecompositionEvent**: Represents a reaction outcome with attributes: `molecule_id`, `potential_v`, `decomposition_energy`, `products_list`.
- **ModelRun**: Represents a training instance with attributes: `model_type`, `potential_bin`, `r2_score`, `feature_importance_map`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model predictive accuracy (R²) is measured against the held-out test set of DFT-calculated decomposition energies (See US-2).
- **SC-002**: Descriptor importance shift is measured by the change in rank position of the top 5 features between low-potential (0-2V) and high-potential (3-5V) bins (See US-2).
- **SC-003**: Physical validity is measured by the Mean Absolute Error (MAE) between predicted onset potentials and experimental values from literature (See US-3).
- **SC-004**: Threshold robustness is measured by the maximum rank change of the top 3 descriptors across the sensitivity sweep $\{0.45, 0.50, 0.55\}$ eV (See US-3).
- **SC-005**: Computational feasibility is measured by total runtime on a standard CI runner, ensuring the job completes within a reasonable time target (See US-1, US-2).

## Assumptions

- The Materials Project and NOMAD repositories provide sufficient coverage of ground-state electronic properties (HOMO/LUMO) for the target electrolyte molecules without requiring on-the-fly DFT recalculations.
- The experimental onset potentials available in public literature (e.g., cyclic voltammetry data) are sufficiently accurate to serve as a ground truth for validation, despite potential variations in experimental conditions.
- The Random Forest algorithm is sufficient to capture the non-linear relationships between descriptors and decomposition energies without requiring deep learning architectures that would exceed CPU constraints.
- The dataset size, after filtering for relevant species and potentials, will be large enough (≥ 200 samples) to support 5-fold cross-validation and meaningful feature importance analysis.
- The decomposition energy formula $E_{decomp} = E_{products} - E_{reactants} - nF\phi$ adequately approximates the thermodynamic stability under varying potentials for the scope of this study, ignoring kinetic barriers.