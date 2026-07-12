# Research: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Research Question
To what extent can 3D geometric and textural fidelity be recovered from low-resolution, cloud-contaminated, or temporally stale satellite imagery using generative 3D Gaussian Splatting, and what are the fundamental limits of restoration when the input signal-to-noise ratio drops below a critical threshold?

## Methodology Overview

The research follows a **Controlled Degradation and Restoration** methodology:
1.  **Ground Truth**: High-fidelity LiDAR point clouds (USGS 3DEP/NYC Open Data) serve as the independent reference standard.
2.  **Input Simulation**: Sentinel-2 imagery (Microsoft Planetary Computer) is synthetically degraded to simulate specific failure modes (resolution loss, occlusion, temporal shift) with known parameters.
3.  **Restoration**: A CPU-optimized 3D Gaussian Splatting pipeline with a diffusion-based inpainting prior (ONNX Runtime, INT8/LCM) attempts to recover the scene.
4.  **Quantification**: Fidelity is measured via geometric (Chamfer Distance) and textural (P-PSNR, P-SSIM) metrics, with specific handling for temporal modes.
5.  **Threshold Detection**: Systematic sweeping of degradation intensity identifies the point where restoration statistically fails to improve over the baseline using Segmented Linear Regression and Bayesian Change Point Detection.

## Dataset Strategy

### Data Sources
This project relies on two primary data sources, verified for public access:
1.  **Sentinel-2 Imagery**: Sourced from **Microsoft Planetary Computer** (via `pystac-client`). This provides programmatic, verified access to Sentinel-2 data.
2.  **LiDAR Ground Truth**: Sourced from **USGS 3DEP** (via OpenTopography API) and **NYC Open Data** (direct download). The plan uses a `city_list.txt` to target specific urban regions (e.g., NYC, Los Angeles, Chicago) where LiDAR availability is confirmed.

### Dataset-Variable Fit Analysis
- **Required Variables**:
  - **Predictors**: Degraded satellite imagery (RGB), Degradation Metadata (NNF, Cloud Opacity, Resolution).
  - **Outcomes**: 3D Point Cloud Geometry (X, Y, Z), Texture (RGB).
  - **Covariates**: Urban region ID, Acquisition Date.
- **Fit Confirmation**:
  - **Sentinel-2**: Provides the necessary optical imagery. The plan explicitly generates the *degraded* versions (predictors) synthetically to ensure the exact NNF is known.
  - **LiDAR**: Provides high-resolution geometry (Outcomes).
  - **Alignment Challenge**: The plan includes a specific alignment step (FR-001) to ensure the Sentinel-2 pixel grid and LiDAR point cloud share a coordinate transform with < 2m error.
- **Gap Handling**: If LiDAR data is unavailable for a specific Sentinel-2 tile, that tile is skipped. The plan does not fabricate LiDAR data.

### Temporal Mismatch Control
- **Issue**: LiDAR and Sentinel-2 may be acquired at different times (e.g., >12 months apart), introducing "geometric change" as a confound for "reconstruction error".
- **Control**: The plan filters the dataset to pairs with acquisition dates within 12 months. For pairs >12 months apart, a `temporal_gap_months` field is recorded, and these samples are excluded from the primary "reconstruction limit" calculation or flagged as "confounded" in the analysis.

## Technical Approach

### 1. Synthetic Degradation Engine (FR-002)
- **Resolution Loss**: Bicubic downsampling to m/pixel (from ~10m native).
- **Cloud Occlusion**: Procedural alpha masks generated via Perlin noise, blended with opacity $\ge 0.9$ to simulate heavy cloud cover.
- **Temporal Shift**: Color histogram shifting to simulate seasonal/illumination changes.
- **Validation (FR-006)**: `02b_validate_masks.py` will fetch a sample of real cloud masks (e.g., from Copernicus Climate Data Store) and compute statistical similarity (SSIM, histogram correlation) against synthetic masks. If similarity < 0.8, the study will be limited to "Synthetic Degradation" claims or switch to real masks.

### 2. CPU-Optimized 3DGS & Inpainting (FR-003)
- **3DGS Baseline**: Standard 3D Gaussian Splatting implementation, restricted to CPU execution.
  - *Constraint*: No CUDA. Uses `torch` CPU tensors.
  - *Optimization*: Limited to $100\text{~m}^2$ patches to fit within 7GB RAM.
- **Inpainting Module**:
  - **Model**: **Stable Diffusion 1.5 via ONNX Runtime (INT8 quantized)** or **Latent Consistency Model (LCM)**. These are proven to run on CPU within memory limits.
  - **Mechanism**: Uses the degraded image as a condition to "hallucinate" missing geometry/texture in the Gaussian initialization or refinement step.
  - **Runtime**: ONNX Runtime ensures CPU-only inference.
  - **Memory Management**: Batch size set to 1. `enable_model_cpu_offload` if available.

### 3. Fidelity Quantification (FR-004)
- **Geometric**: Chamfer Distance (CD) between ReconstructedScene and GroundTruthLiDAR.
  - *Normalization*: Both point clouds normalized to a 0-1 unit cube per scene before CD calculation.
  - *Definition of Recovery*: The metric measures the reduction in geometric error compared to the baseline. It does not claim to recover "missing info" (impossible) but to "recover structure from noise".
- **Textural**: Projected PSNR and P-SSIM.
  - *Constraint*: **Only computed for 'low_res' and 'cloud' modes.** For 'temporal' modes, textural recovery against the *original* (stale) image is invalid. Only geometric metrics are reported for temporal modes.
  - *Method*: Render the reconstructed 3D scene from the original camera angles and compare pixel-wise with the original (non-degraded) Sentinel-2 reference (for non-temporal modes).

### 4. Statistical Analysis & Threshold Detection (FR-005)
- **Hypothesis**: Inpainting significantly reduces Chamfer Distance and improves P-PSNR compared to baseline 3DGS on degraded inputs.
- **Method**:
  - **Segmented Linear Regression**: Instead of a global t-test, a piecewise linear regression is fitted to the "Improvement vs. NNF" curve to identify the breakpoint (inflection point) where the slope becomes non-significant.
  - **Bayesian Change Point Detection**: Used as a robust alternative for sparse data (2-3 samples per bin) to identify the NNF threshold where the probability of improvement drops below a significance level.
  - **Multiple Comparisons**: Bonferroni correction applied if multiple bins are tested individually.
- **Threshold Sweep**:
  - Vary NNF from zero to unity in incremental steps.
  - Identify Critical NNF: The point where the regression slope is not significantly different from zero (or Bayesian posterior probability of improvement < 0.95).

## Statistical Rigor & Constraints

- **Multiple Comparisons**: Bonferroni correction or FDR control applied to p-values in segmented analysis.
- **Power Analysis**: With N=500 (distributed) or N=50 (CI demo), the study is powered to detect medium effect sizes. Bayesian methods are used to handle sparse bins.
- **Causal Claims**: Claims are strictly **associational**. The "restoration" is a function of the algorithm. The "critical threshold" is a property of the algorithm's performance curve.
- **Collinearity**: Degradation modes are applied independently or in controlled combinations. The analysis reports marginal effects.
- **Measurement Validity**:
  - **Chamfer Distance**: Standard for point cloud alignment.
  - **P-PSNR/P-SSIM**: Valid only for non-temporal modes.
- **Limitations**:
  - **CPU Bottleneck**: A time constraint may force reduced Gaussian primitives.
  - **LiDAR Availability**: May introduce selection bias (urban areas with LiDAR).
  - **Synthetic Masks**: Validity depends on FR-006 results.

## Compute Feasibility Plan

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Memory Strategy**:
  - Process scenes sequentially (batch size = 1).
  - Use `mmap` for large point clouds.
  - **Diffusion Model**: Use `Stable Diffusion 1.5` via `ONNX Runtime` with `INT8` quantization or `LCM`.
- **Time Strategy**:
  - Target mins/scene.
  - **CI Demo**: 50 scenes (or 20 for strict 6h limit).
  - **Full Run**: Distributed via GitHub Actions matrix strategy (20 jobs of 25 samples) or local execution.
- **Versioning**: Scripts generate SHA256 hashes for all artifacts and store them in `data/manifest.json`.

## Risks & Mitigation

- **Risk**: LiDAR data not available for selected urban tiles.
  - *Mitigation*: Script checks availability; uses `city_list.txt`; logs exclusion.
- **Risk**: CPU 3DGS too slow.
  - *Mitigation*: Use simplified 3DGS (fewer primitives) or reduce scene size.
- **Risk**: Temporal mismatch (LiDAR vs Image > 12 months).
  - *Mitigation*: Filter dataset; flag confounded samples; exclude from primary threshold calculation.
- **Risk**: Synthetic masks do not match real clouds.
  - *Mitigation*: FR-006 validation step; if similarity < 0.8, switch to real mask dataset or limit conclusions.
- **Risk**: ONNX model fails to load on CPU.
  - *Mitigation*: Fallback to simpler interpolation-based inpainting (e.g., `cv2.inpaint`) if the diffusion prior fails, logging the fallback.