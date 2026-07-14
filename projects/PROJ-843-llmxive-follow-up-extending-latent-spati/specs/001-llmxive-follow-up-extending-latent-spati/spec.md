# Feature Specification: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Latent Spatial Memory for Video World Models'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stratified Dataset Preparation and Feature Extraction (Priority: P1)

The research pipeline MUST automatically ingest the RealEstate10K dataset, stratify it into four distinct subsets based on scene dynamics (static/slow/fast) and texture richness (high/low), and extract sparse SIFT/ORB descriptors from keyframes without generating dense depth maps.

**Why this priority**: This is the foundational data layer. Without correctly stratified data and sparse feature extraction, the comparative analysis between sparse and dense methods cannot be performed. It defines the independent variables (scene conditions) for the study.

**Independent Test**: The system can be tested by running the data preparation script on a small subset and verifying that the output directory contains four distinct folders with the correct metadata labels and that the extracted feature files (e.g., `.npy` or `.pkl`) contain valid coordinate/descriptor pairs for the specified keyframes.

**Acceptance Scenarios**:

1. **Given** the RealEstate10K dataset is available, **When** the stratification script runs, **Then** exactly four subsets (Static-High, Static-Low, Fast-High, Fast-Low) are created with equal number of sequences (N=50) per subset.
2. **Given** a video frame from the "Fast-Low" subset, **When** the feature extractor runs, **Then** it outputs sparse descriptors and 2D coordinates but fails to generate or store a dense depth map, reducing memory footprint.

---

### User Story 2 - Sparse Epipolar Solver and Latent Warping Execution (Priority: P2)

The system MUST implement a differentiable epipolar geometry layer using RANSAC-optimized sparse correspondences to compute the fundamental matrix, project features into 3D space (up to scale), and perform latent-space warping with RBF interpolation for occluded regions, running entirely on a standard 8-core CPU environment.

**Why this priority**: This is the core experimental intervention. It replaces the dense depth baseline with the sparse method. If this fails to run on CPU or produces invalid 3D coordinates, the hypothesis test cannot proceed.

**Independent Test**: The system can be tested by feeding a single video sequence from the "Static-High" subset into the solver and verifying that the output latent warps align with epipolar constraints (low re-projection error) or that the interpolation fills occlusions without crashing, while monitoring that no GPU memory is allocated.

**Acceptance Scenarios**:

1. **Given** a pair of keyframes with sparse correspondences, **When** the RANSAC solver runs, **Then** it outputs a valid fundamental matrix and 3D point cloud (up to scale) within 60 seconds on a standard 8-core CPU environment.
2. **Given** a region of occlusion in the warped frame, **When** the RBF interpolator runs, **Then** it generates a geometrically smooth latent representation for the missing area without introducing NaN values or artifacts larger than ≤ 1.0% of the frame area.

---

### User Story 3 - Comparative Metrics and Statistical Validation (Priority: P3)

The system MUST compute WorldScore (topological fidelity) for the dense baseline and a Sparse-Consistency Score (re-projection error) for the sparse method, perform a two-way ANOVA to test for interaction effects between scene dynamics and texture, and generate a sensitivity report for the RANSAC consistency threshold.

**Why this priority**: This delivers the scientific answer to the research question. It quantifies the trade-off and validates the hypothesis regarding operational boundaries.

**Independent Test**: The system can be tested by running the evaluation script on a pre-computed set of results and verifying that the ANOVA p-value is calculated correctly, the sensitivity sweep produces a table of results for the specified thresholds, and the final report lists the interaction effects.

**Acceptance Scenarios**:

1. **Given** results from both sparse and dense models, **When** the statistical validation runs, **Then** it outputs a two-way ANOVA table with a p-value for the interaction term and a sensitivity analysis table for thresholds including a stringent level below 0.05.
2. **Given** the sensitivity analysis, **When** the report is generated, **Then** it explicitly states the change in WorldScore and Sparse-Consistency Score across the tested thresholds, confirming the robustness of the chosen cutoff.

---

### Edge Cases

- **What happens when** a video sequence has extremely low texture (e.g., a blank white wall) causing RANSAC to fail to find enough inliers? **Then** the system must flag the sequence as "Unsolvable" and exclude it from the statistical analysis rather than crashing or producing garbage 3D data.
- **How does the system handle** rapid motion blur that degrades SIFT/ORB feature detection? **Then** the system must detect low feature density and either fallback to a lower threshold (documented in sensitivity analysis) or mark the frame as invalid for the "Fast" category.
- **What happens when** CPU memory usage approaches a significant memory limit during RBF interpolation? **Then** the system must trigger a batch processing mode to process frames sequentially rather than in parallel, ensuring the job does not OOM (Out Of Memory).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST stratify the RealEstate10K test set into four subsets based on motion magnitude and texture entropy, selecting the a subset of sequences ranked by motion magnitude and a subset by texture entropy within each category to ensure statistical power (n≥50). (See US-1)
- **FR-002**: The system MUST extract sparse SIFT/ORB descriptors and 2D coordinates from keyframes, explicitly skipping dense depth map generation to reduce memory footprint. (See US-1)
- **FR-003**: The system MUST compute the fundamental matrix using a RANSAC-optimized approach on sparse correspondences and project these into a 3D coordinate frame (up to scale) without dense depth inputs, validating via re-projection error. (See US-2)
- **FR-004**: The system MUST perform latent-space warping using the computed sparse 3D points and fill occluded regions using a CPU-based Radial Basis Function (RBF) interpolator to generate geometrically smooth representations. (See US-2)
- **FR-005**: The system MUST execute a two-way ANOVA to test for interaction effects between "scene dynamics" and "texture level" on the respective metrics (WorldScore for dense, Sparse-Consistency for sparse), with a significance threshold of p < 0.05. (See US-3)
- **FR-006**: The system MUST perform a sensitivity analysis sweeping the RANSAC inlier consistency threshold over a set of representative low values and report the resulting variation in WorldScore and Sparse-Consistency Score. (See US-3)
- **FR-007**: The system MUST record wall-clock inference time and peak RAM usage (measured via the Python memory_profiler library) on a standard multi-core CPU environment for both sparse and dense approaches. (See US-3)

### Key Entities

- **StratifiedSubset**: Represents a group of videos categorized by motion (static/slow/fast) and texture (high/low).
- **SparseFeatures**: Represents the extracted 2D coordinates and descriptors (SIFT/ORB) without dense depth data.
- **WarpingResult**: Represents the output of the latent warping and RBF interpolation process, including the reconstructed frame and 3D point cloud (up to scale).
- **MetricReport**: Represents the aggregated results including WorldScore, Sparse-Consistency Score, ANOVA statistics, and sensitivity analysis data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The topological fidelity (WorldScore) of the dense baseline is measured against the sparse method's geometric consistency to determine the percentage difference in static/high-texture scenes. (See US-3)
- **SC-002**: The pixel-level reconstruction quality (FID) of the dense baseline is measured against the sparse method's output to quantify the trade-off in image sharpness. (See US-3)
- **SC-003**: The inference time of the sparse method is measured against the dense baseline to evaluate the hypothesis of a ≥40% reduction in CPU inference time. (See US-3)
- **SC-004**: The interaction effect significance (p-value from two-way ANOVA) is measured against the a standard alpha level to confirm that scene dynamics and texture richness jointly influence the method's performance. (See US-3)
- **SC-005**: The stability of the results is measured by the variation in WorldScore and Sparse-Consistency Score across the sensitivity sweep thresholds including a low-value setting to ensure the chosen threshold is not an arbitrary artifact. (See US-3)

## Assumptions

- The RealEstate10K dataset contains sufficient metadata (motion vectors or optical flow) to accurately stratify videos into "static," "slow," and "fast" categories, and texture metrics can be derived from the RGB frames themselves.
- The "dense depth baseline" is provided as a pre-computed baseline from the RealEstate10K official release (or a validated standard model like MiDaS if official is unavailable) to ensure a scientifically valid comparison for the speed/accuracy trade-off analysis.
- The RANSAC algorithm will converge on a valid fundamental matrix for high-texture scenes; for low-texture scenes, the system assumes a fallback strategy (e.g., flagging as uncomputable) is acceptable for the statistical analysis.
- The standard 8-core CPU environment provides sufficient compute resources for the CPU-optimized RBF interpolation and sparse feature extraction on sampled video sequences.
- The WorldScore metric can be computed using a pre-trained, frozen geometric consistency model that fits within the available CPU memory and does not require GPU acceleration.
- The sensitivity analysis thresholds {, 0.05, 0.1} are sufficient to characterize the robustness of the RANSAC inlier ratio without requiring a full continuous sweep.
- The "Sparse-Consistency Score" (re-projection error) is an appropriate proxy for geometric fidelity in the absence of ground-truth 3D points for the sparse method.