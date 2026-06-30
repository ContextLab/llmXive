# Research: Reproduce & Validate LocateAnything (Eagle)

## Overview

This research phase validates the feasibility of reproducing the "LocateAnything" paper's claims using the vendored `Eagle` codebase on a CPU-only environment. The primary focus is on the "Parallel Box Decoding" (PBD) mechanism's *correctness* and the evaluation pipeline's robustness.

## Dataset Strategy

The evaluation relies on **Ground Truth Bounding Box** datasets. However, **NO verified source** for bounding box annotations (e.g., Flickr30K-FG, RefCOCO) was found in the provided list of verified datasets. The datasets previously cited (clip-ViT, SimCSE) contain only image-caption pairs or embeddings, not bounding boxes.

| Dataset | Verified URL(s) | Usage | Notes |
|---------|-----------------|-------|-------|
| Flickr30K-FG (Ground Truth) | *NO verified source found in list* | Benchmark Evaluation (US-2) | **Critical Gap**: No verified URL with bounding boxes was found. |
| RefCOCO | NO verified source found | Not used | No verified source found. |
| **Synthetic Ground Truth** | N/A | **Primary Validation Strategy** | **Fallback**: Inject known bounding boxes into a subset of images from a verified caption dataset (e.g., `carlosejimenez/flickr30k_clip-ViT-B-32-caption_pairs` for images only) to validate the IoU pipeline. |

**Data Loading Strategy**:
- **Step 0.3** (Phase 0) will explicitly check for a verified dataset with bounding box annotations.
- **If Found**: Load images and bounding boxes from the verified source.
- **If Not Found** (Current State): The evaluation phase will use **Synthetic Ground Truth**.
    - Select a subset of images from a verified caption dataset (image only).
    - Programmatically inject known bounding box coordinates (e.g., center 50x50 patch) into the metadata.
    - Run the model to predict boxes.
    - Calculate IoU between predicted boxes and injected synthetic boxes.
    - **Result**: Validates the *pipeline* (IoU calculation) and *relative quality* (model > random), but does not validate *absolute accuracy* against real human annotations.

## Model & Compute Feasibility

### Hardware Constraints
- **CPU**: 2 cores (GitHub Actions free-tier).
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **Time Limit**: 6 hours.

### Model Loading Strategy
- **Device**: Explicitly set `device="cpu"`.
- **Quantization**: **Mandatory GGUF** (via `llama-cpp-python`) or small model variant (1-3B). 
    - **Prohibited**: `bitsandbytes`, `float32` (for 7B+), `float16` (for 7B+). These will OOM.
- **Precision**: Load GGUF `q4_0` or `q5_0` to fit within 7GB RAM (model + OS + image encoder).
- **PBD Mechanism**: 
    - If the vendored code uses CUDA kernels for PBD, the plan will implement a **CPU-Serial Fallback** (iterative decoding in Python/NumPy) to ensure the model generates boxes.
    - **Verification Metric**: "Correctness of Box Generation" (does it output a box?) AND "Relative Speedup" (Serial Time / PBD Time).
    - **Baseline**: To validate "High-Quality" (relative), the plan compares the model's output against a **Trivial Baseline** (e.g., random box or full-image box) on the same synthetic subset. If the model outperforms random, it passes the "relative quality" check.

### Statistical & Methodological Rigor
- **Sample Size**: The subset of 50 images is used **strictly for Pipeline Correctness Validation** and **Relative Quality** assessment. 
    - **Explicit Limitation**: A sample size of 50 is **statistically insufficient** to validate the "High-Quality" claim (SC-002) or estimate mean IoU with confidence for real-world performance. The plan **does not** claim to reproduce the paper's absolute accuracy numbers.
    - **Reframed Goal**: The goal is to verify that the code *runs* and *parses* correctly, and that the model performs better than a trivial baseline (relative quality).
- **Metric**: Mean IoU is calculated **only if** Ground Truth is available (Synthetic or Real). If not, the metric is "Parsing Success Rate".
- **Baseline**: To validate "High-Quality" (relative), the plan compares the model's output against a **Trivial Baseline** (e.g., random box) on the same subset. If the model outperforms random, it passes the "relative quality" check.
- **Causal Claims**: The reproduction does not claim causal effects; it validates the *implementation*. Claims about "speedup" are measured as the ratio of Serial Time to PBD Time (if PBD runs) or marked as "Unmeasurable" if PBD fails.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Model requires CUDA | High | Critical | Plan uses GGUF/CPU-Serial Fallback. If impossible, report "Hardware Incompatible". |
| OOM on CPU | High | High | Mandatory GGUF quantization. Float32/16 prohibited. |
| Ground Truth Missing | High | High | Switch to "Synthetic Ground Truth" mode for pipeline validation. |
| PBD not implemented in code | Medium | High | Check `external/Eagle` code. If missing, report "Code Discrepancy". |

## Decision Log

- **Decision**: Use GGUF Quantization instead of float16/32.
  - **Rationale**: Limited RAM capacity makes float32/16 impossible for large models. GGUF is the only CPU-tractable path.
- **Decision**: Sample 50 images for Pipeline Validation and Relative Quality, not Absolute Accuracy Validation.
  - **Rationale**: 50 images are insufficient for statistical power. The goal is to verify the *code runs* and *beats random*, not to reproduce the paper's *numbers*.
- **Decision**: Fallback to Synthetic Ground Truth if Real Ground Truth is missing.
  - **Rationale**: No verified bounding box dataset was found in the provided list. Fabricating IoU is scientifically invalid; Synthetic GT allows pipeline validation without fabricating real-world claims.
- **Decision**: Compare against Trivial Baseline for "Relative Quality".
  - **Rationale**: Validates that the model does *something* meaningful without claiming absolute accuracy.
- **Decision**: Measure Serial Fallback Time vs. PBD Time.
  - **Rationale**: Provides a relative speedup metric even on CPU, addressing the "Parallel" claim.
