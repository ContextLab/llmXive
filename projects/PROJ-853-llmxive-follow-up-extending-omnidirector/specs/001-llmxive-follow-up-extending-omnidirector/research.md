# Research: llmXive follow-up: extending "OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired D"

## 1. Problem Statement & Hypothesis

**Problem**: The "OmniDirector" framework generates "empty" camera grid representations to clone camera shots. It is unclear if these 2D grid projections retain sufficient geometric information to invert the 3D camera trajectory and reconstruct scene bounding box *relative* dimensions (aspect ratios) without metric depth sensors.

**Hypothesis**: The grid representation encodes invertible 3D *relative* scene priors (aspect ratios) but discards *absolute* metric scale. Specifically, the perspective distortion of orthogonal grid lines is a deterministic function of the camera's 3D pose relative to a canonical unit grid, allowing for the recovery of relative scene dimensions with a statistically significant correlation between motion complexity and reconstruction accuracy (for aspect ratios).

## 2. Dataset Strategy

**Dataset**: OmniDirector (Camera Grid-Video Pairs).
**Status**: **NO VERIFIED SOURCE FOUND**.
**Strategy**: 
1.  **Data Availability Gate**: The pipeline will first check for the dataset in the local `data/raw/` directory. 
2.  **If Found**: Proceed with full analysis (Internal Consistency + Metric Validity tests).
3.  **If Not Found**: The project proceeds *only* with the **Synthetic Control** to test the *theoretical* invertibility of the grid representation. The core research question regarding the *specific* OmniDirector dataset is flagged as **Untestable** until a verified source is provided.
*Note: The project does not fabricate a URL. The lack of a verified source is a critical limitation.*

**Data Loading**:
- The pipeline will load video sequences and associated metadata (camera intrinsics, extrinsics $R_i, t_i$) if available.
- **Filtering (FR-001)**: Sequences will be filtered based on:
  - Radial motion > 15°
  - Z-axis velocity > 0.1 units/frame
- **Exclusion**: Sequences with purely translational X/Y motion or static cameras will be excluded and logged.

**Synthetic Control**:
- To validate the "metric depth loss" hypothesis (FR-008), a subset of data will be generated or selected where depth was randomized during generation. The solver will attempt to recover these *randomized* depths. 
- **Validation Logic**: High error rates (>50%) on the Synthetic Control (comparing recovered dimensions against the *randomized* depth values) will confirm the hypothesis that the grid representation discards metric information. This is the only test for independent metric validity.

## 3. Methodology & Solver Design

### 3.1 Geometric Inversion (FR-002, FR-003)

**Assumption**: The "empty" grid represents a **Canonical Unit Grid** ($Z=0$ in world frame, unit square spacing).

**Algorithm**:
1.  **Line Detection**: Use `cv2.Canny` and `cv2.HoughLinesP` or `cv2.findContours` to detect orthogonal grid lines in each frame.
2.  **Intersection Tracking**: Compute intersections of orthogonal lines.
3.  **Pose Estimation**: Use `cv2.solvePnP` (Iterative or EPnP) to estimate camera pose ($R, t$) relative to the unit grid.
    - *Input*: 2D intersection points (image) + 3D unit grid points (world).
    - *Constraint*: CPU-only, default precision.
    - *Scale Ambiguity*: `solvePnP` on a planar target yields pose up to a scale factor. The solver will output a `scale_factor` (default 1.0) and relative dimensions.
4.  **Trajectory Integration**: Integrate relative poses to estimate camera path.
5.  **Bounding Box Reconstruction**:
    - Derive *relative* scene dimensions (height, width, depth) by analyzing the extent of the camera path relative to the grid plane.
    - **Scale Anchoring**: For the "Standard Room" test case, assume a canonical height (e.g., 2.4m) to resolve scale. For general analysis, report *aspect ratios* (Width/Depth, Height/Depth) which are scale-invariant.

### 3.2 Statistical Validation (FR-004, FR-005, FR-006, FR-008)

**Metrics**:
- **Reconstruction Error (Internal Consistency)**: Absolute difference between *relative* estimated and ground-truth *relative* dimensions (Aspect Ratio Error). This tests if the solver can re-derive the generation parameters.
- **Reconstruction Error (Metric Validity)**: Absolute difference between *absolute* estimated and *randomized* ground-truth dimensions (Synthetic Control only). This tests if the grid encodes metric info.
- **Complexity Metric**: Variance of camera rotation vectors or path length per frame.
- **Correlation**: Pearson's $r$ between Complexity and *Aspect Ratio Error*.
  - *Hypothesis*: Higher complexity (e.g., rapid orbits) leads to higher *aspect ratio* error due to perspective distortion limits.
- **Aspect Ratio Validation**: Compare $Width/Depth$ of reconstructed box vs. known synthetic room volumes (tolerance $\pm 5\%$).

**Statistical Rigor**:
- **Multiple Comparisons**: If testing multiple room types, apply Bonferroni correction.
- **Sample Size**: Power analysis deferred to implementation; assume sufficient samples in "million-scale" dataset.
- **Causal Inference**: Claims are **associational**. We observe correlation between motion complexity and error; we do not claim causality without controlled randomization of motion (which is not the case here).
- **Collinearity**: Acknowledge that camera motion and grid distortion are definitionally linked; independent effects are not claimed.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 vCPU, ~7GB RAM).
- **Optimization**:
  - Process sequences in batches.
  - Downsample video frames if resolution > 1080p to reduce `solvePnP` overhead.
  - Use `cv2.SOLVEPNP_IPPE` for planar targets if grid is planar (faster than iterative).
  - **No GPU**: Strictly CPU-based libraries.
- **Runtime**: Target < 6 hours for the full filtered dataset. If exceeded, implement adaptive sampling (e.g., process 1 frame per second).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailable** | High | Pipeline fails fast with clear error; Synthetic Control (FR-008) uses generated data to test logic. Project proceeds with "Untestable" status for OmniDirector-specific claims. |
| **Grid Occlusion/Missing Lines** | Medium | Solver skips frames with < 4 detected intersections; interpolates missing poses. |
| **High Motion Blur** | Medium | Flag sequences with high blur (Laplacian variance) and exclude from analysis. |
| **Memory Overflow** | High | Stream data; do not load full dataset into RAM. Process one sequence at a time. |
| **Scale Ambiguity** | High | Explicitly report results as "relative dimensions" or "aspect ratios". Do not claim absolute metric recovery without an external anchor. |
