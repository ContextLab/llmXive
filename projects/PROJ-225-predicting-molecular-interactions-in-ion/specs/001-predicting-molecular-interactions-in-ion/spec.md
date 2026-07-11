# Feature Specification: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Feature Branch**: `001-predict-molecular-interactions`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Interactions in Ionic Liquids via Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Engineering (Priority: P1)

The system MUST ingest the ILThermo dataset and the SAPT/DFT energy decomposition repository, compute physicochemical and graph-based descriptors for every cation/anion pair, AND compute inter-ionic geometric features (e.g., center-of-mass distance, orientation angles) derived **exclusively from the optimized 3D geometries used for the SAPT ground truth calculations**. Pairs lacking these specific optimized geometries MUST be excluded from the training set to prevent construct validity violations.

**Why this priority**: Without a clean, feature-rich dataset that includes exact inter-ionic geometric context derived from the ground truth, no modeling or analysis is possible. This is the foundational step that enables all subsequent research.

**Independent Test**: The pipeline can be tested by running the ingestion script and verifying that the output CSV contains exactly the expected number of rows (matching the count of valid pairs in the **ILThermo v2.1 release after filtering nulls and missing optimized geometries**) and that all required descriptor columns (e.g., `partial_charge_cation`, `h_bond_count_anion`, `node2vec_embedding`, `inter_ionic_distance`) are populated with non-null numeric values.

**Acceptance Scenarios**:

1. **Given** the raw ILThermo and SAPT repositories are available locally, **When** the ingestion script executes, **Then** the system produces a single unified dataset where every row corresponds to a unique cation/anion pair with computed descriptors derived from the exact SAPT geometries.
2. **Given** a cation/anion pair with missing optimized 3D coordinates (required for SAPT), **When** the feature engineering step runs, **Then** the system flags the row as "invalid" and excludes it from the final training set, logging the specific missing variable.

---

### User Story 2 - XGBoost Interaction Energy Regression Modeling (Priority: P2)

The system MUST train three separate XGBoost regressors (one for electrostatic, one for dispersion, one for hydrogen-bonding energy) using the engineered features, performing hyperparameter tuning within strict CPU time limits.

**Why this priority**: This is the core predictive engine. It directly addresses the research question of "which mechanisms dominate" by quantifying them.

**Independent Test**: The modeling step can be tested independently by feeding a pre-computed feature set into the training script and verifying that three distinct model artifacts (`.json` or `.pkl`) are saved, each containing the hyperparameters and cross-validation scores.

**Acceptance Scenarios**:

1. **Given** a training dataset of at least 1,000 IL pairs (minimum required for model convergence), **When** the training script runs with a 5-minute timeout per Optuna trial, **Then** the system outputs three models (Electrostatic, Dispersion, H-Bond) and reports the achieved MAE for each.
2. **Given** a new, unseen IL pair, **When** the trained models are invoked, **Then** the system returns a predicted energy value for each of the three interaction components within 10 seconds.

---

### User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

The system MUST group **ground-truth** (SAPT/DFT) predictions by structural families, perform MANOVA tests to identify significant trends in the physical system, and validate a subset of model predictions against fresh DFT/SAPT calculations using a higher-fidelity method (e.g., CCSD(T)) or distinct basis set.

**Why this priority**: This step translates model outputs into scientific insight (answering "how do they vary?") by testing physical hypotheses on ground truth, and provides the necessary external validation to confirm the model's generalizability against a non-tautological ground truth.

**Independent Test**: The analysis can be tested by running the script on the model outputs and the ground-truth dataset. Verification includes: (1) a heatmap showing mean **ground-truth** interaction energies per family, (2) a statistical report of MANOVA results on ground truth, and (3) a validation report listing the **Pearson** correlation coefficient between ML predictions and the fresh DFT/SAPT ground truth for a set of **50 random pairs not in the training set, stratified by family**.

**Acceptance Scenarios**:

1. **Given** the ground-truth SAPT/DFT dataset and a list of structural families (e.g., imidazolium, BF4-), **When** the analysis script runs, **Then** it produces a statistical report indicating which families have significantly different interaction energy means (p < 0.01) via MANOVA performed on **ground-truth values**.
2. **Given** a subset of 50 IL pairs not in the training data, **When** the system runs single-point DFT/SAPT calculations (higher-fidelity) and compares them to ML predictions, **Then** the mean absolute error on this external validation set is ≤ 0.55 kcal mol⁻¹.

### Edge Cases

- What happens when the SAPT dataset contains cation/anion pairs with zero dispersion energy (e.g., purely ionic models)? The system must handle zero-variance targets gracefully without crashing the regressor.
- How does the system handle a structural family with fewer than 5 samples in the dataset? The MANOVA step must skip families with insufficient sample size to avoid statistical errors, logging a warning.
- What if the DFT validation step fails to converge for a specific IL pair? The system must catch Psi4 runtime exceptions, mark that pair as "validation failed," and proceed with the remaining pairs rather than aborting the entire job.
- What if a pair lacks the specific optimized geometry required for SAPT? The system must exclude the pair from the training set; **approximations using standard ionic radii are strictly prohibited** to prevent tautological correlations.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the ILThermo dataset and the SAPT energy decomposition repository to construct a unified input matrix (See US-1).
- **FR-002**: System MUST compute at least 10 specific physicochemical descriptors (**partial_charge, polarizability, H-bond_count, dipole_moment, refractivity, molecular_weight, logP, topological_polar_surface_area, rotatable_bond_count, and ring_count**), graph embeddings for every ion using RDKit, AND inter-ionic geometric features (e.g., center-of-mass distance, orientation angles) **derived exclusively from the optimized 3D geometries used for the SAPT ground truth**. Pairs lacking these exact geometries MUST be excluded (See US-1).
- **FR-003**: System MUST train three independent XGBoost regressors for electrostatic, dispersion, and hydrogen-bonding energy components, with each hyperparameter tuning trial limited to ≤ 5 minutes of CPU time (See US-2).
- **FR-004**: System MUST perform a stratified train/validation/test split (70/15/15) based on cation/anion families to ensure representative sampling across chemical space (See US-2).
- **FR-005**: System MUST execute a Multivariate Analysis of Variance (MANOVA) with Pillai's trace statistic on the **ground-truth (SAPT/DFT) interaction energies** grouped by structural families to determine statistical significance (p < 0.01) of family-based trends, correctly handling the correlation between energy components. This tests physical reality, not model performance (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis to evaluate the stability of the model's generalization error (MAE on the held-out test set) by sweeping the error tolerance definition over {0.4, 0.5, 0.6} kcal mol⁻¹. The system MUST output a sensitivity report containing the MAE at each threshold and a boolean 'is_robust' flag if the MAE variation is ≤ 0.05 kcal mol⁻¹ across the sweep (See US-3).
- **FR-007**: System MUST apply Multivariate Analysis of Variance (MANOVA) with Pillai's trace statistic when testing multiple hypotheses across the three interaction components using **ground-truth values** to prevent false positives, as the components are mathematically coupled and not independent (See US-3).
- **FR-008**: System MUST execute the full pipeline (ingestion, training, analysis) within the defined resource constraints (See US-1, US-2, US-3).

### Key Entities

- **IonicLiquidPair**: Represents a unique combination of a cation and an anion, identified by their SMILES strings or IUPAC names.
- **InteractionEnergyComponent**: A numeric value representing one of the three decomposed energy terms (Electrostatic, Dispersion, H-Bond) in kcal mol⁻¹.
- **MolecularDescriptor**: A computed feature vector (numeric or embedding) derived from the isolated cation or anion structure.
- **GeometricFeature**: A computed feature representing the spatial relationship between a cation and anion (e.g., distance, angle), **derived strictly from the optimized geometry used for the SAPT calculation**.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the three regression models on the held-out test set is measured against the target of MAE ≤ 0.5 kcal mol⁻¹ (See FR-003, US-2).
- **SC-002**: The statistical significance (p-value) of the MANOVA results comparing **ground-truth** interaction energies across structural families is measured against the threshold of 0.01 (See FR-005, US-3).
- **SC-003**: The **Pearson** correlation coefficient (R²) between ML predictions and the independent DFT/SAPT validation set (n=50, provided n ≥ 30 valid pairs) is measured against the threshold of R² ≥ 0.80 to assess generalization (See FR-005, US-3).
- **SC-004**: The total wall-clock time for the full pipeline (ingestion, training, analysis) is measured against the resource constraints of the GitHub Actions free runner. (See FR-008, US-1, US-2, US-3).
- **SC-005**: The peak memory usage of the feature engineering and training steps is measured against the available RAM limit of the runner. (See FR-002, FR-008, US-1, US-2).
- **SC-006**: The 'is_robust' flag generated by the sensitivity analysis (FR-006) is measured against the criterion: **MAE variation ≤ 0.05 kcal mol⁻¹ across the swept thresholds {0.4, 0.5, 0.6}** (See FR-006, US-3).

## Assumptions

- The ILThermo dataset and the SAPT energy decomposition repository are accessible via the provided URLs and do not require authentication or complex scraping logic.
- The `omegaB97X-D` functional and Psi4 package are available and pre-installed in the GitHub Actions runner environment, or can be installed within the 5-hour job limit (including installation time) without exceeding disk quotas.
- The SAPT dataset contains sufficient sample sizes (≥ 10) for the major cation/anion families (e.g., imidazolium, pyrrolidinium, BF4-, PF6-) to allow for meaningful MANOVA testing on ground truth.
- The "time-bound per trial" hyperparameter tuning limit is sufficient to converge XGBoost models to a local optimum that meets the MAE target on this specific dataset size.
- The relationship between structural descriptors and interaction energies is sufficiently captured by the selected Gradient Boosting algorithm, without requiring deep learning architectures that would exceed CPU constraints.
- The multi-hour and several GB RAM limits are hard engineering constraints for the free tier.; the pipeline must be optimized to fit within these budgets.
- **Approximated geometries (e.g., via ionic radii) are not used**; only pairs with exact optimized geometries from the ground truth source are included.