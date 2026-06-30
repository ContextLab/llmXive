# Feature Specification: Reproduce & Validate Geometry-Aware Representation Denoising (GARD)

**Feature Branch**: `001-reproduce-gard`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction (Paper: https://arxiv.org/abs/). Code vendored at `projects/PROJ-632-https-arxiv-org-abs-2605-26230/external/GARD/`."

## User Scenarios & Testing

### User Story 1 - Execute GARD Inference Pipeline (Priority: P1)

**User Journey**: A researcher downloads the vendored GARD code, configures the environment, and executes the primary inference script to process a sample multi-view dataset, generating 3D reconstruction artifacts and restored RGB images without manual intervention.

**Why this priority**: This is the core value proposition. If the code cannot run end-to-end, the reproduction effort fails immediately. All other validation steps depend on successful execution.

**Independent Test**: The CI job runs the entry script with a minimal sample dataset; the job exits with code 0 and produces specific output files (`.ply` or `.obj` for geometry, `.png` for restored images) in the designated output directory.

**Acceptance Scenarios**:
1. **Given** the GARD submodule is cloned and dependencies are installed, **When** the user executes the standard inference command defined in `README.md`, **Then** the process completes successfully within 6 hours on a CPU-only runner and generates output files in `outputs/`.
2. **Given** the input dataset contains degraded (noisy) multi-view images, **When** the GARD pipeline processes them, **Then** the system outputs reconstructed 3D geometry files (e.g., `.ply`) and restored RGB images without raising runtime exceptions.

### User Story 2 - Validate Output Artifacts Against Paper Claims (Priority: P2)

**User Journey**: A researcher inspects the generated artifacts to confirm they align with the qualitative claims in the paper (e.g., visible noise reduction in restored images, plausible geometry reconstruction) and verifies the file formats are standard and readable.

**Why this priority**: Running the code is insufficient; the outputs must be meaningful. This step validates that the model is actually performing the denoising and reconstruction tasks described, not just crashing or producing empty files.

**Independent Test**: Automated or manual inspection confirms that restored images have higher visual fidelity than inputs and that 3D geometry files are non-empty and loadable in standard viewers (e.g., MeshLab, CloudCompare).

**Acceptance Scenarios**:
1. **Given** the pipeline has generated restored RGB images, **When** a script compares the pixel variance or edge density of restored vs. input images, **Then** the restored images show measurable structural differences consistent with denoising (e.g., reduced high-frequency noise artifacts).
2. **Given** the pipeline has generated 3D geometry files, **When** a standard 3D viewer attempts to load the `.ply` or `.obj` file, **Then** the viewer renders a coherent scene structure without geometry corruption or file parsing errors.

### User Story 3 - Document Reproduction Fidelity (Priority: P3)

**User Journey**: The researcher generates a final report summarizing the reproduction status, noting any deviations from the paper's original experimental setup (e.g., dataset differences, hardware constraints) and confirming whether the qualitative results match the paper's figures.

**Why this priority**: This provides the final "truth" for the project. It contextualizes the results, acknowledging limitations (like CPU-only execution) while confirming the core method works.

**Independent Test**: A `reproduction_report.md` is generated in the project root, explicitly stating "Success" or "Partial Success" with specific references to the artifacts produced and any observed deviations.

**Acceptance Scenarios**:
1. **Given** the pipeline has completed and artifacts exist, **When** the `reproduction_report.md` is generated, **Then** it contains a direct comparison section linking the generated artifacts to the specific figures/claims in the source paper (arXiv:2605.26230).
2. **Given** the execution was performed on a CPU-only environment, **When** the report is finalized, **Then** it explicitly documents this constraint and notes any performance degradation or methodological adaptations required to fit the compute limits.

### Edge Cases

- **Missing Dataset**: What happens if the required DA3 (Depth Anything 3) benchmark data or the specific degraded test set is not present in the expected directory? The system MUST fail gracefully with a clear error message directing the user to download the dataset, rather than crashing with a generic "file not found" stack trace.
- **GPU Dependency**: What happens if the vendored code inadvertently contains hardcoded CUDA calls or `load_in_8bit`? The system MUST detect this during the environment check and abort with a specific error indicating GPU/CUDA is required, preventing a silent failure or hanging process.
- **Memory Overflow**: What happens if the input resolution exceeds the memory limit of the runner? The system MUST either process the images in smaller batches or fail with a clear "Out of Memory" diagnostic, rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST successfully execute the GARD inference entry point (as defined in `README.md`) on a CPU-only environment without requiring CUDA or GPU hardware. (See US-1)
- **FR-002**: System MUST generate valid 3D geometry files (e.g., `.ply`, `.obj`) and restored RGB image files (e.g., `.png`, `.jpg`) in the designated output directory upon successful completion. (See US-1, US-2)
- **FR-003**: System MUST handle missing input datasets by terminating with a descriptive error message that explicitly lists the required dataset name and expected path, rather than failing with a generic traceback. (See US-1)
- **FR-004**: System MUST complete the full inference pipeline on the sample dataset within 6 hours of wall-clock time on a standard 2-core CPU runner. (See US-1, US-3)
- **FR-005**: System MUST produce output artifacts that are non-empty and loadable by standard open-source tools (e.g., MeshLab for geometry, standard image viewers for RGB). (See US-2)

### Key Entities

- **Input Dataset**: Multi-view images with simulated or real degradation (noise, blur), conforming to the DA3 benchmark format.
- **Restored Geometry**: 3D point cloud or mesh representing the scene structure, recovered from degraded inputs.
- **Restored Image**: High-fidelity RGB image output, denoised and corrected by the GARD framework.
- **Reproduction Report**: A markdown document summarizing the execution status, artifacts, and fidelity to the original paper.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The inference pipeline MUST complete with a zero exit code and produce at least one valid 3D geometry file and one valid restored image file within 6 hours. (See FR-001, FR-002, FR-004) (See US-1)
- **SC-002**: The generated 3D geometry files MUST be loadable in MeshLab without errors, and the restored images MUST be viewable in standard image viewers without corruption. (See FR-005) (See US-2)
- **SC-003**: The `reproduction_report.md` MUST explicitly confirm whether the qualitative results (noise reduction, geometry fidelity) match the claims in the source paper, citing specific generated artifacts as evidence. (See FR-004) (See US-3)
- **SC-004**: If the code attempts to access GPU resources, the execution MUST fail immediately with a clear error message indicating "GPU/CUDA not available" rather than proceeding to a silent crash. (See FR-001) (See US-1)
- **SC-005**: The system MUST process the sample dataset within the available memory constraints, evidenced by the absence of OOM (Out of Memory) errors during execution. (See FR-004) (See US-1)

## Assumptions

- The vendored `external/GARD` repository contains a valid, runnable `README.md` with explicit instructions for the inference command and required dependencies.
- The DA3 (Depth Anything 3) benchmark dataset or a compatible sample degraded dataset is available and can be mounted to the runner at a known path (e.g., `data/da3_sample`).
- The GARD model weights are either included in the submodule or can be downloaded automatically by the provided scripts without requiring manual intervention.
- The "degraded" nature of the input images is provided as part of the sample dataset; the system does not need to synthesize noise but rather process existing noisy inputs.
- The 3D reconstruction model used by GARD is compatible with CPU execution (i.e., does not strictly require a specific GPU architecture for inference, only that it fits in RAM).
- The `Depth Anything 3` benchmark data is accessible via a standard URL or local path; if the paper requires a specific private dataset, a public substitute will be used for the reproduction attempt.
