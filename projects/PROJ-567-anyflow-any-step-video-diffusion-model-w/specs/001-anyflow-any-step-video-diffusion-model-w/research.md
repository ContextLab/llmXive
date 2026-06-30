# Research: AnyFlow Reproduction & Validation

## Executive Summary

This research phase validates the feasibility of reproducing the "AnyFlow" video diffusion model on a GitHub Actions free-tier runner (CPU-only, 7GB RAM, 6h limit). The primary constraint is the computational cost of video diffusion, which typically requires high-end GPUs. The strategy relies on using the smallest available model variant (targeting a parameter scale that fits within available RAM constraints). and heavily optimizing the inference pipeline for CPU execution.

**Critical Scope Note**: The goal is to validate the *methodological viability* of the AnyFlow flow-map distillation on CPU (i.e., can the logic execute and produce a coherent video?), not to reproduce the high-resolution results of the 14B model. Comparing a CPU-downscaled output to the paper's 14B GPU baseline is scientifically invalid; therefore, the validation focuses on whether the method produces *coherent video* and *validates the flow-map logic* under constraints.

## Dataset Strategy

The project does not use a traditional "dataset" of video files for training, as it is a reproduction of an inference pipeline. The "test data" consists of the **text prompts** used to generate the artifacts.

| Asset Type | Source | Verification Status | Usage |
|------------|--------|---------------------|-------|
| **Prompt Set** | VBench Official Prompt List (Public) | Verified (URL below) | Input text prompts for generation (e.g., "a cat walking", "sunset over mountains"). |
| Model Checkpoint | HuggingFace (Wan / AnyFlow) | Verified (URL below) | Inference weights (1.3B if available, else 14B with quantization) |
| Evaluation Metrics | `opencv-python`, `scikit-image` | Verified (CPU-native) | Compute SSIM (temporal consistency) and Optical Flow (motion activity) on CPU |
| Reference Claims | Paper Abstract/Tables (Hardcoded) | Verified (Source: Paper) | Textual descriptions of expected behavior (e.g., "smooth motion", "high fidelity") |

**Note on Dataset Fit**: The "variables" are the generated video frames. The research confirms that **SSIM** (Structural Similarity), computed between adjacent frames, serves as a valid CPU-tractable proxy for **Temporal Consistency** (flicker reduction). **Optical Flow Magnitude**, computed via `opencv` `calcOpticalFlowFarneback`, serves as a valid proxy for **Motion Activity** (amount of movement). These metrics do *not* measure "Aesthetic Quality" (composition, lighting) which requires GPU-accelerated feature extractors (CLIP/ViT) and is therefore marked as "Unmeasurable" in the report. The validation is internal to the generated artifacts from the **Prompt Set**.

## Model Strategy

**Target Model**: AnyFlow / Wan2.1 1.3B (Hypothesis A) OR 14B (Hypothesis B).
**Rationale**: The large-scale variant is computationally intractable on a CPU runner with limited memory without extreme measures. The 1.3B variant is the primary candidate.
**Feasibility Gate**: **If the 1.3B model is not publicly available or cannot be loaded within 7GB RAM, the project scope is immediately narrowed to a "Feasibility Study" of the 14B model with extreme quantization, or the project is marked "Blocked" pending a larger runner.** The plan does not proceed with a "downscaled 14B" assumption as a valid reproduction of the 1.3B claims.

**Inference Configuration**:
- **Device**: CPU (Explicitly set `device="cpu"`).
- **Precision**: `float32` (default for CPU stability) or `float16` (if supported by CPU torch).
- **Steps**: Minimal (e.g., 4-8 steps) to reduce runtime.
- **Resolution**: Lowest supported by the model (e.g., 256x256 or 64x64).

## Statistical & Methodological Rigor

Since this is a deterministic reproduction of an existing model (inference only), statistical power analysis is not required for the generation step. However, the **validation** of the paper's claims requires rigor:

1.  **Metric Selection**:
    - **Primary (Temporal Consistency)**: **SSIM (Structural Similarity Index)** computed between adjacent frames. *Rationale: Measures flicker and structural stability, a prerequisite for "smoothness".*
    - **Primary (Motion Activity)**: **Optical Flow Magnitude** (via `opencv` `calcOpticalFlowFarneback`). *Rationale: Measures the amount of motion, distinguishing static frames from moving ones.*
    - **Primary (Validity)**: **Frame Variance** to detect static/black frames.
    - **Excluded**: **Aesthetic Quality** (e.g., CLIP-based scores). *Rationale: Requires GPU; not measurable on CPU. The report will explicitly state "Aesthetic Quality: Unmeasurable on CPU".*
2.  **Baseline Comparison**: The generated scores will be compared against **Reference Claims** (textual descriptions from the paper, e.g., "smooth motion", "no flicker"). **No numeric comparison to the paper's 14B baseline is performed** as it is scientifically invalid due to scale mismatch.
3.  **Limitations**: The comparison is limited by the reduced resolution and step count required for CPU execution. The report will explicitly state these deviations. **No claim of "fidelity" to the 14B paper results will be made.**

## Compute Feasibility Analysis

**Hardware Constraints**: 2 CPU cores, ~7 GB RAM, 14 GB disk, 6h limit.

| Component | Estimated RAM Usage | Estimated Runtime | Feasibility |
|-----------|---------------------|-------------------|-------------|
| Python Env + Dependencies | ~1 GB | < 5 min | ✅ |
| Model Loading (1.3B) | ~2-3 GB | < 10 min | ✅ |
| Model Loading (14B w/ quant) | ~5-6 GB | < 20 min | ⚠️ (Borderline) |
| Inference (a video, 4 steps) | ~4-5 GB (peak) | 30 min - 2 hours | ⚠️ (Borderline) |
| SSIM / Optical Flow Eval | ~2 GB | 5-10 min | ✅ |
| **Total** | **< 7 GB** | **< 3 hours** | **✅ (Conditional)** |

**Risk**: The 1.3B model might still exceed 7GB RAM when loaded with the full Diffusers pipeline overhead.
**Mitigation**:
- Use `torch.load` with `map_location="cpu"`.
- Disable unnecessary caches.
- If OOM occurs, the implementation will catch the error and report a "Memory Limit Exceeded" status, fulfilling the edge case requirement.

## Verified Datasets & Sources

- **Model Checkpoint**:
  - **Primary Hypothesis**: 1.3B variant (URL unverified, to be confirmed in Phase 0).
  - **Fallback (Verified)**: Wan2.1 14B on HuggingFace: `https://huggingface.co/Wan-AI/Wan2.1-T2V-14B`.
  - **Note**: The plan treats the 1.3B variant as a hypothesis. If not found, the 14B variant is the fallback, with the understanding that this changes the scientific question to "AnyFlow on CPU with downscaled architecture" and the project may be blocked if 14B exceeds RAM.
- **Prompt Set**: VBench Official Prompt List (Publicly available in the VBench repository).
- **Evaluation Tools**: `opencv-python` (CPU-native), `scikit-image` (CPU-native).

## Decision Rationale

**Decision**: Proceed with 1.3B model (if available) or 14B with quantization, and CPU-tractable metrics (SSIM/Optical Flow).
**Rationale**: This is the only path that satisfies the "free-tier CI" constraint. A 14B model would require >20GB RAM even with quantization, making it impossible to run on the specified runner without extreme downsampling. The goal is to demonstrate the *pipeline* and *validity* of the method (flow-map distillation) on CPU, not to reproduce the full-scale quality of the paper's 14B results.

## Open Questions

1.  Is the 1.3B model publicly available on HuggingFace? (If not, the project scope changes to "Smallest Available" and the baseline comparison is adjusted).
2.  Does the `opencv` implementation of Optical Flow provide sufficient sensitivity for "motion activity" on low-res videos? (If not, the metric will be adjusted).
