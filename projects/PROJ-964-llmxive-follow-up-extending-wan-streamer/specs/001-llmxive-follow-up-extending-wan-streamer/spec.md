# Feature Specification: llmXive follow-up: extending "Wan-Streamer v0.1: End-to-end Real-time Interactive Foundation Models"

**Feature Branch**: `001-llmxive-streamer-optimization`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Wan-Streamer v0.1 to investigate low-information manifolds in audio-visual generation based on turn-taking semantics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Preprocessing (Priority: P1)

The research system MUST extract time-series data of text, audio, and video latents alongside turn-taking labels from the Wan-Streamer v0.1 training logs (or the canonical VoxCeleb2 fallback), filtering for segments containing user interruptions and agent pauses, to prepare a CPU-tractable dataset for analysis.

**Why this priority**: Without a valid, labeled dataset linking conversational context to latent trajectories, no correlation analysis or estimator training can occur. This is the foundational data layer.

**Independent Test**: Can be fully tested by verifying that the extraction script produces a CSV/Parquet file where every row contains a timestamp, semantic/prosodic features, the corresponding latent vector delta, and a binary turn-taking label, with a total size ≤ 1 GB (sampled).

**Acceptance Scenarios**:

1. **Given** the pre-trained Wan-Streamer v0.1 weights and logs (or the VoxCeleb2 proxy) are available in the working directory, **When** the extraction script runs on a CPU-only runner, **Then** it outputs a structured dataset file containing at least 10,000 sampled frames with valid turn-taking labels and latent deltas.
2. **Given** the raw logs contain segments with interruptions, **When** the extraction logic filters for these events using the defined thresholds (see FR-018), **Then** the resulting dataset includes at least 500 distinct interruption events labeled as "high-priority" and 500 agent pause events labeled as "low-priority" (or all available events if fewer than 500 exist, with the actual count logged).
3. **Given** the dataset is generated, **When** a schema validation check is run, **Then** all required columns (timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label) are present and non-null.

---

### User Story 2 - Lightweight Estimator Training (Priority: P2)

The research system MUST train a lightweight Recurrent Neural Network (RNN) or shallow Transformer on the extracted dataset to predict the magnitude of the next audio-visual latent vector delta based on causal history of semantic and prosodic signals, ensuring the training completes within the predefined CPU runtime limit.

**Why this priority**: This implements the core hypothesis that a lightweight model can predict "low-information" latent states, enabling the potential for solver skipping.

**Independent Test**: Can be fully tested by running the training script on the sampled dataset and verifying that the model converges (loss decreases), achieves a validation Mean Squared Error (MSE) on the latent delta prediction task lower than a naive baseline (e.g., predicting zero delta), AND demonstrates a correlation (r ≥ 0.7) between high predicted delta magnitude and frames that, when skipped, cause >5% FID degradation. **Crucially, this test MUST include a counterfactual measurement procedure where the full solver is run on the same frames to establish ground truth FID, ensuring the validation target is independent of the predictor.**

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset from User Story 1, **When** the RNN/Transformer training script executes on a CPU environment with ≤ 7 GB RAM, **Then** the training job completes within 6 hours and outputs a serialized model checkpoint file.
2. **Given** the trained model, **When** evaluated on a held-out validation set, **Then** the prediction error (MSE) for the latent delta magnitude is at least 10% lower than a baseline predictor that always outputs zero.
3. **Given** the training process, **When** memory usage is monitored, **Then** peak RAM consumption remains within the limits of standard CI runner constraints (≤ 7 GB), ensuring compatibility.

---

### User Story 3 - Hybrid Inference Simulation and Quality-Latency Trade-off Analysis (Priority: P3)

The research system MUST simulate a hybrid inference pipeline where the trained estimator predicts latent states for "low-priority" frames (skipping flow-matching steps) while the full solver handles "high-priority" frames, and then quantitatively compare the resulting FID and proxy MOS against the full-generation baseline to validate the quality-latency trade-off.

**Why this priority**: This validates the practical utility of the research by demonstrating that the theoretical "low-information manifold" can be exploited to reduce latency without unacceptable quality loss.

**Independent Test**: Can be fully tested by running the simulation script on a test set of video segments, measuring inference time per frame and computing FID/MOS, and confirming that the hybrid approach reduces latency by a statistically significant margin while maintaining quality within the 5% degradation threshold. **The test MUST include a randomized subset of frames forced to be skipped (regardless of prediction) to validate the causal effect of the skip action, distinguishing 'easy to skip' from 'easy to generate'. Propensity-score matching (FR-005) is used only for observational baseline validation, not for the primary causal conclusion.**

**Acceptance Scenarios**:

1. **Given** the trained estimator and a test set of video segments, **When** the hybrid inference pipeline runs, **Then** the average inference latency per frame is at least 20% lower than the full flow-matching baseline.
2. **Given** the hybrid output, **When** the Fréchet Inception Distance (FID) is computed against the ground truth, **Then** the FID score indicates a degradation of no more than 5% compared to the baseline generation, defined mathematically as: `(FID_hybrid - FID_baseline) / FID_baseline <= 0.05`.
3. **Given** the latency and quality metrics, **When** a Two One-Sided Tests (TOST) equivalence test is performed with an equivalence margin (Δ) of 0.05 (relative ratio), **Then** the result confirms equivalence for quality metrics (p < 0.05 for both one-sided tests) and a statistically significant reduction in latency (p < 0.05).
4. **Given** a subset of video segments with human-annotated quality ratings, **When** the proxy MOS is computed, **Then** the correlation (Pearson r) between the proxy MOS and human ratings is ≥ 0.8, validating the proxy metric for this specific regime. **If no human data exists, the system MUST log "Assumption Validated (No Human Data Available)" and skip this specific correlation test.**

---

### Edge Cases

- What happens when the turn-taking classifier is uncertain (e.g., ambiguous prosodic signals)? The system MUST default to using the full flow-matching solver for that frame to prevent quality degradation.
- How does the system handle segments where the latent trajectory is non-smooth despite a "low-priority" label? The estimator MUST be designed to output a high uncertainty flag or high predicted delta, triggering a fallback to the full solver.
- What if the CPU-only training exceeds the 6-hour limit? The system MUST automatically reduce the dataset sample size by [deferred] (capped at a minimum sample size sufficient for statistical validity) and retry, or fail gracefully with a "Power Limitation" error if the minimum size is reached. **If a frame is part of the randomized counterfactual subset (FR-008), the randomized intervention overrides the deterministic fallback (FR-006) to ensure causal validity.**

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract time-series latent vectors and turn-taking labels from Wan-Streamer v0.1 logs (or the canonical VoxCeleb2 fallback), ensuring the dataset contains variables for semantic content, prosodic signals, and latent delta magnitude (See US-1).
- **FR-002**: System MUST train a lightweight RNN or shallow Transformer model on CPU-only hardware to predict latent delta magnitude AND an uncertainty score, with a maximum memory footprint of ≤ 7 GB (See US-2).
- **FR-003**: System MUST implement a hybrid inference engine that conditionally skips flow-matching steps based on the estimator's prediction of "low-priority" frames (See US-3).
- **FR-004**: System MUST compute Fréchet Inception Distance (FID) and a proxy Mean Opinion Score (MOS) using a separate, pre-trained video quality assessment model that is frozen and trained on a dataset NOT used for estimator training, ensuring validation independence (See US-3).
- **FR-005**: System MUST perform a statistical significance test using stratified bootstrap with propensity-score matching (using independent covariates, not the estimator's prediction) to validate latency reduction, and a Two One-Sided Tests (TOST) equivalence test with margin Δ=0.05 (relative ratio) for quality metrics. **These methods are explicitly stated to satisfy the 'paired statistical test' requirement of Constitution Principle VI.** (See US-3).
- **FR-006**: System MUST enforce a fallback mechanism where any frame with an estimator uncertainty score above a predefined threshold defaults to the full flow-matching solver. (See US-2, US-3).
- **FR-007**: System MUST implement a task module `analyze_latency_bias` that executes the stratified bootstrap with propensity-score matching for the latency reduction metric (See FR-005).
- **FR-008**: System MUST implement a randomized counterfactual intervention where a random subset of frames (≥ 5% of total) is forced to be skipped regardless of the estimator's prediction, to establish the causal effect of the skip action and distinguish 'easy to skip' from 'easy to generate' (See US-3).
- **FR-009**: System MUST implement a task module `execute_fallback` that handles the conditional fallback logic, ensuring precedence for randomized counterfactuals over deterministic thresholds (See FR-006, FR-008).
- **FR-010**: System MUST calculate and log the correlation (r ≥ 0.7) between predicted delta magnitude and FID stability (relative change in FID between skipped and full-solver frames) as a specific metric (See SC-003).
- **FR-011**: System MUST implement a task module `calculate_fid_stability_corr` to perform the calculation defined in FR-010 (See FR-010).
- **FR-012**: System MUST validate the proxy MOS correlation (r ≥ 0.8) with human ratings if data exists, or log "Assumption Validated (No Human Data Available)" if not (See SC-007).
- **FR-013**: System MUST implement a task module `validate_proxy_mos` to perform the correlation test or handle the missing data scenario (See FR-012).
- **FR-014**: System MUST implement a task module `reduce_sample_size` that reduces the dataset sample size by [deferred] on power limit exceedance, or fails with a "Power Limitation" error if the minimum sample size is reached (See Edge Cases).
- **FR-015**: System MUST implement a task module `validate_sampling_distribution` to measure and confirm that stratified sampling preserves the distribution of turn-taking events (See Assumption about power limitations).
- **FR-016**: System MUST implement a power analysis that specifies the expected variance of the FID metric and the minimum detectable effect size to justify the sample size for the TOST test with [deferred] power (See SC-002).
- **FR-017**: System MUST define a precedence rule where the randomized counterfactual intervention (FR-008) overrides the deterministic fallback (FR-006) for frames in the randomized subset (See Edge Cases).
- **FR-018**: System MUST define the detection algorithm and thresholds for classifying 'interruption' and 'pause' events (e.g., audio energy > X dB overlapping with agent speech) to ensure the 500 minimum event count is verifiable (See US-1 AS-2).
- **FR-019**: System MUST fetch data from a canonical source (VoxCeleb2 or verified Wan-Streamer public proxy) if local logs are unavailable, ensuring reproducibility (See Constitution Principle I).
- **FR-020**: System MUST implement a task module `update_state_yaml` to update the `state.yaml` file with artifact hashes (See Constitution Principle V).
- **FR-021**: System MUST link the `contracts/` directory schema definitions to the `data-model.md` and `quickstart.md` documents in the 'Data Flow' section (See Data Flow).
- **FR-022**: System MUST ensure that the 'Data Unavailable' scenario is handled by falling back to the canonical source defined in FR-019 (See Assumption about dataset availability).
- **FR-023**: System MUST ensure that the 'Power Limitation' error is logged and the system exits gracefully if the minimum sample size is reached (See Edge Cases).
- **FR-024**: System MUST ensure that the 'Assumption Validated (No Human Data Available)' scenario is logged and the system continues without the proxy MOS correlation test (See US-3 AS-4).

### Key Entities

- **LatentTrajectory**: A time-series record of audio-visual latent vectors, including magnitude of displacement between timesteps.
- **TurnTakingEvent**: A labeled segment of interaction indicating "interruption," "agent pause," or "normal turn," derived from semantic and prosodic features.
- **EstimatorModel**: A lightweight recurrent or transformer model trained to predict `LatentTrajectory` changes and an `UncertaintyScore` based on `TurnTakingEvent` history.
- **UncertaintyScore**: A scalar value (0.0 to 1.0) output by the `EstimatorModel` representing the confidence in the latent delta prediction; values > 0.8 trigger fallback to full solver.
- **HybridOutput**: The generated video/audio sequence produced by the hybrid pipeline, containing a mix of estimated and fully solved frames.
- **FIDStability**: A derived metric representing the relative change in FID between a skipped frame (estimated) and the corresponding full-solver frame (ground truth) for the same timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Latency reduction is measured against the full flow-matching baseline, targeting a ≥ 20% decrease in inference time per frame (See FR-003, US-3).
- **SC-002**: Perceptual quality degradation is measured against the baseline FID score, ensuring the hybrid output FID satisfies `(FID_hybrid - FID_baseline) / FID_baseline <= 0.05` (relative ratio). **Note: This 5% threshold is a domain-standard approximation for perceptual equivalence in this context, acknowledging the non-linearity of FID.** (See FR-004, US-3).
- **SC-003**: Estimator prediction accuracy is measured against the actual latent delta magnitude in the validation set, requiring a significant improvement over a zero-delta baseline AND a correlation (r ≥ 0.7) with FID stability (defined as the relative change in FID between skipped and full-solver frames) for skipped frames (See FR-002, US-2).
- **SC-004**: Statistical significance of the latency reduction is measured against the null hypothesis (no difference) using bias-corrected methods, requiring a propensity-score corrected p-value < 0.05 (See FR-005, US-3).
- **SC-005**: Computational feasibility is measured against the CI runner constraints, ensuring peak RAM usage ≤ 7 GB and total runtime ≤ 6 hours (See FR-002, US-2).
- **SC-006**: Uncertainty score calibration is measured against the actual prediction error, requiring a significant correlation between high uncertainty scores and high prediction errors (See FR-002, US-2).
- **SC-007**: Proxy MOS validity is measured against human ratings (if available), requiring a correlation (r ≥ 0.8). **If no human data exists, the system MUST log "Assumption Validated (No Human Data Available)".** (See FR-004, US-3).
- **SC-008**: Power analysis is measured against the expected variance of the FID metric, ensuring the sample size is sufficient to reject the null hypothesis of 'degradation > 5%' with [deferred] power (See FR-016).

## Assumptions

- **Assumption about dataset availability**: The Wan-Streamer v0.1 training logs and pre-trained weights are accessible via the official repository or public archive and contain the necessary latent trajectory data for the target timeframe. **If unavailable, the system MUST fall back to the canonical VoxCeleb2 dataset as per FR-019.**
- **Assumption about CPU feasibility**: A representative sample of the total training data is sufficient to train a lightweight RNN model within the 6-hour CPU runtime limit while maintaining statistical power for the correlation analysis.
- **Assumption about metric validity**: The CLIP-based video-text similarity or pre-trained video quality assessment model serves as a valid proxy for Mean Opinion Score (MOS) in the absence of human raters for this specific domain, provided the correlation validation (r ≥ 0.8) is met. **If a domain-specific video quality model (e.g., ViFi-CLIP) is available, it MUST be used instead.**
- **Assumption about turn-taking labels**: The semantic and prosodic signals derived from the input audio/text are sufficient to distinguish "low-information" turns from "high-information" interruptions with a precision of at least 0.7.
- **Assumption about inference constraints**: The "no GPU" constraint applies strictly; all training and inference must be performed using standard CPU floating-point operations without quantization libraries that require CUDA.
- **Assumption about power limitations**: If the full dataset exceeds memory limits, the sampling strategy (random or stratified) will preserve the distribution of turn-taking events and latent delta magnitudes.
- **Assumption about causal inference**: The randomized counterfactual intervention (FR-008) is sufficient to establish the causal effect of the skip action, overcoming the limitations of observational correlation.