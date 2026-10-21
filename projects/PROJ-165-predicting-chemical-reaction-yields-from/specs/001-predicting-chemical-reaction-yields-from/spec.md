# Feature Specification: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Feature Branch**: `001-predicting-chemical-reaction-yields-from`  
**Created**: 2026-10-21  
**Status**: Draft  
**Input**: User description: "Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Data Ingestion, Preprocessing, and Leakage‑Free Splitting (Priority: P1) (See FR‑001, FR‑002)

**User Journey**: A researcher runs the ingestion pipeline on the USPTO‑50k reaction list. The system queries the NIST Chemistry WebBook and PubChem APIs to retrieve *experimentally measured* IR (400–4000 cm⁻¹) and ¹H‑NMR (0–10 ppm) spectra for every reactant and product. Only reactions for which **both** spectra are successfully obtained for **all** reactants and the product are retained. The spectra are resampled to a common grid (IR: 1 cm⁻¹ steps; NMR: 0.01 ppm steps) and intensity‑normalized. Reaction conditions (solvent, catalyst, temperature) are encoded as additional feature vectors. The dataset is then split 70/15/15 (train/val/test) using a scaffold‑based split (Bemis‑Murcko) as the primary strategy, with a secondary check that reaction‑template IDs do not overlap across splits. MD5 hashes of template IDs are recorded to guarantee leakage‑free partitioning.

**Why this priority**: Without a rigorously curated, leakage‑free dataset that contains real experimental spectra, any downstream claim about “independent predictive signal” would be unsupported.

**Independent Test**: Execution of the ingestion script produces three parquet files (`train.parquet`, `val.parquet`, `test.parquet`) and a `leakage_report.json` showing zero scaffold and template overlap. An `ingestion_log.json` records the number of successful and failed API calls, and a `validation_status.json` confirms that the final matched‑reaction count is ≥ 300 and the retrieval‑failure rate is < 80 %.

**Acceptance Scenarios**:

1. **Given** the USPTO‑50k SMILES list, **When** the ingestion script runs, **Then** it retains only reactions with complete IR and ¹H‑NMR spectra for every reactant and product, logs the counts, and halts with `DATA_INSUFFICIENT` if the final dataset size is < 300 or failure rate > 80 %.
2. **Given** the raw spectra, **When** the preprocessing step runs, **Then** all IR spectra are resampled to 400–4000 cm⁻¹ at 1 cm⁻¹ intervals and all NMR spectra to 0–10 ppm at 0.01 ppm intervals, with each spectrum normalized to unit variance.
3. **Given** the split indices, **When** the scaffold‑overlap check runs, **Then** the training, validation, and test sets contain disjoint Bemis‑Murcko scaffolds and zero overlapping reaction‑template IDs (reported in `leakage_report.json`).

---

### User Story 2 – Attention‑Based Yield Prediction Model Training (Priority: P2) (See FR‑003, FR‑004, FR‑015)

**User Journey**: The researcher launches the training job on the preprocessed dataset. A PyTorch model applies positional encoding along the spectral axis and a 4‑head self‑attention layer over the concatenated IR + NMR spectra. The attention output is fused with the ECFP4 fingerprint vector via a fully‑connected layer to predict reaction yield (0–[deferred]). Training uses Adam (lr = 1e‑3), batch size = 32, and runs for a maximum of 15 epochs with early stopping (patience = 3) on validation RMSE. The script forces CPU‑only execution (`torch.set_num_threads(2)`) and records all random seeds and deterministic‑algorithm flags.

**Why this priority**: This implements the core hypothesis‑testing component—whether spectra add predictive value beyond structure alone.

**Independent Test**: On a GitHub Actions free‑tier runner, the training script completes within 6 hours, saves `model.pth`, and outputs `training_log.csv` showing monotonically decreasing validation RMSE for at least three consecutive epochs. Re‑running with the same seed and deterministic flag reproduces identical weights and metrics.

**Acceptance Scenarios**:

1. **Given** the training split, **When** the training job starts, **Then** it finishes ≤ 6 hours on a CPU‑only runner and produces `model.pth` and a `training_log.csv` with decreasing validation RMSE.
2. **Given** a fixed random seed (e.g., 42) and deterministic PyTorch settings, **When** the training is re‑executed, **Then** the resulting model file and validation metrics are bit‑identical to the original run.

---

### User Story 3 – Model Evaluation, Statistical Significance, and Interpretability (Priority: P3) (See FR‑005‑FR‑013)

**User Journey**: The researcher evaluates the trained attention model against three baselines on the held‑out test set: (1) Fingerprint‑only (ECFP4), (2) Spectra‑only (concatenated IR + ¹H‑NMR), and (3) Condition‑only (solvent, catalyst, temperature). The script computes RMSE, MAE, and R² for each model, performs two Wilcoxon signed‑rank tests (spectra‑only vs. fingerprint‑only; attention model vs. each baseline) with a Bonferroni‑corrected α = 0.0167, and runs a permutation test (100 label shuffles, retraining each time) to confirm that performance collapses to near‑random (mean R² < 0.05). Attention weights are visualized as heatmaps along the spectral axis; the top‑weighted spectral regions are cross‑checked against an independent functional‑group reference table (±100 cm⁻¹ for IR, ±0.2 ppm for NMR). A sensitivity analysis varies the attention‑weight percentile threshold over {90th, 95th, 99th}.

**Why this priority**: This delivers the quantitative answer to the research question (independent predictive signal) and identifies the specific spectral regions responsible.

**Independent Test**: Execution of the evaluation script produces (a) `metrics.csv` containing RMSE/MAE/R² for all four models, (b) `wilcoxon_results.json` with two p‑values < 0.0167, (c) `permutation_report.json` showing mean R² < 0.05, (d) attention heatmap PNG files, and (e) `peak_alignment_report.json` indicating whether each top‑attended peak aligns with a known functional‑group frequency within the specified tolerance.

**Acceptance Scenarios**:

1. **Given** the test‑set predictions, **When** the evaluation script runs, **Then** it outputs a complete metrics table and two Wilcoxon p‑values both < 0.0167 (Bonferroni‑corrected).
2. **Given** a trained model, **When** the permutation test is executed, **Then** the average R² across the 100 shuffled runs is < 0.05.
3. **Given** the attention weight map, **When** the sensitivity analysis runs over the 90th/95th/99th percentiles, **Then** the identified spectral regions remain stable (≥ 80 % overlap across thresholds).
4. **Given** the top‑attended spectral peaks, **When** the peak‑alignment routine runs, **Then** each peak is matched to a known functional‑group frequency within ±100 cm⁻¹ (IR) or ±0.2 ppm (NMR), and the results are recorded in `peak_alignment_report.json`.

### Edge Cases

- **Data Scarcity**: If fewer than 300 reactions with complete IR + NMR spectra are found, the pipeline aborts with `DATA_INSUFFICIENT` and records the failure in `validation_status.json`. No simulated spectra are used.
- **Missing Modality**: Any reaction lacking either IR or NMR data for any reactant or product is excluded; the exclusion count is logged in `ingestion_log.json`.
- **Out‑of‑Distribution Prediction**: If a test‑set prediction yields a coefficient‑of‑variation > 0.2 (computed from deterministic inference), the instance is flagged in `uncertainty_report.json` but does not halt the overall evaluation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preprocess raw IR and ¹H‑NMR spectra by resampling to the fixed grids defined in the `SpectralGrid` entity (IR: 400–4000 cm⁻¹, 1 cm⁻¹ step; NMR: 0–10 ppm, 0.01 ppm step) and normalize each spectrum to unit variance. *(See US‑1)*
- **FR-002**: The system MUST split the curated dataset into training, validation, and test sets (70/15/15) ensuring **zero overlap of Bemis‑Murcko scaffolds** between splits and **zero overlap of reaction‑template IDs**. Overlap checks are performed via MD5 hashing of template identifiers. *(See US‑1)*
- **FR-003**: The system MUST implement a multi‑head self‑attention neural network (4 heads) that accepts a concatenated IR + NMR tensor as input, applies positional encoding along the spectral dimension, and fuses the attention output with an ECFP4 fingerprint vector via a fully‑connected layer to predict yield. *(See US‑2)*
- **FR-004**: The system MUST train the model using Adam (lr = 1e‑3), batch size = 32, for up to 15 epochs with early stopping (patience = 3) on validation RMSE. The training script MUST enforce CPU‑only execution (`torch.set_num_threads(2)`). *(See US‑2)*
- **FR-005**: The system MUST compute RMSE, MAE, and R² on the held‑out test set for (a) the attention model, (b) a fingerprint‑only baseline, (c) a spectra‑only baseline (concatenated IR + ¹H‑NMR), and (d) a condition‑only baseline. *(See US‑3)*
- **FR-006**: The system MUST perform two Wilcoxon signed‑rank tests on per‑sample absolute errors: (a) spectra‑only vs. fingerprint‑only, (b) attention model vs. each baseline. P‑values must be Bonferroni‑corrected (α = 0.0167). *(See US‑3)*
- **FR-007**: The system MUST generate attention‑weight heatmaps mapping the spectral axis to highlight the top‑weighted regions. *(See US‑3)*
- **FR-008**: The system MUST execute a permutation test by shuffling yield labels 100 times, retraining the attention model on each shuffled set, and reporting the mean R² of these null models. The mean must be < 0.05. *(See US‑3)*
- **FR-009**: The system MUST perform a sensitivity analysis on the attention‑weight percentile threshold using the set {90th, 95th, 99th} and report the stability of identified spectral regions. *(See US‑3)*
- **FR-010**: The system MUST retrieve raw spectral files (JCAMP‑DX) from NIST (via InChIKey) and, where available, from PubChem, perform peak detection, and store detected peaks for downstream alignment. *(See US‑3)*
- **FR-011**: The system MUST compare each top‑attended peak to an independent functional‑group reference table, accepting a match if the absolute difference is ≤ 100 cm⁻¹ (IR) or ≤ 0.2 ppm (NMR). Results are recorded in `peak_alignment_report.json`. *(See US‑3)*
- **FR-012**: The system MUST record all random seeds, deterministic‑algorithm flags, and hardware constraints in `state/compute_manifest.json`; re‑running with identical settings MUST reproduce identical model weights and validation metrics. *(See US‑2)*
- **FR-013**: The system MUST include a static‑analysis step (e.g., `ruff`) that verifies no hard‑coded metric values appear in the codebase. *(See US‑3)*
- **FR-014**: The system MUST halt with a `DATA_INSUFFICIENT` error if the final matched‑reaction count is < 300 or the API‑failure rate exceeds 80 %, logging the condition in `validation_status.json`. *(See US‑1)*
- **FR-015**: The system MUST enforce a total wall‑clock runtime ≤ 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM). *(See US‑2)*

### Key Entities

- **ReactionSample**: `reaction_smiles`, `yield_percent`, `ir_spectrum` (array), `nmr_spectrum` (array), `ecfp4` (vector), `template_id`, `solvent`, `catalyst`, `temperature_k`.
- **SpectralGrid**: `type` (IR or NMR), `min_value`, `max_value`, `step`, `num_bins`. Defaults: IR = 400–4000 cm⁻¹, step = 1 cm⁻¹; NMR = 0–10 ppm, step = 0.01 ppm.
- **ModelCheckpoint**: `epoch`, `validation_rmse`, `weights_path`, `config_hash`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All performance metrics (RMSE, MAE, R²) for the four models are computed **at runtime** from the real held‑out test set; a static‑analysis audit (FR‑013) confirms no hard‑coded metric literals exist.
- **SC-002**: Both Wilcoxon signed‑rank tests produce Bonferroni‑corrected p‑values < 0.0167, establishing statistical significance of any performance differences.
- **SC-003**: The attention‑weight heatmaps identify spectral regions; the sensitivity analysis shows ≥ 80 % overlap of identified regions across the 90th/95th/99th percentile thresholds.
- **SC-004**: The permutation test yields a mean R² < 0.05, demonstrating that the model learns genuine signal rather than noise.
- **SC-005**: Execution time on the CI runner is ≤ 6 hours (FR‑015) and CPU usage respects the free‑tier limits.
- **SC-006**: `leakage_report.json` must show **zero** scaffold overlap and **zero** reaction‑template ID overlap (≤ 0 % overlap). Any non‑zero overlap causes failure.
- **SC-007**: Re‑running the training with the same seed and deterministic flags reproduces identical `model.pth` and `training_log.csv` (FR‑012).
- **SC-008**: The `peak_alignment_report.json` confirms that each top‑attended peak aligns with a known functional‑group frequency within the specified tolerance.

## Assumptions

- **Real‑World Spectra Availability**: It is assumed that at least 300 reactions within the USPTO‑50k set have *experimentally measured* IR and ¹H‑NMR spectra retrievable from NIST or PubChem. If fewer are found, the project will halt with `DATA_INSUFFICIENT`.
- **Compute Environment**: All code runs on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, no GPU). Model size, batch size, and epoch limits are scoped to stay within these resources.
- **Spectral Normalization Sufficiency**: Resampling to the common grid and unit‑variance normalization are assumed to harmonize spectra from different instruments for model consumption.
- **Yield Labels**: Reaction yields are taken from the Open Reaction Database (ORD) linked to USPTO patents and expressed as percentages (0–[deferred]). Only reactions with a documented yield are kept.
- **Condition Encoding**: Solvent, catalyst, and temperature are encoded as one‑hot or numeric vectors; this encoding is assumed to capture major environmental effects without introducing leakage.
- **Statistical Thresholds**: The Bonferroni‑corrected α = 0.0167 and the permutation‑test R² < 0.05 thresholds are standard for controlling family‑wise error and confirming null performance, respectively.
- **Functional‑Group Reference**: An independent literature‑compiled reference table of IR band positions and ¹H‑NMR chemical shifts is used for peak‑alignment validation; the table is not derived from the training data.
- **No Simulated or Placeholder Data**: All spectra and yields used are real experimental measurements; no simulated or randomly generated values are permitted at any stage.

