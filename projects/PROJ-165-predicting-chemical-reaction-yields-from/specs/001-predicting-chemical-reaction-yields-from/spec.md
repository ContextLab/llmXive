# Feature Specification: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Feature Branch**: `001-predict-reaction-yields-from-spectra`  
**Created**: 2026-08-14  
**Status**: Draft  
**Input**: User description: "Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Preprocessing, and Leakage-Free Splitting (Priority: P1)

**User Journey**: A researcher initiates the data pipeline to ingest the USPTO-50k reaction dataset. The system programmatically queries the NIST Chemistry WebBook and PubChem APIs to retrieve experimentally measured IR and ¹H-NMR spectra for reactants and products. It filters the dataset to retain only reactions with successfully retrieved real experimental spectra for BOTH modalities (IR and NMR), resamples all spectra to a fixed grid defined by the `SpectralGrid` entity (IR: 400–4000 cm⁻¹ at 1 cm⁻¹ steps, NMR: 0–10 ppm at 0.01 ppm steps), normalizes intensities, and encodes reaction conditions (solvent, temperature) as feature vectors. The system performs a Partial Least Squares (PLS) regression analysis to quantify the shared variance between the binary fingerprint vector and continuous spectral data. Crucially, the system splits the data into training, validation, and test sets using a **scaffold split** (Bemis-Murcko) as the primary strategy to ensure generalization across chemically distinct scaffolds, AND performs a secondary reaction-template-based split check to verify zero overlap of reaction centers. The system validates the split using MD5 hashing of template IDs to prevent leakage.

**Why this priority**: This is the foundational step. Without real experimental data retrieval, rigorous leakage prevention, multi-modal verification, and standardized preprocessing, the subsequent model training and scientific claims regarding "independent predictive signal" are invalid. The pivot to simulated data is explicitly excluded from the primary scientific claim in this spec to address the "FABRICATED-RESULT" concern; the spec requires real data.

**Independent Test**: The pipeline executes on the USPTO-50k subset, producing three distinct CSV/Parquet files (train, val, test) and a `leakage_report.json` confirming zero template overlap (intersection count = 0) and a scaffold overlap check. The system must also generate an `ingestion_log.json` detailing the number of successful API retrievals versus failures, a `vif_report.json` (now `pls_variance_report.json`) listing variance proportions, and a `data/validation_status.json` confirming dataset size ≥ 50 and failure rate < 80%.

**Acceptance Scenarios**:

1. **Given** the USPTO-50k SMILES list, **When** the ingestion script runs, **Then** the system queries NIST/PubChem and retains only samples where *both* reactant and product experimental IR and NMR spectra are successfully retrieved and stored. If the final dataset size is < 50 samples OR the retrieval failure rate exceeds 80%, the system halts with `DATA_INSUFFICIENT`.
2. **Given** the raw spectra, **When** the preprocessing step runs, **Then** all IR spectra are resampled to the standard range (400–4000 cm⁻¹) and NMR to the typical chemical shift range (0–10 ppm) as defined by the `SpectralGrid` entity defaults, with uniform point counts appropriate for each modality, with intensities normalized to unit variance.
3. **Given** the split indices, **When** the scaffold overlap check runs, **Then** the Bemis-Murcko scaffolds in the training set are distinct from those in the test set. A secondary check confirms zero overlap of reaction template IDs between train and test.
4. **Given** the preprocessed data, **When** the PLS analysis runs, **Then** the system computes the proportion of spectral variance explained by the fingerprint vector using PLS regression and flags if > 50% (indicating high redundancy).

---

### User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2)

**User Journey**: A researcher triggers the training job on the preprocessed dataset. The system trains a PyTorch multi-head self-attention model that accepts **separate** inputs for IR spectra, NMR spectra, and ECFP4 fingerprint vectors. Each modality is processed by a dedicated encoder branch (1D CNN for spectra, linear projection for fingerprints) before the outputs are fused along the feature dimension into a single attention input. The training runs on a CPU-only environment (GitHub Actions free tier) for a maximum of 15 epochs with early stopping (patience=3) on validation RMSE. The system saves the model weights, training logs, and a `state/compute_manifest.json` recording the exact random seeds and hardware constraints used.

**Why this priority**: This implements the core hypothesis. It generates the primary results required to answer the research question. The constraint to run on CPU without GPU ensures the project remains feasible within the CI environment.

**Independent Test**: The training script executes successfully on a CPU-only runner, producing a saved model file (`model.pth`) and a `training_log.csv` showing a decreasing validation loss. The total execution time must be ≤ 6 hours.

**Acceptance Scenarios**:

1. **Given** the preprocessed training set, **When** the model training job starts, **Then** the model converges (validation loss decreases) and completes within the 6-hour GitHub Actions CPU limit.
2. **Given** the trained model, **When** it is evaluated on the validation set, **Then** it produces a numerical yield prediction (0–100) for every input sample without CUDA errors.
3. **Given** a specific random seed (e.g., 42), **When** the training is re-run with the same seed, **Then** the resulting model weights and validation metrics are identical (deterministic reproducibility).

---

### User Story 3 - Model Evaluation, Statistical Significance, and Interpretability (Priority: P3)

**User Journey**: A researcher evaluates the trained model against three baselines: (1) Fingerprint-only (ECFP4), (2) Spectrum-only (concatenated IR+NMR), and (3) Condition-only. The system computes RMSE, MAE, and R² for all models, performs a Wilcoxon signed-rank test on absolute errors to assess significance, and generates attention heatmaps. The system also runs a permutation test (shuffling yield labels 100 times) to verify the model is not learning noise. The system retrieves raw spectral data from the NIST Chemistry WebBook, performs peak detection, and validates that the model's top-attended spectral peaks align with known functional group frequencies within defined tolerances. Additionally, the system runs a linear baseline (Ridge Regression, alpha=1.0) on spectra alone and compares its performance to the PLS variance metrics to confirm the spectral signal is not redundant with fingerprints.

**Why this priority**: This delivers the scientific insight required by the research question: quantifying the "independent predictive signal" and identifying "specific spectral regions." It also validates the statistical robustness of the findings.

**Independent Test**: The evaluation script runs on the test set, outputs a comparison table of metrics, reports a p-value from the statistical test, and generates an attention heatmap image. The permutation test must show a performance drop to near-random levels (R² < 0.05 of target variance).

**Acceptance Scenarios**:

1. **Given** the test set predictions from the attention model and the baselines, **When** the evaluation script runs, **Then** it outputs a table comparing RMSE and R², and reports a p-value from a Wilcoxon signed-rank test on absolute errors.
2. **Given** a specific reaction instance, **When** the attention visualization is generated, **Then** the heatmap highlights the top 95th percentile of spectral weights, and a sensitivity analysis is reported over the set {90th, 95th, 99th percentiles}.
3. **Given** a permutation test where *yield* labels are shuffled 100 times, **When** the model is re-evaluated, **Then** the mean R² across permutations (relative to target variance) is < 0.05, confirming the model learned signal rather than noise.
4. **Given** the attention peaks, **When** the validation step runs, **Then** the system retrieves NIST raw spectra, detects local peaks, and reports whether each top-attended peak aligns with a known functional group frequency within ±100 cm⁻¹ (IR) or ±0.2 ppm (NMR).

---

### Edge Cases

- **Data Scarcity (Real Data)**: If the NIST/PubChem API fails to retrieve experimental spectra for >80% of the USPTO-50k subset **OR** if the final valid dataset size is < 50 samples, the system MUST halt with a `DATA_INSUFFICIENT` error and generate a `data/validation_status.json` flagging the inability to proceed with real data. *Note: This spec does NOT allow a pivot to simulated data for the primary scientific claim to avoid fabricated results.*
- **Data Not Found**: If the NIST/PubChem API fails to retrieve experimental spectra for the required minimum threshold, the system MUST terminate with a `DATA_NOT_FOUND` error.
- **Spectral Mismatch**: If a reaction has IR but no NMR data (or vice versa), the system MUST exclude that sample from the dataset to ensure consistent multi-channel input, logging the exclusion count in `ingestion_log.json`. The model strictly requires both modalities.
- **Out-of-Distribution**: If the test set contains reaction templates chemically distinct from the training set (despite template splitting), the model should flag high prediction uncertainty. The evaluation report must include a `scaffold_generalization_score` comparing performance on novel Bemis-Murcko scaffolds.

## Requirements

### Functional Requirements

- **FR-001**: System MUST preprocess raw spectral data by resampling to a fixed grid defined by the `SpectralGrid` entity (IR: 400–4000 cm⁻¹ at 1 cm⁻¹ steps, NMR: 0–10 ppm at 0.01 ppm steps), normalizing to unit variance, and encoding reaction conditions (solvent, catalyst, temperature) as input vectors (See US-1).
- **FR-002**: System MUST split the dataset into training, validation, and test sets ensuring **zero overlap of Bemis-Murcko scaffolds** between splits as the primary validation strategy. A secondary check MUST verify zero overlap of reaction template IDs between splits. Both constraints apply to the source reaction SMILES and must be verified via MD5 hashing of template IDs (See US-1).
- **FR-003**: System MUST implement a multi-head self-attention neural network with multiple attention heads that accepts **separate** inputs for IR spectral tensors, NMR spectral tensors, and ECFP4 fingerprint vectors. Each input type MUST be processed by a dedicated encoder branch before fusion along the feature dimension (See US-2).
- **FR-004**: System MUST train the model using the Adam optimizer with a learning rate of 1e-3 and batch size of 32, running for a maximum of 15 epochs with early stopping on validation RMSE (patience=3). The model architecture MUST use embedding_size=128, hidden_dim=256, and 4 attention heads to ensure the batch size of 32 fits within 7GB RAM (See US-2).
- **FR-005**: System MUST compute and report RMSE, MAE, and R² metrics for the attention model, a fingerprint-only baseline, a spectrum-only baseline, and a condition-only baseline on the test set (See US-3).
- **FR-006**: System MUST perform a statistical significance test on the absolute errors of the attention model versus the best baseline using the Wilcoxon signed-rank test (See US-3).
- **FR-007**: System MUST generate attention weight visualizations mapping the spectral axis to highlight regions with the highest predictive contribution (See US-3).
- **FR-008**: System MUST execute a permutation test where *yield* labels are shuffled 100 times to verify the model is not learning spurious correlations. The mean R² of the permuted models (relative to target variance) MUST be < 0.05 (See US-3).
- **FR-009**: System MUST define the attention visualization threshold as a high percentile of weights by default, and perform a sensitivity analysis over the set of high percentiles {90th, 95th, 99th} to ensure robustness of identified regions (See US-3).
- **FR-010**: System MUST validate the model's predictive performance against an independent experimental dataset (e.g., a held-out subset from a different literature source). If no such external independent dataset exists, the system MUST document this limitation in the final report but MUST NOT substitute simulated data; the project proceeds with internal scaffold-based split validation ONLY if the dataset size ≥ 50 and failure rate < 80% (See US-1).
- **FR-011**: System MUST explicitly encode reaction conditions (solvent, catalyst, temperature) as input features to prevent confounding by reaction environment when splitting by template (See US-1).
- **FR-012**: System MUST retrieve **raw spectral data** from the NIST Chemistry WebBook API endpoint `/webbook/v1/compound/` using the compound's InChIKey (derived from SMILES). The system MUST perform local peak detection on the retrieved spectrum and validate that the model's top-attended peaks align with known functional group frequencies within ±100 cm⁻¹ (IR) or ±0.2 ppm (NMR). If no spectrum is found for a specific compound, that sample is excluded from the validation set for that functional group (See US-3).
- **FR-013**: System MUST correlate attention-weighted spectral features with known chemical shifts from NIST (external validation) by comparing **detected peaks in the input spectrum** against reference frequencies, ensuring the model learned the spectral signature, not just the SMILES structure (See US-3).
- **FR-014**: System MUST use MD5 hashing of reaction template IDs to deterministically verify zero overlap between splits (See FR-002).
- **FR-015**: System MUST compute the proportion of spectral variance explained by the fingerprint vector using Partial Least Squares (PLS) regression and flag if > 50% to detect lack of independent variance (See US-1).
- **FR-016**: System MUST verify that spectra contain independent predictive signal by comparing the PLS variance proportion (from FR-015) with the performance gain of the Attention model over the Fingerprint-only baseline. If PLS variance > 50% but the Attention model gain is negligible, the system MUST flag the spectral signal as redundant (See US-3).
- **FR-017**: System MUST perform a scaffold split (Bemis-Murcko) to verify generalization across chemically distinct scaffolds, acknowledging that template splitting alone is insufficient for full chemical independence (See US-1).
- **FR-018**: System MUST apply a Bonferroni correction to p-values derived from the 3 specific comparisons: (1) Attention vs. Fingerprint-only, (2) Attention vs. Spectrum-only, and (3) Attention vs. Condition-only, to control the family-wise error rate (See US-3).

### Key Entities

- **ReactionSample**: Represents a single chemical reaction instance. Key attributes: `reaction_smiles`, `yield_percent`, `ir_spectrum` (array), `nmr_spectrum` (array), `rfp` (ECFP4 vector), `reaction_template_id`, `solvent_id`, `catalyst_id`, `temperature_k`.
- **SpectralGrid**: Defines the standardized domain for spectral data. Key attributes: `type` (IR, NMR), `min_value` (default 400 for IR, 0 for NMR), `max_value` (default 4000 for IR, 10 for NMR), `num_bins`, `resolution` (default 1 for IR, 0.01 for NMR).
- **ModelCheckpoint**: Represents a saved state of the trained model. Key attributes: `epoch`, `validation_rmse`, `weights_path`, `config_hash`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (RMSE) of the attention model is measured against the fingerprint-only baseline and the flattened-spectrum baseline to quantify the independent signal of spectral data (See FR-005). All metrics MUST be computed at runtime from real experimental data; no hardcoded or simulated values are permitted.
- **SC-002**: The statistical significance of the performance improvement is measured against a null hypothesis of no difference using the Wilcoxon signed-rank test on per-sample errors, with Bonferroni correction applied (See FR-006, FR-018).
- **SC-003**: The interpretability of the model is measured by the system's ability to retrieve NIST raw spectra, perform peak detection, and report whether the model's top-attended peaks align with known frequencies using the "nearest neighbor within tolerance" algorithm (±100 cm⁻¹ for IR, ±0.2 ppm for NMR) (See FR-007, FR-012).
- **SC-004**: The robustness of the model against overfitting is measured by the performance drop in the permutation test where yield labels are shuffled, requiring the mean R² of the permuted models (relative to target variance) to be < 0.05 (See FR-008).
- **SC-005**: The computational feasibility is measured by the total execution time on a CPU-only runner, ensuring it completes within 6 hours (See US-2).

## Assumptions

- **Dataset Availability**: It is assumed that a sufficient subset of reactions with paired *real* experimental IR and ¹H-NMR spectra can be retrieved from the NIST Chemistry WebBook and PubChem APIs within the USPTO-50k dataset. If the API retrieval rate is < 50 samples OR the failure rate exceeds 80%, the project is considered infeasible for this specific research question and will be terminated with a `DATA_NOT_FOUND` report.
- **Compute Constraints**: The entire training and evaluation pipeline is assumed to run on a GitHub Actions free-tier runner (limited CPU cores, ~7 GB RAM, no GPU). The model architecture and dataset size are scoped to fit within these constraints.
- **Spectral Normalization**: It is assumed that resampling to a common grid and normalizing to unit variance is sufficient to align spectra from different sources (e.g., different instruments) for model ingestion.
- **Reaction Yield Definition**: It is assumed that the "yield" values in the USPTO-50k dataset are consistent (0–100) and represent the final isolated yield, not conversion or theoretical yield.
- **Template Leakage Prevention**: Splitting by reaction template (reaction center substructure), combined with explicit encoding of reaction conditions, reduces but does not guarantee full chemical environment independence. Scaffold splitting (FR-017) is required to address residual leakage risks.
- **Threshold Justification**: The attention visualization threshold is set to a high percentile of weights by default, with a sensitivity analysis performed over a range of high percentiles to ensure robustness.
- **Multiplicity Correction**: Since the evaluation involves multiple comparisons (attention model vs. multiple baselines), a Bonferroni correction will be applied to the p-values derived from the Wilcoxon tests to control the family-wise error rate.
- **No Simulated Data for Primary Claim**: This project assumes that *real* experimental data is required to validate the hypothesis of "independent predictive signal." Simulated data (DFT) is explicitly excluded from the primary scientific claim to avoid fabricated results; if real data is unavailable, the project scope is invalid.
- **Data Source Validity**: The NIST Chemistry WebBook and PubChem APIs are assumed to be accessible and return valid spectral data for the queried compounds.
- **No Fabricated Metrics**: All performance metrics (RMSE, R², p-values) MUST be computed at runtime from real experimental data. No hardcoded, simulated, or placeholder metric values are permitted in the final report. State logs in `state/` MUST record the actual computation source.