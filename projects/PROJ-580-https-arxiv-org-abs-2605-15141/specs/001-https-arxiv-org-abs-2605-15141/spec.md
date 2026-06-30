# Feature Specification: Causal Forcing++ Reproduction & Validation

**Feature Branch**: `580-reproduce-causal-forcing-validation`  
**Created**: 2025-05-23  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation. The implementation is vendored at external/Causal-Forcing. Task is to run, validate, and reproduce end-to-end."

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1)

**User Journey**: The researcher clones the repository, initializes the git submodule containing the `Causal-Forcing` code, and installs all Python dependencies required to run the inference and training scripts without import errors.

**Why this priority**: Without a functional environment, no code can be executed. This is the foundational step for all subsequent validation.

**Independent Test**: Successfully execute `python -c "import wan; import model; import pipeline"` within the project virtual environment without raising `ModuleNotFoundError` or `ImportError`.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner environment (Ubuntu, Python 3.10), **When** the user runs the submodule initialization and `pip install -r requirements.txt`, **Then** the installation completes with exit code 0 and no unresolved dependency conflicts.
2. **Given** the installed environment, **When** the user attempts to import the core `wan` and `model` modules, **Then** the imports succeed and the `wan` version matches the commit hash specified in the submodule.

---

### User Story 2 - Lightweight Inference Execution (Priority: P1)

**User Journey**: The researcher executes the `demo.py` or `inference.py` script using a minimal configuration (e.g., a small model variant like `wan_t2v_1_3B` or a pre-trained checkpoint if available, or a dummy initialization if weights are missing) to verify the pipeline logic runs end-to-end and produces a video artifact.

**Why this priority**: This validates the core "forward pass" logic of the Causal Forcing++ pipeline without requiring the full training cycle or massive GPU resources. It confirms the code structure is intact.

**Independent Test**: Run the inference script with `--num_steps 2` and `--frames 16` (or similar low-resource config) and verify a `.mp4` or `.gif` file is generated in the output directory.

**Acceptance Scenarios**:

1. **Given** the environment is ready and a valid configuration file (e.g., `configs/ar_diffusion_tf_framewise.yaml`) is selected, **When** the user runs `python demo.py --config configs/ar_diffusion_tf_framewise.yaml --num_steps 2 --batch_size 1`, **Then** the script completes within 15 minutes and outputs a video file > 1KB.
2. **Given** the script execution, **When** the process terminates, **Then** the logs must contain "Inference complete" and no `CUDA out of memory` errors (assuming CPU-only fallback or small model usage).

---

### User Story 3 - Training Step Validation (Priority: P2)

**User Journey**: The researcher initiates a single step or epoch of the `train.py` script (specifically the `causal_cd` or `dmd` distillation phase) using a synthetic or tiny subset of data to verify the loss calculation, gradient flow, and checkpoint saving mechanisms function correctly.

**Why this priority**: While full training is not feasible on free CI, verifying the *mechanism* of the training loop (loss computation, backprop, saving) is essential to validate the implementation matches the paper's algorithmic claims.

**Independent Test**: Execute `train.py` with `--max_steps 5` and `--batch_size 1` using a dummy dataset loader, and confirm a checkpoint file (`.pt` or `.pth`) is written with valid tensor shapes.

**Acceptance Scenarios**:

1. **Given** a minimal configuration for training (e.g., `configs/causal_cd_framewise.yaml`), **When** the user runs `python train.py --config configs/causal_cd_framewise.yaml --max_steps 5 --batch_size 1`, **Then** the script outputs 5 loss values and exits with code 0.
2. **Given** the training run, **When** the script finishes, **Then** a checkpoint file exists in `outputs/` with a file size > 100KB and contains valid PyTorch state dictionaries.

---

### Edge Cases

- **What happens when CUDA is unavailable?** The system MUST automatically fall back to CPU execution or raise a clear, actionable error message indicating GPU is required for the specific model size, preventing silent failures.
- **How does the system handle missing pre-trained weights?** If the required teacher/student checkpoints are not present in `external/Causal-Forcing/checkpoints`, the system MUST fail fast with a specific error listing the missing file paths, rather than attempting to generate random weights and producing invalid artifacts.
- **What happens if the video generation exceeds memory limits?** The system MUST detect OOM conditions early and either reduce the batch size automatically (if configured) or abort with a "Memory Limit Exceeded" status, logging the peak memory usage.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST initialize the `Causal-Forcing` git submodule and verify the commit hash matches the expected upstream commit. (See US-1)
- **FR-002**: The system MUST resolve all Python dependencies listed in `requirements.txt` and `long_video/requirements.txt` without conflicts. (See US-1)
- **FR-003**: The system MUST execute the inference pipeline (`demo.py` or `inference.py`) using the `wan_t2v_1_3B` configuration (or equivalent smallest available model) to generate a video artifact. (See US-2)
- **FR-004**: The system MUST execute a single training step of the `causal_cd` or `dmd` distillation pipeline to verify loss computation and checkpoint saving. (See US-3)
- **FR-005**: The system MUST output a validation report summarizing the success of the inference run, the generated artifact path, and the training step metrics. (See US-2, US-3)

### Key Entities

- **Artifact**: The generated video file (`.mp4` or `.gif`) produced by the inference pipeline.
- **Checkpoint**: The serialized model state (`.pt`/`.pth`) produced by the training step.
- **Configuration**: The YAML file defining the model architecture, sampling steps, and hyperparameters (e.g., `configs/ar_diffusion_tf_framewise.yaml`).

## Success Criteria

- **SC-001**: Inference artifact generation success rate is measured against the requirement that a video file > 1KB is produced within 15 minutes on a standard runner. (See US-2)
- **SC-002**: Training step completion rate is measured against the requirement that 5 training steps complete without OOM errors and produce a valid checkpoint. (See US-3)
- **SC-003**: Dependency resolution success is measured against the requirement that `pip install` completes with exit code 0 and no unresolved conflicts. (See US-1)
- **SC-004**: Code execution validity is measured against the requirement that no `ImportError` or `AttributeError` occurs during the import of `wan`, `model`, and `pipeline` modules. (See US-1)
- **SC-005**: Resource compliance is measured against the requirement that the entire validation process (inference + training step) completes within the 6-hour CI job limit and uses < 7GB RAM. (See US-2, US-3)

## Assumptions

- **Assumption about Compute Resources**: The validation assumes the use of the `wan_t2v_1_3B` model variant or a similarly sized model that can fit into ~7GB RAM on a CPU-only runner. The `wan_t2v_14B` model is assumed to be out of scope for this specific CI validation due to memory constraints; the spec assumes the user will target the smaller variant for feasibility.
- **Assumption about Data Availability**: The validation assumes that no external dataset is required for the *inference* test (using built-in prompts) and that the *training* test uses a synthetic or tiny dummy dataset loader provided within the codebase to avoid downloading gigabytes of video data.
- **Assumption about GPU Dependency**: The spec assumes that if the codebase contains hardcoded CUDA checks that cannot be bypassed for the 1.3B model, the validation will fail gracefully with a clear error, or the code will be patched to allow CPU execution for the purpose of this specific "run and validate" check.
- **Assumption about Model Weights**: The spec assumes that the repository either includes a small pre-trained checkpoint for the 1.3B model or that the validation will proceed with "random initialization" mode (if supported) to test the pipeline logic without requiring the download of massive weights. If weights are mandatory and missing, the project will flag `[NEEDS CLARIFICATION: Are pre-trained weights for the 1.3B model included in the submodule?]`.
- **Assumption about Validation Scope**: The validation is assumed to confirm *code execution* and *artifact generation*, not the *scientific quality* (e.g., VBench scores) of the generated video, as the latter requires GPU resources and external evaluation models not present in the free CI environment.
