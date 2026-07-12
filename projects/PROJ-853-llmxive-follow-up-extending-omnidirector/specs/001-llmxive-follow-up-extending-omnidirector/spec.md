# Feature Specification: llmXive follow-up: extending "OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired D"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired D'"

## User Scenarios & Testing

### User Story 1 - Dataset Ingestion and Geometric Filtering (Priority: P1)

The system MUST ingest the OmniDirector million-scale camera grid-video pairs, filter sequences to retain only those with defined spatial volumes (e.g., dolly-ins, orbits) using a deterministic heuristic, and output a curated dataset of grid frames paired with their ground-truth camera parameters ($R_i, t_i$) for geometric analysis.

**Why this priority**: Without a clean, geometrically diverse dataset, no inversion algorithm can be trained or tested. This is the foundational data preparation step required for all subsequent analysis.

**Independent Test**: Can be fully tested by running the ingestion pipeline on a small subset (e.g., 50 sequences) and verifying that the output contains valid grid frames and corresponding ground-truth parameters, while correctly excluding sequences lacking spatial volume definitions based on the defined thresholds.

**Acceptance Scenarios**:

1. **Given** the raw OmniDirector dataset containing mixed sequence types, **When** the filtering module processes the data using the defined heuristics (radial motion > 15°, Z-velocity > 0.1 units/frame), **Then** only sequences with defined spatial volumes are retained, and sequences with purely translational X/Y motion or static cameras are excluded.
2. **Given** a retained sequence, **When** the system extracts grid frames, **Then** each frame is paired with its correct ground-truth camera rotation ($R_i$) and translation ($t_i$) parameters.
3. **Given** a sequence with ambiguous spatial definitions, **When** the filter runs, **Then** the sequence is logged as excluded and not included in the final curated dataset.

---

### User Story 2 - CPU-Based Perspective Inversion Solver (Priority: P2)

The system MUST implement a CPU-tractable geometric solver that ingests only the grid video frames, detects orthogonal grid line intersections, tracks perspective distortion over time, and estimates relative 3D camera motion to reconstruct scene bounding box dimensions (floor-to-ceiling height, room width/depth). The solver assumes a canonical unit grid model in the world frame to enable solvePnP.

**Why this priority**: This is the core research hypothesis: inverting the "empty" grid representation. It transforms the generative tool into an analysis method, directly addressing the research question.

**Independent Test**: Can be fully tested by running the solver on a single video sequence and comparing the reconstructed bounding box dimensions against the ground-truth dimensions derived from the original camera trajectory metadata.

**Acceptance Scenarios**:

1. **Given** a grid video frame with visible orthogonal lines, **When** the solver detects line intersections, **Then** the coordinates of these intersections are accurately identified within a tolerance of ≤ 2 pixels against the synthetic grid projection metadata.
2. **Given** a sequence of grid frames, **When** the solver tracks perspective distortion, **Then** it outputs a relative 3D camera motion vector for each frame transition.
3. **Given** the estimated motion vectors, **When** the solver reconstructs the scene bounding box, **Then** it outputs dimensions (height, width, depth) that match the dimensions derived from the original camera trajectory metadata.

---

### User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

The system MUST compute the reconstruction error between estimated and ground-truth dimensions, perform a statistical correlation analysis (Pearson's r) between camera motion complexity and reconstruction accuracy, and validate results against independent aspect ratio metrics. This analysis includes a synthetic control experiment to test for metric depth information loss.

**Why this priority**: This provides the empirical evidence required to answer the research question, determining if the grid representation is a robust, invertible encoding of spatial priors.

**Independent Test**: Can be fully tested by running the analysis on the full curated dataset and generating a report containing the Pearson correlation coefficient, error distribution, and validation against aspect ratios.

**Acceptance Scenarios**:

1. **Given** a set of reconstructed dimensions and ground-truth dimensions, **When** the error metric is computed, **Then** the reconstruction error is calculated as the absolute difference for each dimension.
2. **Given** a set of camera motion complexity metrics and reconstruction errors, **When** the correlation analysis runs, **Then** a Pearson's r coefficient is output, indicating the strength of the relationship.
3. **Given** the reconstructed dimensions, **When** validation against independent aspect ratios is performed, **Then** the system confirms whether the reconstructed aspect ratios match the known synthetic room volumes within a tolerance of ±5%.

---

### Edge Cases

- What happens when grid lines are occluded or missing in certain frames? The solver must handle missing data by interpolating or skipping frames without crashing.
- How does the system handle sequences with extremely high camera motion complexity (e.g., rapid, erratic movements)? The solver must detect and flag sequences where perspective distortion exceeds solvable thresholds.
- What happens if the dataset contains sequences with no defined spatial volume? The filtering step must explicitly exclude these and log the reason.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the OmniDirector dataset and filter sequences to retain only those with defined spatial volumes. The filtering logic MUST classify sequences as 'retained' if radial camera motion > 15° OR Z-axis velocity > 0.1 units/frame, and 'excluded' otherwise, ensuring geometric diversity for analysis (See US-1).
- **FR-002**: System MUST implement a CPU-based geometric solver using OpenCV's `solvePnP` or a least-squares optimizer. The solver MUST assume a 'Canonical Unit Grid' (a unit square grid at Z=0 in the world frame) as the 3D object model to detect orthogonal grid line intersections and track perspective distortion (See US-2).
- **FR-003**: System MUST reconstruct relative 3D bounding box dimensions (floor-to-ceiling height, room width/depth) from estimated motion vectors without requiring GPU acceleration (See US-2).
- **FR-004**: System MUST compute reconstruction error by comparing estimated dimensions against ground-truth scene box derived from original camera trajectories (See US-3).
- **FR-005**: System MUST perform statistical correlation analysis (Pearson's r) between camera motion complexity metrics and reconstruction accuracy to validate the hypothesis (See US-3).
- **FR-006**: System MUST validate aspect ratios of reconstructed scenes against known synthetic room volumes within a tolerance of ±5% (See US-3).
- **FR-007**: System MUST flag sequences where perspective distortion exceeds solvable thresholds (See US-2).
- **FR-008**: System MUST perform a 'Synthetic Control Validation' on a subset of the dataset where metric depth was randomized during generation. The solver MUST attempt to recover these randomized depths; failure to recover them (error > 50%) validates that the grid representation discards metric information (See US-3).

### Key Entities

- **GridFrame**: A video frame from the OmniDirector dataset containing the "empty" camera grid representation, with attributes for image data and associated frame index.
- **CameraPose**: Ground-truth camera parameters ($R_i, t_i$) for each frame, representing the original camera trajectory used to generate the grid.
- **ReconstructedBox**: The estimated 3D bounding box dimensions (height, width, depth) derived from the perspective inversion solver.
- **ComplexityMetric**: A quantitative measure of camera motion complexity (e.g., orbital vs. linear) used for correlation analysis.
- **WorldGridModel**: A canonical unit square grid defined at Z=0 in the world frame, used as the 3D reference for solvePnP to recover camera pose from 2D projections.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reconstruction error (absolute difference between estimated and ground-truth dimensions) is measured against the camera trajectory metadata (See US-3). For the Synthetic Control subset, error is measured against the randomized depth values.
- **SC-002**: Pearson correlation coefficient (r) between camera motion complexity and reconstruction accuracy is measured against the hypothesis that complexity correlates with accuracy (See US-3).
- **SC-003**: Validated aspect ratios of reconstructed scenes are measured against the known aspect ratios of the synthetic room volumes used in the original dataset generation (See US-3).
- **SC-004**: Dataset filtering success rate (percentage of sequences with defined spatial volumes retained) is measured against the total number of sequences in the raw OmniDirector dataset (See US-1).
- **SC-005**: Total execution time for the full curated dataset is measured against the total compute budget constraint for the free-tier CI runner. (See US-2).

## Assumptions

- The OmniDirector dataset repository provides access to million-scale camera grid-video pairs and associated ground-truth camera parameters ($R_i, t_i$) in a format compatible with OpenCV processing.
- The "empty" camera grid representation contains sufficient perspective cues to theoretically encode underlying 3D camera trajectories, even if metric depth information is partially discarded.
- The CPU-based geometric solver (using OpenCV `solvePnP` or least-squares) is computationally feasible within the 6-hour total compute budget and ~7 GB RAM constraint of the free-tier CI runner.
- The ground-truth scene box derived from original camera trajectories is a valid reference for evaluating reconstruction error, **acknowledging that this reference is dependent on the solver's inputs** (the grid frames were generated from these trajectories). This validation tests the solver's ability to re-derive the generation parameters, not to measure independent physical reality.
- The synthetic room volumes used in the original dataset generation have known, verifiable aspect ratios that serve as an independent validation target.
- The OmniDirector dataset does not contain explicit metadata defining "spatial volumes" (e.g., dolly-ins vs. orbits) per sequence. Spatial volume classification is inferred from camera trajectory patterns using the heuristic defined in FR-001 (radial > 15°, Z-velocity > 0.1).