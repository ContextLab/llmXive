# Feature Specification: Extending TriSplat for CPU-only Edge Robotics

## User Stories

### US1: CPU-Feasible Geometry-Only Reconstruction (P1)
**As** an edge robotics developer,
**I want** to run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints,
**So that** I can deploy 3D perception on resource-constrained devices within 30 minutes per scene.

**Acceptance Criteria**:
- Pipeline runs on CPU-only hardware
- Produces valid `.obj`/`.ply` mesh output
- Completes within 30 minutes for a single RealEstate10K scene (320x240)
- Handles monocular input errors gracefully

### US2: Sparsity Threshold Identification (P2)
**As** a researcher,
**I want** to systematically vary input views (2-5) to identify the sparsity threshold where geometric constraints fail,
**So that** I can determine the minimum sensor configuration required for valid reconstruction.

**Acceptance Criteria**:
- Batch processing of a set of scenes across multiple view configurations, including configurations with two views (see e.g., [Citation]).
- Output of Chamfer Distance and PSNR per scene/view-count
- Statistical test to identify the view count where error exceeds a predefined tolerance threshold.
- Results saved to `data/processed/threshold_result.json`

### US3: Quantitative Fidelity and Latency Benchmarking (P3)
**As** a system architect,
**I want** to compare inference latency and geometric fidelity of the geometry-only module against the baseline,
**So that** I can make informed trade-off decisions for edge deployment.

**Acceptance Criteria**:
- Latency measurement for both geometry-only and baseline TriSplat
- Enforced multi-core CPU affinity for baseline comparison. The research question is whether CPU affinity improves performance stability. The method involves comparing baseline and affinity-enforced configurations. References include Smith et al..
- Benchmark report CSV with view_count, latency, chamfer_distance, psnr
- Trade-off curve visualization (PNG)

## Functional Requirements

- **FR-001**: Implement differentiable ray-surface intersection layer
- **FR-002**: Support dynamic view count configuration (2-5 views)
- **FR-003**: Stream RealEstate10K with 320x240 downscaling
- **FR-004**: Output JSON logs with Chamfer Distance and PSNR
- **FR-005**: Perform Shapiro-Wilk, t-test, and Wilcoxon tests
- **FR-006**: Enforce 6-hour batch timeout with N=20 scene limit
- **FR-007**: Hard limit of a predefined maximum number of iterations with non-convergence logging.

## Non-Functional Requirements

- **SC-001**: Strict 2-core CPU affinity for baseline comparison
- **SC-002**: Peak RAM usage < 6 GB
- **SC-003**: Streaming dataset loading to avoid memory overflow
- **SC-004**: No synthetic data fallback; fail loudly on real data fetch errors

## Data Model

- **SceneResult**: `scene_id`, `view_count`, `chamfer_distance`, `psnr`, `latency`, `status`, `error_flag`
- **ThresholdResult**: `threshold_view_count`, `tolerance_threshold`, `relative_error_increase`
- **BenchmarkResult**: `view_count`, `latency`, `chamfer_distance`, `psnr`, `baseline_latency`

## Contracts

- **Input**: RealEstate10K dataset (streaming)
- **Output**: JSON logs, CSV reports, PNG visualizations, mesh files (.obj/.ply)
