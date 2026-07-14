# Research: llmXive follow-up: extending "LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing"

## 1. Research Question & Hypothesis

**Research Question**: Under what specific motion characteristics (optical flow magnitude, divergence) does replacing attention-based temporal modeling with optical flow priors in video editing lead to statistically significant artifact generation, and what is the resulting memory/quality trade-off?

**Hypothesis**: The proposed "Flow-Coherence" module will significantly reduce peak memory usage and inference latency compared to the baseline LiveEdit model. However, this reduction will come at the cost of temporal stability (increased flickering) in high-dynamic scenes, with a distinct threshold of optical flow magnitude where the error distribution shifts significantly.

## 2. Dataset Strategy

The study requires a dataset of video clips stratified by motion complexity. The following sources are used, strictly adhering to the "Verified datasets" block:

| Dataset | Source URL | Usage | Verification Status |
|---------|------------|-------|---------------------|
| **DAVIS Subset** | ` (Metadata) / `j-hartmann/davis` (Video) | Source for video clips with known motion characteristics. | Verified (Metadata Parquet; Video via verified HF loader) |
| **YouTube-VOS Subset** | ` (Metadata) / `facebook/youtube-vos` (Video) | Source for diverse, complex motion clips. | Verified (Metadata Parquet; Video via verified HF loader) |
| **SSIM Reference** | ` | Reference for SSIM calculation methodology (not direct input). | Verified |

**Data Loading Strategy**:
- The plan uses the `datasets` library to load video frames from verified HuggingFace repositories (e.g., `j-hartmann/davis`).
- If a verified URL points only to metadata (Parquet), the plan will use a pre-downloaded subset of video files hosted in the repo's `data/raw/` (with checksums) to ensure reproducibility, citing the original verified URL as the source of truth.
- **Sample Size**: Reduced to **50 clips** to ensure feasibility within the 6-hour GHA limit.
- **Stratification**: Clips are assigned to categories based on **quantitative flow magnitude**:
 - **Static**: Mean flow magnitude < 0.5 px
 - **Slow Rigid**: 0.5 px ≤ Mean flow magnitude < 5.0 px
 - **Fast Non-Rigid**: Mean flow magnitude ≥ 5.0 px
 - *Note*: These thresholds are computed from the flow fields of the candidate clips to ensure objective stratification.

**Dataset Preprocessing**:
- **Synthetic Masks**: Generated programmatically for each clip to simulate editing targets.
- **Optical Flow**: Pre-computed using `cv2.calcOpticalFlowFarneback` (CPU-optimized) or `RAFT-small` (if CPU-wheel available) for all clips.
- **Validation**: Ensure every clip has a corresponding flow field. If flow estimation fails (NaN/Inf), mark as `invalid_flow` and apply identity warp.

## 3. Methodology

### 3.1. Baseline Execution (US-1)
- **Model**: **LiveEdit architecture with temporal attention layers ENABLED**. This is the true baseline for comparison.
- **Input**: Stratified video clips with synthetic masks.
- **Output**: Edited video frames, peak memory, FPS, SSIM (consecutive frames), **Background Stability Score (BSS)**, **Flow-Normalized SSIM**.
- **Constraint**: Must run on CPU-only runner.

### 3.2. Flow-Coherence Module (US-2)
- **Modification**: **LiveEdit architecture with temporal attention layers REMOVED**, replaced by Flow-Coherence module.
- **Mechanism**: Warp latent features from $t-1$ to $t$ using pre-computed optical flow.
- **Edge Case Handling**: If flow vector is invalid (NaN/Inf), apply identity warp and flag `invalid_flow`.
- **Output**: Same metrics as baseline.

### 3.3. Metric Collection (Updated for Validity)
- **Background Stability Score (BSS)**:
 - *Definition*: SSIM calculated between the **background region** of the edited frame $t$ and the **background region** of the **original frame $t$** (or a warped version of frame 0 if motion is present).
 - *Purpose*: Isolates geometric warping errors from valid motion. Prevents circular validation where the warp operation itself guarantees high SSIM.
- **Flow-Normalized SSIM**:
 - *Definition*: Raw SSIM drop divided by the optical flow magnitude for the frame.
 - *Purpose*: Distinguishes between artifacts caused by motion freezing (high SSIM drop, low flow) and valid motion tracking. Normalizes the metric against expected motion magnitude.
- **Temporal Gradient Variance**: Calculated on background regions to quantify instability.
- **Resource**: Peak RAM (using `psutil`), Inference Time per frame.

### 3.4. Statistical Analysis (Updated for Threshold Identification)
- **Primary Method: Piecewise Regression (Change-Point Detection)**:
 - *Model*: Error metric (BSS or Flow-Normalized SSIM) as a function of flow magnitude.
 - *Goal*: Identify the "kink" or threshold where the slope of the error curve changes significantly (indicating the onset of artifacts).
 - *Tool*: `ruptures` library or custom implementation.
- **Secondary Method: Kolmogorov-Smirnov (K-S) Test**:
 - *Purpose*: Compare the distribution of error magnitudes between Baseline and Flow-Coherence to confirm a significant difference in performance.
 - *Null Hypothesis*: The two distributions are identical.
 - *Significance Level*: $\alpha = 0.05$.
- **Sensitivity Analysis**: Sweep cutoff values {0.01, 0.05, 0.1} and report artifact rates.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: The sensitivity analysis involves 3 specific cutoffs. A Bonferroni correction or False Discovery Rate (FDR) adjustment will be noted if multiple hypothesis tests are run per cutoff.
- **Sample Size**: 50 clips. The plan acknowledges this is a **limited sample size** for detecting small effect sizes. Power analysis indicates sufficient power (>0.8) for **large effect sizes** (d > 0.8) typical of architectural changes. If power is low for smaller effects, this limitation will be explicitly stated.
- **Causal Inference**: This is an observational comparison of two methods on the same dataset. Claims are framed as **associational** (Method A vs. Method B) rather than causal, as no randomization of the video content itself is performed.
- **Measurement Validity**: BSS and Flow-Normalized SSIM are designed to address the specific failure modes of flow-based warping. They explicitly isolate background regions and normalize for motion magnitude.
- **Collinearity**: Flow magnitude and divergence are inherently related. The regression will treat them carefully, or focus on magnitude as the primary predictor to avoid multicollinearity issues.

## 5. Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM).
- **Strategy**:
 - **Pilot Phase**: Run 5 clips first to measure actual runtime.
 - **Dynamic Sample Size**: Adjust final N to ensure total runtime < 5.5 hours.
 - **Batching**: Process clips in small batches (or one at a time) to avoid OOM.
 - **Downsampling**: If a clip exceeds RAM limits, it will be downsampled or split.
 - **No GPU**: All operations (inference, flow, metrics) are CPU-only.
 - **Libraries**: `torch` (CPU), `opencv-python`, `scikit-learn`, `ruptures`.
- **Runtime**: Total pipeline (50 clips x 2 models) must complete within 6 hours. If not, the sample size is reduced.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Mismatch** | The verified DAVIS/VOS subsets may lack specific motion types. | Stratify carefully; if a category is missing, note it as a limitation. |
| **CPU Inference Time** | 50 clips x 2 models may exceed 6h. | Downsample video resolution; use `torch.compile` (if available on CPU); implement aggressive batching; reduce N if necessary. |
| **Flow Estimation Failure** | High motion blur causes invalid flow. | Identity warp fallback; flag and include in analysis (not exclude). |
| **Memory Limit** | Peak RAM > 7 GB. | Process one clip at a time; clear cache between clips; use `torch.no_grad()`. |
| **Baseline Validity** | Using a generic SD checkpoint instead of LiveEdit. | **Explicitly use LiveEdit weights** (or verified reproduction) with temporal layers enabled for the baseline. |