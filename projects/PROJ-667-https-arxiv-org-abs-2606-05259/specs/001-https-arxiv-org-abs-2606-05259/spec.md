# Feature Specification: Reproduce & Validate VideoKR

**Feature Branch**: `667-reproduce-validate-videokr`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1)

The system MUST successfully initialize a CPU-only runtime environment, install all dependencies listed in the vendored `VideoKR` repository (including `llamafactory` and `lmms_eval`), and verify that the core Python entry points are importable without GPU-specific errors.

**Why this priority**: Without a functioning environment, no code execution, data processing, or validation can occur. This is the foundational step for the entire reproduction effort.

**Independent Test**: A CI job can be triggered that installs dependencies and runs a "smoke test" script (e.g., `python -c "import llamafactory; print('Import OK')"`) and fails immediately if CUDA-specific libraries (like `bitsandbytes` or `flash-attn`) are required but not present or if imports fail.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner with 2 CPU cores and 7 GB RAM, **When** the dependency installation script runs, **Then** the process must complete within 30 minutes and report "0 errors" regarding missing packages, while explicitly avoiding installation of GPU-only binaries (e.g., `bitsandbytes` must be skipped or installed in CPU-compatible mode if available, otherwise the requirement is to note the skip).
2. **Given** the environment is initialized, **When** the script attempts to import `llamafactory.train.sft`, **Then** the import must succeed without raising `ImportError: CUDA` or `ImportError: torch.cuda` exceptions.

---

### User Story 2 - Data Preparation and Subsampling Execution (Priority: P2)

The system MUST execute the data preparation script (`prepare_videokr_sft_data.py`) to process a **subsampled** portion of the VideoKR dataset (e.g., 100 samples) into the format required by the training framework, confirming that the pipeline logic executes end-to-end without memory overflow.

**Why this priority**: The original dataset (a large-scale collection of examples) is too large for the free-tier CI runner (7 GB RAM). Validating the *logic* of the data pipeline on a small sample is the minimum viable proof that the code is runnable and the format is correct.

**Independent Test**: Run the data preparation script with a `--limit 100` flag (or equivalent) and verify that output files (JSONL/Parquet) are generated in the expected directory with valid schema.

**Acceptance Scenarios**:

1. **Given** the environment is ready and a small subset of raw data is available (or mocked), **When** the `prepare_videokr_sft_data.py` script runs with a limit of 100 examples, **Then** it must generate output files within 5 minutes and the output file size must be < 10 MB.
2. **Given** the output files are generated, **When** a schema validation script reads the first 5 lines, **Then** it must confirm the presence of required fields (e.g., `video_path`, `question`, `answer`, `rationale`) and report no parsing errors.

---

### User Story 3 - Validation Run on Small Model and Dataset (Priority: P3)

The system MUST execute a "dry-run" or "validation-only" training/evaluation pass using a small pre-trained model (e.g., Qwen2-VL-2B or smaller) on the subsampled dataset to confirm that the training loop initializes, processes at least one batch, and produces a log artifact without crashing.

**Why this priority**: This confirms the integration between the data loader, model loader, and training logic. It does not require full training to completion but proves the "run" aspect of the reproduction.

**Independent Test**: Execute the training script with `--num_train_epochs 0.001` (or `--max_steps 1`) and `--model_name_or_path` pointing to a small, CPU-compatible model, and verify that a log file is created containing at least one "Step X" entry.

**Acceptance Scenarios**:

1. **Given** the data is prepared and a small model is specified, **When** the training script runs with `--max_steps 1`, **Then** the process must complete within 20 minutes and exit with code 0.
2. **Given** the process completes, **When** the log file is inspected, **Then** it must contain a line indicating "Training started" and a line indicating "Step 1 completed" or "Validation completed".

---

### Edge Cases

- **What happens when** the dataset path is missing or the video files are inaccessible? The system must fail gracefully with a clear error message "Data path not found" rather than a generic stack trace, and the script must not hang.
- **How does system handle** GPU-only dependencies (e.g., `bitsandbytes`) being present in `requirements.txt`? The system must detect the lack of CUDA and either skip these dependencies or fail with a clear "GPU not available, skipping GPU-only libraries" message, ensuring the CI job does not crash.
- **What happens when** the subsampled data is still too large for 7 GB RAM? The system must fail with an "Out of Memory" error during the data loading phase, triggering a retry with a smaller limit (e.g., `--limit 10`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute the data preparation script on a subsampled dataset (limit ≤ 100 examples) to verify the data pipeline logic works without memory overflow (See US-1, US-2).
- **FR-002**: System MUST initialize the training/evaluation environment on a CPU-only runner, explicitly skipping or mocking GPU-specific libraries (e.g., `bitsandbytes`, `flash-attn`) to prevent import errors (See US-1).
- **FR-003**: System MUST execute a training or evaluation loop for at least one step (or one batch) using a small, CPU-compatible model to verify the integration of data loader, model, and trainer (See US-3).
- **FR-004**: System MUST generate and persist a log artifact (e.g., `train.log` or `eval.log`) containing the output of the validation run to serve as proof of execution (See US-3).
- **FR-005**: System MUST report the execution status (Success/Failure) and any encountered errors in a structured format (e.g., a summary JSON or a final log message) for the reproduction report (See US-1, US-2, US-3).

### Key Entities

- **Subsampled Dataset**: A reduced version of the VideoKR training data (≤ 100 examples) used for validation.
- **Validation Log**: The artifact produced by the training/evaluation run, containing timestamps, step counts, and error messages.
- **CPU-Compatible Model**: A small vision-language model (e.g., Qwen2-VL-2B) that can be loaded and run on 7 GB RAM without GPU.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data preparation success is measured against the generation of a valid JSONL/Parquet file with the expected schema (See US-2).
- **SC-002**: Environment initialization success is measured against the absence of CUDA-related import errors in the CI log (See US-1).
- **SC-003**: Training loop validation success is measured against the presence of at least one "Step completed" entry in the log file within the 6-hour CI limit (See US-3).
- **SC-004**: Reproducibility report completeness is measured against the inclusion of the execution log, environment details, and a pass/fail status (See US-1, US-2, US-3).

## Assumptions

- **Assumption about data**: The raw VideoKR dataset is accessible via the vendored submodule, but a full download is not performed; instead, a small, representative subset (or mocked data) is used for validation to fit within the 7 GB RAM constraint.
- **Assumption about scope boundaries**: Full training to convergence and evaluation on the full VideoKR-Eval benchmark are out of scope for this feature; the scope is limited to verifying the code runs end-to-end on a minimal scale.
- **Assumption about target users**: The "user" is the CI system and the researcher validating the codebase, not an end-user of the video understanding model.
- **Assumption about hardware**: The GitHub Actions free-tier runner (limited CPU, 7 GB RAM) is the only available compute resource; no GPU, TPU, or external cloud resources are available.
- **Assumption about dependencies**: The `llamafactory` and `lmms_eval` libraries have CPU-compatible modes or can be configured to skip GPU-specific dependencies without breaking the core data processing logic.
