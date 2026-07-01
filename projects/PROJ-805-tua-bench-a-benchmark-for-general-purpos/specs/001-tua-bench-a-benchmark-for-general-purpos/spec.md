# Feature Specification: Reproduce & validate: TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents

**Feature Branch**: `805-reproduce-tua-bench`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

## User Scenarios & Testing

### User Story 1 - Execute the TUA-Bench Quickstart Validation Pipeline (Priority: P1)

As a researcher, I need to execute the TUA-Bench validation pipeline on a representative subset of tasks to confirm the vendored code runs end-to-end and produces executable artifacts, so that I can verify the benchmark is functional before attempting full-scale reproduction.

**Why this priority**: This is the foundational step. If the environment cannot be spun up or the basic task runner fails, no further validation is possible. It establishes the "works on my machine" (or CI) baseline.

**Independent Test**: Run the `repo_env/setup_env.py` and a single representative task (e.g., `000-count-nuclei`) via the provided test harness. The test must exit with code 0 and generate a JSON report file in the task's `tests/` directory.

**Acceptance Scenarios**:

1. **Given** the project root and the `external/TUA-Bench` submodule is initialized, **When** the user executes the quickstart script for task `000-count-nuclei`, **Then** the script completes without error and produces `tests/results.json` containing a pass/fail status.
2. **Given** a clean GitHub Actions runner environment (CPU only, ~7GB RAM), **When** the validation script is triggered, **Then** the required Docker/Podman containers are pulled and instantiated, and the task logic executes within a time-limited timeout of 30 minutes per task.

---

### User Story 2 - Validate Execution-Based Scoring Protocol (Priority: P2)

As a reviewer, I need to verify that the execution-based scoring protocol correctly compares agent outputs against ground-truth references, so that I can trust the benchmark's evaluation metrics (e.g., the reported success rate).

**Why this priority**: The core value of TUA-Bench is its evaluation rigor. If the scoring logic is flawed (e.g., false positives/negatives), the entire benchmark is invalid. This must be validated before scaling to the full set of tasks.

**Independent Test**: Manually trigger the verification logic (`tests/test_outputs.py` or `verify.py`) for a task with a known solution and a deliberately corrupted solution. The system must correctly identify the pass and fail states respectively.

**Acceptance Scenarios**:

1. **Given** a task directory with a valid `solution/reference` file and a `tests/reference` file, **When** the verification script is run against the reference solution, **Then** the script returns a success status (score = 1.0).
2. **Given** the same task, **When** the verification script is run against a modified output file that deviates from the reference by >5% (or violates a specific constraint defined in `verify.py`), **Then** the script returns a failure status (score = 0.0) and logs the specific mismatch reason.

---

### User Story 3 - Generate Reproduction Report for Paper Claims (Priority: P3)

As a project lead, I need a consolidated report comparing the executed results of the TUA-Bench suite against the paper's claimed metrics (e.g., task families, success rates), so that I can confirm the reproduction matches the published findings.

**Why this priority**: This is the final deliverable. It synthesizes the execution results into a format that answers the research question: "Does the code reproduce the paper?"

**Independent Test**: Generate a Markdown report summarizing the pass/fail rates of the executed task subset and comparing them to the abstract's claims.

**Acceptance Scenarios**:

1. **Given** the results from a subset of 5 tasks across different families, **When** the report generator is run, **Then** it produces a Markdown document listing the task ID, family, execution time, and pass/fail status, explicitly noting any deviation from the paper's expected outcomes.
2. **Given** the paper's claim of "A diverse set of real-world tasks across five task families", **When** the report is generated, **Then** it confirms the existence of these 5 families in the `tasks/` directory and lists the count of tasks found in each.

---

### Edge Cases

- **Container Runtime Failure**: What happens if Podman/Docker is not installed or fails to pull a large image? The system must fail fast with a clear error message indicating the missing dependency, rather than hanging.
- **Non-Deterministic Task Setup**: Some tasks might rely on external services (e.g., "live-web information seeking"). If the external service is unreachable during CI, the task must fail gracefully with a specific "Network Timeout" error code, not a generic crash.
- **Resource Exhaustion**: If a task exceeds the GB RAM limit (e.g., due to a memory leak in the reference solution), the CI job must be terminated, and the failure must be logged as "OOM" rather than a logic error.
- **Deterministic Drift**: If a task relies on floating-point operations where slight CPU architecture differences might cause minor numerical drift, the verification script must use a relative tolerance of ≥ 1e-5 or an absolute tolerance of ≥ 1e-3 for numerical comparisons, rather than strict equality.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `repo_env/setup_env.py` script to initialize the containerized environment for at least one task from each of the five task families identified in the paper (See US-1).
- **FR-002**: The system MUST run the verification script (`tests/test_outputs.py` or `verify.py`) for every executed task and capture the exit code and standard output (See US-2).
- **FR-003**: The system MUST compare the generated output artifacts against the `tests/reference` files using the exact logic defined in the vendored code, without modification (See US-2).
- **FR-004**: The system MUST produce a structured JSON report for each task containing: `task_id`, `execution_time_seconds`, `status` (pass/fail), and `error_message` (if applicable) (See US-3).
- **FR-005**: The system MUST aggregate individual task results into a summary report that explicitly lists the task families and the count of tasks per family, verifying the paper's claim of "120 tasks across five families" (See US-3).
- **FR-006**: The system MUST enforce a hard timeout of 30 minutes per task execution to prevent CI resource exhaustion (See US-1).
- **FR-007**: The system MUST log the specific reason for any test failure (e.g., "File Missing", "Value Mismatch", "Timeout") to the standard error stream (See US-2).

### Key Entities

- **Task**: A unit of work defined by a directory in `tasks/`, containing `instruction.md`, `task.toml`, `solution/`, and `tests/`.
- **Environment**: A containerized runtime (Docker/Podman) defined by `environment/Dockerfile` in each task directory.
- **Reference**: The ground-truth output file located in `tests/reference/` used for validation.
- **Report**: The aggregated JSON/Markdown output summarizing execution results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The percentage of executed tasks that complete without environment initialization errors is measured against the total number of tasks attempted (See US-1).
- **SC-002**: The accuracy of the scoring protocol is measured by running the verification script against a known "pass" and a known "fail" input; the system must achieve ≥ 95% accuracy on these control cases (See US-2).
- **SC-003**: The existence of the five task families is measured by counting the distinct categories in the `tasks/` directory and comparing the count to the paper's claim of "five task families" (See US-3).
- **SC-004**: The total execution time for the validation subset is measured against the CI runner's -hour limit to ensure the reproduction is feasible within free-tier constraints (See US-1).
- **SC-005**: The reproducibility of the paper's claimed task count is measured by verifying the `dataset.toml` or directory listing contains ≥ 110 tasks ([deferred] of the claimed 120) to account for potential submodule versioning differences (See US-3).

## Assumptions

- The `external/TUA-Bench` submodule is correctly cloned and contains the full source code as of the paper's publication date.
- The CI runner has sufficient disk space to pull and store the necessary Docker/Podman images for the tasks.
- The "live-web information seeking" tasks can be simulated or are excluded from the initial validation subset if they require external network access that is blocked or unreliable in the CI environment.
- The paper's claim of "120 tasks" is accurate for the version of the code in the submodule; if the submodule contains fewer tasks, the report will reflect the actual count found.
- The validation scripts (`test_outputs.py`, `verify.py`) are self-contained and do not require additional Python packages beyond those listed in `pyproject.toml`.
- The containerized environments for the tasks do not require GPU acceleration, as the paper focuses on terminal agents which are primarily CPU-bound for script execution and file manipulation.
- The "deterministic setup script" mentioned in the abstract functions correctly without requiring manual intervention or external state initialization beyond what is provided in the `environment/` and `input/` directories.
