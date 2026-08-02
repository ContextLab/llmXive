# Research: llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

## Executive Summary
This research investigates the performance ceiling of agentic spatial reasoning when constrained to 2D geometric operations. By enforcing a restricted execution kernel that blocks 3D libraries (`trimesh`, `pytorch3d`) and forces the use of 2D primitives (`shapely`, `numpy`), we measure the degradation in success rate and latency compared to a re-run 3D baseline. The study addresses the trade-off between computational efficiency (edge deployment) and spatial expressiveness. The data source is the **Synthetic SpatialClaw Proxy**, a verified, self-contained dataset generator that replicates the conceptual difficulty of the SpatialClaw benchmark while ensuring reproducibility and CI compatibility.

## Dataset Strategy

### Synthetic SpatialClaw Proxy
- **Description**: A procedurally generated dataset that replicates the occlusion, depth estimation, and relative position tasks of the SpatialClaw benchmark.
- **Availability Status**: **Verified** (Self-contained code generator).
- **Strategy**: 
  - The generator uses procedural generation logic based on [Citation: Procedural Generation for Spatial Reasoning Benchmarks] to create 3D scenes with controlled geometric complexity.
  - It ensures that 3D invariants (e.g., objects overlapping in 3D but not in 2D) are preserved to measure the "loss ceiling".
  - The generator is the source of truth; all data is checksummed and reproducible.
- **Validation**: A pilot set is generated to verify that 2D projection loses critical information for a subset of tasks (Validity Check).

### Baseline Data
- **Source**: Re-run 3D baseline agent on the same task instances (FR-007).
- **Strategy**: The 3D baseline is re-executed on the *exact same* task instances as the 2D agent to generate a paired dataset. The `data/baseline_spatialclaw.csv` is used as a reference for expected behavior, but the actual comparison is against the *re-run* results.

## Technical Methodology

### 1. Restricted Execution Kernel (FR-001)
- **Mechanism**: Python's `sys.modules` interception and AST parsing.
  - On import of `trimesh`, `pytorch3d`, `open3d`, raise `RestrictedActionError`.
  - Intercept function calls within allowed modules that invoke 3D rendering.
- **Validation**: Log every blocked attempt. Grep logs for "trimesh" to ensure count=0 in successful 2D runs.

### 2. 2D Projection Logic (FR-002)
- **Input**: 3D point clouds or scene descriptions.
- **Transformation**:
  - **Bounding Boxes**: Project 3D AABBs to 2D XY planes.
  - **Depth Histograms**: Bin Z-values into 2D histograms per region to preserve some depth cues without 3D primitives.
  - **Occlusion**: Use `shapely` polygon intersections to determine 2D occlusion.
- **Constraint**: No 3D reconstruction libraries. Only 2D vector math.

### 3. Stochasticity Control (FR-008)
- **Configuration**:
  - `random.seed(42)` (or specific seed per run).
  - `numpy.random.seed(42)`.
  - Agent temperature = 0.
- **Runs**: N runs per task instance (N determined by power analysis, minimum 5).

### 4. Statistical Analysis (FR-005, FR-006)
- **Primary Test (Binary)**: **McNemar's test** for paired success/failure outcomes (avoiding the misuse of Wilcoxon on proportions).
- **Primary Test (Continuous)**: **Wilcoxon signed-rank test** for continuous metrics (e.g., depth estimation error in meters).
- **Correction**: Bonferroni correction applied for multiple comparisons across multiple task types.
- **Sensitivity Analysis**: Sweep depth-estimation threshold (e.g., a range from a lower bound to 1.0m) and report False Positive/Negative rates against the **independent ground truth** (synthetic generator's known geometric parameters), not the 3D baseline's output, to avoid circular validation.

## Compute Feasibility (CPU-First)

- **Target**: GitHub Actions free-tier (multiple vCPU, ample RAM).
- **Strategy**:
  - **Data**: Synthetic proxy generator produces data on-the-fly; no large downloads.
  - **Processing**: `shapely` and `numpy` are CPU-native and highly efficient.
  - **Memory**: Streaming approach for point clouds (process in chunks) if synthetic data exceeds RAM.
  - **Time**: N runs × N tasks should complete well within 6 hours (N calculated in Phase 0).
- **GPU Escape Hatch**: Not required for this specific experiment as the 2D agent is CPU-bound. The 3D baseline re-run might use `trimesh` (CPU) or a lightweight 3D renderer; if the baseline requires CUDA, the execution stage will auto-offload to Kaggle GPU. However, the spec implies a CPU-first approach for the *restricted* agent, and the baseline re-run is expected to be feasible on CPU for a small benchmark subset.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Dataset Unavailability** | Synthetic Proxy Generator implemented to ensure reproducibility and CI compatibility. |
| **3D Library Leakage** | Strict `sys.modules` hooking + AST validation + log grepping. |
| **Memory Overflow** | Chunked processing of point clouds; streaming data generation. |
| **Statistical Power** | N calculated via power analysis; if variance is too high, increase N (within time budget). |
| **Circular Validation** | Sensitivity analysis uses independent ground truth (generator parameters), not 3D baseline output. |

## References
- **SpatialClaw**: Conceptual benchmark; no verified URL found. Synthetic Proxy used as verified data source.
- **Procedural Generation**: [Citation: Procedural Generation for Spatial Reasoning Benchmarks] (to be filled with verified source).
- **RestrictedActionError**: Custom implementation; no external source.
- **Shapely**: https://shapely.readthedocs.io/
- **NumPy**: https://numpy.org/
- **McNemar's Test**: Standard statistical method for paired binary data (no external URL needed for method definition).

