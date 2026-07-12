# Feature Specification: llmXive follow-up: extending "ABot-Earth 0.5: Generative 3D Earth Model"

**Feature Branch**: `001-generative-3d-earth-fidelity`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "To what extent can 3D geometric and textural fidelity be recovered from low-resolution, cloud-contaminated, or temporally stale satellite imagery using generative 3D Gaussian Splatting, and what are the fundamental limits of restoration when the input signal-to-noise ratio drops below a critical threshold?"

## User Scenarios & Testing

### User Story 1 - Synthetic Degradation & Ground Truth Alignment (Priority: P1)

**Journey**: A researcher prepares a controlled experiment by downloading 500 urban $1\text{~km}^2$ regions from Sentinel-2 and aligning them with independent ground-truth LiDAR data from OpenTopography. The system then applies programmable, reproducible degradation masks (low resolution, cloud cover, temporal shifts) to the imagery to simulate specific failure modes without altering the ground truth.

**Why this priority**: This is the foundational step. Without a controlled, reproducible degradation pipeline and a verified alignment with independent ground truth, no subsequent fidelity measurement is valid. It directly addresses the "Dataset-variable fit" by ensuring the predictors (degraded images) and outcomes (LiDAR geometry) are correctly paired.

**Independent Test**: The system can generate a dataset of 500 degraded scenes with a unique seed for each, and a script can verify that the spatial alignment error between the degraded image coordinate system and the LiDAR point cloud is $< 2$ meters for all samples.

**Acceptance Scenarios**:

1. **Given** a valid Sentinel-2 tile ID and a corresponding OpenTopography LiDAR file, **When** the curation script runs, **Then** the system outputs a paired dataset where the image and point cloud share a verified coordinate transform with a residual error $< 2$ meters.
2. **Given** a high-resolution image, **When** a "low-resolution" degradation (downscale to 30m/pixel) is applied, **Then** the output image has a confirmed resolution of 30m/pixel $\pm 1\%$ and the original high-resolution data is preserved in a separate asset for reference.
3. **Given** a clear image, **When** a cloud mask with opacity $\ge 0.9$ is applied to simulate occlusion, **Then** the resulting image has a confirmed cloud coverage area of $50\% \pm 2\%$ (where pixels with opacity $\ge 0.9$ are counted as cloud) and the underlying pixel values are masked (not interpolated).

---

### User Story 2 - CPU-Optimized Generative Restoration (Priority: P2)

**Journey**: A researcher runs the baseline 3D Gaussian Splatting (3DGS) generation and the proposed inpainting module on the degraded dataset using only CPU resources. The system generates 3D scenes from the degraded inputs, attempting to recover lost geometric and textural details using a distilled diffusion prior optimized for CPU execution (ONNX Runtime), while strictly adhering to memory and time limits.

**Why this priority**: This addresses the core "Compute feasibility" constraint. The research question is moot if the method cannot run on the target infrastructure (GitHub Actions free-tier). This story ensures the methodology is executable without GPU acceleration.

**Independent Test**: The system can process a single degraded $100\text{~m}^2$ patch through the full generation and inpainting pipeline, completing within 45 minutes on a standard 2-core CPU runner, with peak RAM usage $< 6.5$ GB, and producing a valid 3DGS `.ply` file.

**Acceptance Scenarios**:

1. **Given** a degraded satellite image and a 2-core CPU environment, **When** the baseline 3DGS inference runs, **Then** the process completes without CUDA errors and outputs a scene file within 30 minutes.
2. **Given** a degraded scene and the CPU-optimized inpainting module, **When** the restoration runs, **Then** the process uses only CPU instructions (no GPU device calls), completes within 45 minutes, and peak RAM usage remains $< 6.5$ GB.
3. **Given** a generated 3D scene, **When** the output is validated, **Then** the file format is a standard `.ply` compatible with standard 3DGS viewers, and the file size is $< 500$ MB per scene.

---

### User Story 3 - Fidelity Quantification & Threshold Analysis (Priority: P3)

**Journey**: A researcher analyzes the generated scenes to quantify the recovery of geometric and textural fidelity. The system computes Projected PSNR (P-PSNR), Projected SSIM (P-SSIM), and Chamfer Distance against the ground truth LiDAR for both baseline and inpainted scenes, performs statistical significance testing, and sweeps the decision thresholds to identify the critical NNF point where restoration fails.

**Why this priority**: This delivers the scientific answer to the research question. It transforms raw model outputs into the "fundamental limits" and "critical thresholds" required by the hypothesis.

**Independent Test**: The system can process the metrics for the full 500-sample dataset, output a CSV with all metrics, and generate a plot showing the performance drop-off curve, identifying a specific NNF threshold where the improvement from inpainting becomes statistically insignificant (p-value $> 0.05$).

**Acceptance Scenarios**:

1. **Given** a generated 3D scene and its ground truth LiDAR, **When** the evaluation script runs, **Then** it outputs P-PSNR, P-SSIM, and Chamfer Distance values, ensuring the Chamfer Distance is calculated on a normalized scale (e.g., meters) and is reproducible.
2. **Given** the metrics for 500 samples, **When** the statistical analysis runs, **Then** a paired t-test confirms whether the difference between baseline and inpainted metrics is significant at $\alpha = 0.05$, and the result is logged.
3. **Given** a range of degradation intensities, **When** the sensitivity analysis runs, **Then** the system sweeps the Normalized Noise Fraction (NNF) threshold in configurable steps (default setting) and reports the false-positive rate (points > 2m from LiDAR in occluded regions) at each step.

### Edge Cases

- What happens when the LiDAR ground truth for a specific region is missing or misaligned beyond the $< 2$ meter threshold? (System should flag and exclude the sample, logging the exclusion reason).
- How does the system handle a scene where the cloud cover is total ([deferred]), making geometric recovery impossible? (The system should detect this, skip the inpainting attempt, and record the result as a "complete failure" data point for the threshold analysis).
- How does the system behave if the CPU runner runs out of memory during the diffusion prior loading? (The system should gracefully fail with a specific error code `ERR_OOM_CPU` and trigger a retry with a smaller batch size or sample subset).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and align 500 urban $1\text{~km}^2$ Sentinel-2 tiles with independent OpenTopography LiDAR ground truth, ensuring spatial alignment error is $< 2$ meters for all samples (See US-1).
- **FR-002**: System MUST apply three distinct synthetic degradation modes (downscale to 30m/pixel, procedural cloud masks with variable opacity, temporal shifts) to the input imagery with reproducible random seeds (See US-1).
- **FR-003**: System MUST execute the 3D Gaussian Splatting generation and the CPU-optimized inpainting module using only CPU resources on $100\text{~m}^2$ patches, ensuring no CUDA or GPU-specific libraries are invoked (See US-2).
- **FR-004**: System MUST compute geometric consistency (Chamfer Distance) and textural fidelity (Projected PSNR, Projected SSIM) metrics for both baseline and inpainted scenes against the independent LiDAR ground truth (See US-3).
- **FR-005**: System MUST perform a paired t-test on the metric improvements across a sufficiently large sample of data. and execute a sensitivity analysis sweeping the Normalized Noise Fraction (NNF) threshold in configurable steps to identify the critical failure point (See US-3).
- **FR-006**: System MUST validate the synthetic cloud degradation approximation by comparing statistical properties of synthetic masks against a sample of real cloud-masked images (See Assumptions).

### Key Entities

- **DegradedScene**: Represents a satellite image region with applied synthetic degradation (resolution, cloud mask, temporal shift) and its associated metadata (NNF, degradation type).
- **ReconstructedScene**: Represents the 3D Gaussian Splatting output generated from a DegradedScene, containing geometry and texture data in `.ply` format.
- **GroundTruthLiDAR**: Represents the independent, high-fidelity point cloud data used as the reference standard for validation.
- **FidelityMetrics**: A record containing P-PSNR, P-SSIM, and Chamfer Distance values comparing a ReconstructedScene to a GroundTruthLiDAR.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Geometric recovery rate (measured by the reduction in Chamfer Distance between baseline and inpainted scenes) is measured against the baseline degraded scenes to determine the extent of fidelity recovery (See US-3).
- **SC-002**: The critical NNF threshold (the point where restoration fails to recover structure) is measured against the degradation intensity curve to identify the specific Normalized Noise Fraction value where the p-value of improvement rises above the conventional threshold for statistical significance. (See US-3).
- **SC-003**: Computational feasibility (measured by peak RAM usage and total wall-clock time per scene) is measured against the GitHub Actions free-tier constraints (GB RAM, 6 hours total job time) to ensure the analysis runs without hardware failure (See US-2).
- **SC-004**: Statistical significance of the restoration improvement (measured by the p-value from the paired t-test) is measured against the $\alpha = 0.05$ threshold to confirm the inpainting module provides a non-random benefit (See US-3).

## Assumptions

- **Assumption about dataset availability**: Public Sentinel-2 data and OpenTopography LiDAR data are available for at least 500 distinct urban $1\text{~km}^2$ regions with sufficient spatial overlap to allow alignment.
- **Assumption about model weights**: A lightweight, CPU-compatible quantization of the diffusion prior (e.g., distilled Stable Diffusion via ONNX) exists or can be derived from open weights without requiring GPU-specific training.
- **Assumption about ground truth independence**: The LiDAR data provided by OpenTopography or city portals is independent of the optical satellite imagery used as input, ensuring the evaluation is not circular.
- **Assumption about degradation simulation**: Synthetic cloud masks (using alpha-blended procedural masks) can accurately approximate the information loss found in real-world satellite data degradation modes for the purpose of this study, provided validation against real masks (FR-006) confirms statistical similarity.
- **Assumption about compute limits**: The GitHub Actions free-tier runner provides a consistent multi-core CPU environment with sufficient I/O bandwidth to handle the target dataset within the 6-hour window., assuming scene complexity is limited to $100\text{~m}^2$ patches.