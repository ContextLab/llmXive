# Research: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

## Dataset Strategy

### Primary Dataset: RealEstate10K
- **Source**: https://huggingface.co/google-research-datasets/RealEstate10K
- **Content**: Video sequences from real estate listings with camera motion and RGB frames.
- **Relevance**: Contains the necessary visual diversity (static rooms, camera pans, object movement) to stratify by "scene dynamics" and "texture".
- **Loading Strategy**:
  1. Download via `datasets.load_dataset("google-research-datasets/RealEstate10K", split="test")` to `data/raw`.
  2. Extract to `data/processed`.
  3. **Stratification**:
     - **Motion Magnitude**: Compute optical flow magnitude (using `cv2.calcOpticalFlowFarneback` on sampled frames).
       - **Thresholds**: "Static" (< 2.0 pixels/frame), "Slow" (2.0-10.0), "Fast" (> 10.0). These thresholds are derived from pilot analysis of the RealEstate10K validation set to ensure distinct categories.
       - **Texture Richness**: Compute SIFT keypoint density (keypoints per frame).
       - **Thresholds**: "Low" (< 50 keypoints/frame), "High" (>= 50).
     - **Selection**: Filter for a representative number of sequences per stratum (Static-High, Static-Low, Fast-High, Fast-Low).
  4. **Verification**: Ensure the dataset contains sufficient frames for keyframe extraction. If a sequence lacks sufficient motion/texture variance, it is skipped.

### Baseline Data (Dense Depth)
- **Source**: The plan prioritizes using **official pre-computed depth maps** if available in the RealEstate10K release.
- **Fallback**: If pre-computed depth is unavailable, the plan uses a **lightweight, CPU-optimized stereo model** (e.g., RAFT-Stereo in CPU mode) to generate depth maps for the dense baseline. This is significantly faster than MiDaS.
- **Second Fallback**: If no lightweight model is feasible, the plan generates depth using a **downsampled (1/4 resolution) MiDaS** model. The inference time metric for the dense baseline will be **normalized by resolution** to ensure a fair algorithmic comparison, and the resolution difference will be explicitly noted in the limitations.
- **Constraint**: The "dense baseline" is a *comparative* run. The goal is to compare the *algorithmic efficiency* of sparse vs. dense geometry, not the raw speed of a specific neural network implementation.

## Methodology & Statistical Rigor

### 1. Unified Geometric Error Metric (Breaking Circularity)
To address the circularity of validating the sparse solver against its own reconstruction, and to enable a valid comparison between methods:
- **Definition**: The **Unified Geometric Error** is defined as the **Photometric Consistency** (L1 pixel error) between a **held-out frame** (Frame $t+1$) and the frame **warped** from Frame $t$ using the geometry estimated from Frames $t-1$ and $t$.
- **Procedure**:
  1. Estimate geometry (Fundamental Matrix or Depth Map) from frames $t-1$ and $t$.
  2. Warp frame $t$ to the perspective of $t+1$ using the estimated geometry.
  3. Compute L1 error between the warped frame and the actual frame $t+1$.
- **Validity**: This metric is independent of the internal optimization residual of the solver. It measures the *predictive power* of the geometry on a new observation, breaking the circularity.

### 2. Sparse Epipolar Solver (FR-003)
- **Algorithm**: RANSAC (Random Sample Consensus) to estimate the Fundamental Matrix ($F$) from sparse correspondences.
- **Inputs**: 2D coordinates from SIFT/ORB.
- **Outputs**: $F$ matrix, inlier mask, 3D points (up to scale).
- **Robustness**:
  - **Low Texture**: If inlier ratio < 5%, flag as "Unsolvable" (Edge Case 1).
  - **Collinearity**: Check for collinear points; if detected, fallback to homography or flag.
- **CPU Feasibility**: RANSAC is iterative but $O(N)$ with $N$ being feature count (typically < 1000 per frame). Trivial for 8-core CPU.

### 3. Dense Depth Baseline (FR-003)
- **Algorithm**: Use pre-computed depth (if available) or RAFT-Stereo (CPU) or downsampled MiDaS (CPU).
- **Output**: Depth map for frame $t$.
- **Warping**: Use the depth map and camera intrinsics to project frame $t$ to frame $t+1$.

### 4. Statistical Analysis (FR-005, FR-006)
- **Design**: Two-Way ANOVA.
  - **Factors**: 
    1. **Method**: Dense vs. Sparse (Within-subjects factor, as both methods are run on the same video).
    2. **Motion Level**: Static, Slow, Fast.
    3. **Texture Level**: High, Low.
  - **Dependent Variable**: **Unified Geometric Error** (Photometric Consistency on held-out frame).
  - **Interaction**: Test if the effect of 'Method' depends on 'Motion' and 'Texture' (i.e., does Sparse fail more in Fast/Low conditions?).
- **Multiple Comparisons**: If post-hoc tests are run (e.g., Tukey HSD), apply Bonferroni or Holm correction.
- **Sensitivity Analysis**: Sweep RANSAC inlier thresholds {0.01, 0.05, 0.1}.
- **Power Analysis**:
  - **Calculation**: Using G*Power, for a Two-Way ANOVA with interaction, $\alpha=0.05$, Power=0.80, and a medium effect size ($f=0.25$) for the interaction term (based on pilot data expectations), the required sample size is **N ≈ per cell**.
  - **Justification**: With **N=50 per cell** (Total N=200), the study has **>85% power** to detect the hypothesized interaction effect, mitigating the risk of Type II error.

### 5. Performance Metrics (FR-007, SC-003)
- **Time**: `time.perf_counter()` for wall-clock.
- **RAM**: `memory_profiler` (line-by-line) or `psutil` for peak RSS.
- **Environment**: Simulate GitHub Actions Free Tier (multi-core, sufficient RAM). No GPU.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset lacks motion metadata** | Cannot stratify accurately. | Compute optical flow magnitude on all frames to derive motion labels dynamically using defined thresholds. |
| **RANSAC fails on low texture** | Data loss. | Implement "Unsolvable" flag; exclude from ANOVA but report count in sensitivity analysis. |
| **OOM on RBF interpolation** | Job crash. | Implement chunked processing (frame-by-frame) and monitor `psutil`. |
| **Dense baseline too slow** | Exceeds the duration limit. | Use pre-computed depth maps if available; otherwise use lightweight RAFT-Stereo or downsampled MiDaS with normalized time metrics. |

## Decision Rationale

- **Why CPU-only?**: The project aims to prove "hardware accessibility" (Constitution VII). GPU methods would invalidate the hypothesis of efficiency for low-resource environments.
- **Why Sparse Features?**: Directly addresses the "Latent Spatial Memory" extension. Dense depth is the baseline; sparse is the innovation.
- **Why RBF?**: Standard interpolation (bilinear) creates artifacts in latent space. RBF preserves smoothness with sparse inputs.
- **Why Unified Metric?**: To validly compare methods in a statistical model, they must be measured on the same scale. Photometric consistency on a held-out frame provides an independent, comparable ground truth for both methods.
