# Feature Specification: AdaPlanBench Reproduction & Validation

**Feature Branch**: `668-ada-plan-bench-reproduction`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce and validate AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Agents under World and User Constraints (arXiv:2606.05622) using the vendored submodule."

## User Scenarios & Testing

### User Story 1 - Environment Initialization & Dependency Resolution (Priority: P1)

**User Journey**: The researcher (CI runner) MUST be able to clone the project, initialize the git submodule containing the AdaPlanBench code, and install all Python dependencies required to run the benchmark without manual intervention or GPU requirements.

**Why this priority**: Without a reproducible, dependency-resolved environment, no experiments can be run. This is the foundational step that enables all subsequent validation.

**Independent Test**: Can be fully tested by running the setup script in a fresh Docker container (CPU-only) and verifying that `python -c "import env; import env.runner"` executes without import errors or CUDA warnings.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner (2 CPU, 7GB RAM, no GPU), **When** the setup script clones the submodule and installs dependencies, **Then** all Python imports succeed and no CUDA/GPU libraries are loaded.
2. **Given** the installed environment, **When** the system checks for required data files (e.g., `domain_metadata/housing/final/query_housing_macgyver_resample.json`), **Then** all referenced files exist and are readable.

### User Story 2 - Single-Task Execution & Artifact Generation (Priority: P1)

**User Journey**: The researcher MUST be able to execute the benchmark on a single, representative task (or a small subset of tasks) using a mocked or lightweight LLM interface to verify the execution loop, constraint checking, and plan revision logic works as described in the paper.

**Why this priority**: This validates the core logic of the benchmark (the "adaptive planning" mechanism) before attempting full-scale runs. It ensures the code actually runs and produces the expected intermediate artifacts.

**Independent Test**: Can be tested by running a single task with a deterministic "mock" agent (or a small, CPU-tractable model) and verifying that the output log contains the expected sequence of: Initial Plan -> Constraint Violation Feedback -> Revised Plan -> Final Result.

**Acceptance Scenarios**:

1. **Given** a valid task configuration from `domain_metadata`, **When** the `runner.py` is invoked with a mock agent, **Then** the system outputs a log file containing at least one constraint violation and one subsequent plan revision.
2. **Given** a completed single-task run, **When** the output artifacts are inspected, **Then** a JSON result file exists containing the `initial_plan`, `feedback_history`, `final_plan`, and `success_status` fields.

### User Story 3 - Full-Scale Reproduction & Metric Validation (Priority: P2)

**User Journey**: The researcher MUST be able to run the benchmark on a scaled-down subset of the household tasks (e.g., 10-20 tasks) using a CPU-tractable LLM (e.g., a small open-source model via HuggingFace or a local mock) to reproduce the paper's primary metric: adaptive planning accuracy under dual constraints.

**Why this priority**: This confirms the benchmark produces the specific quantitative results claimed in the paper (e.g., accuracy degradation with constraint accumulation) within the compute limits.

**Independent Test**: Can be tested by running the subset and comparing the calculated accuracy and constraint accumulation trends against the paper's reported trends (e.g., "performance degrades as more constraints accumulate").

**Acceptance Scenarios**:

1. **Given** a subset of 20 tasks and a CPU-tractable model, **When** the full evaluation loop completes, **Then** the merged results file reports an accuracy metric and a list of per-task outcomes.
2. **Given** the results, **When** the data is analyzed, **Then** the trend shows a correlation between the number of accumulated constraints and the failure rate (or a qualitative confirmation that the mechanism is active).

### Edge Cases

- **What happens when the LLM API times out or fails?** The system MUST implement a retry mechanism (e.g., a configurable number of retries with exponential backoff) and log the failure as a "timeout/error" rather than a logic failure, ensuring the benchmark continues without crashing.
- **How does the system handle a plan that violates multiple constraints simultaneously?** The constraint checker MUST identify and report the *first* violated constraint (or a prioritized list) to ensure the feedback loop is deterministic and testable.
- **What if the dataset file is corrupted or missing a key field?** The data loader MUST validate the JSON structure upon load and fail fast with a clear error message, rather than silently skipping tasks.

## Requirements

### Functional Requirements

- **FR-001**: System MUST initialize the git submodule and install Python dependencies in a CPU-only environment without requiring CUDA or GPU drivers (See US-1).
- **FR-002**: System MUST execute the benchmark loop for a single task, capturing the sequence of plan generation, constraint feedback, and plan revision (See US-2).
- **FR-003**: System MUST validate that the output artifacts (JSON logs) contain the required fields: `initial_plan`, `feedback_history`, `final_plan`, and `success_status` (See US-2).
- **FR-004**: System MUST handle LLM API errors or timeouts by retrying up to 3 times before marking the task as failed, ensuring the benchmark does not crash (See US-3).
- **FR-005**: System MUST compute and report the "adaptive planning accuracy" metric based on the ratio of successful final plans to total tasks attempted (See US-3).
- **FR-006**: System MUST log the number of constraints encountered per task to verify the "accumulating feedback" mechanism described in the paper (See US-3).

### Key Entities

- **Task Instance**: A single household problem instance from the `domain_metadata` containing the initial goal and hidden constraints.
- **Plan History**: A chronological list of the agent's proposed plans and the environment's constraint feedback responses.
- **Evaluation Result**: A structured record containing the final plan, success status, and the list of constraints violated during the process.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The setup process MUST complete in a timely manner on a standard CI runner., measured against the execution time of the setup script (See FR-001).
- **SC-002**: The single-task execution MUST produce a valid JSON artifact with all required fields within 60 seconds (excluding LLM latency), measured against the output file structure (See FR-003).
- **SC-003**: The full-scale subset run MUST successfully process at least 90% of the attempted tasks (e.g., 18/20) without crashing, measured against the task count (See FR-004).
- **SC-004**: The reported accuracy metric MUST be a valid float between 0.0 and 1.0, calculated as `successful_tasks / total_tasks`, measured against the aggregated results (See FR-005).
- **SC-005**: The constraint accumulation log MUST show that at least one task in the subset encountered ≥2 constraints, verifying the dual-constraint mechanism (See FR-006).

## Assumptions

- **Assumption about compute resources**: The benchmark will run on a CPU-only GitHub Actions runner with a limited number of vCPUs and approximately 7GB RAM, with a maximum job duration of 6 hours.; no GPU acceleration is available or required.
- **Assumption about model availability**: A CPU-tractable LLM (e.g., a small quantized model via HuggingFace or a local mock implementation) is available to drive the agent; full-scale LLM APIs (e.g., GPT-4, Gemini) are not required for the reproduction validation step.
- **Assumption about dataset integrity**: The vendored dataset (`query_housing_macgyver_resample.json`) is complete and valid as provided in the submodule, requiring no additional preprocessing or downloading.
- **Assumption about network access**: The CI runner has internet access to clone the git submodule and download Python dependencies, but external LLM API calls (if used) are limited to a mock or local model to ensure reliability.
- **Assumption about paper claims**: The paper's claim of a comprehensive set of household tasks is accurate for the full dataset, but the reproduction will focus on a representative subset (e.g., 10-20 tasks) to fit within the 6-hour compute window.
