# Feature Specification: MMSkills Reproduction & Validation

**Feature Branch**: `001-mmskills-reproduction`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: MMSkills: Towards Multimodal Skills for General Visual Agents"

## User Scenarios & Testing

### User Story 1 - Environment Setup & CPU-Only Execution (Priority: P1)

As a researcher, I want to install the MMSkills dependencies and execute the provided entry point scripts in a CPU-only environment so that the baseline code runs without hardware-specific errors (e.g., CUDA mismatch) and produces initial output artifacts.

**Why this priority**: This is the foundational step. If the code cannot execute in the specified CI environment (CPU-only, constrained memory), no further validation or reproduction is possible. It verifies the "compute feasibility" constraint explicitly required by the project stage.

**Independent Test**: Run the installation and execution scripts in a clean virtual environment; verify that the process exits with code 0 and generates at least one log file or result JSON in the designated output directory without importing CUDA libraries.

**Acceptance Scenarios**:
1. **Given** a clean virtual environment with Python 3.10+ and no GPU drivers, **When** the user runs `pip install -r requirements.txt` and the entry script `osworld_integration/run.py`, **Then** the process completes without GPU/CUDA import errors and generates a `results_log.json` or similar artifact.
2. **Given** the environment has no GPU drivers installed, **When** the script attempts to load the agent model, **Then** it defaults to CPU inference (or a CPU-tractable fallback) without crashing and logs "Device: cpu" in the execution trace.

---

### User Story 2 - Skill Loading & Structural Validation (Priority: P2)

As a validator, I want the system to successfully load a specific multimodal skill (e.g., `CHROME_Search_Web`) from the `skills_library` and have the agent execute the associated plan so that I can confirm the skill package structure (state cards, keyframes, images) is correctly interpreted and all file references are valid.

**Why this priority**: This validates the core "multimodal procedural knowledge" claim of the paper. It ensures the agent can actually consume the data structures (images, text plans) defined in the repository without runtime parsing errors.

**Independent Test**: Execute a single-task run using one of the provided Chrome or LibreOffice skills; verify that the agent reads the `plan.json` and associated `state_cards.json` without parsing errors and that all referenced image files exist.

**Acceptance Scenarios**:
1. **Given** the `skills_library/chrome/CHROME_Search_Web_And_Open_Target_Result` directory exists, **When** the agent resolver loads this skill, **Then** it successfully parses the `plan.json`, `state_cards.json`, and validates that all image paths in `IMAGE_REFERENCE_LIST.md` exist on the filesystem.
2. **Given** a loaded skill, **When** the agent attempts to execute the first step of the plan, **Then** it produces a structured action output (e.g., a JSON action object) that matches the expected schema defined in the agent adapter and logs the step execution.

---

### User Story 3 - Benchmark Subset Execution & Metrics Logging (Priority: P3)

As a researcher, I want to run the agent on a small, fixed subset of tasks (e.g., 5 tasks) from the OSWorld or gaming benchmarks and generate a structured metrics report so that I can validate the execution flow and prepare for comparison with the paper's reported numbers.

**Why this priority**: This moves beyond "code runs" to "results generation." It confirms the evaluation pipeline works end-to-end and produces the data artifacts necessary for the final scientific validation, while adhering to the 6-hour CI time limit.

**Independent Test**: Run the evaluation script on a small, fixed subset of tasks (e.g., `--num-tasks=5`) and generate a `metrics_summary.csv` containing success/failure counts and timestamps.

**Acceptance Scenarios**:
1. **Given** a subset of 5 tasks from the OSWorld benchmark, **When** the MMSkills agent executes them, **Then** the system produces a `metrics_summary.csv` containing `task_id`, `status` (success/fail/timeout), and `duration_seconds` for each task.
2. **Given** the `metrics_summary.csv`, **When** the user reviews the output, **Then** the file contains no empty rows and all task IDs match the requested subset.

### Edge Cases

- **Missing Image Assets**: What happens if an image file referenced in `IMAGE_REFERENCE_LIST.md` is missing or corrupted? The system must log a warning, record the specific skill step as "SKIPPED" or "ERROR" in the logs, and continue to the next step rather than crashing the entire run.
- **Timeout on Complex Tasks**: How does the system handle a task that exceeds the 6-hour CI job limit? The agent must implement a hard timeout of 1800 seconds (30 minutes) per task; if exceeded, the task is recorded as "TIMEOUT" in `metrics_summary.csv` and the agent proceeds to the next task.
- **Model Load Failure**: If the default multimodal model fails to load on CPU due to memory constraints (OOM), the system must gracefully fall back to a smaller, non-quantized CPU model (if available in `requirements`) or exit with a clear `OOM` error code and a stack trace, rather than hanging.
- **Submodule Corruption**: What happens if the git submodule `external/MMSkills` is incomplete? The system must detect missing files during the initial setup phase and exit with a specific error code `1` indicating "Submodule Integrity Check Failed."

## Requirements

### Functional Requirements

- **FR-001**: The system MUST install dependencies from `requirements.txt` without requiring CUDA-enabled libraries (e.g., `torch` with CUDA backend) to ensure CPU-only compatibility (See US-1).
- **FR-002**: The system MUST load skill packages from `skills_library` by parsing `plan.json`, `state_cards.json`, and `IMAGE_REFERENCE_LIST.md` and validating that all referenced image paths exist before execution begins (See US-2).
- **FR-003**: The agent MUST execute the first step of a loaded skill plan and output a structured action object (JSON) to standard output or a log file to confirm plan interpretation (See US-2).
- **FR-004**: The system MUST run the evaluation script on a configurable subset of tasks (e.g., `--num-tasks=5`) and generate a `metrics_summary.csv` with success/failure status per task (See US-3).
- **FR-005**: The system MUST implement a per-task timeout of 1800 seconds (30 minutes) to prevent individual tasks from hanging the CI job (See US-3).
- **FR-006**: The system MUST detect if a GPU is unavailable and explicitly force CPU inference mode for all model loads, logging the device type used (See US-1).
- **FR-007**: The system MUST handle missing image assets by logging a warning and marking the specific step as "ERROR" in the metrics log without terminating the entire job (See Edge Cases).

### Key Entities

- **Skill Package**: A directory containing `plan.json`, `state_cards.json`, `runtime_state_cards.json`, `grounding_audit.json`, and an `Images/` folder.
- **Agent Action**: A structured JSON object representing a single step in a plan (e.g., `{"action": "click", "coordinate": [x, y]}`).
- **Evaluation Metric**: A record containing `task_id`, `status` (success/fail/timeout), `duration_seconds`, and `error_message` (if applicable).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The percentage of tasks in the subset that complete without runtime errors (exit code 0) is measured against the total number of tasks attempted in the `metrics_summary.csv` (See US-1).
- **SC-002**: The success rate of the MMSkills agent on the subset is measured against the baseline success rate reported in the MMSkills paper (arXiv:2605.13527) for the same benchmark (See US-3).
- **SC-003**: The time-to-completion for a single skill step is measured against the 30-minute per-task timeout threshold to ensure CI feasibility (See US-3).
- **SC-004**: The peak memory usage during agent execution is measured against the 7 GB RAM limit of the CI runner to verify resource constraints (See US-1).
- **SC-005**: The number of missing or corrupted image files in the `skills_library` is measured against zero to ensure data integrity (See US-2).
- **SC-006**: The reproducibility of the execution flow is measured by the successful generation of a valid `metrics_summary.csv` for [deferred] of the requested subset tasks (See US-3).

## Assumptions

- The `external/MMSkills` submodule contains a complete and uncorrupted copy of the repository, including all binary assets (images) and configuration files.
- The CI environment has sufficient disk space (≥14 GB) to unpack dependencies and store temporary execution logs.
- The paper's reported baseline metrics are available in the abstract or main text for comparison, as the codebase does not include a pre-computed baseline file.
- The Python version in the CI environment is compatible with the `pyproject.toml` or `requirements.txt` specifications (Python 3.10+).
- The multimodal model weights required for inference are either included in the submodule or can be downloaded via Hugging Face without requiring a paid API key or GPU.
- The "OSWorld" or "Gaming" benchmarks referenced in the code can be simulated or run in a headless environment without requiring a full desktop GUI session.
- The execution of the agent on CPU will not exceed the 6-hour job limit for a subset of 5 tasks, assuming a hard timeout of 30 minutes per task is enforced.
