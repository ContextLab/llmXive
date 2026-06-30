# Research: Reproduce & Validate Geometry-Aware Representation Denoising (GARD)

## 1. Problem Definition & Scope

The objective is to reproduce the GARD framework (arXiv:2605.26230) in a CPU-constrained environment (GitHub Actions free tier). The core challenge is adapting a likely GPU-accelerated 3D reconstruction pipeline to run within 7GB RAM and 2 CPU cores without losing the ability to generate valid 3D geometry and restored images. A critical methodological challenge is validating the "denoising" and "geometry-aware" claims in the absence of ground truth (GT) clean images or depth maps. The primary risk is circular validation: measuring "denoising" by simply comparing the output to the noisy input (which is a tautology). This research plan corrects this by establishing a **Gaussian Blur Baseline** and using **Blind Metrics** to prove the output is perceptually superior to simple smoothing.

## 2. Dataset Strategy

**Target Dataset**: DA3 (Depth Anything 3) benchmark format with degraded multi-view images.

**Verified Sources Analysis**:
The provided verified dataset list contains metadata and tokenized data but **no verified source for the raw image pixels** required for 3D reconstruction.
- `da3-giant-blind-spots` (CSV): Contains metadata only.
- `massive_5_lang_DA3_tokenized` (Parquet): Contains tokenized text/data, not images.
- `massive_val_DA3_tokenized` (Parquet): Tokenized data.

**Conclusion**: The verified sources do **not** contain the raw image data (RGB/Depth) necessary for the GARD pipeline.
**Action**: The plan assumes a sample dataset will be provided via the `data/` directory in the repository or a local mount. If the dataset is missing or lacks image files, the system MUST trigger a **Scientific Null** condition (distinct from a generic pipeline error). The error message will state: "Scientific Null: Raw image data missing. Validation of GARD claims impossible without input pixels."

**Dataset Loading Strategy**:
1.  Check for `data/da3_sample` directory.
2.  Verify presence of `.png`/`.jpg` files and corresponding depth maps (if applicable) using `gard_input.schema.yaml`.
3.  If missing, raise `FileNotFoundError` with the specific "Scientific Null" message.
4.  Do **not** attempt to download from unverified URLs.

## 3. Technical Approach & Constraints

### 3.1 Environment Constraints
- **Hardware**: 2 vCPU, ~7 GB RAM, No GPU.
- **Time Limit**: 6 hours.
- **Library Constraints**:
  - `torch`: Must use CPU-only wheel.
  - `transformers` (if used): Disable GPU acceleration flags.
  - **Forbidden**: `load_in_8bit`, `bitsandbytes`, `device_map="cuda"`, `torch.cuda`.

### 3.2 Adaptation Strategy
1.  **Pre-flight Check**: Scan the vendored `external/GARD` code for `cuda`, `gpu`, or `device_map` imports. If found, patch them to `cpu` or abort with `SC-004` error.
2.  **Memory Management**:
    - Process images in small batches if the dataset is large.
    - If the model requires >7GB RAM, the plan acknowledges this as a **fatal limitation** of the free-tier runner and logs a warning, but attempts to run with reduced resolution or subset.
3.  **Inference Pipeline**:
    - Load model weights (CPU).
    - Iterate through sample images.
    - Generate restored images and geometry.
    - Save to `outputs/`.

### 3.3 Control Group & Baseline (Corrected Methodology)
To address the "blurring vs. denoising" concern and avoid circular logic:
-   **Baseline**: Generate a Gaussian-blurred version of the input images (standard deviation tuned to match expected noise level).
-   **Comparison**: Compare GARD output against the **Baseline** using LPIPS and NIQE.
    -   **NIQE**: Lower NIQE indicates a more natural image. The goal is `NIQE(Output) < NIQE(Blur)`.
    -   **LPIPS**: Measures perceptual distance. We compare `LPIPS(Output, Blur)`. A significant distance implies the output is not just a blurred version of the input.
-   **Decision Logic**:
    -   **Success**: Output has better NIQE than the Blur baseline AND is perceptually distinct from the Blur baseline (indicating detail recovery, not just smoothing).
    -   **Failure (Over-Smoothing)**: Output NIQE is worse than or equal to the Blur baseline.
    -   **Failure (No Effect)**: Output is perceptually identical to the Noisy Input (LPIPS(Output, Input) ~ 0).

## 4. Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing Image Data** | Fatal (Scientific Null) | Explicit "Scientific Null" error; no generic crash. |
| **GPU Hardcoding** | Fatal (Runtime crash) | Pre-flight code scan; abort if CUDA required. |
| **OOM (Out of Memory)** | Fatal (Hanging) | Batch processing; explicit OOM catch with diagnostic. |
| **Slow Execution** | Timeout (>6h) | Use a minimal sample dataset; reduce image resolution. |
| **Circular Validation** | False Positive | Use Gaussian Blur baseline; compare Output vs. Blur (not Output vs. Noisy Input) for quality. |

## 5. Validation Plan

### 5.1 Functional Validation
1.  **Exit Code**: Must be 0.
2.  **Files**: `.ply` and `.png` generated.
3.  **Loadability**: Files loadable in `open3d` and `PIL`.

### 5.2 Scientific Validation (No Ground Truth)
Since GT is absent, the plan uses **Blind Metrics** and **Control Baselines** with corrected logic:
1.  **NIQE (Natural Image Quality Evaluator)**:
    -   Metric: `NIQE(Output)` vs `NIQE(Blur)`.
    -   Goal: `NIQE(Output) < NIQE(Blur)`. This proves the output is more "natural" than a simple blur.
2.  **LPIPS (Learned Perceptual Image Patch Similarity)**:
    -   Metric: `LPIPS(Output, Blur)`.
    -   Goal: Significant distance (not near zero). This proves the output is not just a blurred version of the input.
    -   *Note*: We do **not** use `LPIPS(Output, Input)` as the primary success metric, as a low distance there could mean "no denoising happened".
3.  **Geometry Consistency (Proxy)**:
    -   If DA3 depth estimator is available, compute reprojection error of GARD geometry vs. DA3 depth.
    -   If DA3 is unavailable, state "Geometry-Aware claim: Unvalidated (No Proxy Data)".

### 5.3 Reporting
The `reproduction_report.md` MUST explicitly state:
-   "Success" if all functional and scientific checks pass (NIQE(Output) < NIQE(Blur) AND significant LPIPS difference from Blur).
-   "Partial Success" if functional checks pass but scientific metrics are inconclusive (e.g., no proxy data).
-   "Scientific Null" if raw data is missing.
-   "Failure (Over-Smoothing)" if NIQE(Output) >= NIQE(Blur).

## 6. Decision Rationale

**Why CPU-only?** The spec explicitly requires `FR-001` (CPU-only execution). The free-tier runner does not support GPU.
**Why graceful failure on missing data?** The verified dataset sources do not contain the required raw images. A generic crash would be unhelpful. `FR-003` mandates a specific error message.
**Why no GPU quantization?** `load_in_8bit` requires CUDA. The spec forbids GPU dependencies.
**Why LPIPS/NIQE?** Standard variance metrics are tautological. LPIPS/NIQE provide a perceptual baseline to distinguish restoration from blurring.
**Why Gaussian Blur Control?** To isolate the effect of the model from simple smoothing.
**Why Corrected Logic?** The previous logic (comparing output to noisy input) was circular. Comparing output to a blur baseline (which represents the "worst case" of smoothing) provides a valid lower bound for quality. If the model cannot beat the blur baseline, it is not denoising.
