# Research: llmXive follow-up: extending "Wan-Streamer v0.1"

## 1. Problem Statement & Hypothesis

**Problem**: Real-time interactive foundation models (like Wan-Streamer v0.1) suffer from high latency due to flow-matching steps. The hypothesis is that a "low-information manifold" exists in the latent trajectory, where certain frames (e.g., during agent pauses) can be approximated or skipped without perceptible quality loss.

**Hypothesis**: A lightweight CPU-tractable estimator can predict the magnitude of latent vector deltas ($\Delta z$) based on turn-taking semantics. Frames with low predicted $\Delta z$ and high uncertainty can be skipped, reducing latency by ≥20% while maintaining FID degradation ≤5%.

## 2. Dataset Strategy

### Verified Sources
Per the project constraints and the `verified datasets` block, we will use the following sources:

| Dataset Role | Source Name | URL / Loader | Rationale |
|:--- |:--- |:--- |:--- |
| **Primary Latent/Turn-Taking Data** | Wan-Streamer v0.1 Logs | **Local/Verified Archive** (FR-019) | The spec requires latent trajectory data. **If this data is not present in the local environment or a verified public archive, the project MUST fail with "Data Unavailable" (FR-022).** No verified public URL for the specific Wan-Streamer training logs or weights exists in the `verified datasets` block. |
| **Fallback Audio/Video (Proxy)** | VoxCeleb2 | ` | Canonical fallback for audio-visual turn-taking data. **Used ONLY if Wan-Streamer logs are present to extract turn-taking labels, but cannot substitute for missing latent deltas.** |
| **Quality Assessment Proxy** | MOS / Video Quality | **Generated Data** | The plan will not use external datasets like Mosi-AI for MOS correlation as they lack the specific frame-level pairing. Instead, the system will log "Assumption Validated (No Human Data Available)" (FR-024) if no human ratings are found in the specific Wan-Streamer context. |
| **Statistical Baseline** | FID / Latency | **Generated via Inception-v3** | FID will be computed using `torchvision.models.inception_v3` on the generated frames vs. ground truth. |

*Note: The "re-generation" of latents via a public model is **removed** as a fallback strategy because no verified URL for the Wan-Streamer v0.1 inference code exists in the `verified datasets` block. Attempting to re-run the model without a verified source violates Constitution Principle I (Reproducibility) and II (Verified Accuracy).*

### Data Extraction & Preprocessing (FR-001, FR-018)
1. **Source Selection**: Check for local Wan-Streamer v0.1 logs. **If missing, exit with "Data Unavailable" (FR-022).** If present, proceed.
2. **Feature Engineering**:
 * **Semantic Features**: Extract text embeddings (e.g., BERT-base-cpu) from the transcript.
 * **Prosodic Features**: Extract audio energy, pitch, and silence duration.
 * **Latent Deltas**: Compute $\Delta z_t = ||z_t - z_{t-1}||_2$ from the latent trajectory.
 * **Turn Labels**: Classify frames as "interruption" (high energy + agent speech overlap), "pause" (silence), or "normal". Thresholds for "interruption" (e.g., energy > X dB) will be derived from the data distribution (FR-018).
3. **Sampling**: Filter for a substantial number of interruption and pause events. If fewer exist, use all available. Sample to ≤1 GB total size.
4. **Split**: [deferred] Train, [deferred] Val, [deferred] Test. Stratified by turn-label.

## 3. Methodology

### 3.1 Estimator Training (FR-002, FR-006)
* **Model**: Lightweight RNN (GRU) or shallow Transformer (2 layers, 4 heads) running on CPU.
* **Input**: Causal history of semantic and prosodic features (window size = [deferred]).
* **Output**: Predicted $\Delta z$ magnitude and Uncertainty Score ($U \in [0, 1]$).
* **Loss**: MSE for $\Delta z$ + Calibration loss for $U$.
* **Constraints**: Batch size tuned to keep RAM ≤ 7 GB. Training stops if 6h limit approached; sample size reduced (FR-014).
* **Baseline**: Zero-delta predictor ($\hat{\Delta z} = 0$).

### 3.2 Hybrid Inference Simulation & Counterfactual Generation (FR-003, FR-008, FR-009, FR-017)
* **Logic**:
 1. For each frame $t$:
 * Run Estimator.
 * **Randomized Intervention**: If $t \in \text{RandomSubset}$ (≥5% of frames, capped at 200 for CPU feasibility), force skip regardless of prediction (FR-008).
 * **Deterministic Fallback**: Else if $U_t > 0.8$, use full solver (FR-006).
 * **Skip**: Else, skip flow-matching step (use interpolated/estimated latent).
 2. **Counterfactual Ground Truth Generation**: For the **RandomSubset** only:
 * After generating the "Skipped" frame, the system **must re-run the full flow-matching solver** *only for that specific frame* to generate the "Full" ground truth.
 * **Resource Constraint**: To fit within the 6-hour CPU limit, the randomized subset size is capped (e.g., 200 frames) and the re-run may use a downsampled resolution (e.g., 128x128) or a reduced number of flow-matching steps, with the variance adjustment documented in the power analysis.
 * This ensures a paired comparison (Skipped vs. Full) on the exact same frame, isolating the causal effect of the skip action.

### 3.3 Quality & Latency Metrics (FR-004, FR-010, FR-012, FR-013)
* **FID**: Computed using `torchvision.models.inception_v3` (CPU-quantized or standard float32) on the generated frames vs. ground truth.
 * *Constraint*: The evaluation model must be distinct from the estimator (Constitution Principle VII).
 * *Note*: If `inception_v3` is too heavy, the feature extraction will be done in batches or on a downsampled set, but the metric remains "FID".
* **Proxy MOS**: Correlation with human ratings (if available in the specific Wan-Streamer context). If not, log "Assumption Validated (No Human Data Available)" (FR-024).
* **Latency**: Measured as time per frame (CPU cycles).
* **Validation Target**: Calculate Pearson $r$ between **predicted $\Delta z$** and **Observed FID Degradation** (calculated as $|FID_{skipped} - FID_{full}| / FID_{full}$ from the counterfactual re-run). This breaks the tautology because $FID_{full}$ is generated by the full solver, not the estimator.

### 3.4 Statistical Validation (FR-005, FR-016)
* **Pilot Study & Power Analysis**: Before the main experiment, run a **small pilot (e.g., 50 frames)** of the randomized counterfactual process (Skipped vs. Full) to estimate the variance of the FID metric. This pilot is computationally cheap and provides the necessary variance estimate for the power analysis of the main study (FR-016).
* **Latency Reduction**: Two One-Sided Tests (TOST) with $\Delta = 0.05$ (relative ratio) to prove equivalence in quality and significant reduction in latency.
* **Bias Correction**: Stratified bootstrap with propensity-score matching (using covariates like frame duration, speaker identity) to validate latency reduction (FR-005).
* **Power Analysis**: Calculate expected variance of FID (from pilot) to justify sample size. If power is insufficient, log limitation (FR-016).
* **Correlation**: Pearson $r$ between predicted $\Delta z$ and actual FID stability (FR-010).

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | High | The plan now explicitly treats missing Wan-Streamer logs as a hard blocker (FR-022). No "re-generation" fallback is attempted. |
| **CPU Time Limit** | High | Strict monitoring of RAM and time. Automatic sample size reduction (FR-014) or graceful failure. The randomized subset is capped to ensure the counterfactual re-runs fit in 6h. |
| **FID Model Availability** | Medium | Use `inception_v3` (standard FID). If memory is an issue, use batch processing or downsampled images, but maintain the metric name "FID". |
| **Causal Inference Failure** | High | The randomized counterfactual (FR-008) with re-run is mandatory. If the random subset is too small to show significance, the result is reported as "Inconclusive". |