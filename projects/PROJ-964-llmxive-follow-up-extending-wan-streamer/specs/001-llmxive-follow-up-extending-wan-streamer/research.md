# Research: llmXive follow-up: extending "Wan-Streamer v0.1"

## Problem Statement

The research investigates whether "low-information manifolds" in audio-visual generation (characterized by low latent vector delta magnitude) can be predicted using turn-taking semantics (semantic/prosodic features). If predictable, flow-matching steps can be skipped for these frames, reducing inference latency without degrading perceptual quality (FID/MOS) beyond a 5% threshold.

## Dataset Strategy

### Primary Data Source: Wan-Streamer v0.1 Logs
- **Status**: **NO VERIFIED SOURCE FOUND**.
- **Description**: The spec assumes the availability of pre-trained Wan-Streamer v0.1 weights and training logs containing time-series latent vectors, audio/video inputs, and turn-taking metadata.
- **Strategy**: The implementation will expect these logs to be provided locally in `data/raw/`.
- **Fallback Strategy (Task T003)**: If logs are missing, the pipeline **MUST** load a verified public proxy dataset: `carnival13/video_conversation_v1` (URL: `https://huggingface.co/datasets/carnival13/video_conversation_v1`). This ensures FR-001 is testable and satisfies Constitution Principle I (Reproducibility) on a fresh runner.
- **Schema Verification (Task T004b)**: If the fallback dataset lacks pre-extracted latents, a lightweight extraction script will generate them from raw video/audio to match the primary schema.

### Calibration Dataset for FID/MOS (Principle VII)
- **Source**: `kinetics-400` (subset) or `activitynet` (verified video datasets).
- **Purpose**: To calibrate FID and Proxy MOS models on a dataset **completely separate** from the Wan-Streamer logs and the fallback conversation dataset. This ensures Validation Independence (Principle VII) by preventing any overlap in temporal patterns or content between the estimator training data and the quality metric calibration data.
- **Strategy**: Load a random subset of frames from Kinetics-400 to tune FID/MOS thresholds.

## Methodology

### 1. Data Extraction & Preprocessing (US-1, FR-001)
- **Input**: Wan-Streamer v0.1 logs (local) OR verified fallback dataset (`carnival13/video_conversation_v1`).
- **Process**:
  - Extract latent vectors ($z_t$) for each frame.
  - Compute delta magnitude: $\Delta_t = ||z_t - z_{t-1}||$.
  - Extract semantic features (text embeddings) and prosodic features (audio energy, pitch).
  - Label turn-taking events: "Interruption" (High Priority), "Agent Pause" (Low Priority), "Normal".
- **Output**: Parquet file with columns: `timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`, `uncertainty_flag`.
- **Validation**: Task T015 (Distribution Validation) ensures the sampling preserves the distribution of turn-taking events. **Gate**: Halt if shift > 5%.

### 2. Estimator Training (US-2, FR-002)
- **Model**: Lightweight GRU (Gated Recurrent Unit).
  - *Rationale*: GRUs are computationally cheaper than Transformers and well-suited for time-series prediction on CPU.
- **Input**: Causal history of semantic/prosodic features.
- **Target**: Predict `latent_delta_magnitude` and `uncertainty_score`.
- **Loss Function**: Mean Squared Error (MSE) for delta magnitude + Binary Cross-Entropy for uncertainty.
- **Baseline**: Naive predictor (always predicts 0 delta).
- **Constraints**:
  - Training on CPU only.
  - Batch size tuned to fit ≤ 7 GB RAM.
  - Max runtime: reasonable duration.
  - **Power Limitation Fallback (Task T016)**: If memory limits are hit, reduce sample size by a substantial margin (maintaining ratios) or fail with "Power Limitation" error.

### 3. Hybrid Inference Simulation (US-3, FR-003)
- **Logic**:
  - For each frame $t$:
    - Run Estimator.
    - If `predicted_delta_magnitude` < threshold AND `uncertainty_score` < 0.8: **Skip** flow-matching steps (use estimated latent).
    - Else: **Execute** full flow-matching solver.
- **Fallback Mechanism (FR-006)**: If `uncertainty_score` > 0.8, force full solver. Task T009 explicitly tests this condition.

### 4. Quality-Latency Trade-off Analysis (US-3, FR-004, FR-005)
- **Metrics**:
  - **Latency**: Inference time per frame (ms).
  - **Quality**: FID (Fréchet Inception Distance) and Proxy MOS.
- **Statistical Tests (Mandatory)**:
  - **Latency Reduction**: **Stratified Bootstrap with Propensity-Score Matching** (FR-005). Propensity scores are derived from the **Observational Group** (estimator-driven skips) to balance covariates. The **Randomly Forced Skip Group** (Counterfactual) provides the unbiased causal estimate (ATE) for comparison. This satisfies the "paired statistical test" requirement of Constitution Principle VI.
  - **Quality Equivalence**: **Two One-Sided Tests (TOST)** with $\Delta = 0.05$ (FR-005). Null hypothesis: Quality degradation > 5%. Alternative: Degradation ≤ 5%.
  - **Correlation (SC-003)**: Pearson $r$ between predicted delta and FID stability. **Gate**: Halt if r < 0.7 (Task T013).
  - **Proxy MOS Validation (Task T014)**: Correlation with human ratings. If human data is missing, log "Assumption Validated (No Human Data Available)". If human data exists and r < 0.8, log warning.

## Causal Inference Strategy

To avoid circular validation and establish causality:
1.  **Counterfactual Simulation (Task T017)**: Randomly force skips on a subset of frames regardless of the estimator's prediction.
2.  **Analysis**: Compare the quality degradation (FID) between the **Estimator-Driven Skip Group** and the **Randomly Forced Skip Group**.
3.  **Conclusion**: If the degradation is negligible in the Estimator group but significant in the Random group, it proves the skipping mechanism (driven by low delta) does not introduce artifacts distinct from the natural manifold. This breaks the tautological link between "low delta" and "low information".
4.  **Statistical Correction**: Propensity Score Matching is used **only** to balance covariates within the observational group to estimate the treatment effect from observational data. The randomized group provides the unbiased estimate without needing propensity correction.

## Validation Independence Protocol

To satisfy Constitution Principle VII:
- **FID/MOS Models**: These models are **frozen** and **not trained** on the estimator data.
- **Calibration Set**: A separate dataset (Kinetics-400 subset) is used to tune FID/MOS thresholds and verify metric stability. This dataset is **disjoint** from the Wan-Streamer logs and the fallback conversation dataset.
- **No Circular Dependency**: The estimator is never evaluated against itself.

## Statistical Rigor & Limitations

- **Power Analysis Source**: The expected variance for FID will be derived from a **Pilot Study** (Task T018). The **Minimum Detectable Effect Size (MDES)** is pre-defined as a **[deferred] relative FID degradation**, based on literature values for video generation stability. This ensures the sample size ([deferred] frames) is sufficient to reject the null hypothesis of "degradation > 5%" with [deferred] power.
- **Multiple Comparisons**: If multiple thresholds are tested for the "skip" condition, a correction (e.g., Bonferroni) will be applied to the significance level.
- **Collinearity**: Semantic and prosodic features may be correlated. The GRU model will be evaluated for feature importance, but independent effects will not be claimed if predictors are definitionally related.
- **Proxy MOS Validity**: The plan acknowledges that CLIP-based models may have poor correlation with human perceptual quality for video. If the proxy fails (r < 0.8), a domain-specific metric (e.g., VQ-VAE based) will be used as a fallback.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU and RAM resources).
- **Strategy**:
  - **No GPU**: All training and inference uses CPU.
  - **Model Size**: GRU hidden size $\le$ 256.
  - **Data**: Sampled to ≤ 1 GB.
  - **Libraries**: `torch` (CPU wheel), `scikit-learn`, `pandas`.
  - **Runtime**: Training loop optimized for early stopping if convergence is reached.

## Decision/Rationale

- **Why GRU?** Transformers are powerful but heavier. A shallow GRU is sufficient for time-series prediction of latent deltas and fits comfortably within the 7 GB RAM limit on CPU.
- **Why Stratified Bootstrap?** The "skip" decision is non-random (based on predicted low delta). Simple random sampling for significance testing would be biased. Propensity-score matching adjusts for the probability of a frame being "skippable", derived from the randomized intervention to avoid circularity.
- **Why TOST?** The goal is to prove *equivalence* (quality loss ≤ 5%), not just a difference. Standard t-tests cannot prove equivalence.
- **Why 5% Threshold?** Based on conservative estimates from video compression literature, providing empirical justification for the perceptual equivalence threshold.
- **Why Proxy MOS Fallback?** If CLIP proxy fails (r < 0.8), use a verified, domain-specific video quality metric (e.g., `video-fid` or `VQ-VAE` based metric) to ensure scientific soundness.
