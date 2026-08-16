# Feature Specification: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Feature Branch**: `001-predict-sn1-rate-constants`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Predicting Rate Constants of SN1 Reactions from Molecular Structure"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST ingest public SN kinetic datasets from HuggingFace (specifically `DTS-SN1-15-01-2024` and `SN18-All-20240204`), parse SMILES strings into molecular graphs using RDKit, and compute electronic descriptors (Gasteiger partial charges, topological indices) to produce a clean, stratified dataset ready for modeling. The system MUST verify the presence of explicit 'temperature' and 'solvent' columns in the source metadata *before* ingestion. If these columns are missing, the dataset MUST be excluded entirely. The system MUST also verify that explicit 'substrate class' (secondary/tertiary) labels exist in the source data; if missing, the dataset MUST be excluded entirely (no derivation allowed).

**Why this priority**: Without a validated, reproducible dataset containing the required structural and kinetic variables, no modeling can occur. This is the foundational step that determines data quality and variable availability.

**Independent Test**: Can be fully tested by running the ingestion script on a known subset of the `DTS-SN1-15-01-2024` dataset and verifying that the output CSV contains non-null values for all required columns (SMILES, rate constant, substrate class, temperature, solvent) and that electronic descriptors are computed without GPU acceleration.

**Acceptance Scenarios**:

1. **Given** a raw dataset file from HuggingFace containing SMILES, rate constants, and explicit substrate class labels, **When** the ingestion pipeline is executed, **Then** the output is a processed CSV where ≥ 95% of rows have valid molecular graphs and computed electronic descriptors (Gasteiger charges, topological indices).
2. **Given** a dataset with mixed substrate classes (e.g., secondary, tertiary alkyl halides), **When** the stratification step is executed, **Then** the train/validation/test splits (70/15/15) maintain proportional representation of each substrate class with a variance of ≤ 5% from the original distribution (required to maintain distributional fidelity across splits). Stratification is performed ONLY if explicit substrate class labels exist in the source data. If labels are missing, the dataset is excluded.
3. **Given** a dataset row with a missing rate constant, temperature, solvent, or unparseable SMILES, **When** the cleaning step is executed, **Then** the row is logged to an exclusion report and removed from the final training set, ensuring the final dataset has no missing values in predictor or outcome columns.
4. **Given** a dataset where units are inconsistent (e.g., M⁻¹s⁻¹ vs s⁻¹), **When** the cleaning step is executed, **Then** the row is excluded and the exclusion reason is logged.

### User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

The system MUST train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization via random search (≤50 configurations) within a Nested Cross-Validation framework, and evaluate performance against baselines (random, linear regression, and Kernel Ridge Regression) using R² and Mean Absolute Error (MAE). The system MUST enforce deterministic settings (seed=42, `torch.use_deterministic_algorithms(True)`) in `code/config.py` at the line calling `set_seed(42)` prior to data loading. The main script `code/main.py` MUST orchestrate this flow.

**Why this priority**: This is the core research engine. It determines whether structural features alone can predict SN1 rates. The CPU-only constraint is critical for feasibility. Nested CV prevents selection bias from hyperparameter optimization.

**Independent Test**: Can be fully tested by running the training script on the validation set, verifying that the model converges within the 6-hour CI limit, and that the test set R² score is calculated and compared against the linear regression and KRR baselines using Holm-Bonferroni correction.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset, **When** the MPNN training job starts, **Then** the job completes within 6 hours on a 2-core CPU runner without requesting GPU resources, and the final model weights are saved to the artifacts directory.
2. **Given** the trained model and a held-out test set, **When** predictions are generated, **Then** the system outputs R² and MAE metrics, and a bootstrap-based comparison (sufficient resamples, fixed seed) confirms whether the MPNN performance is statistically significantly better than the linear regression and KRR baselines (p < 0.05 after Holm-Bonferroni correction) (required to establish statistical significance of model improvement).
3. **Given** the hyperparameter search space (learning rate, hidden dimension, dropout), **When** the random search completes (≤50 configurations), **Then** the system selects the configuration with the highest validation R² from a set of sampled configurations and logs the top configurations with their respective metrics. The outer loop of the Nested CV must use scaffold splitting to ensure generalization to unseen chemistry.

### User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

The system MUST generate feature importance analysis (using SHAP or attention weights) to identify structural attributions of rate, perform a sensitivity analysis on any decision thresholds or model hyperparameters to ensure robustness, and validate findings via perturbation studies. The system MUST frame SHAP results as "model attributions" and "associational" patterns, explicitly forbidding causal language (e.g., "determinants", "causes").

**Why this priority**: Understanding *why* the model makes predictions is as important as the prediction accuracy itself for scientific validity. Sensitivity analysis ensures the findings are not artifacts of arbitrary parameter choices.

**Independent Test**: Can be fully tested by generating a SHAP summary plot, a sensitivity report that sweeps a key parameter, and a perturbation study that removes top features to verify importance.

**Acceptance Scenarios**:

1. **Given** a trained MPNN model, **When** the interpretability module runs, **Then** it produces a ranked list of up to 10 structural features (atoms, bonds, or electronic descriptors) contributing most to rate prediction, with a corresponding SHAP summary plot. The output MUST NOT use causal language.
2. **Given** a specific threshold or hyperparameter (e.g., a cutoff for descriptor inclusion), **When** the sensitivity analysis sweeps the value over a range of small magnitudes, **Then** the system reports the resulting variation in R² and MAE, confirming that the model's performance does not degrade significantly across the sweep (required to verify model stability against small perturbations in regularization thresholds and intermediate values).
3. **Given** the final model, **When** the collinearity diagnostic is run on the predictors, **Then** the system identifies any pairs of distinct descriptor classes (e.g., topological vs. quantum) with a Variance Inflation Factor (VIF) > 5 and flags them for descriptive joint analysis (Gasteiger charges are excluded as they are derived from topology).
4. **Given** the top features identified by SHAP, **When** the perturbation study runs, **Then** the system removes these features from the input and measures the drop in R², confirming that the importance scores correlate with predictive performance (serves as a robustness check).

### Edge Cases

- What happens when the dataset contains molecules with no carbocation intermediate potential (e.g., primary alkyl halides that strictly follow SN2)? The system MUST filter these outliers during preprocessing using an independent chemical rule: filter if substrate class is explicitly labeled primary in the source. If explicit substrate class labels are missing, the dataset is excluded entirely. No proxy (e.g., steric hindrance index) is used.
- How does the system handle SMILES strings with undefined stereochemistry or ambiguous bond orders? The system MUST either standardize these using RDKit's canonicalization rules or exclude the row with a specific error code indicating "ambiguous structure."
- What happens if the Gasteiger charge calculation fails for a specific molecule due to convergence issues? The system MUST log the failure, exclude the molecule from the training set, and record the exclusion reason to maintain data integrity.
- What happens if the dataset lacks temperature or solvent metadata? The system MUST exclude the entire dataset from training and log a fatal error (see FR-009).
- What happens if the dataset size is < 500 rows? The system MUST frame the study as a feasibility demonstration and report the limitation, rather than attempting to train a complex MPNN and claiming underpowering post-hoc.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and parse SN1 kinetic data from HuggingFace datasets `DTS-SN1-15-01-2024` and `SN18-All-20240204`, extracting SMILES and rate constants, and compute electronic descriptors (Gasteiger charges, topological indices) using RDKit without GPU acceleration. The system MUST verify the presence of 'temperature', 'solvent', and explicit 'substrate class' columns. NIST/Reaxys/UCI are excluded because the provided URLs in the verified block are non-kinetic (cybersecurity embeddings). (See US-1).
- **FR-002**: System MUST split the dataset into train/validation/test sets, stratified by explicit substrate class labels to prevent data leakage. If labels are missing, the dataset is excluded. No derivation of substrate class from SMILES is permitted. (See US-1).
- **FR-003**: System MUST train a Message Passing Neural Network (MPNN) with a fixed architecture (pre-defined complexity) on 2-core CPU hardware, optimizing hyperparameters via random search (≤50 configurations) using Nested Cross-Validation with scaffold splitting for the outer loop. The model complexity is NOT adjusted post-hoc based on dataset size. (See US-2).
- **FR-004**: System MUST evaluate model performance using R² and MAE, comparing results against random, linear regression, and Kernel Ridge Regression (KRR) baselines via bootstrap-based comparison (a large number of resamples, with a fixed random seed) of mean squared errors, with Holm-Bonferroni correction applied to all comparisons (MPNN vs Random/Linear/KRR on R²/MAE). The Linear Regression baseline MUST use the same Gasteiger/topological descriptors as the MPNN inputs. (See US-2).
- **FR-005**: System MUST generate feature importance rankings using SHAP values or attention weights to identify structural attributions of SN1 rates. The output MUST NOT use causal language (e.g., "determinants", "causes"). Results MUST be framed as "model attributions" and "associational patterns". (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping top-k descriptors across a range of k values. selected by absolute SHAP value and report performance variance. (See US-3).
- **FR-007**: System MUST run a collinearity diagnostic (VIF) on distinct descriptor classes (e.g., topological vs. quantum) and flag any pairs with VIF > 5. Gasteiger charges are excluded from this test as they are derived from topology. The system MUST output a JSON report with keys: "descriptor_a", "descriptor_b", "vif_score", "flag_reason". No chemical interpretation dictionary is generated. (See US-3).
- **FR-008**: System MUST perform a perturbation study removing top SHAP features and measure the resulting drop in R² to serve as a robustness check (not causality). (See US-3).
- **FR-009**: System MUST exclude the entire dataset from training and log a fatal error if the primary dataset lacks temperature, solvent, or explicit substrate class metadata. (See US-1).

### Key Entities

- **Molecule**: Represents a chemical substrate with attributes: SMILES string, substrate class (secondary/tertiary only), and computed electronic descriptors.
- **ReactionRate**: Represents the experimental outcome with attributes: rate constant value, temperature, solvent, and source database ID.
- **ModelConfiguration**: Represents a specific set of hyperparameters (learning rate, hidden dimension, dropout) and the resulting performance metrics.
- **CollinearPair**: Represents a pair of collinear descriptors with attributes: descriptor_a (string), descriptor_b (string), vif_score (float), flag_reason (string).
- **Descriptor**: Represents a computed molecular feature (e.g., Gasteiger charge, topological index) with attributes: name, value, type (topological/quantum/electronic), and source_method.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The predictive accuracy (R²) of the MPNN on the held-out test set must be > 0.05 higher than the linear regression baseline (MPNN_R2 - Linear_R2 > 0.05) with p < 0.05 after Holm-Bonferroni correction (See US-2).
- **SC-002**: The computational feasibility (total runtime) is measured against the CI limit for a standard 2-core CPU environment (See US-2).
- **SC-003**: The robustness of the model is measured by the variance of R² across the sensitivity sweep of key thresholds over a range of small magnitudes. The variance must be < 0.01 (See US-3).
- **SC-004**: The validity of structural attributions is measured by the consistency of SHAP feature rankings across different random seeds and the magnitude of performance drop in the perturbation study. This MUST be measured on the full available dataset. If the full dataset is computationally feasible (defined as < 5.5 hours training time on 2-core CPU), it MUST be used. If not, the largest feasible subset (max rows within 5.5 hours) MUST be used (See US-3).
- **SC-005**: The data quality is measured by the percentage of rows successfully processed without exclusion due to parsing or calculation errors, with success defined as ≥ 95% (See US-1).

## Assumptions

- The HuggingFace datasets `DTS-SN1-15-01-2024` and `SN18-All-20240204` contain all necessary variables: molecular structure (SMILES), experimental rate constants, explicit substrate class labels, temperature, and solvent. The dataset size is [deferred] (source: DTS-SN1-15-01-2024 repository URL). If the actual count is <500, the study is a feasibility demonstration.
- The Gasteiger partial charge method and topological indices are computationally tractable on a 2-core CPU runner for the expected dataset size ([deferred] rows, ≤14 GB disk usage), whereas PM is too expensive for the imposed time limit.
- The relationship between molecular structure and SN1 rate constants is primarily driven by electronic and steric features that can be captured by graph-based descriptors and MPNNs.
- The dataset size is sufficient to train a shallow MPNN without severe overfitting, or regularization techniques (dropout) will be sufficient to mitigate overfitting. If N < 500, the study is framed as a feasibility demonstration.
- The SN1 reaction mechanism is the dominant pathway for the majority of the dataset entries; entries with competing mechanisms (e.g., SN2) will be filtered or flagged during preprocessing using explicit source labels (no proxy derivation).
- The HuggingFace datasets provide rate constants in a consistent unit system (e.g., s⁻¹ or M⁻¹s⁻¹). If units are inconsistent (e.g., M⁻¹s⁻¹ vs s⁻¹), the row is excluded and the exclusion reason is logged.
- Semi-empirical quantum chemical calculations are out of scope for the initial MVP due to computational constraints but may be added as an optional feature in future iterations if hardware allows.
- NIST/Reaxys/UCI are excluded as primary sources because the provided URLs in the project's verified block are non-kinetic (cybersecurity embeddings). HuggingFace is the sole primary source.