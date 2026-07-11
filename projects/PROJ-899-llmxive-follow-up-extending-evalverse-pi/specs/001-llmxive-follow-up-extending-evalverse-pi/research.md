# Research: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

## Research Question

To what extent do low-level visual parameters (motion consistency, lighting distribution, composition geometry) suffice to explain **human expert judgments** of cinematic quality, and which specific qualitative dimensions of "professionalism" inherently require high-level semantic reasoning beyond these physical descriptors?

## Dataset Strategy

The core dataset is **EvalVerse**, a large-scale collection of video clips with expert-annotated sub-dimension scores.

| Dataset Name | Description | Source / URL | Status |
| :--- | :--- | :--- | :--- |
| **EvalVerse** | Video clips with **human expert-annotated sub-dimension scores** (e.g., "camera smoothness", "lighting consistency"). This is the primary ground truth for the main distillation study. | **NO verified public URL.** Local manual download required. User must download EvalVerse and place in `data/raw/evalverse/`. Checksummed upon download via `scripts/checksum_data.py` and recorded in `state/projects/.../artifact_hashes`. | *Local Manual Download / Verified via Local Checksumming.* |
| **Synthetic Video/Audio Data** | Synthetic video frames (generated via OpenCV) and synthetic audio signals (generated via scipy.signal) for unit testing optical flow extraction, HOG computation, and audio feature extraction in a CPU-native environment. | Synthetic generation (no external URL). | *Verified / Synthetic / Generated On-the-Fly.* Generated during unit tests for reproducibility. |
| **Synthetic Feature Matrices** | Synthetic HOG feature matrices and optical flow vectors for testing the feature extraction pipeline and ensuring correct shape/dtype. | Synthetic generation (no external URL). | *Verified / Synthetic / Generated On-the-Fly.* Generated during unit tests. |

**Note on EvalVerse**: Since no verified public URL exists for the primary dataset, the plan assumes the user will provide the data in `data/raw/evalverse/`. The `download.py` script will check for the existence of this directory and validate the checksum against the recorded value in `state/projects/.../artifact_hashes`. If the checksum does not match, an error is raised, indicating data corruption or tampering. No fabricated URLs are used.

**Note on VLM Scores**: If EvalVerse metadata includes VLM-generated reference scores, these are used ONLY for the preliminary validation step (FR-009) to confirm alignment with human expert ratings (r ≥ 0.70). The main study target variable is ALWAYS human expert scores, not VLM scores. If VLM scores are unavailable or validation fails, the study proceeds with human scores as the sole target.

## Methodology

### 1. Data Preprocessing & Feature Extraction
- **Visual Features**: Use `opencv-python` to compute:
  - **Optical Flow**: Magnitude and variance of flow fields (Farneback method, CPU-optimized).
  - **HOG Density**: Histogram of Oriented Gradients per frame, aggregated over the clip.
  - **Global Histograms**: RGB and HSV channel statistics (mean, std, skewness).
- **Audio Features**: Use `librosa` to compute:
  - **Spectral Centroid**: Center of mass of the spectrum.
  - **Zero-Crossing Rate**: Frequency of sign changes in the waveform.
- **Handling Edge Cases**:
  - **Missing Audio**: If a clip lacks an audio track, return a null vector for audio features and log a warning.
  - **Optical Flow Failure**: If flow calculation fails (e.g., all black frames), return a "zero-motion" vector and flag the sample as "low-quality data."

### 2. Preliminary Validation (FR-009) — GATE STEP

**Purpose**: Validate that any optional VLM proxy is aligned with human experts before considering it for secondary analyses. This gate ensures the main target variable (human expert scores) is robust.

- **Action**: If EvalVerse metadata includes VLM reference scores, correlate them with a subset of human expert ratings (n ≥ 30) from EvalVerse.
- **Criterion**: If Pearson r < 0.70, the VLM proxy is invalid. **The study halts or proceeds with human scores only.**
- **Output**: A validation report confirming or rejecting the use of VLM scores for secondary analyses.
- **If Validation Passes (r ≥ 0.70)**: The VLM proxy may be used for optional secondary validations (not the main study).
- **If Validation Fails (r < 0.70) or VLM Scores Unavailable**: The study proceeds with human expert scores as the sole target variable.

**CRITICAL**: The main distillation study (Steps 3–6) ALWAYS uses **human expert scores** as the target variable, regardless of the VLM validation outcome. The VLM proxy is never the primary target.

### 3. Model Training & Evaluation (Against Human Expert Ground Truth)

- **Target Variable**: **EvalVerse human expert-annotated sub-dimension scores** (the ground truth for cinematic quality).
- **Rationale**: The research question asks "Do low-level features explain human expert judgments?" This is answered directly by training models against human scores, not against a VLM proxy. Using human ground truth ensures the study answers the actual research question: whether low-level features are sufficient for human quality judgment, not whether they are sufficient for a VLM's opinion (which may be inherently high-level semantic). This avoids a circular validity loop.
- **Models**:
  - **Ridge Regression**: L2 regularization to handle multicollinearity among visual features.
  - **Lasso Regression**: L1 regularization for feature selection.
  - **XGBoost**: Shallow tree-based model (max_depth=3, n_estimators=50) to capture non-linear interactions.
- **Metrics**:
  - **Pearson & Spearman Correlation**: Between model predictions and human expert scores.
  - **Bootstrapped 95% CIs**: Resampling (n=1000) to estimate confidence intervals for correlations.
- **Thresholds**:
  - **Feature-Sufficient**: Lower 95% CI > 0.85 (dimension can be predicted reliably from low-level features).
  - **VLM-Required**: Lower 95% CI < 0.70 (dimension requires high-level semantic reasoning; low-level features insufficient).
  - **Ambiguous**: Between 0.70 and 0.85 (borderline case; requires manual review).

### 4. Baseline Comparisons

To contextualize the low-level model's correlation, the plan will compare against two baselines:

- **Mean Predictor**: Train a model that always predicts the mean human expert score for a dimension. This baseline should yield r ≈ 0 and serves as a sanity check.
- **Shuffled Features**: Train the same models (Ridge, Lasso, XGBoost) on randomly permuted feature values. This baseline should also yield near-zero correlation and tests for overfitting.
- **Permutation Test for Significance**: Use a permutation test to determine whether the low-level model's correlation significantly exceeds both baselines (p < 0.05). A model is classified as "feature-sufficient" ONLY if:
  1. Lower 95% CI > 0.85 (high absolute correlation), AND
  2. Permutation test p < 0.05 (significantly exceeds baselines).
- **Criterion for Sufficiency**: If the low-level model barely exceeds these baselines or the permutation test p ≥ 0.05, the dimension is flagged as "insufficient" regardless of the absolute correlation value.

### 5. Sensitivity Analysis (FR-005)

- **Action**: Sweep the classification threshold across a range of high-confidence values.
- **Metric**: Calculate the "flip rate" (proportion of dimensions changing status between "feature-sufficient" and "VLM-required").
- **Flag**: If flip rate > 5%, the dimension is flagged as "threshold-sensitive" and requires manual review.

### 6. Compute Feasibility Profiling (FR-006)

- **Action**: Run the full pipeline on a representative subset of clips.
- **Metrics**: Peak memory usage (via `psutil`), total inference time.
- **Constraint**: Must not exceed 7GB RAM and must scale to N=10,000 clips within 6 hours.

## Statistical Rigor

- **Multiple Comparisons**: Since multiple dimensions are tested, the plan will apply three complementary approaches:
  1. **Bonferroni Correction**: Conservative baseline; adjusts α by the number of dimensions tested.
  2. **Benjamini-Hochberg FDR Control**: Less conservative; controls the false discovery rate.
  3. **Permutation-Based FWER Control**: Accounts for the observed correlation structure of the target dimensions. The plan will compute a dimension-to-dimension Pearson r matrix and use this structure to inform the permutation test. This method is more powerful than Bonferroni for correlated targets.
  - **Reporting**: Results will be reported under all three methods to allow readers to assess sensitivity to the multiple-comparison procedure.
  
- **Dimension Correlation Structure**: The plan will compute and report a dimension-to-dimension correlation matrix (Pearson r) to characterize the dependence structure of the target variables. This informs the permutation-based FWER control and helps readers understand whether dimensions are independent or highly correlated.

- **Sample Size / Power**: The plan acknowledges that the power of the correlation test depends on the number of clips (N). For N=10,000, the power to detect r=0.70 is effectively 1.0. However, for smaller subsets used in validation (n ≥ 30), a power analysis will be noted (e.g., power to detect r=0.70 at n=30 is approximately 0.75 at α=0.05).

- **Causal Inference**: This is an **observational** study. Claims will be framed as **associational** (e.g., "low-level features are predictive of...") rather than causal. No causal claims about the mechanisms underlying cinematic quality are made.

- **Measurement Validity**: 
  - **Human Expert Scores**: Treated as the ground truth for cinematic quality. No external validation is required; these are the target variable.
  - **Hand-Crafted Features** (HOG, optical flow, spectral centroids): Validity is supported by established literature in video quality assessment (VQA). The plan does not validate these features against external standards; their validity is assumed based on prior work.
  - **VLM Scores** (if used for validation): Validity is explicitly tested in Step 2 (Preliminary Validation) via correlation with human expert scores (r ≥ 0.70 required).

- **Collinearity**: Optical flow magnitude and variance are definitionally related. The plan will report their correlation; if r > 0.9, the plan will avoid claiming independent effects and instead report the relationship descriptively, acknowledging the collinearity.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (multi-core CPU, substantial RAM).
- **Strategy**:
  - **No GPU**: All libraries (`opencv`, `librosa`, `xgboost`) are CPU-native.
  - **Data Sampling**: If N=10,000 clips exceeds memory limits, the pipeline will process clips in batches (e.g., 100 at a time) and aggregate results.
  - **Memory Monitoring**: `psutil` will track peak memory; if it exceeds 6GB, the batch size will be reduced dynamically.
  - **Time Limit**: The 6-hour limit is tight for a large-scale dataset of video clips. The plan includes a "fast mode" that processes a subset (e.g., [deferred] clips) for initial validation, with the full run scheduled as a separate long-running job if needed.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **EvalVerse Data Unavailable** | High | The plan explicitly handles this by requiring manual download and providing a clear error message. Data is validated via local checksumming (scripts/checksum_data.py). No fabricated URLs are used. |
| **VLM Proxy Invalid (r < 0.70)** | Medium | FR-009 detects invalid VLM alignment. If validation fails, the study proceeds with human expert scores only. The main study is never dependent on VLM scores. |
| **Memory Overflow** | Medium | Batch processing and dynamic batch size reduction ensure the pipeline stays within 7GB. |
| **Time Limit Exceeded** | Medium | The plan includes a "fast mode" for initial validation and optimizes feature extraction (e.g., downsampling frames for optical flow). |
| **Correlated Target Dimensions** | Low | Addressed via permutation-based FWER control that accounts for observed target correlation structure. Results reported under multiple methods. |
| **Low-Level Features Insufficient** | Low | Baseline comparisons (Mean Predictor, Shuffled Features) with permutation tests ensure that the low-level model's correlation significantly exceeds random chance (p < 0.05) before flagging a dimension as "feature-sufficient." |
| **Circular Validity Loop** | Low | The main study uses human expert scores as the target, not VLM scores. VLM scores are used only for an optional validation gate (FR-009). This avoids the confound where a VLM's (inherently semantic) opinion is used to validate low-level features. |
