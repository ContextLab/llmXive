# Feature Specification: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Feature Branch**: `001-predict-molecular-interactions`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Interactions in Ionic Liquids via Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Engineering (Priority: P1)

The system MUST ingest the ILThermo dataset and the curated SAPT/DFT energy decomposition repository, then generate a unified feature set containing molecular descriptors (partial charges, polarizability, H-bond counts) and graph embeddings for every IonPair. **All structural descriptors and graph embeddings MUST be pre-computed** before the model training loop begins to ensure training trials do not exceed time limits.

**Why this priority**: Without a clean, engineered dataset linking structural features to interaction energy components, no model can be trained. This is the foundational data pipeline.

**Independent Test**: The pipeline can be tested by running the ingestion script on a small subset (e.g., 50 IonPairs) and verifying the output CSV contains the expected columns (cation_id, anion_id, electrostatic_energy, dispersion_energy, hbond_energy, partial_charge, polarizability, graph_embedding) with no null values in critical columns.

**Acceptance Scenarios**:

1. **Given** the raw ILThermo and SAPT datasets are available locally, **When** the ingestion script runs, **Then** a unified dataframe is produced where every row represents a unique IonPair with all required interaction energy components and structural descriptors populated.
2. **Given** an IonPair exists in the SAPT dataset but not ILThermo, **When** the ingestion script runs, **Then** the row is included with SAPT values and ILThermo-derived descriptors, ensuring no data loss for the training target.
3. **Given** a molecular structure lacks a defined partial charge in the source, **When** the feature engineering step runs, **Then** the system calculates it using RDKit's built-in methods or flags the row for exclusion, preventing null propagation to the model.

---

### User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

The system MUST train three separate Gradient-Boosting Regressors (XGBoost) to predict electrostatic, dispersion, and hydrogen-bonding energy components, optimizing hyperparameters via Optuna within a strict CPU time budget and a fixed maximum number of trials.

**Why this priority**: This is the core analytical engine. It transforms the engineered features into predictive models, directly addressing the research question of which mechanisms dominate.

**Independent Test**: The training script can be tested by running it on a toy dataset (e.g., 100 samples) with a 2-minute timeout. It should output three model artifacts (`.json` or `.pkl`) and a log file showing the best hyperparameters found for each component.

**Acceptance Scenarios**:

1. **Given** the engineered dataset is split into [deferred] train, [deferred] validation, [deferred] test sets, **When** the training script executes, **Then** three distinct XGBoost models are saved, one for each interaction energy component, with no errors during the fitting process. The split MUST be stratified by StructuralFamily.
2. **Given** the Optuna optimization is running, **When** a trial exceeds 5 minutes of CPU time, **Then** the trial is terminated immediately, and the system logs the timeout and proceeds to the next trial without crashing.
3. **Given** the validation set, **When** the final models are evaluated, **Then** the Mean Absolute Error (MAE) for each component is recorded and logged, ensuring the models have converged to a non-trivial state.

---

### User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

The system MUST group predictions by cation/anion structural families, compute mean/variance statistics, perform ANOVA tests to identify families deviating from global trends, and compare ML predictions against a subset of **experimental enthalpy of mixing data** from ILThermo for independent validation.

**Why this priority**: This step answers the specific research question about trends across families and validates the model's generalizability. The ANOVA test is used not to prove the obvious (structure determines energy) but to identify *which specific families* deviate significantly from the global trend, enabling targeted analysis of outliers. Validating against experimental data ensures the model predicts real physical interactions, not just interpolation of SAPT artifacts.

**Independent Test**: The analysis script can be tested by running it on the test set predictions and a subset of 20 experimental data points. It should output a JSON report containing ANOVA p-values for each family and a comparison plot (or data) of ML vs. Experimental errors.

**Acceptance Scenarios**:

1. **Given** the trained models and the test set, **When** the analysis script groups predictions by structural family (e.g., imidazolium, BF4-), **Then** it calculates the mean and variance of each interaction component per family and stores them in a structured report.
2. **Given** the grouped predictions, **When** an ANOVA test is performed with multiple-comparison correction, **Then** the script outputs a corrected p-value for each interaction component indicating whether family membership significantly explains the variance.
3. **Given** a subset of 20 IonPairs not in the training data with available experimental enthalpy data, **When** the ML predictions are compared to experimental values, **Then** the system reports the MAE for this out-of-sample set, confirming generalization performance.

### Edge Cases

- What happens when the SAPT dataset contains an ion pair with an undefined structural family (e.g., a novel, uncategorized ion)?
- How does the system handle a case where the experimental validation data is missing for one of the 20 validation IonPairs?
- What if the Optuna optimization finds that a simpler model (e.g., linear regression) outperforms XGBoost on the validation set?

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the ILThermo dataset and the curated SAPT/DFT energy decomposition repository to create a unified training dataset of IonPairs. (See US-1)
- **FR-002**: System MUST generate molecular descriptors (partial charges, polarizability, H-bond counts) and graph embeddings for every IonPair using RDKit. These features MUST be pre-computed prior to training. (See US-1)
- **FR-003**: System MUST train three separate Gradient-Boosting Regressors (XGBoost) to predict electrostatic, dispersion, and hydrogen-bonding energy components. (See US-2)
- **FR-004**: System MUST perform hyperparameter tuning with Optuna, limiting each trial to ≤ 5 minutes of CPU time. (See US-2)
- **FR-005**: System MUST group predictions by cation/anion structural families and compute mean/variance statistics for each interaction component. (See US-3)
- **FR-006**: System MUST perform an ANOVA test to determine if family membership significantly explains variance in each interaction term, applying a multiple-comparison correction (e.g., Bonferroni) to control family-wise error rate. The significance threshold is [deferred] (targeting a corrected p < 0.01/N_tests). This test is designed to identify specific families that deviate from global trends, not merely confirm the structure-energy relationship. (See US-3)
- **FR-007**: System MUST compare ML predictions against a subset of 20 IonPairs with available experimental enthalpy of mixing data to assess out-of-sample generalization. (See US-3)
- **FR-008**: System MUST limit the total number of Optuna trials to a fixed, resource-constrained maximum to ensure the total pipeline execution time remains within the designated time budget. (See US-2)

### Key Entities

- **IonPair**: Represents a unique cation/anion combination, with attributes for cation_id, anion_id, and interaction energy components (electrostatic, dispersion, hbond).
- **StructuralFamily**: A categorical grouping of ions based on their chemical structure (e.g., imidazolium, BF4-), used for statistical analysis.
- **ModelArtifact**: The serialized output of the training process, containing the trained XGBoost model and its hyperparameters for a specific interaction component.
- **ValidationSet**: A subset of 20 IonPairs with experimental data, not present in the training data, used for independent validation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Mean Absolute Error (MAE) of the trained models is measured against the held-out test set. The specific threshold is [deferred] (targeting ≤ 0.5 kcal mol⁻¹, subject to SAPT data noise). (See US-2)
- **SC-002**: Statistical significance of family trends is measured against the ANOVA p-value. The specific threshold is [deferred] (targeting a corrected p < 0.01/N_tests). (See US-3)
- **SC-003**: Out-of-sample generalization is measured against the MAE of the 20 experimental validation points. Success is defined as out-of-sample MAE ≤ 2.0 × baseline test set MAE. (See US-3)
- **SC-004**: Computational feasibility is measured against the 6-hour GitHub Actions job limit to ensure the entire pipeline (ingestion, training, validation) completes within the resource constraints, given a maximum of 60 trials. (See US-2)
- **SC-005**: Model robustness is measured against the sensitivity analysis of the MAE across different hyperparameter configurations found by Optuna. Success is defined as the variance of MAE across configurations being < 0.1 kcal mol⁻¹. (See US-2)

## Assumptions

- The ILThermo dataset and the curated SAPT/DFT energy decomposition repository are accessible and contain the necessary variables (cation/anion structures, interaction energy components) for the analysis.
- The **combined** dataset (ILThermo + SAPT) is large enough (≥ 5,000 IonPairs) to support a stratified split (70/15/15) while maintaining sufficient samples per family for ANOVA.
- The experimental validation calculations (or data retrieval) can be completed within the 6-hour job limit on a CPU-only runner.
- The XGBoost models trained on the CPU will achieve a reasonable MAE without requiring GPU acceleration or large-scale model architectures.
- The structural families (e.g., imidazolium, BF4-) are well-defined and can be consistently mapped to the ions in the dataset.
- The multiple-comparison correction (e.g., Bonferroni) will not overly penalize the statistical power to detect significant family trends.
- The dataset is large enough to support the required stratified split by StructuralFamily.
- The RDKit library can successfully generate the required graph embeddings and descriptors for all ions in the dataset without encountering parsing errors.
- The Optuna hyperparameter optimization will converge to a reasonable set of hyperparameters within the 5-minute trial limit and 60 trial count.
- The experimental validation data will be available for at least 20 IonPairs not in the training set.
- The family-wise error rate correction will be applied to the ANOVA p-values to ensure the statistical findings are robust.