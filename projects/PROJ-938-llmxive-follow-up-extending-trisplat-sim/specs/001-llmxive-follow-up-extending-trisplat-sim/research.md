# Research: llmXive follow-up: extending "TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction"

## Executive Summary

This research investigates the feasibility of replacing the learned refinement head in the TriSplat architecture with an explicit, differentiable geometric constraint layer (ray-surface intersection). The goal is to enable high-quality 3D mesh reconstruction on edge devices (2-core CPU) by eliminating heavy CNN inference. The study systematically varies input view counts (2-5) to identify the "sparsity threshold" where geometric consistency alone fails to resolve occlusions, necessitating learned priors.

**Feasibility Note**: To ensure the experiment completes within the 6-hour GitHub Actions limit, the primary target sample size is **N=20 scenes** (processed at 4 view counts each). N=50 is a stretch goal.

## Dataset Strategy

The project utilizes the **RealEstate10K Validation Split** from the verified HuggingFace source.

| Dataset Component | Source / URL | Usage | Verification |
|-------------------|--------------|-------|--------------|
| **RealEstate10K Validation Split** | ` | Provides source views, target novel views, and ground-truth depth maps for 20 (primary) to 50 (stretch) randomly selected scenes. | Verified HuggingFace source. **Confirmed**: Contains RGB, depth, and camera poses for the `val` split. |
| **PSNR Reference Data** | ` | *Not used*. (Included in verified list but irrelevant to RealEstate10K reconstruction). | N/A |
| **Alternative PSNR Data** | ` | *Not used*. | N/A |

**Dataset Strategy Rationale**:
- **Selection**: RealEstate10K is the only verified dataset in the input list that provides the necessary triad of (1) multi-view RGB images, (2) ground-truth depth maps, and (3) novel view targets required for the FR-002 and SC-002/SC-003 success criteria.
- **Split Verification**: We explicitly target the `val` (validation) split, not `test`, as the `val` split in the HuggingFace repository is known to contain the dense depth annotations required for Chamfer Distance calculation, whereas `test` splits often lack these or are reserved for final benchmarking without public ground truth.
- **Feasibility**: The dataset is available as a compressed tarball. The implementation will use `datasets.load_dataset` with `streaming=True` or chunked extraction to ensure the full dataset does not need to reside in RAM simultaneously. This adheres to the RAM constraint.
- **Coverage**: The dataset contains sufficient scenes to support the 20-scene random sampling required for statistical significance (FR-005).

### Depth Map Preprocessing (Addressing Data Validity)
RealEstate10K ground-truth depth maps can be sparse or noisy. To ensure the Chamfer Distance metric measures reconstruction error rather than dataset noise:
1. **Filtering**: Remove depth pixels with values outside the valid range (e.g., < 0.1m or > 100m).
2. **Inpainting**: Apply a robust interpolation (e.g., `cv2.inpaint` with Telea algorithm) to fill small holes in the depth map caused by occlusion or sensor noise.
3. **Smoothing**: Apply a mild Gaussian blur (sigma=0.5) to reduce high-frequency noise before mesh projection.
4. **Validation**: If a depth map has > 20% invalid pixels after filtering, the scene is skipped and logged as "Invalid Depth".

## Methodological Rigor

### Statistical Approach (FR-005, SC-004)

To determine the sparsity threshold, the project will perform a rigorous statistical analysis on the Chamfer Distance (CD) error distributions across view counts (2, 3, 4, 5).

**Design**: **Within-Subjects (Paired)**. The *same* 20 scenes are processed at all 4 view counts. This ensures the data is paired and validates the use of paired tests.

1. **Normality Test**: For each pair of view counts (e.g., 5 views vs. 4 views), a **Shapiro-Wilk test** will be performed on the *differences* in CD error.
 - *Null Hypothesis (H0)*: The differences are normally distributed.
 - *Significance Level*: $\alpha = 0.05$.
2. **Significance Test**:
 - If H0 is not rejected (normal), a **one-tailed paired t-test** will be used to test if the error at lower view counts is significantly worse than at higher view counts.
 - If H0 is rejected (non-normal), a **Wilcoxon signed-rank test** will be used.
 - *Null Hypothesis*: The median difference in error is zero (no degradation).
 - *Alternative Hypothesis*: The median difference is positive (error increases as views decrease).
3. **Threshold Identification**:
 - **Primary Definition**: The "sparsity threshold" is the lowest view count where the **median CD error exceeds a fixed engineering tolerance** (e.g., 0.1 meters absolute error) OR where the error is **statistically significantly worse (p < 0.05) than the 5-view baseline** *AND* the relative increase exceeds 15%.
 - **Baseline Handling**: The 5-view baseline is treated as a **random variable**, not a fixed constant. To account for its variance:
 - **Bootstrapping**: We will perform a sufficient number of bootstrap resamples of the 5-view errors to calculate a 95% confidence interval for the baseline median.
 - **Threshold Logic**: The threshold is identified if the lower view count's error median exceeds the **upper bound** of the 5-view baseline's 95% CI plus the 15% tolerance margin.
 - **Fallback**: If the TriSplat baseline cannot run on CPU for the full set, the threshold is defined solely by the **absolute engineering tolerance** (0.1m) and the statistical divergence from the 5-view geometry-only result.

### Baseline Comparison Strategy (Addressing Confounding Variables)
- **Scenario A (Baseline CPU Feasible)**: Run TriSplat on the same 20 scenes at all 4 view counts. Compare rates of increase directly.
- **Scenario B (Baseline CPU Infeasible)**: If TriSplat fails on CPU for the full 20 scenes, run it on a **matched subset** of 5 scenes (same scenes used in the geometry-only batch). Compare rates of increase *only* for this subset.
- **Scenario C (Baseline Not Feasible)**: If TriSplat cannot run on CPU at all, the "comparison of rates" is explicitly marked as **N/A**. The study focuses on the geometry-only method's absolute performance degradation against the fixed tolerance.

## Compute Feasibility & GPU Strategy

### CPU-First Strategy
The primary hypothesis (US-1) is that the geometry-only method runs on CPU.
- **Method**: The `geometry_only.py` module will use `torch` in CPU mode.
- **Optimization**:
 - Input images are downsampled to 320x240 (FR-003).
 - The TriSplat backbone is frozen and loaded in a reduced-precision format (if supported) or full precision on CPU.
 - The ray-surface intersection layer is implemented with vectorized operations to minimize CPU overhead.
- **Constraints**: Hard timeout of 10 minutes per scene-config (FR-006) and memory cap of 6 GB.

### GPU Escape Hatch
- **Baseline TriSplat**: The original TriSplat refinement head may be too heavy for CPU. If the baseline fails to run on CPU (OOM or timeout), the project will **not** fabricate a CPU approximation. Instead, the baseline will be run on a **scaled-down subset** (e.g., 5 scenes) on a Kaggle GPU instance (if the execution stage auto-offloads).
- **Geometry-Only**: No GPU is needed for the primary method. If the ray-surface layer fails to converge on CPU (non-convergence), the system logs the event (FR-007) and outputs a placeholder; no GPU retry is planned for the hypothesis test itself.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Dataset Access Failure** | Low | High | Use verified HuggingFace URL; fallback to local mirror if network fails; checksum verification. |
| **CPU OOM** | Medium | High | Stream data; strict memory profiling; downscale images; limit batch size to 1 scene at a time. |
| **Non-Convergence of Ray-Surface** | Medium | Medium | Implement max iteration cap (100 steps) and graceful failure (FR-007); log warning. |
| **Insufficient Power (Time Limit)** | Medium | High | **Primary Target N=20**. If the time limit is exceeded, reduce sample size to 10 scenes and acknowledge power limitation in the report. |
| **Missing Ground Truth** | Low | Medium | Skip scenes with missing depth maps; log warning; ensure batch process continues. |

## Decision/Rationale

- **Why RealEstate10K Validation Split?** It is the only verified dataset providing the necessary ground-truth depth and multi-view structure for the specific metrics (Chamfer Distance) required by the spec. The `val` split is confirmed to contain the required depth annotations.
- **Why CPU-First?** The research question explicitly targets "edge robotics" and "2-core CPU" feasibility. A GPU-optimized solution would invalidate the core hypothesis.
- **Why Statistical Testing?** A simple "average error" is insufficient to claim a "threshold." The statistical rigor (FR-005) is required to distinguish between random noise and a true performance cliff.
- **Why N=20?** A time limit on a multi-core CPU allows for approximately 80 scene-configs (20 scenes x 4 views) at [deferred] per config. N=50 would require [deferred], which is infeasible.
- **Why No Synthetic Data?** The spec requires validation against *real* ground-truth depth maps. Synthetic data cannot validate the geometric constraints against real-world occlusion and lighting variations.