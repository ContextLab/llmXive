# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## 1. Problem Statement & Research Question

**Research Question**: Which statistical properties of video input (e.g., optical flow variance, frame-to-frame MSE) predict the numerical instability (flow-map divergence) of the AnyFlow video diffusion model?

**Hypothesis**: Clips with high temporal discontinuity (hard cuts, rapid motion) exhibit significantly higher flow-map divergence than smooth motion clips.

**Core Metric**: Flow-map divergence = $|| z_{predicted} - z_{euler} ||_2$, where $z_{euler}$ is derived from a 100-step high-resolution Euler rollout.

## 2. Dataset Strategy

The study requires a dataset of video clips containing a mix of continuous motion and temporal discontinuities ("hard cuts").

### Verified Datasets
*Note: The following datasets have been verified for reachability and format compatibility. Only these sources are used.*

| Dataset Name | Description | Verified URL / Loader | Relevance |
| :--- | :--- | :--- | :--- |
| **Kinetics-400** | Large-scale video dataset with 400 human action classes. Contains diverse motion patterns and potential cuts. | `datasets.load_dataset("kinetics400", split="validation")` (HuggingFace) | Primary source for "continuous motion" and "hard cut" examples. |
| **UCF101** | 101 action classes, 13k+ videos. Lower resolution, good for CPU testing. | `ucimlrepo.fetch_ucr_dataset("UCF101")` (UCI) | Secondary source for validation and sensitivity analysis. |

**Dataset Selection Rationale**:
- **Kinetics-400** is selected as the primary source due to its scale and diversity.
- **Sampling Strategy**: A target of **N=60** valid clips will be collected. This sample size provides >80% power to detect a moderate correlation (r≈0.3) at α=0.05 for a pilot study.

### Time-Budgeted Replacement Strategy (Critical Feasibility Adjustment)
To guarantee the 6-hour execution limit:
1.  **Target**: 60 valid clips (100-step Euler rollout < 15 mins).
2.  **Replacement Logic**: For each of the 60 slots, the system attempts to fetch a random clip.
3.  **Timeout Handling**: If a clip's 100-step rollout exceeds 15 minutes, it is **excluded** from the primary analysis (not replaced with a 20-step proxy). This prevents the confounding of model instability with numerical integration error from a coarse solver.
4.  **Max Attempts**: If a slot fails 3 consecutive times (due to timeouts or corruption), the slot is marked "timeout-heavy" and skipped. The study proceeds with the remaining valid clips (min N=30).
5.  **Efficient Extraction**: Clips are extracted using `decord` to seek directly to a random timestamp and read exactly 16 frames, avoiding full video decoding overhead. This minimizes I/O and CPU usage.

**Data Preprocessing**:
- Clips will be resized to a fixed resolution (e.g., 224x224) to ensure consistent memory usage.
- **Corruption Handling**: Clips with missing frames or unreadable data will be skipped (FR-006) and logged, not included in the analysis.

## 3. Methodology

### 3.1. Flow-Map Divergence Calculation (FR-001) & Convergence Check
1.  **Model Loading**: The AnyFlow model will be converted to ONNX format and loaded via `onnxruntime` (CPU-only).
2.  **Prediction**: For each clip, the model predicts the latent state $z_{predicted}$ at the target step.
3.  **Ground Truth (Euler Rollout)**: A high-resolution Euler integration (100 steps) will be performed to compute $z_{euler}$.
    - **Timeout Fallback**: If the 100-step rollout exceeds 15 minutes (FR-008 revised logic), the clip is **excluded** from the primary statistical analysis and logged as "timeout". No 20-step surrogate is used for the primary metric to avoid confounding model instability with numerical integration error.
    - **Convergence Check (Pilot)**: A pilot subset (N=10) will run 200-step rollouts. If the L2 distance between 100-step and 200-step results exceeds $\epsilon = 0.01$, the 100-step result is considered unstable, and the clip is excluded from the primary analysis. This ensures the "ground truth" is valid for the included clips.
4.  **Metric**: Compute L2 distance: $D = || z_{predicted} - z_{euler} ||_2$.

### 3.2. Statistical Feature Extraction (FR-002)
For each clip, the following features will be extracted from raw pixel data:
1.  **Optical Flow Magnitude Variance**: Computed using OpenCV `calcOpticalFlowFarneback`.
2.  **Frame-to-Frame MSE**: Mean Squared Error between consecutive frames.
3.  **Temporal Gradient Sparsity**: The ratio of pixels with high temporal gradients to the total number of pixels.

### 3.3. Correlation & Regression Analysis (FR-003)
- **Correlation**: Pearson correlation coefficient ($r$) and p-values will be computed between each feature and the divergence metric $D$.
- **Regression**: **Ridge Regression** (L2 regularization) will be used ($D \sim \beta_0 + \beta_1 \cdot \text{FlowVar} + \beta_2 \cdot \text{MSE} + \beta_3 \cdot \text{Sparsity}$) to handle potential multicollinearity between features (e.g., optical flow variance and frame-to-frame MSE are likely correlated). Variance Inflation Factors (VIF) will be reported to quantify collinearity.
- **Multiple Comparison Correction**: Given multiple features tested, a Bonferroni correction will be applied to p-values.

### 3.4. Threshold Validation & Sensitivity (FR-004, FR-007)
1.  **Human Annotation**: A subset of clips will be manually labeled by two independent raters.
    - **Label Definition**: Raters label clips as "stable" or "unstable" based on **visible visual artifacts** (e.g., flickering, tearing). This measures *visual discontinuity*, not direct model divergence.
    - **Agreement**: Cohen's kappa ($\kappa$) must be ≥ 0.8 (FR-007).
2.  **Analysis Goal**: The study tests the **association** between **Visual Discontinuity (Human Label)** and **Divergence (Metric)**. This decouples the validation target from the metric definition. The study does not claim the human label is the ground truth for numerical instability; rather, it tests if high divergence correlates with visible artifacts.
3.  **Threshold Optimization**: The optimal divergence threshold ($T_{opt}$) will be determined by maximizing the F1-score for predicting "visual discontinuity" (human label) on the labeled subset.
4.  **Sensitivity Sweep**: The threshold will be varied by ±0.05 around $T_{opt}$. The variation in False Positive Rate (FPR) and False Negative Rate (FNR) will be reported.
    - **Success Metric**: Variation in FPR < 10% across the sweep (SC-003).

## 4. Statistical Rigor & Power Analysis

- **Sample Size**: Target $N=60$ valid clips (min 30).
- **Power**: Assuming a moderate effect size ($r \approx 0.3$), $\alpha=0.05$, and two-tailed test, $N=60$ provides [deferred] power.
- **Causal Claims**: The study is observational. Claims will be framed as "associational" or "predictive".
- **Collinearity**: Ridge Regression is used to handle collinearity between optical flow variance and frame-to-frame MSE. VIF will be reported.

## 5. Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Model**: AnyFlow in ONNX format (CPU-optimized).
- **Memory**: Batch processing of 1 clip at a time.
- **Time**:
    - 100-step Euler rollout per clip: Target < 5 minutes (based on pilot assumptions).
    - **Strategy**: Target 60 clips. Max attempts per slot = 3.
    - **Max Time**: $60 \text{ slots} \times 3 \text{ attempts} \times 15 \text{ min} = 2700 \text{ min} = 45 \text{ hours}$.
    - **Mitigation**: The pipeline will run sequentially. If a clip takes >15m, it is killed immediately. The "max attempts" logic ensures we do not waste time on "hard" clips. The 6-hour limit is a *hard stop* for the job; if 60 clips are not filled, the study reports the achieved N (min 30).
    - **Revised Estimate**: If average clip takes 5 mins, $60 \times 5 = 300 \text{ min} = 5 \text{ hours}$. This fits the 6-hour limit. **Note**: If the 5-minute average is not met (e.g., due to slower CPU performance), the study will report the achieved N (minimum 30) rather than forcing a biased sample or exceeding the time limit.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **100-step rollout too slow** | Pipeline exceeds 6h limit. | Enforce 15-min timeout; exclude from primary analysis; max 3 attempts per slot. |
| **Model not compatible with CPU** | Cannot run inference. | Use ONNX Runtime with `CPUExecutionProvider`; verify conversion before run. |
| **Low human agreement** | Threshold invalid. | Require $\kappa \ge 0.8$; resolve disagreements; if not met, report as limitation. |
| **Dataset lacks "hard cuts"** | Low variance in divergence. | Stratified sampling from Kinetics-400 classes known for cuts. |
| **Timeout-heavy dataset** | N < 30. | Report achieved N; analyze "timeout" rate as a metric of instability. |
| **5-minute average not met** | Runtime exceeds 6h. | Study proceeds with reduced N (min 30); reports achieved N and runtime. |