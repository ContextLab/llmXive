# Research: DomainShuttle Reproduction & Validation

## Executive Summary

This research phase investigates the feasibility of reproducing the "DomainShuttle" text-to-video generation method on a CPU-only GitHub Actions runner. The primary challenge is adapting a likely GPU-optimized diffusion model to a constrained CPU environment with limited RAM and without CUDA acceleration. The strategy involves selecting a lightweight model variant, reducing temporal resolution (frame count), and rigorously validating that the output artifacts meet structural requirements using **CPU-optimized quantitative proxies** (CLIP similarity) rather than subjective human inspection.

**Key Methodological Decision**: To address the concern of confounding variables (hardware constraints vs. model performance), this research employs a **Resolution Sensitivity Analysis**. If the primary 16-frame run fails to meet fidelity thresholds, a secondary 8-frame run is triggered. This isolates whether failure is due to the hardware-imposed frame limit or the model's inherent inability to generate the content.

## Dataset Strategy

The reproduction of the inference pipeline does not require a large training dataset. The "dataset" for this task consists of:
1.  **Reference Image**: A single static image provided by the user (or a sample from the `assets/` folder).
2.  **Text Prompt**: A natural language description.
3.  **Model Weights**: Pre-trained weights for the `DomainShuttle` (likely based on `wan2.2` or similar architecture) downloaded from Hugging Face.

**Verified Datasets**:
- **Model Weights**: The plan relies on Hugging Face Hub for model weights. As per the spec, if the specific `DomainShuttle` weights are not publicly available as a verified dataset, the implementation will attempt to load the base model (e.g., `Wan2.2-Fun`) from the Hugging Face Hub.
- **Reference Data**: No external dataset URL is required. The spec explicitly states the assumption that "only a single reference image and a text prompt are required."

*Note: The verified dataset list provided in the prompt (FID, CLIP) is unrelated to this inference task and is not used.*

## Technical Feasibility Analysis

### 1. Compute Constraints (CPU vs. GPU)
The primary constraint is the lack of GPU. Diffusion models are computationally intensive.
- **Memory**: 7GB RAM is tight for modern video generation models which often require 12GB+ VRAM.
  - *Strategy*: Use `torch_dtype=torch.float32` (or `float16` if supported on CPU) and offload layers if possible. Drastically reduce the number of frames (e.g., 16 frames) to reduce the attention matrix size.
- **Time**: A reasonable time limit for processing a single short clip on CPU is established, provided the model size is manageable.
  - *Strategy*: Limit the number of inference steps (e.g., 20-30 steps instead of 50) to stay within the time budget.

### 2. Model Architecture Adaptation
- **Quantization**: The spec forbids `load_in_8bit` or `bitsandbytes` as they require CUDA.
  - *Decision*: Run in standard `float32` or `float16` (if CPU support is available in the specific `torch` version).
- **Architecture**: Assuming the `DomainShuttle` uses a standard UNet or DiT backbone, the inference logic can be adapted by setting `device="cpu"` in the `pipeline`.

### 3. Validation Metrics (Quantitative Proxy)
- **Quantitative**: Full FID/CLIP scores are not feasible without a large dataset and GPU.
  - *Decision*: Use a **CPU-optimized CLIP `ViT-B/32`** model. This model is small enough (~400MB) to run in float32 on CPU within 7GB RAM. It will compute the cosine similarity between the reference image and the generated video's first frame. This provides a **numerical fidelity score** (0.0-1.0) that can be averaged across the 3 independent runs to analyze variance (signal vs. noise).
- **Qualitative**: The report will focus on:
  - **Subject Fidelity**: Measured by the CLIP similarity score.
  - **Cross-Domain Flexibility**: Measured by text-image alignment score (CLIP text encoder vs. video frame).
  - **Structural Integrity**: Resolution, duration, and format.

## Resolution Sensitivity Analysis (Methodology Update)

To address the concern that reducing frame count (16) and resolution (512x512) introduces a severe confound:
1.  **Primary Run**: Execute with 16 frames.
2.  **Sensitivity Check**: If the primary run fails (fidelity_score < 0.5), execute a secondary run with 8 frames.
3.  **Attribution Logic**:
    - If 8-frame succeeds: The failure of the 16-frame run is attributed to **Hardware Constraint** (16 frames too large for model capacity under 7GB RAM).
    - If 8-frame also fails: The failure is likely due to **Model Incompatibility** or **Prompt Mismatch**.
This ensures the report does not falsely attribute hardware limitations to model failure.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **CPU-Only Execution** | Required by the GitHub Actions free-tier constraint. |
| **Reduced Frame Count (16)** | Necessary to fit the video tensor into 7GB RAM. Full resolution (e.g., 64 frames) would likely cause OOM. |
| **No Quantization** | `bitsandbytes` and 8-bit loading are CUDA-dependent. Running in `float32` is the only CPU-safe option, despite higher memory usage. |
| **Single Inference Run (x3)** | The goal is validation, not benchmarking. Three runs allow for variance analysis (signal vs. noise) without human raters. |
| **CPU-Optimized CLIP Proxy** | While full FID is infeasible, a single-image CLIP similarity score is computationally trivial on CPU and provides the necessary quantitative metric to replace subjective "Likert" ratings. |
| **Resolution Sensitivity Analysis** | Addresses the confound concern by isolating hardware constraints from model capability. |

## Risk Assessment

1.  **OOM (Out of Memory)**: High risk. Even with reduced frames, the model weights + activations might exceed 7GB.
    - *Mitigation*: Implement a "graceful exit" with a specific error code and memory log. If it fails, the report will state "Model too large for 7GB RAM constraint."
2.  **Timeout**: Medium risk. CPU inference for video can be slow.
    - *Mitigation*: Use a reduced number of diffusion steps (e.g., 20).
3.  **Missing Dependencies**: High risk. System libraries (ffmpeg, libgl) are often missing in minimal runners.
    - *Mitigation*: Explicitly install system dependencies in `install_deps.sh`.
4.  **CLIP Proxy Failure**: Low risk. The `ViT-B/32` model is well-supported on CPU.
    - *Mitigation*: Fallback to a simple pixel-difference metric if CLIP fails to load.
5.  **Confounding Variable**: High risk of misattributing failure to the model when it is actually the frame count.
    - *Mitigation*: **Resolution Sensitivity Analysis** as described above.

## Conclusion

The reproduction is feasible *if* the model weights are not excessively large (e.g., < 4GB) and the frame count is strictly limited. The plan prioritizes a "smoke test" approach: if a single 16-frame video can be generated and validated with a **quantitative CLIP score**, the core reproduction claim is supported. If the model is too large for 7GB RAM, the report will explicitly state this as a hardware limitation, which is a valid scientific finding. The use of a CPU-optimized CLIP proxy resolves the methodological concern of lacking quantitative metrics without violating compute constraints. The **Resolution Sensitivity Analysis** ensures that hardware constraints are not conflated with model failure.