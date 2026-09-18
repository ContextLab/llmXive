# Feature Specification: llmXive follow-up: extending "TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction"

**Feature Branch**: `001-llmxive-trisplat-ext`  
**Created**: 2026-09-18  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending TriSplat for CPU-only edge robotics by replacing learned refinement with explicit geometric constraints and determining sparsity thresholds."

## User Scenarios & Testing

### User Story 1 - CPU-Feasible Geometry-Only Reconstruction (Priority: P1)

As a robotics researcher, I want to run a 3D scene reconstruction pipeline on a standard 2-core CPU (simulating GitHub Actions free-tier) using only explicit geometric consistency constraints, so that I can generate simulation-ready meshes without relying on heavy learned refinement heads or GPU acceleration.

**Why this priority**: This is the core hypothesis of the project. If the system cannot run on CPU or fails to produce a mesh, the entire research question regarding the "geometry-only" boundary is moot. This validates the feasibility of the method on constrained hardware.

**Independent Test**: Can be fully tested by executing the reconstruction pipeline on a single RealEstate10K scene (downscaled to 320x240) on a CPU-only runner and verifying that a valid mesh file (`.obj` or `.ply`) is output within the 6-hour CI time limit.

**Acceptance Scenarios**:

1. **Given** a single input scene from RealEstate10K validation set with 3 input views at 320x240 resolution, **When** the pipeline executes on a 2-core CPU environment, **Then** a valid mesh file is generated within 30 minutes without GPU errors or out-of-memory exceptions.
2. **Given** the frozen TriSplat backbone, **When** the new differentiable ray-surface intersection layer is applied, **Then** the output mesh topology is valid (no non-manifold edges) and contains at least 10% of the face count of the ground-truth depth map (projected to mesh) for that scene.
3. **Given** a standard CI runner with 7 GB RAM, **When** the full inference and mesh generation process runs, **Then** peak memory usage remains below 6 GB to ensure stability.

---

### User Story 2 - Sparsity Threshold Identification (Priority: P2)

As a computer vision scientist, I want to systematically vary the number of input views (2, 3, 4, 5) and baseline distances, so that I can identify the specific sparsity threshold where explicit geometric constraints fail to resolve occlusions and learned priors become necessary.

**Why this priority**: This addresses the primary research question ("at what sparsity threshold..."). It transforms the project from a simple feasibility study into a scientific inquiry about the limits of geometry-driven methods.

**Independent Test**: Can be fully tested by running the reconstruction pipeline across a representative set of random scenes from the RealEstate10K validation set with varying view counts and comparing the Chamfer Distance metrics to determine the inflection point where performance degrades significantly.

**Acceptance Scenarios**:

1. **Given** a test set of 50 scenes with known ground-truth depth maps, **When** the pipeline processes each scene with 2, 3, 4, and 5 input views respectively, **Then** the system outputs a structured log of Chamfer Distance and PSNR for each view count configuration.
2. **Given** a scene with high occlusion complexity, **When** the input view count is reduced from 5 to 2, **Then** the rate of Chamfer Distance increase per view reduction is statistically significantly steeper (p < 0.05) for the geometry-only method than for the baseline TriSplat method.
3. **Given** the collected metrics across 50 random scenes, **When** a statistical significance test (paired t-test or Wilcoxon signed-rank test) is performed, **Then** a clear "threshold" view count is identified where the geometric-only method's error rate exceeds a pre-defined engineering tolerance of 15% relative increase in error compared to the 5-view baseline.

---

### User Story 3 - Quantitative Fidelity and Latency Benchmarking (Priority: P3)

As an edge-systems engineer, I want to compare the inference latency and geometric fidelity of the geometry-only module against the original TriSplat baseline, so that I can quantify the trade-off between computational efficiency and mesh quality for real-time applications.

**Why this priority**: This provides the necessary context for the "efficiency" claim. It validates that the CPU-only approach actually offers a latency benefit, even if fidelity drops at high sparsity.

**Independent Test**: Can be fully tested by running both the baseline TriSplat (if CPU feasible) and the new geometry-only module on the same hardware and comparing the recorded inference times and fidelity metrics.

**Acceptance Scenarios**:

1. **Given** the same input image pair, **When** the geometry-only module and the baseline TriSplat refinement head are executed on a 2-core CPU, **Then** the geometry-only module's inference latency is at least as fast as the baseline (speedup ratio ≥ 1.0); if the baseline fails to execute on CPU, the requirement is satisfied if the geometry-only module succeeds within 30 minutes.
2. **Given** a set of 50 scenes, **When** PSNR is calculated on novel views for both methods, **Then** the geometry-only method maintains a PSNR within 5.0 dB of the baseline for low-sparsity scenes (≥ 4 views), acknowledging expected degradation at higher sparsity (≤ 2 views).
3. **Given** the final benchmark report, **When** the data is visualized, **Then** a clear trade-off curve is presented showing latency reduction vs. Chamfer Distance degradation as sparsity increases.

### Edge Cases

- What happens when the input view count is 1 (monocular)? The system should gracefully fail or output a warning that 2 views are the minimum for triangulation, rather than crashing.
- How does the system handle scenes with extreme lighting changes or low texture (e.g., white walls)? The ray-surface intersection layer may fail to converge; the system should detect non-convergence after a set iteration limit (e.g., 100 steps) and output a placeholder mesh or error flag.
- What if the ground-truth depth map for a scene is missing or corrupted in the RealEstate10K validation set? The pipeline should skip that scene and log a warning, ensuring the batch process does not halt.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a differentiable ray-surface intersection layer that computes surface normals from local triangle connectivity and depth gradients, replacing the learned CNN refinement head. (See US-1)
- **FR-002**: System MUST support dynamic configuration of input view counts (2, 3, 4, 5) and baseline distances via command-line arguments or a configuration file. (See US-2)
- **FR-003**: System MUST downscale input images to 320x240 resolution prior to processing to simulate edge-device constraints. (See US-1)
- **FR-004**: System MUST output valid mesh files (`.obj` or `.ply`) and associated metadata logs containing Chamfer Distance and PSNR metrics for every processed scene. (See US-2)
- **FR-005**: System MUST perform statistical significance testing on the Chamfer Distance metrics across the 50 random test scenes defined in US-2. The system MUST first test for normality of the error differences (Shapiro-Wilk test). If normality holds, it MUST perform a one-tailed paired t-test with the null hypothesis that the error distribution is not significantly worse at lower view counts. If normality fails, it MUST perform a Wilcoxon signed-rank test. The result must identify a view count threshold where the error exceeds the 15% tolerance. (See US-2)
- **FR-006**: System MUST enforce a hard timeout and a memory cap to ensure compatibility with GitHub Actions free-tier runners. (See US-1)
- **FR-007**: System MUST detect and log non-convergence events in the ray-surface intersection layer after a maximum of 100 iterations per ray, preventing infinite loops. (See Edge Cases)

### Key Entities

- **Scene Configuration**: Represents the input parameters for a single test, including view count, baseline distance, and image paths.
- **Reconstruction Result**: Represents the output of the pipeline, containing the mesh geometry, computed metrics (Chamfer Distance, PSNR), and latency data.
- **Statistical Summary**: Aggregated data across multiple scenes, including mean metrics, standard deviation, and p-values from significance tests.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Inference latency (seconds) is measured against the baseline TriSplat execution time on the same 2-core CPU hardware to quantify speedup. (See US-3)
- **SC-002**: Geometric fidelity (Chamfer Distance) is measured against the ground-truth depth map (projected to mesh) provided by the RealEstate10K validation set to assess reconstruction accuracy. (See US-2)
- **SC-003**: Novel view synthesis quality (PSNR) is measured against the ground-truth novel views from the RealEstate10K dataset to evaluate rendering capability. (See US-3)
- **SC-004**: Statistical significance (p-value) of the performance drop is measured against a standard significance threshold to confirm the existence of a sparsity threshold. (See US-2)
- **SC-005**: Memory usage (MB) is measured against the available RAM limit of the GitHub Actions free-tier runner to verify feasibility. (See US-1)

## Assumptions

- The RealEstate validation set contains sufficient ground-truth depth maps and novel view images to support the evaluation of random scenes.
- The TriSplat backbone weights are available and can be loaded without requiring a GPU (CPU-compatible checkpoint format).
- The "sparsity threshold" identified will be a discrete number of views (e.g., 3 views) rather than a continuous baseline distance, due to the discrete nature of the dataset's camera poses.
- The downscaling of images to 320x240 does not introduce artifacts that disproportionately affect the ray-surface intersection layer compared to the original resolution.
- The GitHub Actions free-tier runner provides consistent CPU performance (multiple cores) sufficient to complete the 50-scene evaluation within the 6-hour window.
- The differentiable ray-surface intersection layer will converge within 100 iterations for the majority of scenes; non-convergence is treated as a failure case rather than a methodological flaw.