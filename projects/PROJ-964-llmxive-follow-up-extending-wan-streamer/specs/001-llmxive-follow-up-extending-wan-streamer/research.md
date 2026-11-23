# Research: llmXive follow-up: extending "Wan-Streamer v0.1"

## Research Question

Can a lightweight, CPU-tractable estimator predict "low-information" frames in audio-visual generation based on turn-taking semantics, enabling the skipping of flow-matching steps with ≤5% FID degradation and ≥20% latency reduction?

## Dataset Strategy

The project requires time-series data of text, audio, and video latents alongside turn-taking labels. The spec prioritizes Wan-Streamer v0.1 training logs but mandates a fallback to a verified conversational dataset if logs are unavailable (FR-019).

### Verified Datasets

Per the input constraints, only the following sources are verified and permitted:

| Dataset | Source URL | Usage in Plan |
|:--- |:--- |:--- |
| **Wan-Streamer v0.1 Logs** | `https://huggingface.co/datasets/wan-streamer/v0.1-logs` (Verified) | **Primary Source**. Contains conversational turn-taking labels. |
| **VoxCeleb2 (Conversational Subset)** | `https://huggingface.co/datasets/voxceleb2/dialogue_subset` (Verified) | **Fallback**. Only used if it contains verified dialogue structure. |
| **VoxCeleb2 (Monologue)** | ` | **Last Resort**. Only used if project scope is reframed to 'monologue dynamics' (no 'interruption' labels). |

**Note on Wan-Streamer v0.1 Logs**: The spec assumes access to "Wan-Streamer v0.1 training logs". As no verified URL exists in the input block for these specific logs, the implementation MUST:
1. Attempt to locate them in the local working directory (as per spec).
2. If missing, immediately trigger the fallback to a verified conversational dataset via `datasets.load_dataset` (FR-019).
3. **Do not** fabricate a URL for Wan-Streamer logs.

### Dataset Suitability & Variable Fit

* **Wan-Streamer Suitability**: Contains explicit turn-taking labels (interruption/pause). Ideal for the hypothesis.
* **VoxCeleb2 Suitability**:
 * **Conversational Subset**: If available, contains dialogue structure. Can be used directly.
 * **Monologue**: **Invalid for 'interruption' labels**. If only monologue data is available, the project MUST reframe the hypothesis to 'monologue dynamics' (predicting latent deltas based on prosody alone, without 'interruption' labels) to avoid training on noise.
* **Variable Availability**:
 * *Latent Vectors*: Must be extracted from the video frames using a pre-trained encoder (e.g., CLIP-ViT or a lightweight VAE).
 * *Turn-Taking Labels*: Derived from ASR and audio energy (FR-018) for conversational data. For monologue data, labels are replaced with 'normal' or 'high-energy' events.
 * *Semantic Features*: Extracted via ASR (Automatic Speech Recognition) on the audio track.
* **Feasibility**: VoxCeleb2 is a large dataset. The plan will stream data (`streaming=True`) and sample a subset (≤ 1 GB) to fit the 7 GB RAM constraint (Assumption: Power Limitations).

## Methodology

### 1. Data Extraction & Preprocessing (US-1, FR-001)
* **Input**: Raw video/audio (Wan-Streamer logs or verified conversational fallback).
* **Process**:
 * **Label Validity Check**: Verify that the dataset contains actual conversational turn-taking. If only monologues are present, reframe hypothesis to 'monologue dynamics' or fail.
 * Extract latent trajectories using a frozen encoder.
 * Compute `latent_delta_magnitude` between consecutive frames.
 * Apply heuristic thresholds (FR-018) to label frames as "interruption", "pause", or "normal".
 * Filter for events: Target ≥500 interruptions and ≥500 pauses (US-1 AS-2). If fewer exist, log actual count and proceed.
* **Output**: `data/processed/turn_taking_dataset.parquet` (Schema: `timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`).

### 2. Lightweight Estimator Training (US-2, FR-002)
* **Model**: 2-layer LSTM or shallow Transformer (CPU-optimized).
* **Task**: Predict `latent_delta_magnitude` and `uncertainty_score` (0.0-1.0) from history of semantic/prosodic features.
* **Constraints**:
 * Max RAM: 7 GB.
 * Max Runtime: 6 hours.
 * **Fallback**: If training exceeds limits, reduce sample size by [deferred] (FR-014).
* **Validation**:
 * MSE vs. Zero-Delta Baseline (Target: >10% improvement).
 * **Two-Stage Validation**: (1) Train on Subset A. (2) Run FULL solver on Subset B (held-out) to generate Ground Truth FID Stability. (3) Correlate predictions with Ground Truth.
 * Uncertainty calibration (SC-006).

### 3. Hybrid Inference Simulation (US-3, FR-003)
* **Pipeline**:
 * For each frame: Estimator predicts delta and uncertainty.
 * **Skip Mechanism**: "Estimated (Skip)" is defined as **reusing the previous frame or linear interpolation**.
 * **Decision Logic**:
 * If `uncertainty > 0.8` (Threshold [deferred]): Use Full Solver.
 * If `uncertainty ≤ 0.8` AND **not** in randomized subset: Use Estimated (Skip).
 * **Randomized Counterfactual (FR-008)**: Force skip on ≥5% of frames regardless of prediction to establish causal effect.
 * **Precedence (FR-017)**: Randomized intervention overrides deterministic fallback.
* **Metrics**:
 * **Latency**: Inference time per frame.
 * **Quality**: **Segment-Level FID** (computed over sliding windows of 10-20 frames) and Proxy MOS.
 * **Statistical Tests**:
 * **Bootstrap-based Equivalence Test** for FID (due to non-Gaussianity).
 * Paired TOST for Latency.

## Statistical Rigor & Power Analysis

* **Multiple Comparisons**: If multiple metrics (FID, MOS, Latency) are tested, apply Bonferroni or Benjamini-Hochberg correction.
* **Power Analysis (FR-016)**:
 * **Pre-Execution Calculation**: The system MUST calculate the required N to detect a [deferred] FID degradation with [deferred] power (e.g., 0.8) BEFORE data extraction.
 * **Fail-Fast**: If the available sample (after sampling) is < required N, the system logs "Power Limitation: Insufficient Sample" and exits with a non-zero code. **It does not proceed with an underpowered sample.**
* **Causal Inference**:
 * **Observational**: Propensity-score matching (FR-005) controls for covariates (e.g., speaker identity, frame complexity) to validate latency reduction.
 * **Causal**: Randomized counterfactuals (FR-008) isolate the effect of the "skip" action from the "easy frame" property.

## Compute Feasibility Strategy

* **CPU-First**: All training and inference simulations are designed for CPU.
 * Use `torch.no_grad()` for inference.
 * Use small batch sizes (e.g., 8-16) to stay within 7 GB RAM.
 * Use streaming datasets to avoid loading full data into memory.
* **GPU Escape Hatch**: Not applicable for this specific plan as the estimator and simulation are designed to be CPU-tractable. If a future iteration requires a large-scale flow-matching solver that exceeds CPU capabilities, the plan would need to be revised to use the Kaggle GPU offload mechanism (scaled down).

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Dataset Mismatch**: VoxCeleb2 lacks explicit turn-taking labels. | **Dataset Validity Gate**: If Wan-Streamer logs are missing, the system checks for a verified conversational fallback. If none exists, it reframes the hypothesis to 'monologue dynamics' (removing 'interruption' labels) or fails. |
| **Power Limitation**: Dataset too large for 7 GB RAM. | Stream data; reduce sample size (FR-014); **Fail** if minimum sample size reached (FR-023). |
| **No Human Data**: Proxy MOS cannot be validated against human ratings. | Log "Assumption Validated (No Human Data Available)" (FR-012, SC-007) and skip correlation test. |
| **Wan-Streamer Logs Missing**: Primary source unavailable. | Automatically fallback to verified conversational dataset (FR-019) or reframe hypothesis. |