# Feature Specification: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Feature Branch**: `001-predict-sn1-rate-constants`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Rate Constants of SN1 Reactions from Molecular Structure"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST ingest public SN1 kinetic datasets (NIST, Reaxys open subsets, or UCI), parse SMILES strings into molecular graphs using RDKit, and compute electronic descriptors (Gasteiger partial charges, topological indices) to produce a clean, stratified dataset ready for modeling.

**Why this priority**: Without a validated, reproducible dataset containing the required structural and kinetic variables, no modeling can occur. This is the foundational step that determines data quality and variable availability.

**Independent Test**: Can be fully tested by running the ingestion script on a known subset of the NIST database and verifying that the output CSV contains non-null values for all required columns (SMILES, rate constant, substrate class) and that electronic descriptors are computed without GPU acceleration.

**Acceptance Scenarios**:

1. **Given** a raw dataset file containing SMILES and experimental rate constants, **When** the ingestion pipeline is executed, **Then** the output is a processed CSV where ≥ 95% of rows have valid molecular graphs and computed electronic descriptors (Gasteiger charges, topological indices).
2. **Given** a dataset with mixed substrate classes (e.g., secondary, tertiary alkyl halides), **When** the stratification step is executed, **Then** the train/validation/test splits (70/15/15) maintain proportional representation of each substrate class with a variance of ≤ 5% from the original distribution (required to maintain distributional fidelity across splits).
3. **Given** a dataset row with a missing rate constant or unparseable SMILES, **When** the cleaning step is executed, **Then** the row is logged to an exclusion report and removed from the final training set, ensuring the final dataset has no missing values in predictor or outcome columns.

### User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

The system MUST train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization via random search, and evaluate performance against baselines (random and linear regression) using R² and Mean Absolute Error (MAE).

**Why this priority**: This is the core research engine. It determines whether structural features alone can predict SN1 rates. The CPU-only constraint is critical for feasibility.

**Independent Test**: Can be fully tested by running the training script on the validation set, verifying that the model converges within the 6-hour CI limit, and that the test set R² score is calculated and compared against the linear regression baseline.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset, **When** the MPNN training job starts, **Then** the job completes within 6 hours on a 2-core CPU runner without requesting GPU resources, and the final model weights are saved to the artifacts directory.
2. **Given** the trained model and a held-out test set, **When** predictions are generated, **Then** the system outputs R² and MAE metrics, and a bootstrap-based comparison confirms whether the MPNN performance is statistically significantly better than the linear regression baseline (p < 0.05) (required to establish statistical significance of model improvement).
3. **Given** the hyperparameter search space (learning rate, hidden dimension, dropout), **When** the random search completes, **Then** the system selects the configuration with the highest validation R² from a set of sampled configurations and logs the top configurations with their respective metrics.

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

The system MUST generate feature importance analysis (using SHAP or attention weights) to identify structural determinants of rate, perform a sensitivity analysis on any decision thresholds or model hyperparameters to ensure robustness, and validate findings via perturbation studies.

**Why this priority**: Understanding *why* the model makes predictions is as important as the prediction accuracy itself for scientific validity. Sensitivity analysis ensures the findings are not artifacts of arbitrary parameter choices.

**Independent Test**: Can be fully tested by generating a SHAP summary plot, a sensitivity report that sweeps a key parameter, and a perturbation study that removes top features to verify importance.

**Acceptance Scenarios**:

1. **Given** a trained MPNN model, **When** the interpretability module runs, **Then** it produces a ranked list of up to 10 structural features (atoms, bonds, or electronic descriptors) contributing most to rate prediction, with a corresponding SHAP summary plot.
2. **Given** a specific threshold or hyperparameter (e.g., a cutoff for descriptor inclusion), **When** the sensitivity analysis sweeps the value over a range of small magnitudes, **Then** the system reports the resulting variation in R² and MAE, confirming that the model's performance does not degrade significantly across the sweep (required to verify model stability against small perturbations in regularization thresholds and intermediate values).
3. **Given** the final model, **When** the collinearity diagnostic is run on the predictors, **Then** the system identifies any pairs of predictors with a Variance Inflation Factor (VIF) > 5 and flags them for descriptive joint analysis rather than independent causal claims (required to ensure feature importance is not driven by multicollinearity).
4. **Given** the top features identified by SHAP, **When** the perturbation study runs, **Then** the system removes these features from the input and measures the drop in R², confirming that the importance scores correlate with predictive performance.

### Edge Cases

- What happens when the dataset contains molecules with no carbocation intermediate potential (e.g., primary alkyl halides that strictly follow SN2)? The system MUST filter these outliers during preprocessing using an independent chemical rule: filter if substrate class is explicitly labeled primary in the source OR if steric hindrance index > 2.0 (calculated via RDKit) to ensure the SN1-specific model is not trained on incompatible mechanisms.
- How does the system handle SMILES strings with undefined stereochemistry or ambiguous bond orders? The system MUST either standardize these using RDKit's canonicalization rules or exclude the row with a specific error code indicating "ambiguous structure."
- What happens if the Gasteiger charge calculation fails for a specific molecule due to convergence issues? The system MUST log the failure, exclude the molecule from the training set, and record the exclusion reason to maintain data integrity.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and parse SN1 kinetic data from NIST/Reaxys/UCI sources, extracting SMILES and rate constants, and compute electronic descriptors (Gasteiger charges, topological indices) using RDKit without GPU acceleration (See US-1).
- **FR-002**: System MUST split the dataset into train/validation/test sets (70/15/15) stratified by substrate class to prevent data leakage (See US-1).
- **FR-003**: System MUST train a Message Passing Neural Network (MPNN) with a configurable number of layers. on 2-core CPU hardware, optimizing hyperparameters via random search (≤50 configurations) (See US-2).
- **FR-004**: System MUST evaluate model performance using R² and MAE, comparing results against random and linear regression baselines via bootstrap-based comparison of mean squared errors (a large number of resamples) (See US-2).
- **FR-005**: System MUST generate feature importance rankings using SHAP values or attention weights to identify structural determinants of SN1 rates (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping key thresholds (e.g., descriptor inclusion cutoffs) over a set of representative values and report performance variance (See US-3).
- **FR-007**: System MUST run a collinearity diagnostic (VIF) on predictors and flag any pairs with VIF > 5 for descriptive joint analysis (See US-3).
- **FR-008**: System MUST perform a perturbation study removing top SHAP features and measure the resulting drop in R² to validate that feature importance is not circularly defined by input descriptors (See US-3).

### Key Entities

- **Molecule**: Represents a chemical substrate with attributes: SMILES string, substrate class (secondary/tertiary only), and computed electronic descriptors.
- **ReactionRate**: Represents the experimental outcome with attributes: rate constant value, temperature, solvent, and source database ID.
- **ModelConfiguration**: Represents a specific set of hyperparameters (learning rate, hidden dimension, dropout) and the resulting performance metrics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The predictive accuracy (R²) of the MPNN on the held-out test set is measured against the linear regression baseline and a random baseline (See US-2).
- **SC-002**: The computational feasibility (total runtime) is measured against the CI limit for a standard 2-core CPU environment (See US-2).
- **SC-003**: The robustness of the model is measured by the variance in R² across the sensitivity sweep of key thresholds over a range of small magnitudes. (See US-3).
- **SC-004**: The validity of structural determinants is measured by the consistency of SHAP feature rankings across different random seeds and the magnitude of performance drop in the perturbation study (See US-3).
- **SC-005**: The data quality is measured by the percentage of rows successfully processed without exclusion due to parsing or calculation errors, with success defined as ≥ 95% (See US-1).

## Assumptions

- The public SN1 kinetic datasets (NIST, Reaxys open subsets, UCI) contain all necessary variables: molecular structure (SMILES), experimental rate constants, and substrate classification.
- The Gasteiger partial charge method and topological indices are computationally tractable on a 2-core CPU runner for the expected dataset size (≤14 GB disk usage), whereas PM is too expensive for the imposed time limit.
- The relationship between molecular structure and SN1 rate constants is primarily driven by electronic and steric features that can be captured by graph-based descriptors and MPNNs.
- The dataset size is sufficient to train a shallow MPNN without severe overfitting., or regularization techniques (dropout) will be sufficient to mitigate overfitting.
- The SN1 reaction mechanism is the dominant pathway for the majority of the dataset entries; entries with competing mechanisms (e.g., SN2) will be filtered or flagged during preprocessing using independent chemical rules.
- The NIST Reaction Database and Reaxys open subsets provide rate constants in a consistent unit system (e.g., s⁻¹ or M⁻¹s⁻¹) that can be standardized without loss of information.
- Semi-empirical quantum chemical calculations are out of scope for the initial MVP due to computational constraints but may be added as an optional feature in future iterations if hardware allows.