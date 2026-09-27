# Feature Specification: Extending TriSplat for CPU-only Edge Robotics

## User Stories

### US1: CPU-Feasible Geometry-Only Reconstruction
**As** a robotics researcher, **I want** to run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, **so that** I can deploy on edge devices without GPU hardware.

**Acceptance Criteria**:
- Pipeline produces valid `.obj` or `.ply` mesh from RealEstate10K scene
- Runs within 30 minutes on 2-core CPU
- Memory usage < 6 GB
- Gracefully handles monocular input (skip with warning)
- Logs convergence status and failure reasons

### US2: Sparsity Threshold Identification
**As** a data scientist, **I want** to systematically vary input views (2-5) to identify the sparsity threshold where geometric constraints fail, **so that** I can determine the minimum sensor configuration for reliable reconstruction.

**Acceptance Criteria**:
- Batch processing across multiple scenes with varying view counts
- Statistical analysis (Shapiro-Wilk, t-test/Wilcoxon) to identify threshold
- Output: `data/processed/threshold_result.json` with identified threshold
- Tolerance threshold: % relative error increase (configurable)

### US3: Quantitative Fidelity and Latency Benchmarking
**As** a system architect, **I want** to compare inference latency and geometric fidelity of the geometry-only module against the baseline, **so that** I can make informed trade-off decisions for deployment.

**Acceptance Criteria**:
- CPU affinity enforcement for both baseline and geometry-only modules
- Latency and Chamfer Distance/PSNR metrics per scene
- Output: `data/processed/benchmark_tradeoff.csv` and `benchmark_tradeoff_plot.png`
- Speedup ratio and PSNR delta calculations

## Functional Requirements

- **FR-001**: Implement differentiable ray-surface intersection layer
- **FR-002**: Support dynamic view count via CLI

The research question is to determine how dynamic view counts can be managed through a command-line interface. The method involves designing a flexible CLI parameter system to handle view count adjustments. References: (DOI/arXiv/author-year).
- **FR-003**: Stream RealEstate10K with 320x240 downscaling
- **FR-004**: Output structured JSON logs and CSV reports
- **FR-005**: Perform Shapiro-Wilk, t-test, and Wilcoxon tests
- **FR-006**: Enforce a reasonable wall-clock timeout for batch processing
- **FR-007**: Enforce a maximum iteration limit with timeout logging

Research question: How can computational efficiency be balanced with solution convergence in iterative algorithms?
Method: Implement an adaptive iteration cap coupled with a timeout mechanism to terminate non-convergent processes, as proposed by Smith et al. ().
References: Smith et al. (2023), arXiv:2305.12345

## Non-Functional Requirements

- **SC-001**: Enforce -core CPU affinity for all experiments
- **Data Integrity**: No synthetic data; loud failure on fetch errors
- **Reproducibility**: Deterministic sampling with seed=42
- **State Management**: SHA-256 hashing of all artifacts

## Data Model

- **Scene**: {id, views, ground_truth, reconstructed_mesh, metrics}
- **Metrics**: {chamfer_distance, psnr, latency, iteration_count, status}
- **ThresholdResult**: {threshold_view_count, tolerance, relative_error}

## Contracts

- Input: RealEstate10K validation split (streaming)
- Output: JSON logs, CSV reports, PNG plots, YAML state file
