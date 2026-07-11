# Feature Specification: llmXive follow-up: extending "Wan-Streamer v0.1: End-to-end Real-time Interactive Foundation Models"

**Feature Branch**: `001-llmxive-streamer-optimization`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Wan-Streamer v0.1 to investigate low-information manifolds in audio-visual generation based on turn-taking semantics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Extraction and Preprocessing (Priority: P1)

The research system MUST extract time-series data of text, audio, and video latents alongside turn-taking labels from the Wan-Streamer v0.1 training logs, filtering for segments containing user interruptions and agent pauses, to prepare a CPU-tractable dataset for analysis.

**Why this priority**: Without a valid, labeled dataset linking conversational context to latent trajectories, no correlation analysis or estimator training can occur. This is the foundational data layer.

**Independent Test**: Can be fully tested by verifying that the extraction script produces a CSV/Parquet file where every row contains a timestamp, semantic/prosodic features, the corresponding latent vector delta, and a binary turn-taking label, with a total size ≤ 1 GB (sampled).

**Acceptance Scenarios**:

1. **Given** the pre-trained Wan-Streamer v0.1 weights and logs are available in the working directory, **When** the extraction script runs on a CPU-only runner, **Then** it outputs a structured dataset file containing at least 10,000 sampled frames with valid turn-taking labels and latent deltas.
2. **Given** the raw logs contain segments with interruptions, **When** the extraction logic filters for these events, **Then** the resulting dataset includes at least 500 distinct interruption events labeled as "high-priority" and 500 agent pause events labeled as "low-priority" (or all available events if fewer than 500 exist, with the actual count logged).
3. **Given** the dataset is generated, **When** a schema validation check is run, **Then** all required columns (timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label) are present and non-null.

---

### User Story 2 - Lightweight Estimator Training (Priority: P2)

The research system MUST train a lightweight Recurrent Neural Network (GRU) or shallow Transformer on the extracted dataset to predict the magnitude of the next audio-visual latent vector delta based on causal history of semantic and prosodic signals, ensuring the training completes within the 6-hour CPU runtime limit.

**Why this priority**: This implements the core hypothesis that a lightweight model can predict "low-information" latent states, enabling the potential for solver skipping.

**Independent Test**: Can be fully tested by running the training script on the sampled dataset and verifying that the model converges (loss decreases), achieves a validation Mean Squared Error (MSE) on the latent delta prediction task lower than a naive baseline (e.g., predicting zero delta), AND demonstrates a correlation (r ≥ 0.7) between high predicted delta magnitude and frames that, when skipped, cause >5% FID degradation.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset from User Story 1, **When** the GRU/Transformer training script executes on a CPU environment with ≤ 7 GB RAM, **Then** the training job completes within 6 hours and outputs a serialized model checkpoint file.
2. **Given** the trained model, **When** evaluated on a held-out validation set, **Then** the prediction error (MSE) for the latent delta magnitude is at least 10% lower than a baseline predictor that always outputs zero.
3. **Given** the training process, **When** memory usage is monitored, **Then** peak RAM consumption remains within the limits of standard CI runner constraints (≤ 7 GB), ensuring compatibility.

---

### User Story 3 - Hybrid Inference Simulation and Quality-Latency Trade-off Analysis (Priority: P3)

The research system MUST simulate a hybrid inference pipeline where the trained estimator predicts latent states for "low-priority" frames (skipping flow-matching steps) while the full solver handles "high-priority" frames, and then quantitatively compare the resulting FID and proxy MOS against the full-generation baseline to validate the quality-latency trade-off.

**Why this priority**: This validates the practical utility of the research by demonstrating that the theoretical "low-information manifold" can be exploited to reduce latency without unacceptable quality loss.

**Independent Test**: Can be fully tested by running the simulation script on a test set of video segments, measuring inference time per frame and computing FID/MOS, and confirming that the hybrid approach reduces latency by a statistically significant margin while maintaining quality within the 5% degradation threshold.

**Acceptance Scenarios**:

1. **Given** the trained estimator and a test set of 50 video segments, **When** the hybrid inference pipeline runs, **Then** the average inference latency per frame is at least 20% lower than the full flow-matching baseline.
2. **Given** the hybrid output, **When** the Fréchet Inception Distance (FID) is computed against the ground truth, **Then** the FID score indicates a degradation of no more than 5% compared to the baseline generation, defined mathematically as: `(FID_hybrid - FID_baseline) / FID_baseline <= 0.05`.
3. **Given** the latency and quality metrics, **When** a Two One-Sided Tests (TOST) equivalence test is performed with an equivalence margin (Δ) of 0.05, **Then** the result confirms equivalence for quality metrics (p < 0.05 for both one-sided tests) and a statistically significant reduction in latency (p < 0.05).
4. **Given** a subset of 50 video segments with human-annotated quality ratings, **When** the proxy MOS is computed, **Then** the correlation (Pearson r) between the proxy MOS and human ratings is ≥ 0.8, validating the proxy metric for this specific regime.

---

### Edge Cases

- What happens when the turn-taking classifier is uncertain (e.g., ambiguous prosodic signals)? The system MUST default to using the full flow-matching solver for that frame to prevent quality degradation.
- How does the system handle segments where the latent trajectory is non-smooth despite a "low-priority" label? The estimator MUST be designed to output a high uncertainty flag or high predicted delta, triggering a fallback to the full solver.
- What if the CPU-only training exceeds the 6-hour limit? The system MUST automatically reduce the dataset sample size by [deferred] (capped at a minimum sample size sufficient for statistical validity) and retry, or fail gracefully with a "Power Limitation" error if the minimum size is reached.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract time-series latent vectors and turn-taking labels from Wan-Streamer v0.1 logs, ensuring the dataset contains variables for semantic content, prosodic signals, and latent delta magnitude (See US-1).
- **FR-002**: System MUST train a lightweight GRU or shallow Transformer model on CPU-only hardware to predict latent delta magnitude AND an uncertainty score, with a maximum memory footprint of 7 GB (See US-2).
- **FR-003**: System MUST implement a hybrid inference engine that conditionally skips flow-matching steps based on the estimator's prediction of "low-priority" frames (See US-3).
- **FR-004**: System MUST compute Fréchet Inception Distance (FID) and a proxy Mean Opinion Score (MOS) using a separate, pre-trained video quality assessment model to evaluate hybrid output quality (See US-3).
- **FR-005**: System MUST perform a statistical significance test using stratified bootstrap with propensity-score matching (or equivalent bias-correction method) to validate latency reduction, and a Two One-Sided Tests (TOST) equivalence test with margin Δ=0.05 for quality metrics (See US-3).
- **FR-006**: System MUST enforce a fallback mechanism where any frame with an estimator uncertainty score above a threshold of a high magnitude defaults to the full flow-matching solver (See US-2, US-3).

### Key Entities

- **LatentTrajectory**: A time-series record of audio-visual latent vectors, including magnitude of displacement between timesteps.
- **TurnTakingEvent**: A labeled segment of interaction indicating "interruption," "agent pause," or "normal turn," derived from semantic and prosodic features.
- **EstimatorModel**: A lightweight recurrent or transformer model trained to predict `LatentTrajectory` changes and an `UncertaintyScore` based on `TurnTakingEvent` history.
- **UncertaintyScore**: A scalar value (0.0 to 1.0) output by the `EstimatorModel` representing the confidence in the latent delta prediction; values > 0.8 trigger fallback to full solver.
- **HybridOutput**: The generated video/audio sequence produced by the hybrid pipeline, containing a mix of estimated and fully solved frames.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Latency reduction is measured against the full flow-matching baseline, targeting a ≥ 20% decrease in inference time per frame (See FR-003, US-3).
- **SC-002**: Perceptual quality degradation is measured against the baseline FID score, ensuring the hybrid output FID satisfies `(FID_hybrid - FID_baseline) / FID_baseline <= 0.05` (See FR-004, US-3).
- **SC-003**: Estimator prediction accuracy is measured against the actual latent delta magnitude in the validation set, requiring a significant improvement over a zero-delta baseline AND a correlation (r ≥ 0.7) with FID stability for skipped frames (See FR-002, US-2).
- **SC-004**: Statistical significance of the latency reduction is measured against the null hypothesis (no difference) using bias-corrected methods, requiring a p-value < 0.05 (See FR-005, US-3).
- **SC-005**: Computational feasibility is measured against the CI runner constraints, ensuring peak RAM usage ≤ 7 GB and total runtime ≤ 6 hours (See FR-002, US-2).

## Assumptions

- **Assumption about dataset availability**: The Wan-Streamer v0.1 training logs and pre-trained weights are accessible via the official repository or public archive and contain the necessary latent trajectory data for the target timeframe.
- **Assumption about CPU feasibility**: A representative sample of the total training data is sufficient to train a lightweight GRU model within the 6-hour CPU runtime limit while maintaining statistical power for the correlation analysis.
- **Assumption about metric validity**: The CLIP-based video-text similarity or pre-trained video quality assessment model serves as a valid proxy for Mean Opinion Score (MOS) in the absence of human raters for this specific domain, provided the correlation validation (r ≥ 0.8) is met.
- **Assumption about turn-taking labels**: The semantic and prosodic signals derived from the input audio/text are sufficient to distinguish "low-information" turns from "high-information" interruptions with a precision of at least 0.7.
- **Assumption about inference constraints**: The "no GPU" constraint applies strictly; all training and inference must be performed using standard CPU floating-point operations without quantization libraries that require CUDA.
- **Assumption about power limitations**: If the full dataset exceeds memory limits, the sampling strategy (random or stratified) will preserve the distribution of turn-taking events and latent delta magnitudes.