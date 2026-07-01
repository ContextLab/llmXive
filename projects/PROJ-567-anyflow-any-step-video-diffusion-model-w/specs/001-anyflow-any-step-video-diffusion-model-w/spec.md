# Feature Specification: AnyFlow Reproduction & Validation

**Feature Branch**: `001-anyflow-reproduction-validation`  
**Created**: 2026-07-01  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distillation"

## User Scenarios & Testing

### User Story 1 - Environment Initialization & CPU-Only Constraint Enforcement (Priority: P1)

The researcher MUST be able to initialize a clean Python environment, install all required dependencies from the vendored `AnyFlow` repository, and explicitly enforce CPU-only execution (disabling CUDA/GPU) to ensure the pipeline runs within the free-tier CI constraints (2 cores, ~7 GB RAM).

**Why this priority**: This is the foundational prerequisite. Without a reproducible environment that strictly adheres to CPU constraints, no further validation can occur, and the project risks failing on hardware incompatibility (e.g., CUDA errors).

**Independent Test**: Can be fully tested by executing the dependency installation script and running a "dry-run" import of the inference pipeline with `device="cpu"` forced, verifying a successful exit code and absence of GPU-related errors.

**Acceptance Scenarios**:
1. **Given** a clean GitHub Actions runner environment, **When** the user executes `pip install -r requirements.txt` and sets `CUDA_VISIBLE_DEVICES=""`, **Then** all packages install successfully without version conflicts or CUDA-specific dependency errors.
2. **Given** the dependencies are installed, **When** the user runs `python -c "from far.models import WanModel; print('Import OK')"`, **Then** the import completes successfully without raising `ImportError` or attempting to allocate CUDA memory.

---

### User Story 2 - Minimal Inference Execution with Valid Artifact Generation (Priority: P1)

The researcher MUST be able to run the `demo.py` script or a minimal inference configuration to generate at least one valid `.mp` video artifact using the smallest available model variant (prioritizing 1.3B if present; otherwise, the 14B model with strict resolution/batch-size constraints) strictly on CPU.

**Why this priority**: This validates the core "AnyFlow" logic (flow map transitions) executes end-to-end and produces real artifacts, which is the primary definition of "done" for a reproduction project. It directly addresses the concern that the method cannot be run at the parameters required to produce results.

**Independent Test**: Can be fully tested by executing the inference script with a dummy prompt and a small model checkpoint, verifying that a valid video file is written to the output directory within the 6-hour job limit.

**Acceptance Scenarios**:
1. **Given** the environment is initialized and a model checkpoint is available, **When** the user runs `python far/main.py --config options/test/anyflow/test_AnyFlow-Wan2.1-T2V-1.3B-Diffusers.yml --device cpu --steps 4` (or the 14B fallback config), **Then** the script completes within 360 minutes and outputs a video file (`.mp4`) that is not empty (size > 100KB) and has a valid header.
2. **Given** the inference is running, **When** the process is monitored via system logs, **Then** the process utilizes CPU resources only and does not attempt to allocate CUDA memory or exceed 7 GB RAM.
3. **Given** the model selection logic, **When** the 1.3B config is missing from `options/test`, **Then** the system automatically falls back to the 14B model with `--resolution 256` and `--batch_size 1`, and logs a warning indicating the fallback.
4. **Given** the generated video, **When** the video is inspected, **Then** it contains ≥ 8 frames (≥ 1 second at 8 fps) to satisfy the minimum generation requirement.

---

### User Story 3 - CPU-Tractable Quality Validation & Report Generation (Priority: P2)

The researcher MUST be able to execute a validation pipeline that computes a specific, CPU-tractable subset of quality metrics (SSIM, Optical Flow, and Frame Count) on the generated artifacts and produces a structured `results.json` report conforming to the project's evaluation contract schema.

**Why this priority**: Reproduction requires validating claims. Since full VBench (requiring I3D/GPU) is infeasible, this story ensures the output includes a scientifically valid, CPU-tractable approximation of video quality (motion smoothness and structural integrity) to assess the method's behavior, rather than a generic "pass/fail."

**Independent Test**: Can be fully tested by running the validation script on the artifacts from US-02 and verifying a `results.json` file is generated containing numeric scores for SSIM, Optical Flow, and Frame Count, matching the `contracts/evaluation_report.schema.yaml`.

**Acceptance Scenarios**:
1. **Given** a generated video artifact, **When** the user runs `python src/anyflow/validation.py --input outputs/video.mp4 --schema contracts/evaluation_report.schema.yaml`, **Then** the script completes and writes a `results.json` file containing at least the metrics: `ssim_score`, `optical_flow_magnitude`, and `frame_count`.
2. **Given** the results file, **When** the researcher reviews it, **Then** the file structure strictly matches the `contracts/evaluation_report.schema.yaml` (including `status`, `metrics`, and `metadata` fields) and contains no `null` values for the primary metrics.
3. **Given** the metadata fields, **When** the report is generated, **Then** it explicitly records the `model_variant`, `resolution`, and `step_count` used for generation.

---

### Edge Cases

- **What happens when the model checkpoint is missing?** The system MUST fail gracefully with a clear error message indicating the missing file path and a specific instruction to download the `AnyFlow` weights from the provided HuggingFace/ModelScope URL, rather than crashing with a generic stack trace.
- **How does the system handle insufficient RAM (OOM)?** If the dataset or model exceeds the available RAM limit, the system MUST terminate with an explicit "Out of Memory" error and a suggestion to reduce the batch size or use a lower resolution configuration, rather than hanging indefinitely.
- **What happens when the video generation produces a black/empty frame?** The validation logic MUST detect empty or constant-frame videos (e.g., average standard deviation of pixel values across ALL frames < 5) and flag them as "Invalid Artifact" in the report, rather than counting them as a successful generation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `far/main.py` entry point using only CPU resources, explicitly disabling any CUDA/GPU device allocation via environment variables or configuration flags to satisfy the free-tier CI constraint (See US-01).
- **FR-002**: System MUST load and run the smallest available model variant (prioritizing the smallest parameter count if present in `options/test`; otherwise, the 14B model with `--resolution 256` and `--batch_size 1`) to ensure the computation fits within the job time limit and memory constraint (See US-02).
- **FR-003**: System MUST generate at least one valid `.mp4` video file of length ≥ 1 second (≥ 8 frames at 8 fps) using the inference script with a dummy text prompt (See US-02).
- **FR-004**: System MUST compute a CPU-tractable subset of quality metrics on the generated video:
    - **SSIM**: Computed using `skimage.metrics.structural_similarity` on grayscale frames with default parameters.
    - **Optical Flow**: Computed using `cv2.calcOpticalFlowFarneback` with default parameters, reporting the mean magnitude of flow vectors across all frames.
    - **Frame Count**: Total number of frames in the video.
    The system MUST output a structured report (JSON) containing these calculated scores (See US-03).
- **FR-005**: System MUST validate that the generated video is not empty (non-zero file size) and contains at least 10 frames before including it in the final report. If the video has < 10 frames, the report status MUST be "Invalid Artifact" (See US-02).
- **FR-006**: System MUST validate the output `results.json` against `contracts/evaluation_report.schema.yaml` before considering the validation step complete (See US-03).
- **FR-007**: System MUST explicitly record the model variant, resolution, and step count used for generation in the `results.json` metadata to enable traceability (See US-03).
- **FR-008**: System MUST verify that the `far/pipelines/pipeline_wan_anyflow.py` logic path is executed without modification by comparing the upstream commit hash used for the reproduction against the repository's main branch (See US-02).
- **FR-009**: System MUST log the specific upstream commit hash of the `AnyFlow` repository used for the reproduction in the `results.json` metadata (See US-02).
- **FR-010**: System MUST perform a sensitivity analysis by running the inference at multiple distinct step counts (e.g., varying from coarse to fine granularity) and reporting the trend of SSIM and Optical Flow metrics to validate internal consistency (See US-03).

### Key Entities

- **ModelCheckpoint**: The pre-trained weights for the AnyFlow/Wan2.1 architecture. Primary source: HuggingFace `Wan-AI/Wan-T2V-14B` (https://huggingface.co/Wan-AI/Wan2.1-T2V-14B). Fallback source: AnyFlow adapter weights (https://huggingface.co/AnyFlow/AnyFlow-Wan2.1). The smallest available variant is the primary target; otherwise, a larger model with reduced resolution is used.
- **GeneratedVideo**: The output artifact (`.mp4`) produced by the diffusion model, representing the visual realization of the text prompt.
- **EvaluationReport**: A structured data object containing the CPU-tractable metrics (SSIM, Optical Flow, Frame Count) and a pass/fail status relative to the evaluation contract.

### Contracts

The `contracts/evaluation_report.schema.yaml` file defines the required structure for the `results.json` output. The `validation.py` implementation MUST validate its output against this specific file before completion.

```yaml
type: object
required:
  - status
  - metrics
  - metadata
properties:
  status:
    type: string
    enum: ["Valid", "Invalid Artifact", "Error"]
  metrics:
    type: object
    required:
      - ssim_score
      - optical_flow_magnitude
      - frame_count
    properties:
      ssim_score:
        type: number
      optical_flow_magnitude:
        type: number
      frame_count:
        type: integer
  metadata:
    type: object
    required:
      - model_variant
      - resolution
      - step_count
      - upstream_commit_hash
    properties:
      model_variant:
        type: string
      resolution:
        type: string
      step_count:
        type: integer
      upstream_commit_hash:
        type: string
```

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Video generation success is measured as a binary pass/fail: a valid `.mp4` file with ≥ 8 frames is produced (See FR-003, US-02).
- **SC-002**: Computational resource usage is measured against the constraint of ≤ 7 GB RAM and ≤ 6 hours total runtime on a 2-core CPU runner (See FR-002, US-02).
- **SC-003**: Evaluation completeness is measured against the presence of SSIM, Optical Flow, and Frame Count metrics in the final output report (See FR-004, US-03).
- **SC-004**: Schema compliance is measured by the successful validation of `results.json` against `contracts/evaluation_report.schema.yaml` (See FR-006, US-03).
- **SC-005**: Environment portability is measured by the ability to install all dependencies from `requirements.txt` without manual intervention or CUDA-specific errors (See FR-001, US-01).
- **SC-006**: Method logic fidelity is measured by the successful execution of the "on-policy flow map" logic path in `far/pipelines/pipeline_wan_anyflow.py` without modification, confirmed by matching the upstream commit hash (See FR-008, FR-009, US-02).
- **SC-007**: Reproduction fidelity is measured against **internal consistency** (trend of metrics across step counts) and **artifact validity**. Absolute metric values are NOT compared to paper baselines due to architectural mismatch (model scale/resolution) (See FR-010, US-03).
- **SC-008**: Success Rate is measured only if multiple runs are executed (out of scope for v1). For v1, success is binary (See SC-001).

## Constitution Compliance

This project explicitly adheres to the following constitutional principles:
- **Principle I (SSoT)**: The `contracts/evaluation_report.schema.yaml` serves as the Single Source of Truth for output validation (See FR-006).
- **Principle V (Real-Call Testing)**: The CPU-only constraint and model fallback logic (FR-002) are validated by real execution on CI runners, ensuring the method is feasible without GPU acceleration.
- **Principle III (Feasibility)**: The redefinition of success to "feasibility reproduction" (valid artifact + logic fidelity) rather than "full fidelity reproduction" (matching paper baselines) satisfies the constraint that the project must be executable within available resources.

## Assumptions

- **Assumption about model availability**: The `AnyFlow` repository MAY contain a configuration for a large-scale parameter model. If the 1.3B config is missing from `options/test`, the system will automatically fall back to the 14B model with `--resolution 256` and `--batch_size 1`. This fallback is explicitly acknowledged as a "feasibility reproduction" of the *method* (flow map logic) rather than a "full fidelity reproduction" of the paper's 14B model performance.
- **Assumption about metric validity**: The CPU-tractable metrics (SSIM, Optical Flow) provide a sufficient approximation of video quality for the purpose of validating the "any-step" behavior (smoothness and structural consistency) in the absence of full VBench/I3D, which requires GPU acceleration. This is supported by common practice in CPU-tractable video validation literature where SSIM and Optical Flow are standard proxies for structural integrity and motion smoothness.
- **Assumption about inference framing**: Since this is a reproduction of an existing model, the "results" are deterministic given the same seed and weights; no statistical power analysis is required for the inference step itself, only for the validation of the paper's claims regarding step-scaling.
- **Assumption about threshold justification**: The "validity" of a generated video (non-empty, >10 frames) uses a fixed, community-standard threshold for video files; no sensitivity analysis is required for this binary pass/fail metric.
- **Assumption about data-source fit**: The `demo.py` script and `options/test` configurations rely on local or public model checkpoints that can be downloaded within the CI time limit. Specific sources: HuggingFace `Wan-AI/Wan2.1-T2V-14B` and `AnyFlow/AnyFlow-Wan2.1`.
- **Assumption about compute constraints**: The model with a moderate parameter count (or a heavily quantized/sampled version of the large-scale model) is sufficient to generate a valid video within the 6-hour CI time limit and 7GB RAM constraint. without GPU acceleration.
- **Assumption about Scope Boundary**: This project explicitly redefines the research question to "Validate the feasibility and logic fidelity of AnyFlow on CPU" due to hardware constraints. It does not aim to reproduce the full step-scaling curve or absolute performance metrics of the paper, as those require GPU and full model scale. This scope boundary is justified by the Constitution's requirement for feasibility.
- **Assumption about Baseline Comparison**: Absolute metric values (e.g., specific SSIM scores) are NOT compared to paper baselines because the paper's baselines are derived from the 14B model at high resolution, while this project may run the 14B model at reduced resolution or a 1.3B model. Comparing these would be a category error. Success is defined by internal consistency (trends) and artifact validity.