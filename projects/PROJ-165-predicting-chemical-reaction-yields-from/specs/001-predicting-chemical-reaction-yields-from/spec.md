# Feature Specification: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Feature Branch**: `001-predict-reaction-yields-from-spectra`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Preprocessing, and Leakage-Free Splitting (Priority: P1) (See SC-007)

**User Journey**: A researcher initiates the data pipeline to ingest the USPTO reaction dataset. The system programmatically queries the NIST Chemistry WebBook (via JCAMP‑DX downloads) and PubChem APIs to retrieve experimentally measured IR, ¹H‑NMR, **and Raman** spectra for reactants and products. It filters the dataset to retain only reactions with successfully retrieved real experimental spectra for **all three** modalities (IR, NMR, Raman), resamples all spectra to a fixed grid defined by the `SpectralGrid` entity (IR: 400–4000 cm⁻¹ at 1 cm⁻¹ steps, NMR: 0–10 ppm at 0.01 ppm steps, Raman: 400–4000 cm⁻¹ at 1 cm⁻¹ steps), normalizes intensities, and encodes reaction conditions (solvent, catalyst, temperature) as feature vectors. The system splits the data into training, validation, and test sets using a **scaffold split** (Bemis‑Murcko) as the primary strategy to ensure generalization across chemically distinct scaffolds, AND performs a secondary reaction‑template‑based overlap check to verify zero overlap of reaction centers. The system validates the split using MD5 hashing of template IDs to prevent leakage.

**Why this priority**: This is the foundational step. Without real experimental data retrieval, rigorous leakage prevention, multi‑modal verification, and standardized preprocessing, the subsequent model training and scientific claims regarding "independent predictive signal" are invalid. The spec explicitly excludes simulated data for the primary scientific claim to avoid fabricated results.

**Independent Test**: The pipeline executes on the USPTO-50k subset, producing three distinct CSV/Parquet files (train, val, test) and a `leakage_report.json` confirming zero template overlap (intersection count = 0) and a scaffold overlap check. The system must also generate an `ingestion_log.json` detailing the number of successful API retrievals versus failures, and a `data/validation_status.json` confirming dataset size ≥ 50 and failure rate < 80 %.

**Acceptance Scenarios**:

1. **Given** the USPTO-50k SMILES list, **When** the ingestion script runs, **Then** the system queries NIST/PubChem and retains only samples where *all three* reactant and product experimental IR, NMR, **and Raman** spectra are successfully retrieved and stored. If the final dataset size is < 50 samples **or** the retrieval failure rate exceeds 80 %, the system halts with `DATA_INSUFFICIENT`.
2. **Given** the raw spectra, **When** the preprocessing step runs, **Then** all IR and Raman spectra are resampled to the standard range (400–4000 cm⁻¹) and NMR to the typical chemical shift range (0–10 ppm) as defined by the `SpectralGrid` entity defaults, with uniform point counts appropriate for each modality, and intensities normalized to unit variance.
3. **Given** the split indices, **When** the scaffold overlap check runs, **Then** the Bemis‑Murcko scaffolds in the training set are distinct from those in the test set. A secondary check confirms zero overlap of reaction template IDs between train and test (reported in `leakage_report.json`).

---

### User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2) (See SC-008)

**User Journey**: A researcher triggers the training job on the preprocessed dataset. The system trains a PyTorch multi‑head self‑attention model that accepts **separate** inputs for IR spectra, NMR spectra, Raman spectra, and ECFP4 fingerprint vectors. Each modality is processed by a dedicated encoder branch (1D CNN for spectra, linear projection for fingerprints) before the outputs are fused along the feature dimension into a single attention input. The training runs on a CPU‑only environment (GitHub Actions free tier) for a maximum of 15 epochs with early stopping (patience = 3) on validation RMSE. The system saves the model weights, training logs, and a `state/compute_manifest.json` recording the exact random seeds, deterministic‑algorithm flag, and hardware constraints used.

**Why this priority**: This implements the core hypothesis. It generates the primary results required to answer the research question. The constraint to run on CPU without GPU ensures the project remains feasible within the CI environment.

**Independent Test**: The training script executes successfully on a CPU‑only runner, producing a saved model file (`model.pth`) and a `training_log.csv` showing a decreasing validation loss. The total execution time must be ≤ 6 hours.

**Acceptance Scenarios**:

1. **Given** the preprocessed training set, **When** the model training job starts, **Then** the model converges (validation loss decreases) and completes within the 6‑hour GitHub Actions CPU limit.
2. **Given** the trained model, **When** it is evaluated on the validation set, **Then** it produces a numerical yield prediction (0–100) for every input sample without CUDA errors.
3. **Given** a specific random seed (e.g., 42), **When** the training is re‑run with the same seed and deterministic‑algorithm flag enabled, **Then** the resulting model weights and validation metrics are identical (deterministic reproducibility). *(See FR-019)*

---

### User Story 3 - Model Evaluation, Statistical Significance, and Interpretability (Priority: P3) (See SC-009)

**User Journey**: A researcher evaluates the trained model against three baselines: (1) Fingerprint‑only (ECFP4), (2) Spectrum‑only (concatenated IR+NMR+Raman), and (3) Condition‑only. The system computes RMSE, MAE, and R² for all models, performs **two** Wilcoxon signed‑rank tests: (a) spectrum‑only vs. fingerprint‑only, and (b) attention model vs. each baseline, applying a Bonferroni‑corrected significance threshold α = 0.0167. It generates attention heatmaps. The system also runs a permutation test (re‑training the model on shuffled yield labels 100 times) to verify the model is not learning noise. The system retrieves raw spectral data from the NIST Chemistry WebBook, performs peak detection, and validates that the model's top‑attended spectral peaks align with known functional‑group frequencies from an **independent** reference table (±100 cm⁻¹ for IR/Raman, ±0.2 ppm for NMR). Additionally, the system runs a linear baseline (Ridge Regression, α = 1.0) on spectra alone and compares its performance to the PLS variance metrics to confirm the spectral signal is not redundant with fingerprints.

**Why this priority**: This delivers the scientific insight required by the research question: quantifying the "independent predictive signal" and identifying "specific spectral regions." It also validates the statistical robustness of the findings.

**Independent Test**: The evaluation script runs on the test set, outputs a comparison table of metrics, reports p‑values from the two Wilcoxon tests (both < 0.0167), and generates an attention heatmap image. The permutation test must show a performance drop to near‑random levels (mean R² < 0.05 of target variance).

**Acceptance Scenarios**:

1. **Given** the test set predictions from the attention model and the baselines, **When** the evaluation script runs, **Then** it outputs a table comparing RMSE and R², and reports p‑values from the two Wilcoxon signed‑rank tests (α = 0.0167). *(See FR-006, FR-018)*
2. **Given** a specific reaction instance, **When** the attention visualization is generated, **Then** the heatmap highlights the top 95th percentile of spectral weights, and a sensitivity analysis is reported over the set {90th, 95th, 99th percentiles}. *(See FR-009)*
3. **Given** a permutation test where *yield* labels are shuffled 100 times, **When** the model is re‑trained on each shuffled set and re‑evaluated, **Then** the mean R² across permutations (relative to target variance) is < 0.05, confirming the model learned signal rather than noise. *(See FR-008)*
4. **Given** the attention peaks, **When** the validation step runs, **Then** the system retrieves NIST raw spectra, detects local peaks, and reports whether each top‑attended peak aligns with a known functional‑group frequency within ±100 cm⁻¹ (IR/Raman) or ±0.2 ppm (NMR) using an external reference table. *(See FR-012, FR-013)*

---

### Edge Cases

- **Data Scarcity (Real Data)**: If the NIST/PubChem API fails to retrieve experimental spectra for > 80 % of the USPTO-50k subset **or** if the final valid dataset size is < 50 samples, the system MUST halt with a `DATA_INSUFFICIENT` error and generate a `data/validation_status.json` flagging the inability to proceed with real data. *Note: This spec does NOT allow a pivot to simulated data for the primary scientific claim to avoid fabricated results.*
- **Data Not Found**: (Consolidated with Data Scarcity – see above.)
- **Spectral Mismatch**: If a reaction has any missing modality (IR, NMR, or Raman), the system MUST exclude that sample from the dataset to ensure consistent multi‑channel input, logging the exclusion count in `ingestion_log.json`. The model strictly requires all three modalities.
- **Out‑of‑Distribution**: If the test set contains reaction templates chemically distinct from the training set (despite template splitting), the system reports the degree of scaffold overlap in `leakage_report.json` and flags any samples where the predicted uncertainty (computed via deterministic inference) exceeds a coefficient‑of‑variation threshold of 0.2 in `uncertainty_report.json`. *Justified as a safeguard to highlight predictions that may be unreliable on novel chemistry.*

## Requirements

### Functional Requirements

- **FR-001**: System MUST preprocess raw spectral data by resampling to a fixed grid defined by the `SpectralGrid` entity (IR: 400–4000 cm⁻¹ at 1 cm⁻¹ steps, NMR: 0–10 ppm at 0.01 ppm steps, Raman: 400–4000 cm⁻¹ at 1 cm⁻¹ steps), normalizing to unit variance, and encoding reaction conditions (solvent, catalyst, temperature) as input vectors (See US-1). *Raman inclusion satisfies Constitution VI which mandates Raman handling despite limited coverage.*
- **FR-002**: System MUST split the dataset into training, validation, and test sets ensuring **zero overlap of Bemis‑Murcko scaffolds** between splits as the primary validation strategy. A secondary check MUST verify zero overlap of reaction template IDs between splits. Both constraints apply to the source reaction SMILES and must be verified via MD5 hashing of template IDs (See US-1). *If a strict three‑way zero‑overlap split is infeasible, the system MUST fall back to a split that maximizes scaffold disjointness while maintaining ≥ 10 samples per split and report actual overlap counts in `leakage_report.json` (See FR-021).*
- **FR-003**: System MUST implement a multi‑head self‑attention neural network with multiple attention heads that accepts **separate** inputs for IR spectra, NMR spectra, Raman spectra, and ECFP4 fingerprint vectors. Each input type MUST be processed by a dedicated encoder branch before fusion along the feature dimension into a single attention input (See US-2).
- **FR-004**: System MUST train the model using the Adam optimizer with a learning rate of 1e-3 and batch size of 32, running for a maximum of 15 epochs with early stopping on validation RMSE (patience=3). The model architecture MUST use embedding_size=128, hidden_dim=256, and 4 attention heads to ensure the batch size of 32 fits within 7 GB RAM (See US-2).
- **FR-005**: System MUST compute and report RMSE, MAE, and R² metrics for the attention model, a fingerprint‑only baseline, a **spectrum‑only baseline (concatenated IR+NMR+Raman)**, and a condition‑only baseline on the test set (See US-3).
- **FR-006**: System MUST perform **two** Wilcoxon signed‑rank tests on absolute errors: (a) spectrum‑only vs. fingerprint‑only, and (b) attention model vs. each baseline, to isolate the contribution of spectral information (See US-3).
- **FR-007**: System MUST generate attention weight visualizations mapping the spectral axis to highlight regions with the highest predictive contribution (See US-3).
- **FR-008**: System MUST execute a permutation test where *yield* labels are shuffled 100 times, **re‑training** the model on each shuffled set, and report that the mean R² of the permuted models (relative to target variance) is < 0.05 (See US-3).
- **FR-009**: System MUST define the attention visualization threshold as a high percentile of weights by default, and perform a sensitivity analysis over the set of high percentiles {90th, 95th, 99th} to ensure robustness of identified regions (See US-3).
- **FR-010**: System MUST validate the model's predictive performance against an **independent experimental dataset** (e.g., the Reaxys experimental reaction dataset with measured yields) **if such a dataset is available**; otherwise, it MUST generate `external_validation_report.json` with a “unavailable” flag and proceed with internal scaffold‑based split validation ONLY if the dataset size ≥ 50 and failure rate < 80 % (See US-1).
- **FR-011**: System MUST explicitly encode reaction conditions (solvent, catalyst, temperature) as input features to prevent confounding by reaction environment when splitting by template (See US-1).
- **FR-012**: System MUST retrieve **raw spectral data** from the NIST Chemistry WebBook via JCAMP‑DX file downloads using the compound's InChIKey (derived from SMILES) and, where available, from PubChem spectral files. The system MUST perform local peak detection on the retrieved spectrum. *(Reference table used for validation is an external literature compilation, not derived from the training data.)* (See US-3)
- **FR-013**: System MUST correlate attention‑weighted spectral features with known functional‑group frequencies from an **independent reference table** (e.g., SDBS or literature compilations) by comparing detected peaks in the input spectrum against these references, ensuring the model learned the spectral signature, not just the SMILES structure (See US-3).
- **FR-014**: System MUST use MD5 hashing of reaction template IDs to deterministically verify zero overlap between splits (See FR-002).
- **FR-016**: System MUST flag redundancy when the Attention model gain over the fingerprint‑only baseline is **negligible**, defined as an RMSE improvement < 5 % **or** a Bonferroni‑corrected p‑value > 0.05 (See US-3).
- **FR-017**: System MUST perform a scaffold split (Bemis‑Murcko) to verify generalization across chemically distinct scaffolds, acknowledging that template splitting alone is insufficient for full chemical environment independence (See US-1).
- **FR-018**: System MUST apply a Bonferroni correction to p‑values derived from the 3 specific comparisons (1) Attention vs. Fingerprint‑only, (2) Attention vs. Spectrum‑only, (3) Attention vs. Condition‑only, to control the family‑wise error rate, using a significance threshold α = 0.0167 (0.05/3) (See US-3).
- **FR-019**: System MUST pin random seeds and record them in `state/compute_manifest.json`; re‑running with the same seed **and** enabling deterministic PyTorch algorithms (`torch.use_deterministic_algorithms(True)`) MUST reproduce identical model weights and validation metrics (See US-2).
- **FR-020**: *(Removed per scope concern – functionality for scaffold_generalization_score omitted.)*
- **FR-021**: System MUST attempt a zero‑overlap scaffold split; if infeasible, it MUST report actual scaffold and template overlap counts in `leakage_report.json` and proceed with a split that maximizes disjointness while maintaining ≥ 10 samples per split (See internal consistency‑63da4bbb).
- **FR-022**: System MUST retrieve reaction yield values from the Open Reaction Database (ORD) linked to USPTO patents; reactions without a documented yield are excluded from the dataset (See US-1). *(See US-1)*
- **FR-023**: *(Removed per scope concern – Monte‑Carlo dropout uncertainty estimation omitted.)*
- **FR-024**: System MUST run a static‑analysis audit (e.g., via `ruff` rule `no-hardcoded-metrics`) on the codebase to verify that no hard‑coded metric values are present (supports SC-001 testability).

### Key Entities

- **ReactionSample**: Represents a single chemical reaction instance. Key attributes: `reaction_smiles`, `yield_percent`, `ir_spectrum` (array), `nmr_spectrum` (array), `raman_spectrum` (array), `rfp` (ECFP4 vector), `reaction_template_id`, `solvent_id`, `catalyst_id`, `temperature_k`.
- **SpectralGrid**: Defines the standardized domain for spectral data. Key attributes: `type` (IR, NMR, Raman), `min_value` (default 400 for IR/Raman, 0 for NMR), `max_value` (default 4000 for IR/Raman, 10 for NMR), `num_bins`, `resolution` (default 1 for IR/Raman, 0.01 for NMR). *Raman spectra are now included to satisfy Constitution VI.*
- **ModelCheckpoint**: Represents a saved state of the trained model. Key attributes: `epoch`, `validation_rmse`, `weights_path`, `config_hash`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (RMSE) of the attention model is measured against the fingerprint‑only baseline and the **spectrum‑only baseline (concatenated IR+NMR+Raman)** to quantify the independent signal of spectral data (See FR-005). All metrics MUST be computed at runtime from real experimental data; no hard‑coded or simulated values are permitted. A static‑analysis audit (FR‑024) must verify the absence of hard‑coded metric literals.
- **SC-002**: The statistical significance of the performance improvement is measured against a null hypothesis of no difference using the Wilcoxon signed‑rank test on per‑sample errors, with Bonferroni correction applied (α = 0.0167) (See FR-006, FR-018).
- **SC-003**: The interpretability of the model is measured by the system's ability to retrieve NIST raw spectra, perform peak detection, and report whether the model's top‑attended peaks align with known frequencies using the "nearest neighbor within tolerance" algorithm (absolute difference, tie‑break by smallest difference) (±100 cm⁻¹ for IR/Raman, ±0.2 ppm for NMR) against an independent reference table (See FR-007, FR-012, FR-013). The algorithm details are defined in SC-003.
- **SC-004**: The robustness of the model against overfitting is measured by the performance drop in the permutation test where yield labels are shuffled and the model is re‑trained, requiring the mean R² of the permuted models (relative to target variance) to be < 0.05 (See FR-008).
- **SC-005**: The computational feasibility is measured by the total execution time on a CPU‑only runner, ensuring it completes within 6 hours (See US-2).
- **SC-006**: **Data Ingestion Success** – The pipeline must produce a `data/validation_status.json` indicating dataset size ≥ 50 and retrieval failure rate < 80 %; `leakage_report.json` must show zero scaffold and template overlap (or report maximal disjointness if zero‑overlap is infeasible); `ingestion_log.json` must record counts of successful and failed API calls. All three files constitute measurable acceptance for User Story 1.
- **SC-007**: **Training Success** – Validation loss must decrease monotonically for at least three consecutive epochs, final validation RMSE must be recorded, and total wall‑clock time must be ≤ 6 hours. Deterministic reproducibility is verified by re‑running with the same seed and confirming identical `model.pth` and `training_log.csv` (FR‑019).
- **SC-008**: **Evaluation Success** – The evaluation report must include (a) a table of RMSE/MAE/R² for all baselines, (b) two Wilcoxon p‑values both < 0.0167, (c) attention heatmap files, (d) permutation‑test mean R² < 0.05, (e) peak‑alignment verification results for each top‑attended peak, and (f) `external_validation_report.json` indicating whether an independent dataset was used. All items are required for User Story 3.

## Assumptions

- **Dataset Availability**: It is assumed that a sufficient subset of reactions with paired *real* experimental IR, ¹H‑NMR, **and Raman** spectra can be retrieved from the NIST Chemistry WebBook (via JCAMP‑DX) and PubChem APIs within the USPTO‑50k dataset. If the API retrieval rate is < 50 samples **or** the failure rate exceeds 80 %, the project is considered infeasible for this specific research question and will be terminated with a `DATA_INSUFFICIENT` report.
- **Compute Constraints**: The entire training and evaluation pipeline is assumed to run on a GitHub Actions free‑tier runner (limited CPU cores, ~ GB RAM, no GPU). The model architecture and dataset size are scoped to fit within these constraints.
- **Spectral Normalization**: Resampling to a common grid and normalizing to unit variance is assumed sufficient to align spectra from different instruments for model ingestion.
- **Reaction Yield Definition**: Reaction yields are sourced from the Open Reaction Database (ORD) linked to USPTO patents; values are expressed as percentages (0–100) representing isolated yields.
- **Template Leakage Prevention**: Splitting by reaction template (reaction center substructure), combined with explicit encoding of reaction conditions, reduces but does not guarantee full chemical environment independence. Scaffold splitting (FR‑017) is required to address residual leakage risks.
- **Threshold Justification**: The attention visualization threshold is set to a high percentile of weights by default, with a sensitivity analysis performed over a range of high percentiles to ensure robustness.
- **Multiplicity Correction**: Since the evaluation involves multiple comparisons (attention model vs. three baselines), a Bonferroni correction is applied to the p‑values derived from the Wilcoxon tests to control the family‑wise error rate.
- **No Simulated Data for Primary Claim**: This project assumes that *real* experimental data is required to validate the hypothesis of "independent predictive signal" from spectra. Simulated data (e.g., DFT) is explicitly excluded from the primary scientific claim; if real data is unavailable, the project scope is invalid.
- **Data Source Validity**: The NIST Chemistry WebBook (JCAMP‑DX) and PubChem spectral files are assumed to be accessible and return valid spectral data for the queried compounds.
- **Raman Inclusion**: Raman spectra are included despite limited coverage; missing Raman data for a reaction leads to sample exclusion, ensuring modality consistency.
- **No Fabricated Metrics**: All performance metrics (RMSE, R², p‑values) MUST be computed at runtime from real experimental data. No hardcoded, simulated, or placeholder metric values are permitted in the final report. State logs in `state/` MUST record the actual computation source.