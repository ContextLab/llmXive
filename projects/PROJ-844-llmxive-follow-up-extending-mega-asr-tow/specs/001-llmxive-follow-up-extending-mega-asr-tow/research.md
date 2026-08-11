# Research: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Dataset Strategy

The study requires a dataset of clean audio with valid transcripts to serve as the "ground truth" for stress testing. The spec mentions "Voices-in-the-Wild-2M", but this dataset is not in the **Verified datasets** block. Per the rules, we must use an open, directly-downloadable substitute that supports the same question (clean audio + transcript).

**Selected Dataset**: `hf-audio/open-asr-leaderboard` (AMI subset) and `mozilla-foundation/common_voice_17_0` (English subset).
*   **Rationale**: These datasets provide clean audio segments with high-quality transcripts, suitable for applying synthetic distortions.
*   **Verified Source**: Canonical Hugging Face dataset IDs: `hf-audio/open-asr-leaderboard` and `mozilla-foundation/common_voice_17_0`.
*   **Strategy**:
    1.  Load the `open-asr-leaderboard` (AMI) dataset via `datasets.load_dataset("hf-audio/open-asr-leaderboard", split="test")`.
    2.  Filter for English audio segments > 3s and < 15s.
    3.  Stratify by speaker ID and duration to ensure diversity.
    4.  Sample **N=100** clips for the CPU pilot (feasible within 6h) and **N=500** clips for the GPU primary run (required for f² ≥ 0.02 power).
    5.  **Note on "Voices-in-the-Wild-2M"**: Since no verified URL exists for this specific dataset, we proceed with the AMI/Common Voice mix as the valid open substitute for clean audio stress testing.

**Real-World Validation Data (FR-018)**:
*   **Requirement**: Validate synthetic distortions against ≥50 real-world noisy clips.
*   **Status**: No verified real-world dataset (DNS Challenge, CHiME-5) is available in the **Verified datasets** block.
*   **Action**: We will replace the 'real-world' validation with a **Synthetic Realism Check**. We will compare the spectral envelope of our synthetic distortions against the noise floor of the target dataset (AMI/Common Voice) to ensure they are physically plausible. The limitation (lack of real-world validation) will be explicitly noted in the final report.

## 2. Methodology & Statistical Rigor

### 2.1 Stress Curve Generation (FR-002, FR-024)
*   **Method**: Apply Cartesian product of 9 SNR levels (-10 to 30 dB) and 6 RT60 levels (0.1s to 0.6s) = 54 scenarios.
*   **Tool**: `pyroomacoustics` for room impulse response (RIR) generation and convolution; `torchaudio` for additive noise.
*   **Constraint**: Must run on CPU. We will process clips in batches of 10 to manage memory.
*   **Completeness Check (FR-017)**: Before generation, the system will verify that the source dataset supports the required diversity. If specific SNR/RT60 combinations are missing in the source metadata (unlikely for synthetic generation, but possible for stratification), a warning is logged and the final report notes the missing scenarios.

### 2.2 Semantic Similarity Score (FR-003, FR-010, FR-011, FR-022)
*   **Model**: `all-MiniLM-L6-v2` (Q801455).
*   **Metric**: Cosine similarity between clean transcript embedding and ASR hypothesis embedding.
*   **Normalization**: SSS will be normalized relative to the model's baseline SSS on clean audio (FR-010).
*   **Validation (FR-011)**:
    *   **Task**: Download a held-out subset of Common Voice English (≥100 samples) with human annotations.
    *   **Metric**: Pearson correlation between SSS and human-rated semantic integrity.
    *   **Composite Score**: To avoid p-hacking (data-dependent switching), we pre-register a **Composite Semantic Integrity Score** = 0.7 * SSS + 0.3 * (1 - PhonemeEditDistance). This composite score is used regardless of individual metric performance.
    *   **Gate**: If the correlation of the composite score with human judgment is < 0.6, the workflow halts (FR-016).

### 2.3 Collapse Intensity Identification (FR-021, FR-012)
*   **Algorithm**:
    1.  Compute first derivative of the SSS curve.
    2.  Identify inflection point (max negative derivative).
    3.  **Gate**: If SSS < 0.5 (normalized) AND WER > 2× baseline → Record inflection intensity.
    4.  **Fallback**: If no inflection, find first step where SSS < 0.5 AND WER > 2× baseline.
    5.  **Interpolation (FR-020)**: If SSS and WER thresholds cross at different steps, linearly interpolate the intensity.
*   **Curve Morphology (FR-012)**:
    *   Fit both a sigmoid and a linear model to each stress curve.
    *   Output the best-fit type (sigmoid/linear) and the maximum derivative as distinct fields.
*   **Edge Case**: If SSS never drops, record "None".

### 2.4 Regression & Interaction Analysis (FR-005, FR-013, FR-025)
*   **Model**: Hierarchical Linear Model (HLM) or Random Forest with SHAP.
*   **Features**: SNR, RT60, SNR², RT60², SNR×RT60.
*   **Target**: Collapse Intensity (continuous) or Binary (Collapse/No Collapse).
    *   **Clarification**: The target is the *boundary* (specific SNR/RT60 combination) where the composite score crosses the threshold. This is a non-trivial boundary detection problem, not a trivial prediction of the input grid, as the boundary varies by audio content.
*   **Universal Vector**: Compare coefficients across a set of ASR models (Whisper-tiny, Distil-Whisper, etc.).
*   **Multiple Comparison Correction (FR-008)**: **Benjamini-Hochberg False Discovery Rate (FDR)** correction applied to p-values of interaction terms across 54 scenarios. (Bonferroni is too conservative for correlated tests).
*   **Causal Framing (FR-007)**: All claims framed as associational. No causal inference without randomization.

### 2.5 Sensitivity Analysis (FR-006)
*   **Goal**: Ensure the 'critical interaction vector' is not an artifact of fixed thresholds.
*   **Method**:
    1.  Sweep SSS threshold across a range of values.
    2.  Sweep WER multiplier across a range of values.
    3.  Re-run regression for each combination.
    4.  Calculate variance of the interaction term coefficients (`SNR * RT60`) across sweeps.
*   **Output**: Report the standard deviation of the critical vector coefficients. High variance indicates instability.

## 3. Compute Feasibility & Escape Hatch

*   **CPU Plan**:
    *   **ASR**: `whisper-tiny` (CPU). Inference time ~-5s per 10s clip on 2-core CPU.
    *   **Embeddings**: `all-MiniLM-L6-v2` (CPU). Fast inference.
    *   **Distortion**: `pyroomacoustics` (CPU).
 * **Total Runtime**: [deferred] inferences (N=100). At 5s/inference = [deferred]. **CRITICAL**: Slightly exceeds 6h limit.
 * **Mitigation**: We will sample **N=80** clips for the CPU pilot to fit within 6 hours (80 × 54 × 5s [deferred]). This is a power limitation acknowledged in the plan.
*   **GPU Escape Hatch**:
    *   If the CPU run fails or is too slow, the execution stage will auto-offload to Kaggle GPU.
    *   **Scaled GPU Plan**: Run on 16GB VRAM, full N=500 clips, 54 scenarios. Use `device="cuda"`.
    *   **Decision**: The plan defaults to CPU for N=80 (Pilot). The primary scientific result (N=500) relies on the GPU escape hatch.

## 4. Decision Rationale

*   **Why AMI/Common Voice?** They are the only verified open datasets with clean audio and transcripts suitable for synthetic distortion stress testing.
*   **Why N=80 (CPU) vs N=500 (GPU)?** FR-001 requests N=500 for power, but CI limits (6h) make this infeasible on CPU. We prioritize running a *real* pipeline on a smaller sample over a fake CPU simulation. The GPU escape hatch allows the full N=500 if resources permit.
*   **Why Hierarchical Regression?** To isolate the "universal" interaction vector from model-specific noise (FR-025).
*   **Why FDR instead of Bonferroni?** The 54 tests are highly correlated (grid structure). Bonferroni would cause severe Type II errors (false negatives), failing to detect the small effect size (f² ≥ 0.02).

## 5. Deferred Parameters

*   **Sample Size**: N=80 (CPU Pilot), N=500 (GPU Primary).
*   **Correlation Threshold (FR-011)**: `[deferred]` (Target r ≥ 0.6 for composite score).
*   **R² Target (SC-001)**: `[deferred]` (Target > 0.6).
*   **Human Validation Subset Size**: `[deferred]` (Target ≥ 100 samples).
