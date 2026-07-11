# Research: llmXive follow-up: extending "SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diff"

## Research Question

To what extent does the geometric consistency of SANA-WM's minute-scale video generation depend on learned semantic priors versus its architectural inductive biases when driven exclusively by symbolic, rule-based 6-DoF camera trajectories?

## Methodology

### Experimental Design
This is a **controlled computational experiment**.
- **Independent Variable**: Encoder Type (Symbolic Hard-coded vs. Learned Text-to-Image).
- **Dependent Variable**: Geometric Consistency (Mean Euclidean Pose Error after Procrustes alignment).
- **Control Variables**: Camera trajectory (identical 500 sequences), Model Architecture (SANA-WM or verified fallback), Quantization (NVFP4), Hardware (CPU-only), Resolution (720p, fallback 360p), Duration (short interval, fallback 10s), **Prompt (Calibrated)**.
- **Hypothesis**: The architectural inductive biases of SANA-WM are sufficient to maintain geometric consistency even without semantic priors, though likely with higher variance than the learned baseline.

### Dataset Strategy

The study relies on **synthetic data generation** rather than external datasets for the primary input, ensuring ground-truth availability for all 6-DoF poses.

| Dataset/Source | Type | Role | Verified URL / Loader |
| :--- | :--- | :--- | :--- |
| **Synthetic Kinematic Trajectories** | Generated | Ground-truth 6-DoF poses (Input). | Generated via `code/data/trajectory_generator.py` using `numpy`. No external URL. |
| **SANA-WM Model Weights** | Pre-trained | Inference Backbone. | **Pilot Phase Selection**: If SANA-WM NVFP4 weights are unavailable, fallback to **Stable Video Diffusion (SVD) XT** (Verified URL: `https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt-1-1`). Loaded via `diffusers` library. |
| **COLMAP Test Data** | Reference | Pose Estimator Validation. | `https://huggingface.co/datasets/cssen/colmap_test/resolve/main/images.zip` (Used for validating the COLMAP wrapper, not as primary input). |
| **Quantization Library** | Reference | NVFP4 Support. | `bitsandbytes` (CPU support verified in docs) and `transformers` quantization guide. Fallback to SVD-XT if NVFP4 CPU support fails. |

**Dataset-Variable Fit Verification**:
- **Required Variables**: 6-DoF Pose (x, y, z, roll, pitch, yaw) at $t=0..60s$.
- **Source**: Synthetic Generator.
- **Fit**: Perfect. The generator produces exact floating-point values matching the kinematic equations (FR-001). No missing variables.
- **Texture Strategy**: Synthetic videos will use **3D Perlin Noise** (where time is the third dimension) to ensure distinct, **temporally consistent** features for COLMAP. This mitigates the risk of low-texture failure and ensures feature trackability.

### Baseline Translation Protocol (Calibration)
To avoid the confound of a separate text-generation model or translation quality, the 'Learned Baseline' will use a **Calibrated Prompt**.
1.  **Pilot Search**: Run a small pilot (N=5) with multiple candidate prompts (e.g., "camera moves at {velocity} m/s", "motion: {velocity}").
2.  **Selection**: Select the prompt that minimizes the geometric error against the ground truth.
3.  **Execution**: Use this **single** "Calibrated Prompt" for all N=500 baseline runs. This ensures the baseline condition is empirically verified to trigger the motion, isolating the encoder's effect.

### Statistical Rigor

1.  **Multiple-Comparison Correction**: Not required. The study performs exactly **one** aggregate hypothesis test (Permutation Test or Paired T-Test on the distribution of 500 errors) as per FR-006.
2.  **Power Justification**: The sample size is fixed at $N=500$ trajectories (subject to Pilot Phase adjustment). While a formal power analysis is deferred, $N=500$ provides high statistical power for detecting even small effect sizes in a paired design, assuming the variance of the error differences is not extreme.
3.  **Causal Inference**: Claims are framed as **associational**. The study isolates the effect of the encoder type on geometric error under controlled conditions. It does not claim causal generalizability to real-world video generation without semantic priors, as the "world" is synthetic.
4.  **Measurement Validity**: Geometric consistency is measured via Euclidean distance between **Procrustes-aligned** estimated and ground-truth poses. This resolves the scale mismatch between COLMAP (relative) and Ground Truth (absolute). SSIM is used as a secondary metric for texture degradation.
5.  **Collinearity**: The motion types (constant, sinusoidal, chaotic) are distinct experimental conditions. The analysis will not claim independent effects of motion type on error without a collinearity diagnostic, as parameters may be mathem related.
6.  **Failure Mode Handling & Statistical Method**:
    - **Non-Detection**: If COLMAP fails to track features, the frame is marked invalid.
    - **Trajectory Failure**: If >50% of frames in a trajectory are invalid, the trajectory is marked as "Failed" and assigned a **Capped Maximum Error** (100m).
    - **Statistical Adjustment**: **If the failure rate > 5%**, the standard t-test is invalid due to the discrete capped values. The plan mandates a **Permutation Test on Censored Data** as the primary method. This non-parametric test correctly handles the mixture of continuous errors and discrete capped values, ensuring the comparison of "extent of dependency" is valid even with model collapse.

### Compute Feasibility Analysis

- **Hardware Constraints**: 2 CPU cores, 7GB RAM, 14GB Disk, 6h limit.
- **Model Size**: SANA-WM (approx. [deferred] parameters) or SVD-XT (Verified Fallback).
- **Quantization**: NVFP4 is mandatory for SANA-WM. If unavailable or unsupported on CPU, fallback to SVD-XT (verified CPU-tractable).
- **Inference Strategy**:
  - Batch size: 1 (frame-by-frame or small chunk).
  - Resolution: High-definition (downsampled to a lower resolution if OOM occurs, per Assumption).
  - Duration: A short, fixed interval.
- **Pilot Phase**:
  - Run N=10 trajectories.
  - Measure actual inference time per sequence.
  - **Decision Rule**: If projected time for N=500 > 6 hours, **automatically reduce** duration to 10s or resolution to 360p before proceeding.
- **Risk Mitigation**:
  - If NVFP4 loading fails: Abort with `ERR_QUANT_UNSUPPORTED` or fallback to SVD-XT.
  - If OOM occurs: Reduce resolution to 360p or sequence length to 10s.
  - Runtime: **Hard Constraint**. The pipeline includes a runtime check and early termination if the projected time exceeds 6 hours.

### Decision Rationale

- **Why Symbolic Encoder?**: To strictly satisfy Constitution Principle VI and isolate the architectural bias.
- **Why CALIBRATED Prompt?**: To remove the translation confound and ensure the baseline is empirically valid.
- **Why COLMAP?**: Industry standard for 6-DoF pose recovery; robust to synthetic geometry if features exist (ensured by 3D Perlin Noise).
- **Why Paired T-Test / Permutation Test?**: The same 500 trajectories are used for both conditions, creating paired data. The Permutation Test is mandated for censored data to avoid statistical artifacts.
- **Why CPU Only?**: To satisfy the "Low-Compute" constraint and ensure reproducibility on free-tier CI.
- **Why Procrustes Alignment?**: To mathematically resolve the scale mismatch between COLMAP's relative output and the absolute ground truth.
- **Why Failure Handling?**: To ensure the metric reflects the *extent* of degradation (including collapse) rather than just the error of successful frames.
- **Why 3D Perlin Noise?**: To ensure temporally consistent features for COLMAP, preventing "black box" tracking failures.

## Assumptions & Risks

- **Assumption**: NVFP4 quantized weights are available and loadable on CPU without CUDA kernels. **Risk**: If not, fallback to verified SVD-XT model.
- **Risk**: COLMAP fails on low-texture synthetic video. **Mitigation**: Synthetic data generation will use **3D Perlin Noise** to ensure feature detectability.
- **Risk**: Inference time exceeds 6 hours. **Mitigation**: Pilot Phase with explicit **Dynamic Fallback** to shorter duration/lower resolution.
- **Assumption**: The symbolic mapping produces valid condition vectors that the model can interpret as "camera motion" even without semantic text.
- **Assumption**: The Calibrated Prompt is sufficient to trigger the learned encoder's geometric priors.
- **Assumption about Failure Handling**: Non-detections (COLMAP failures) are treated as "Capped Maximum Error" to prevent bias.