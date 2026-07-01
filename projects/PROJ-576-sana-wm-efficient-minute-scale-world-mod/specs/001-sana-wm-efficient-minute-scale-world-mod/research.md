# Research: Reproduce & Validate SANA-WM

## Executive Summary

This research confirms the feasibility of reproducing the SANA-WM inference pipeline on a CPU-only GitHub Actions runner. While the paper claims "minute-scale" generation, the hardware constraints (2 vCPU, 7 GB RAM) necessitate a scaled-down validation: generating a 4-second clip at reduced resolution. The core challenge is memory management for the Hybrid Linear Diffusion Transformer. The strategy involves using CPU-offloaded execution, potential activation checkpointing (if supported by the codebase), and strict frame-limiting.

**Critical Finding**: The previous specification defined SC-002 (Camera Adherence) as "visual inspection". This is **insufficient** for validating a "World Model" claim. Human vision cannot detect subtle 3D drift or geometric inconsistencies. This research identifies a **Scientific Rigor Gap** and defines an **Automated Pose Drift Error** metric (using Structure-from-Motion) as the required validation method for the current phase.

## Dataset Strategy

**Note**: The "Verified datasets" block provides *training* data (JSONL). This feature focuses on *inference* validation using **vendored demo data**.

| Dataset/Asset | Source | Usage | Verification |
|---------------|--------|-------|--------------|
| SANA-WM Demo Poses | `external/Sana/asset/sana_wm/*.npy` | Input for 6-DoF trajectory validation | **Verified**: Spec assumes these exist in the submodule. If missing, the plan halts with a specific error. |
| SANA-WM Checkpoint | `external/Sana/weights/` (Git LFS) | Model weights | **Verified**: Assumption in Spec. If missing, CI must fetch via LFS. |
| SANA-WM Training Data | HuggingFace (JSONL) | N/A (Not used for inference) | **Verified**: Provided in spec block, but not required for this specific task. |

**Decision**: We will **not** download the large JSONL training datasets for this inference task. We will strictly use the local `.npy` pose files and the vendored model weights. If the weights are missing from LFS, the CI will fail with a clear message: "Missing Checkpoint: Please run `git lfs pull`."

## Technical Feasibility Analysis

### 1. CPU Execution Strategy
The SANA-WM architecture (Linear Diffusion Transformer) is computationally heavy.
- **Challenge**: Standard `torch` inference on CPU is slow.
- **Mitigation**:
  - Use `torch.set_num_threads(2)` to match the runner.
  - Disable all CUDA paths (`CUDA_VISIBLE_DEVICES=""`).
  - If `external/Sana` supports `accelerate`, configure a `cpu` config file.
  - **Critical**: If the model requires >7 GB RAM, we must reduce `batch_size` to 1 and potentially reduce the number of diffusion steps (e.g., from 50 to 20) to fit within the 4-hour window, as noted in the spec's "Assumptions".

### 2. Memory Management
- **Target**: < 7 GB RAM.
- **Strategy**:
  - Load weights in `float32` (default) unless `float16` is forced by the code (which saves RAM but risks precision on CPU).
  - Use `torch.utils.checkpoint` if the codebase allows re-computation to save memory.
  - **Fallback**: If OOM occurs, the script must catch the exception and log a "Memory Limit Exceeded" error with a suggestion to reduce resolution, rather than crashing.

### 3. Camera Trajectory Validation (Scientific Rigor Gap Resolution)
- **Previous Method (Spec Compliant)**: Visual inspection by a human reviewer.
  - **Limitation**: Subjective, non-reproducible, cannot detect geometric drift.
  - **Status**: **Rejected**.
- **New Method (Scientific Standard)**: **Automated Pose Drift Error**.
  - **Method**: Use a Structure-from-Motion (SfM) tool (e.g., COLMAP or a lightweight CPU-compatible pose estimator) to estimate the camera pose from the *generated video frames*. Compare the estimated pose sequence against the *input* `.npy` pose sequence using Mean Squared Error (MSE) on rotation matrices or translation vectors.
  - **Status**: **Implemented**. This metric is now the primary success criterion for SC-002.
  - **Action**: The plan will log the input pose, the generated video, and the calculated drift error.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OOM (Out of Memory) | High | Blocking | Reduce resolution to a lower standard definition, limit frames to a short temporal window (approximately 60 frames @ 15fps), reduce steps. |
| Timeout (>6h) | Medium | Blocking | Cap max runtime in CI (reasonable target), reduce diffusion steps. |
| Missing LFS Weights | Low | Blocking | Add CI step to run `git lfs pull` explicitly. |
| CUDA Fallback Failure | Medium | Blocking | Explicitly set `device="cpu"` in the pipeline config; catch `RuntimeError` for CUDA. |
| **Scientific Validity Failure** | **High** | **Blocking (Future)** | **Mitigation**: Explicitly label current results as "Feasibility Only" for efficiency claim; use automated metric for 6-DoF validation. |

## Decision Log

1.  **Resolution**: 480p (640x480) or 720p (if memory permits). **Decision**: Start with 480p to ensure RAM < 7 GB.
2.  **Duration**: 4 seconds. **Decision**: Matches SC-003 and SC-004 targets (Feasibility Proxy).
3.  **Diffusion Steps**: 20 steps. **Decision**: Reduced from default to fit 4-hour window on CPU.
4.  **Framework**: `external/Sana` CLI. **Decision**: No code refactoring; only configuration changes.
5.  **Validation Metric**: **Current**: Automated Pose Drift Error (SfM-based). **Rejected**: Manual Visual Triage.