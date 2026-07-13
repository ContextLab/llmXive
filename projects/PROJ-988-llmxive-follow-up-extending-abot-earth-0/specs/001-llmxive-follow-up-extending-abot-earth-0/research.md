# Research: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

## Research Question
To what extent can 3D geometric and textural fidelity be recovered from low-resolution, cloud-contaminated, or temporally stale satellite imagery using generative 3D Gaussian Splatting, and what are the fundamental limits of restoration when the input signal-to-noise ratio drops below a critical threshold?

## Dataset Strategy

### Primary Data Sources
1.  **Satellite Imagery (Sentinel-2)**:
    *   **Source**: Sentinel-2 Level-2A data (via HuggingFace `datasets` library or direct S3 access).
    *   **Usage**: Provides the base optical imagery for 1km² urban regions.
    *   **Coverage**: A set of distinct urban tiles selected for high-density geometry.
    *   **Verified Status**: **NO verified source found** for a specific pre-packaged 500-tile urban dataset. The plan will programmatically fetch tiles using the `sentinel-2` loader from HuggingFace or the Copernicus Open Access Hub API, filtering for urban coordinates.
    *   **Constraint**: Must verify spatial overlap with LiDAR.

2.  **Ground Truth (LiDAR)**:
    *   **Source**: OpenTopography.
    *   **Usage**: High-fidelity point clouds for geometric validation (Chamfer Distance).
    *   **Coverage**: Independent LiDAR datasets for multiple urban regions.
    *   **Verified Status**: **NO verified source found** for a specific pre-packaged LiDAR dataset aligned with Sentinel-2. The plan will use the OpenTopography API or `opentopo` Python client to fetch tiles matching the Sentinel-2 bounding boxes.
    *   **Constraint**: Alignment error must be < 2 meters (FR-001).

### Dataset Variable Fit & Mismatch Handling
*   **Required Variables**:
    *   *Predictors*: Degraded RGB imagery (Low-res, Cloud-masked, Temporal-shifted).
    *   *Outcomes*: 3D Geometry (X, Y, Z point clouds) and Texture (RGB values at 3D points).
    *   *Covariates*: Cloud opacity, resolution level, Normalized Noise Fraction (NNF).
*   **Fit Confirmation**:
    *   Sentinel-2 provides the necessary spectral bands (B04, B03, B02) for RGB reconstruction.
    *   OpenTopography LiDAR provides the necessary XYZ geometry for ground truth.
    *   **Potential Mismatch**: OpenTopography data is often sparse or regionally limited. If a specific Sentinel-2 tile lacks a corresponding LiDAR dataset within the 2m alignment tolerance, the sample will be **excluded** and logged (Edge Case: "LiDAR missing").
    *   **No Fabrication**: If a dataset is not available via the verified sources or programmatic loaders, the plan will **not** invent a URL. Instead, it will use a smaller, verified subset or a synthetic proxy (if validated by FR-006) to demonstrate the pipeline, noting the limitation in the final paper.

### Synthetic Degradation Strategy
Since real-world "perfect ground truth" degraded scenes are rare, the plan implements **Synthetic Degradation** (FR-002):
1.  **Resolution Reduction**: Downscale high-res Sentinel to 30m/pixel.
2.  **Cloud Simulation**: Procedural alpha-blended masks (opacity ≥ 0.9) to simulate occlusion.
3.  **Temporal Shift**: Simulate time-lapse artifacts (if multi-temporal data exists) or noise injection.
*   **Validation**: FR-006 requires comparing statistical properties of these synthetic masks against a sample of real cloud-masked images to ensure validity.

## Methodology

### Phase 1: Data Curation & Alignment
1.  **Download**: Fetch 500 Sentinel-2 tiles and corresponding OpenTopography LiDAR.
2.  **Align**: Compute spatial transform (HOMOGRAPHY/PROJECTION) to align image coordinates with LiDAR point cloud.
    *   *Success Metric*: Alignment error < 2 meters for all samples.
    *   *Failure*: Exclude sample, log reason.
3.  **Extract Patches**: Extract 100m² patches from the 1km² tiles for computational feasibility (100m² is ~300x300 pixels at 30m resolution, manageable for CPU 3DGS).

### Phase 2: Synthetic Degradation
1.  Apply programmable degradation masks to the extracted patches.
2.  Generate a "DegradedScene" dataset with metadata (NNF, degradation type, seed).
3.  **Validation**: Run statistical comparison (FR-006) between synthetic and real cloud masks.

### Phase 3: CPU-Optimized Generation (The Core Pipeline)
*Addressing the "Consumer before Producer" and "Missing Producer" concerns:*
This phase is orchestrated by a single script (`run_full_experiment.py`) that processes one sample at a time to ensure memory safety.

1.  **Baseline 3DGS**:
    *   Input: Degraded Scene.
    *   Process: Run 3D Gaussian Splatting (CPU-only, simplified initialization) to generate a baseline `.ply`.
    *   *Constraint*: Must complete in < 30 mins, RAM < 6.5 GB.
2.  **Inpainting Restoration**:
    *   Input: Baseline 3DGS output (or degraded image + baseline geometry hint).
    *   Process: Apply CPU-optimized diffusion prior (ONNX Runtime) to inpaint missing geometry/texture.
    *   *Constraint*: Must complete in < 45 mins total, RAM < 6.5 GB.
3.  **Performance Instrumentation**:
    *   **Action**: Log `wall_clock_time`, `peak_ram_mb`, and `success_status` to `data/results/performance_log.csv` (Satisfies SC-003).
    *   *Error Handling*: If OOM occurs, log `ERR_OOM_CPU`, reduce batch size, and retry.

### Phase 4: Fidelity Quantification & Threshold Analysis
1.  **Metric Computation**:
    *   Compute P-PSNR, P-SSIM, and Chamfer Distance for both Baseline and Inpainted scenes against Ground Truth LiDAR.
2.  **Statistical Testing**:
    *   Perform **Wilcoxon signed-rank test** on the improvement (Inpainted - Baseline) across the sample set to account for non-normal distributions and heteroscedasticity.
    *   Perform **Linear Mixed-Effects (LMM)** modeling with `scene_complexity` as a random effect to control for varying urban densities.
    *   *Significance*: $\alpha = 0.05$.
3.  **Threshold Sweep**:
    *   Sweep the Normalized Noise Fraction (NNF) in configurable steps.
    *   Identify the critical NNF where the p-value of improvement > 0.05 (SC-002).
    *   Plot the "Performance Drop-off Curve".

## Statistical Rigor & Assumptions

### Statistical Assumptions
*   **Independence**: Samples are spatially distinct; LiDAR is independent of Sentinel-2.
*   **Collinearity**: Predictors (degradation levels) are synthetically generated, avoiding natural collinearity issues.
*   **Multiple Comparisons**: When sweeping NNF thresholds, apply **Bonferroni correction** or **False Discovery Rate (FDR)** control to the p-values to avoid Type I errors.
*   **Normality**: Rejected for difference scores; using non-parametric Wilcoxon signed-rank test.
*   **Heteroscedasticity**: Addressed via Wilcoxon and LMM.

### Computational Feasibility (CPU-Only)
*   **Model Choice**: Use a distilled, quantized diffusion model (e.g., ONNX version of Stable Diffusion or a smaller UNet) specifically optimized for CPU inference.
*   **Data Subsampling**: Limit DGS optimization to 100m² patches to fit RAM constraints.
*   **No GPU**: Strictly forbid CUDA. Use `torch.set_num_threads()` to match runner cores.
*   **Rationale**: If the spec implies a heavy method, this plan uses a CPU-tractable approximation (smaller model, sampled data) and documents it.

### Limitations
*   **Generalizability**: Results are specific to urban environments and the synthetic degradation model.
*   **Dataset Availability**: If OpenTopography lacks coverage for 500 distinct urban regions, the final sample size $N$ will be reduced, and power analysis will be adjusted accordingly.