# Research: llmXive follow-up: extending "Wan-Streamer v0.1"

## 1. Problem Formulation

The "Wan-Streamer v0.1" architecture generates real-time audio-visual content using flow-matching solvers. This research hypothesizes that a subset of frames ("low-information manifolds") exhibits low latent trajectory displacement (small deltas) that can be predicted from turn-taking semantics (e.g., agent pauses, non-interruption states). By predicting these deltas, the system can skip expensive flow-matching steps, reducing latency. The core challenge is to validate this hypothesis on CPU-only hardware while ensuring that skipping does not degrade perceptual quality (FID) beyond [deferred].

**Limitations**: If Wan-Streamer logs are unavailable, the project defaults to VoxCeleb2 for *methodological validation* only. The results in this mode are framed as "Proof-of-Concept for the Pipeline" and do not claim direct optimization of Wan-Streamer's latent manifold.

## 2. Dataset Strategy

### Verified Datasets
Per the project constraints and verified dataset list, the following sources are available:

| Dataset Name | Verified URL(s) | Relevance to Project |
|:--- |:--- |:--- |
| **VoxCeleb2** | `<br>` | **Primary Fallback Source**. Contains audio-visual data suitable for extracting turn-taking semantics and proxy latent trajectories if Wan-Streamer logs are unavailable. |
| **MOS Proxy** | *None verified* | **Metric Validation**. No verified dataset with human video quality ratings for this specific domain exists. Proxy MOS will be validated against FID or optical flow consistency. If human data is unavailable, the system logs "Assumption Validated (No Human Data Available)" (FR-012). |
| **RNN/Training** | *None verified* | **Baseline/Reference**. Removed. The baseline is now a "Zero-Delta Predictor" and "Previous-Frame Predictor". |

**Dataset Selection Rationale**:
The spec requires latent vectors from "Wan-Streamer v0.1 training logs." As no verified URL for Wan-Streamer logs is provided in the "# Verified datasets" block, the plan **MUST** fall back to the canonical **VoxCeleb2** dataset (FR-019, Assumption about dataset availability).
* **Fit**: VoxCeleb2 contains speaker identification and audio-visual data. We will use it to simulate turn-taking events and extract proxy latent trajectories using a pre-trained encoder (e.g., a lightweight audio-visual encoder) if direct Wan-Streamer logs are missing.
* **Constraint**: If Wan-Streamer logs are not locally available, the system will load VoxCeleb2 via `datasets.load_dataset("acul3/voxceleb2")` and process it to generate the required `timestamp`, `semantic_feature`, `prosodic_feature`, and `latent_delta_magnitude` fields.
* **Missing Data Handling**: If the verified datasets do not contain specific "Wan-Streamer" latent vectors, the research will explicitly state this gap and proceed with the VoxCeleb2 proxy, noting that results are indicative of the *methodology* rather than the specific Wan-Streamer model.

## 3. Methodology

### Phase 0: Preliminary Validation (New)
Before training the main estimator, we must empirically verify the core hypothesis: "Small latent delta magnitude correlates with low perceptual degradation (FID)."
1. **Sample**: Extract a small subset (e.g., 500 segments) from the available data.
2. **Generate**: For each segment, generate a "Full" version and a "Skipped" version (using linear interpolation or a simple estimator).
3. **Measure**: Compute the correlation (r) between the *average latent delta* of the segment and the *segment-level FID degradation*.
4. **Decision**: If r < 0.3, the hypothesis is weak; the plan will flag this as a "Hypothesis Failure" and pivot to a different metric or abort the main experiment.

### Phase 1: Data Extraction & Preprocessing (US-1)
1. **Source**: Attempt to load local Wan-Streamer logs. If missing, load **VoxCeleb2** (verified URL).
2. **Event Detection**: Implement `detect_turn_events` (FR-018) to label segments as "interruption" (high priority) or "pause" (low priority) based on audio energy and speech overlap.
3. **Latent Extraction**:
 * If Wan-Streamer logs exist: Parse latent vectors directly.
 * If VoxCeleb2: Use a frozen, CPU-efficient encoder (e.g., a small ResNet+CNN for audio-visual features) to generate proxy latent vectors.
 * Compute `latent_delta_magnitude` as the Euclidean distance between $t$ and $t-1$.
4. **Sampling**: Stratified sampling to ensure ≥500 interruption and ≥500 pause events (or all available if fewer). Target size: [deferred] frames (≤1 GB).
5. **Validation**: Check schema (timestamp, features, delta, label) and distribution preservation (FR-015).

### Phase 2: Estimator Training (US-2)
1. **Model**: Lightweight RNN (GRU) or shallow Transformer (2 layers, 128 hidden dim) to predict `latent_delta_magnitude` and `uncertainty_score`.
2. **Input**: Causal history of semantic/prosodic features.
3. **Loss**: MSE for delta magnitude; Calibration loss for uncertainty.
4. **Baselines**:
 * **Zero-Delta Predictor**: Always predicts 0.
 * **Previous-Frame Predictor**: Predicts the last observed delta.
 * Target: [deferred] MSE improvement over Zero-Delta baseline.
5. **Constraints**:
 * CPU-only training (no CUDA).
 * Batch size tuned to keep RAM ≤ 7 GB.
 * Early stopping if loss does not improve.
 * **Power Limitation**: If training > 6h, reduce sample size by [deferred] (FR-014).

### Phase 3: Hybrid Inference Simulation (US-3)
**Conditional Execution**:
* **If Wan-Streamer logs available**: Run full Hybrid Simulation against Wan-Streamer baseline.
* **If logs missing**: Run "Proxy Simulation" using linear interpolation baseline. Report results as "Methodological Feasibility" with disclaimers.

1. **Pipeline**:
 * For each frame/segment: Run Estimator.
 * **Decision Logic**:
 * If `uncertainty > 0.8` (FR-006): Use Full Solver (or Linear Interpolation in Proxy mode).
 * If `randomized_subset` (FR-008): Force Skip (regardless of prediction) for ≥5% of segments to establish causal effect.
 * Else: Use Estimated Delta (Skip Solver).
2. **Metrics**:
 * **Latency**: Measure time per segment (Hybrid vs. Full).
 * **Quality**: Compute FID (using `torchmetrics` over a batch of frames/segments) and Proxy MOS (using a frozen video-quality model).
 * **Stability**: Calculate correlation (r) between *average predicted delta* of the segment and *segment-level FID stability* (FR-010).
3. **Statistical Validation**:
 * **TOST**: Equivalence test for quality (margin Δ=0.05). TOST is a paired test comparing Hybrid vs. Baseline on the same segments.
 * **Bootstrap**: Stratified bootstrap with propensity-score matching for latency reduction (FR-005, FR-007).
 * **Power Analysis**: Calculate sample size needed for TOST (FR-016).

### Phase 4: Validation & Reporting
1. **Proxy MOS**: If human data exists, correlate r ≥ 0.8. Else, log "Assumption Validated (No Human Data Available)" (FR-012, SC-007).
2. **Uncertainty Calibration**: Correlate uncertainty score with prediction error (SC-006).
3. **Artifact Hashing**: Update `state.yaml` with hashes of all artifacts (FR-020).

## 4. Statistical Rigor & Assumptions

* **Multiple Comparisons**: Bonferroni correction applied if multiple TOST tests are run across different metrics.
* **Power Limitation**: Acknowledged that CPU constraints may limit the sample size for the TOST test. The plan includes a fallback to reduce sample size or fail gracefully (FR-014).
* **Causal Inference**: The randomized counterfactual (FR-008) is the primary method for causal claims. Propensity matching (FR-005) is used only for observational baseline validation.
* **Collinearity**: Semantic and prosodic features may be correlated. The model will report feature importance descriptively without claiming independent causal effects for each.
* **Dataset Fit**: The plan explicitly acknowledges that VoxCeleb2 is a proxy. If Wan-Streamer logs are unavailable, the "latent" vectors are derived, not native, and results are framed as "methodological validation" rather than "Wan-Streamer specific optimization."
* **FID Validity**: FID is computed over segments (batches) to maintain mathematical validity. The "per-frame" requirement in the spec is interpreted as "per-segment" to satisfy the batch nature of FID.

## 5. Compute Feasibility

* **Hardware**: 2 CPU, 7 GB RAM, 14 GB Disk.
* **Strategy**:
 * Data subset to ≤ 1 GB.
 * Model: Small RNN/Transformer (no large LLMs).
 * Libraries: `torch` (CPU wheel), `scikit-learn`.
 * No GPU/CUDA dependencies.
 * **Runtime**: Estimated < 4 hours for training + simulation on sampled data.