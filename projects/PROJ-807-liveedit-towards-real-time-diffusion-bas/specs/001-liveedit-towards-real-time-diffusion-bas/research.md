# Research: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

## Problem Statement

The goal is to reproduce and validate the claims of the "LiveEdit" paper (Paper #408) regarding real-time diffusion-based streaming video editing. The core challenge is adapting a likely GPU-optimized research codebase (`author-kit`) to run on a CPU-only CI environment (GitHub Actions Free Tier) while maintaining the integrity of the "three-stage distillation" and "AR-oriented mask cache" mechanisms. 

**CRITICAL METHODOLOGICAL SHIFT**: Because the target environment (CPU) differs from the paper's likely environment (GPU), absolute FPS comparisons are scientifically invalid. The validation strategy now relies on **Relative Metrics**: comparing the Distilled model against a Non-Distilled Baseline on the *same* CPU hardware. This isolates the algorithmic efficiency gain and stability improvements from hardware variance.

**SPEC CONFLICT ALERT**: The project's `spec.md` Success Criteria (SC-002, SC-003) mandate absolute thresholds (±20% of 12.66 FPS, ≥30dB PSNR) that contradict this revised methodology. The research will enforce the scientifically valid relative metrics but will explicitly flag these SCs as "Spec-Root Cause" blocking gaps.

## Dataset Strategy

The project relies on **vendored sample data** within the `external/author-kit` submodule, as per the project's assumption that no external downloads are required for the benchmark.

| Dataset/Resource | Source/Location | Variables/Content | Fit for Purpose |
| :--- | :--- | :--- | :--- |
| **Sample Video Clip** | `external/author-kit/samples/` (Vendored) | Raw video frames (H.264/MP4), 720p resolution, ≤5s duration. | **High Fit**: Sufficient to test inference speed and background stability without exceeding RAM. |
| **Mask Definitions** | `external/author-kit/samples/` (Vendored) | Binary masks (PNG/NPY) corresponding to video frames. | **High Fit**: Required for the "AR-oriented mask cache" logic. |
| **Distillation Weights** | `external/author-kit/models/` (Vendored) | Pre-trained diffusion model weights (CPU-compatible). | **High Fit**: Essential for the "three-stage distillation pipeline". |
| **Static Calibration Video** | `external/author-kit/samples/static.mp4` (Synthetic/Vendored) | A video with identical frames (or a static scene). | **High Fit**: Required to measure the "Noise Floor" for flicker detection calibration. |

**Note**: No external datasets (e.g., DAVIS, YouTube-VOS) are used. The validation is strictly against the provided sample data to ensure CI reproducibility. If the vendored data is missing, the system will fail with a "Missing Sample Data" error (Edge Case).

## Methodology & Statistical Rigor

### 1. Inference Speed Measurement (Relative Speedup)
*   **Method**: 
    *   Run the **Distilled** model on the CPU sample video. Measure wall-clock time `T_distilled`.
    *   Run the **Non-Distilled (Baseline)** model (standard diffusion without the streaming optimization) on the *same* CPU and video. Measure wall-clock time `T_baseline`.
    *   Calculate **Relative Speedup** = `T_baseline / T_distilled` (or `FPS_distilled / FPS_baseline`).
*   **Statistical Handling**:
    *   **Hardware Variance**: Eliminated by running both models on the same hardware.
    *   **Reproducibility**: The benchmark will be run multiple times for each model, and the median time will be used.
*   **Success Metric**: Relative Speedup ≥ 1.0 (Distilled is faster or equal). The "Real-Time" claim is validated by demonstrating the *relative* efficiency gain of the distillation method, not by matching an absolute GPU FPS number.
*   **Spec Conflict**: SC-002 mandates ±20% of 12.66 FPS. This is a **category error** (CPU vs GPU). The plan will log absolute CPU FPS as a "Feasibility Metric" but will treat SC-002 as **BLOCKED** due to the spec's invalid requirement.

### 2. Background Stability (Relative PSNR/SSIM)
*   **Method**:
    *   Generate Output A (Distilled) and Output B (Baseline/No-Edit) for the same input.
    *   Extract non-masked regions from both outputs.
    *   Compute **PSNR** and **SSIM** between Output A (Distilled) and Output B (Baseline).
    *   *Correction*: Do not compare Output to Input (tautological). Compare Distilled vs. Baseline to measure *degradation* caused by the distillation process.
*   **Statistical Handling**:
    *   **Success Metric**: Distilled PSNR is expected to remain comparable to the Baseline PSNR, with only minimal degradation (e.g., < 5% drop).
    *   **Multiple Comparisons**: If multiple clips are tested, report mean and std dev of the degradation ratio.
*   **Spec Conflict**: SC-003 mandates ≥ 30 dB. This is **arbitrary** without a baseline. The plan will enforce the relative degradation metric but will treat SC-003 as **BLOCKED** if the absolute threshold is not met.

### 3. Flicker Detection (Temporal Stability)
*   **Method**:
    *   **Noise Floor Calibration**: Process a "Static Video" (identical frames) through the Distilled pipeline. Compute the frame-to-frame difference (L2 norm) of the background. Calculate the Mean (`μ_noise`) and Standard Deviation (`σ_noise`) of this difference. This establishes the pipeline's inherent noise floor.
    *   **Flicker Measurement**: Process the actual Sample Video. Compute the frame-to-frame difference of the *Output Background* pixels (Output(t) vs Output(t+1)).
    *   **Metric**: `Flicker Score = Mean(Background_Diff) / σ_noise`.
*   **Statistical Handling**:
    *   **Threshold**: The Flicker Score must be < 3.0 (i.e., induced flicker is within 3 standard deviations of the pipeline noise).
    *   **Validation**: Automated script will flag any sequence where the score exceeds 3.0.

### 4. Chunk Boundary Artifact Test
*   **Method**:
    *   For a video processed in chunks (e.g., Chunk 1 ends at frame 30, Chunk 2 starts at frame 31).
    *   Compute the difference between the last frame of Chunk 1 and the first frame of Chunk 2 in the *Output* video.
    *   Compare this difference against the global frame-to-frame variance of the background.
*   **Success Metric**: Boundary difference < 1.5 * Global Background Variance.
*   **Spec Gap**: The `spec.md` Success Criteria (SC-001 to SC-005) do not include a specific pass/fail condition for this test. The plan implements this test with the above threshold but will flag the lack of a corresponding SC as a **blocking gap**.

## Technical Feasibility & Constraints

### Memory Management (7GB RAM)
*   **Challenge**: Diffusion models and video buffers are memory-intensive.
*   **Solution**:
    *   **Chunked Processing**: The pipeline will process the video in short temporal chunks.
    *   **Lazy Loading**: Video frames will be decoded on-the-fly using `opencv-python` rather than loading the entire video into a numpy array.
    *   **Garbage Collection**: Explicit `del` and `gc.collect()` calls after each chunk to free memory.
*   **Risk**: If the model weights themselves exceed a substantial threshold, the 7GB limit may still be breached.
    *   **Mitigation**: The plan assumes the "distilled" model is lightweight (as per paper title). If weights are too large, the plan will fail, and the spec will need to be updated to allow model quantization (8-bit) or a smaller sample.

### CPU-Only Execution
*   **Challenge**: `diffusers` and `torch` often default to CUDA.
*   **Solution**:
    *   Force `torch.device("cpu")` in the runner.
    *   Ensure `torch` is installed via the CPU-only wheel (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
    *   Disable any CUDA-specific optimizations in the `author-kit` config.

### Edge Case Handling
*   **Missing Masks**: The `validators.py` module will check for the existence of mask files before execution. If missing, it logs "ERROR: Missing mask" and exits with code 1 (Graceful Failure).
*   **Corrupted Weights**: The runner will attempt to load model weights with a checksum verification (if available) or a `try-except` block catching `OSError`/`RuntimeError`. It will exit with "Model Integrity Failed".
*   **OOM**: The chunked processing strategy is the primary defense. If OOM occurs, the system will catch the exception, log "OOM: Reduce chunk size", and exit.

## Decision Rationale

1.  **Chunked Processing vs. Full Load**: Full load is rejected due to the RAM constraint. Chunking is the only viable path for 720p video.
2.  **CPU-Only Build**: GPU is unavailable in the target CI. The plan accepts lower FPS as a trade-off for feasibility, focusing on the *validity* of the method via relative comparison.
3.  **Relative Metrics vs. Absolute Thresholds**: Absolute thresholds (e.g., 30dB PSNR, 12.66 FPS) are invalid without a baseline or matching hardware. Relative comparisons (Distilled vs. Baseline) isolate the algorithmic contribution.
4.  **Automated Metrics vs. Visual Inspection**: Automated PSNR/SSIM and frame-difference are required for SC-003 and SC-004 to be objectively verifiable in CI.
5.  **Noise Floor Calibration**: Essential to define flicker thresholds scientifically, avoiding arbitrary static values.
6.  **Chunk Boundary Test**: Essential to ensure the memory-saving strategy (chunking) does not introduce the very artifacts (flickering) the method aims to prevent.