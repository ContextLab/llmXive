# Feature Specification: AnyFlow Reproduction & Validation

**Feature Branch**: `001-anyflow-reproduction-validation`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation"

## User Scenarios & Testing

### User Story 1 - Environment Initialization & Dependency Resolution (Priority: P1)

The researcher MUST be able to initialize a clean Python environment, install all required dependencies from the vendored `AnyFlow` repository, and verify that the entry scripts (`far/main.py`, `demo.py`) can be imported without errors.

**Why this priority**: Without a functional environment, no reproduction can occur. This is the foundational step that validates the codebase's portability to the CI runner.

**Independent Test**: Can be fully tested by executing the dependency installation script and attempting to import the main modules in a fresh Python interpreter, returning exit code 0.

**Acceptance Scenarios**:
1. **Given** a clean GitHub Actions runner environment, **When** the user executes the dependency installation command defined in `requirements.txt`, **Then** all packages install successfully without version conflicts or CUDA-specific errors.
2. **Given** the dependencies are installed, **When** the user runs `python -c "import far.main"`, **Then** the import completes successfully without raising `ImportError` or `ModuleNotFoundError`.

---

### User Story 2 - Minimal Inference Execution (Priority: P1)

The researcher MUST be able to run the `demo.py` script or a minimal inference configuration to generate a single short video artifact using a small, CPU-tractable model variant (e.g., 1.3B parameters if available, or a heavily subsampled configuration) without requiring GPU acceleration.

**Why this priority**: This validates that the core "AnyFlow" logic (flow map transitions) executes end-to-end and produces real artifacts, which is the primary definition of "done" for a reproduction project.

**Independent Test**: Can be fully tested by executing the demo script with a dummy prompt and a small model checkpoint, verifying that a valid video file is written to the output directory.

**Acceptance Scenarios**:
1. **Given** the environment is initialized and a small model checkpoint is available, **When** the user runs `python demo.py --prompt "a cat" --steps 4 --model small`, **Then** the script completes within 60 minutes and outputs a video file (`.mp4`) that is not empty and has a valid header.
2. **Given** the inference is running, **When** the process is monitored, **Then** the process utilizes CPU resources only and does not attempt to allocate CUDA memory.

---

### User Story 3 - Quantitative Validation Report Generation (Priority: P2)

The researcher MUST be able to execute the evaluation pipeline against the generated artifacts and produce a JSON/Markdown report comparing the AnyFlow results against the paper's claimed metrics (e.g., VBench scores) for the specific model size used.

**Why this priority**: Reproduction is not just about running code; it requires validating the claims. This story ensures the output includes the necessary data to confirm if the method works as described.

**Independent Test**: Can be fully tested by running the evaluation script on the artifacts from US-02 and verifying a report file is generated containing numeric scores.

**Acceptance Scenarios**:
1. **Given** a generated video artifact, **When** the user runs `python far/main.py --mode eval --config options/test/anyflow/test_AnyFlow-Wan2.1-T2V-1.3B-Diffusers.yml`, **Then** the script completes and writes a `results.json` file containing at least one VBench metric.
2. **Given** the results file, **When** the researcher reviews it, **Then** the file contains a clear comparison between the AnyFlow output and the baseline (if applicable) or the paper's reported numbers.

---

### Edge Cases

- **What happens when the model checkpoint is missing?** The system MUST fail gracefully with a clear error message indicating the missing file path, rather than crashing with a generic stack trace.
- **How does the system handle insufficient RAM (OOM)?** If the dataset or model exceeds the 7GB RAM limit, the system MUST terminate with an explicit "Out of Memory" error and a suggestion to reduce the batch size or use a smaller model, rather than hanging indefinitely.
- **What happens when the video generation produces a black/empty frame?** The validation logic MUST detect empty or constant-frame videos and flag them as "Invalid Artifact" rather than counting them as a successful generation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `far/main.py` entry point using only CPU resources, explicitly disabling any CUDA/GPU device allocation to satisfy the free-tier CI constraint (See US-02).
- **FR-002**: System MUST load and run the 1.3B parameter model variant (or the smallest available variant in `options/test`) to ensure the computation fits within the 6-hour job limit and 7GB RAM constraint (See US-02).
- **FR-003**: System MUST generate at least one valid `.mp4` video file of length ≥ 1 second using the `demo.py` script with a dummy text prompt (See US-02).
- **FR-004**: System MUST execute the VBench evaluation metrics on the generated video and output a structured report (JSON or CSV) containing the calculated scores (See US-03).
- **FR-005**: System MUST validate that the generated video is not empty (non-zero file size) and contains at least 10 frames before including it in the final report (See US-02).

### Key Entities

- **ModelCheckpoint**: The pre-trained weights for the AnyFlow/Wan2.1 architecture (1.3B or 14B variant), stored as a `.pth` or `.safetensors` file.
- **GeneratedVideo**: The output artifact (`.mp4`) produced by the diffusion model, representing the visual realization of the text prompt.
- **EvaluationReport**: A structured data object containing the VBench scores (e.g., aesthetic quality, motion smoothness) and a pass/fail status relative to paper claims.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Video generation success rate is measured against the requirement to produce a non-empty, valid `.mp4` file (See FR-003, US-02).
- **SC-002**: Computational resource usage is measured against the constraint of ≤ 7 GB RAM and ≤ 6 hours total runtime on a 2-core CPU runner (See FR-002, US-02).
- **SC-003**: Evaluation completeness is measured against the presence of at least one VBench metric in the final output report (See FR-004, US-03).
- **SC-004**: Reproduction fidelity is measured by comparing the generated VBench scores against the baseline values reported in the AnyFlow paper (See US-03).
- **SC-005**: Environment portability is measured by the ability to install all dependencies from `requirements.txt` without manual intervention or CUDA-specific errors (See FR-001, US-01).

## Assumptions

- **Assumption about compute constraints**: The model with a moderate parameter count (or a heavily quantized/sampled version of the 14B model) is sufficient to generate a valid video within the 6-hour CI time limit and 7GB RAM constraint without GPU acceleration. If the 1.3B model is unavailable, the project scope is limited to the smallest available variant.
- **Assumption about data availability**: The `demo.py` script and `options/test` configurations rely on local or public model checkpoints that can be downloaded within the CI time limit; if a private checkpoint is required, the project will fail until access is granted.
- **Assumption about dataset-variable fit**: The VBench evaluation suite is fully compatible with the generated video format (resolution, frame rate) produced by the AnyFlow model on the CI runner.
- **Assumption about inference framing**: Since this is a reproduction of an existing model, the "results" are deterministic given the same seed and weights; no statistical power analysis is required for the inference step itself, only for the validation of the paper's claims.
- **Assumption about threshold justification**: The "validity" of a generated video (non-empty, >10 frames) uses a fixed, community-standard threshold for video files; no sensitivity analysis is required for this binary pass/fail metric.
