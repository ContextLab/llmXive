# Feature Specification: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Feature Branch**: `001-predict-reaction-yields-from-spectra`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**User Journey**: A researcher uploads or selects a dataset of chemical reactions containing SMILES strings, spectroscopic data (IR, Raman, NMR), and reaction conditions (solvent, catalyst, temperature). The system ingests this data, encodes the conditions, resamples all spectra to a standardized wavenumber/chemical shift grid, normalizes intensities, and generates a clean, split-ready dataset with a 70/15/15 train/validation/test partition ensuring no reaction template leakage between sets. The pipeline must also validate against an independent experimental dataset if available.

**Why this priority**: Without a robust, leakage-free data pipeline that accounts for reaction conditions and validates against independent data, no model training or validation is possible. This is the foundational step that enables all subsequent analysis and determines the validity of the research question.

**Independent Test**: The pipeline can be executed on a subset of the USPTO or ZINC data, producing three distinct CSV/Parquet files (train, val, test) and a log confirming the absence of overlapping reaction templates across splits, and verifying that reaction conditions are encoded as features.

**Acceptance Scenarios**:

1. **Given** a raw dataset containing reaction SMILES, raw spectral arrays, and reaction conditions, **When** the preprocessing script is executed, **Then** the output files contain resampled spectra on a common grid (e.g., 400–4000 cm⁻¹), normalized intensities, and encoded condition vectors.
2. **Given** the training and test splits, **When** the reaction template substructures are extracted and compared, **Then** the intersection of templates between the training set and test set is exactly zero.
3. **Given** an independent experimental validation dataset (e.g., from a separate publication), **When** the pipeline processes it, **Then** the system generates a separate evaluation report comparing predictions against this independent ground truth to verify lack of circular validation.

---

### User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2)

**User Journey**: A researcher initiates the training of the attention-based neural network. The system trains the model on the prepared dataset, combining spectral inputs, structural fingerprints, and reaction condition vectors, and saves the model weights and training logs (loss curves) to a reproducible artifact.

**Why this priority**: This implements the core hypothesis that spectroscopic data contains independent predictive signal. It is the primary mechanism for generating the results required to answer the research question.

**Independent Test**: The training script executes successfully on a CPU-only environment, producing a saved model file and a log showing a decreasing validation loss over a defined number of epochs (or early stopping), without requiring GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the preprocessed training set, **When** the model training job starts, **Then** the model converges (validation loss decreases) and completes within the 6-hour GitHub Actions CPU limit.
2. **Given** the trained model, **When** it is evaluated on the validation set, **Then** it produces a numerical yield prediction (0–100) for every input sample.
3. **Given** a random seed configuration, **When** the training is re-run with the same seed, **Then** the resulting model weights and validation metrics are identical (deterministic reproducibility).

---

### User Story 3 - Model Evaluation and Interpretability Analysis (Priority: P3)

**User Journey**: A researcher evaluates the trained model against baselines (fingerprint-only, flattened-spectrum-only, condition-only) and visualizes the attention weights to identify which spectral regions (wavenumbers/chemical shifts) the model deems most predictive of yield, specifically analyzing the correlation between attention peaks and yield residuals.

**Why this priority**: This delivers the scientific insight required by the research question: quantifying the "independent predictive signal" and identifying "specific spectral regions." Without this, the model is a black box with no scientific utility.

**Independent Test**: The evaluation script runs on the test set, outputs RMSE/MAE/R² metrics for all models, performs a paired t-test on errors, and generates an attention heatmap image highlighting specific wavenumber ranges.

**Acceptance Scenarios**:

1. **Given** the test set predictions from the attention model and the baseline models, **When** the evaluation script runs, **Then** it outputs a table comparing RMSE and R², and reports a p-value from a paired t-test on absolute errors.
2. **Given** a specific reaction instance, **When** the attention visualization is generated, **Then** the heatmap highlights the top [deferred] of spectral weights, and a sensitivity analysis is reported over {5%, 10%, 15%} thresholds.
3. **Given** a permutation test where *yield* labels are shuffled, **When** the model is re-evaluated, **Then** the performance drops to near-random levels (e.g., R² < 0.05), confirming the model learned signal rather than noise.

---

### Edge Cases

- **Data Scarcity**: What happens if the experimental spectral dataset (NIST/ZINC) is insufficient to train a meaningful model? The system must pivot to using simulated DFT spectra (MolSpectra) and flag this limitation in the output report.
- **Spectral Mismatch**: How does the system handle reactions where only IR is available but not NMR? The system must either exclude these samples or use a masking mechanism to handle missing channels, ensuring the model architecture does not crash.
- **Out-of-Distribution**: How does the system handle a reaction type in the test set that was not present in the training set (template leakage prevention ensures this, but chemical similarity might still be an issue)? The model should flag high prediction uncertainty or the evaluation should note the performance drop on these specific templates.

## Requirements

### Functional Requirements

- **FR-001**: System MUST preprocess raw spectral data by resampling to a fixed grid (typical IR/Raman ranges, 0–10 ppm for NMR), normalizing to unit variance, and encoding reaction conditions (solvent, catalyst, temperature) as input vectors (See US-1).
- **FR-002**: System MUST split the dataset into training ([deferred]), validation ([deferred]), and test ([deferred]) sets ensuring zero overlap of reaction templates (substructures at the reaction center) between splits (See US-1).
- **FR-003**: System MUST implement a multi-head self-attention neural network that accepts concatenated spectral tensors, ECFP4 fingerprint vectors, and reaction condition embeddings as input (See US-2).
- **FR-004**: System MUST train the model using the Adam optimizer with a learning rate of 1e-3 and batch size of 32, running for a maximum of 10 epochs with early stopping on validation RMSE (See US-2).
- **FR-005**: System MUST compute and report RMSE, MAE, and R² metrics for the attention model, a fingerprint-only baseline, a spectrum-only baseline, and a condition-only baseline on the test set (See US-3).
- **FR-006**: System MUST perform a paired t-test on the absolute errors of the attention model versus the best baseline to determine statistical significance (See US-3).
- **FR-007**: System MUST generate attention weight visualizations mapping the spectral axis to highlight regions with the highest predictive contribution (See US-3).
- **FR-008**: System MUST execute a permutation test where *yield* labels are shuffled to verify the model is not learning spurious correlations or structural priors alone (See US-3).
- **FR-009**: System MUST define the attention visualization threshold as a high percentile of weights by default, and perform a sensitivity analysis over a range of thresholds to ensure robustness of identified regions. (See US-3).
- **FR-010**: System MUST validate the model's predictive performance against an independent experimental dataset (if available) to prevent circular validation and confirm generalizability (See US-1).
- **FR-011**: System MUST explicitly encode reaction conditions (solvent, catalyst, temperature) as input features to prevent confounding by reaction environment when splitting by template (See US-1).

### Key Entities

- **ReactionSample**: Represents a single chemical reaction instance. Key attributes: `reaction_smiles`, `yield_percent`, `ir_spectrum` (array), `nmr_spectrum` (array), `rfp` (ECFP4 vector), `reaction_template_id`, `solvent_id`, `catalyst_id`, `temperature_k`.
- **SpectralGrid**: Defines the standardized domain for spectral data. Key attributes: `type` (IR, Raman, NMR), `min_value`, `max_value`, `num_bins`.
- **ModelCheckpoint**: Represents a saved state of the trained model. Key attributes: `epoch`, `validation_rmse`, `weights_path`, `config_hash`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (RMSE) of the attention model is measured against the fingerprint-only baseline and the flattened-spectrum baseline to quantify the independent signal of spectral data (See FR-005).
- **SC-002**: The statistical significance of the performance improvement is measured against a null hypothesis of no difference using a paired t-test on per-sample errors (See FR-006).
- **SC-003**: The interpretability of the model is measured by the correlation between attention-weighted spectral features and yield residuals (after controlling for fingerprints), requiring a statistically significant correlation (p < 0.05) and that ≥80% of the top 5 attention peaks fall within ±50 cm⁻¹ of literature values for known functional group frequencies (See FR-007).
- **SC-004**: The robustness of the model against overfitting is measured by the performance drop in the permutation test where yield labels are shuffled, requiring R² < 0.05 (See FR-008).
- **SC-005**: The computational feasibility is measured by the total execution time on a CPU-only runner, ensuring it completes within a predefined time limit. (See US-2).

## Assumptions

- **Dataset Availability**: It is assumed that a sufficient subset of reactions with paired experimental or high-fidelity simulated (DFT) spectra can be assembled from USPTO, NIST, ZINC, or MolSpectra within a feasible disk storage limit. If experimental data is insufficient, the project will pivot to simulated data with a clear limitation note.
- **Compute Constraints**: The entire training and evaluation pipeline is assumed to run on a GitHub Actions free-tier runner (limited CPU cores, constrained RAM, no GPU). The model architecture and dataset size are scoped to fit within these constraints.
- **Spectral Normalization**: It is assumed that resampling to a common grid and normalizing to unit variance is sufficient to align spectra from different sources (e.g., different instruments or simulation methods) for model ingestion.
- **Reaction Yield Definition**: It is assumed that the "yield" values in the source datasets are consistent (0–100) and represent the final isolated yield, not conversion or theoretical yield.
- **Template Leakage Prevention**: It is assumed that splitting by reaction template (reaction center substructure), combined with explicit encoding of reaction conditions, effectively prevents data leakage and ensures the model generalizes to new reaction types.
- **Threshold Justification**: The attention visualization threshold is set to the top 10% of weights by default, with a sensitivity analysis performed over {[deferred], [deferred], [deferred]} to ensure robustness.
- **Multiplicity Correction**: Since the evaluation involves multiple comparisons (attention model vs. multiple baselines), a Bonferroni correction will be applied to the p-values derived from the t-tests to control the family-wise error rate.