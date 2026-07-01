# Feature Specification: Agents' Last Exam Reproduction

**Feature Branch**: `688-agents-last-exam-repro`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Agents' Last Exam"

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Sanity Check (Priority: P1)

The system MUST successfully initialize the execution environment by cloning the `agents-last-exam` submodule, installing dependencies, and verifying that the entry point (`ale_run/__main__.py`) is executable without immediate runtime errors (e.g., missing Python packages, syntax errors).

**Why this priority**: Without a functional environment, no reproduction can occur. This is the foundational step for all subsequent validation.

**Independent Test**: Execute the environment setup script and verify the entry point returns a usage help string or a controlled error regarding missing API keys (expected), rather than a Python traceback or import error.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner with Python 3.10+, **When** the user runs the initialization script to install `ale_run` dependencies, **Then** the process exits with code 0 and the `ale_run` package is importable.
2. **Given** the installed package, **When** the user runs `python -m ale_run --help`, **Then** the system outputs the CLI help text and exits with code 0.

---

### User Story 2 - Single Task Execution and Artifact Generation (Priority: P1)

The system MUST execute a single, representative task from the benchmark (e.g., a business finance or agriculture task) using a lightweight or dummy agent configuration to verify the execution pipeline, sandbox provisioning, and artifact generation logic works end-to-end.

**Why this priority**: This validates the core "reproduction" claim by proving the code can run a task and produce the expected output artifacts (logs, trajectory files) without crashing.

**Independent Test**: Run one specific task (e.g., `tasks/business_finance/ar_full_300/main.py`) with a `dummy` agent or a minimal local configuration and confirm the existence of output files in the designated `artifacts/` directory.

**Acceptance Scenarios**:

1. **Given** the environment is initialized, **When** the user executes the task runner for `ar_full_300` with a dummy agent, **Then** the runner completes within 60 minutes and generates a `trajectory.json` and `summary.json` in the output directory.
2. **Given** a task execution, **When** the process finishes, **Then** the exit code is 0 (success) or a specific non-0 code indicating a "task failed" (acceptable) rather than an "environment crash" (unacceptable).

---

### User Story 3 - Validation Report Generation (Priority: P2)

The system MUST aggregate the results of the executed tasks and generate a validation report that explicitly compares the observed behavior (e.g., pass/fail rate, execution time) against the paper's claims (e.g., "hardest tier remains far from saturated," "low average full pass rate").

**Why this priority**: This fulfills the "validate" requirement of the project, ensuring the reproduction is not just a run, but a scientific verification of the paper's assertions.

**Independent Test**: Generate a `validation_report.md` that lists the executed tasks, their outcomes, and a direct statement confirming or refuting the paper's headline statistics based on the limited sample run.

**Acceptance Scenarios**:

1. **Given** a set of completed task runs, **When** the validation script is triggered, **Then** it produces a Markdown report containing a table of results and a summary section.
2. **Given** the report, **When** a reviewer reads the "Comparison to Paper Claims" section, **Then** the report explicitly states whether the observed pass rate aligns with the paper's [deferred] claim (within the limits of the sample size) or notes the discrepancy.

---

### Edge Cases

- **What happens when API keys are missing?** The system MUST detect missing environment variables (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) and fail gracefully with a clear error message instructing the user to set them, rather than crashing with a generic `KeyError`.
- **How does the system handle sandbox timeout?** If a task exceeds the 6-hour CI limit or a specific task timeout (e.g., 60 mins), the runner MUST terminate the specific task, log a `TIMEOUT` status, and proceed to the next task (if any) or exit cleanly, rather than hanging the entire CI job.
- **What happens if the submodule is corrupted?** The initialization step MUST verify the integrity of the git submodule and fail immediately with a descriptive error if the `external/agents-last-exam` directory is incomplete.

## Requirements

### Functional Requirements

- **FR-001**: System MUST clone the `agents-last-exam` repository into `projects/PROJ-688-agents-last-exam/external/agents-last-exam/` and install its Python dependencies via `pip` (See US-1).
- **FR-002**: System MUST execute at least one task from the `tasks/` directory using the `ale_run` CLI with a configured agent (See US-2).
- **FR-003**: System MUST generate and persist execution artifacts (trajectory logs, task summaries) for every executed task in a designated output directory (See US-2).
- **FR-004**: System MUST detect missing API credentials and output a specific error code and message directing the user to configure them (See US-1).
- **FR-005**: System MUST produce a `validation_report.md` that aggregates task outcomes and compares them against the paper's stated metrics (See US-3).
- **FR-006**: System MUST enforce a per-task timeout of ≤ 60 minutes to ensure CI feasibility (See US-2).
- **FR-007**: System MUST handle sandbox provisioning failures by logging the error and marking the task as "FAILED" rather than crashing the runner (See US-2).
- **FR-008**: System MUST run exclusively on CPU without requiring CUDA, GPU acceleration, or 8-bit/4-bit quantization libraries that depend on GPU hardware (See US-2, Assumption: Compute Limits).

### Key Entities

- **Task**: A specific workflow definition (e.g., `ar_full_300`) containing the prompt, expected outcome, and evaluation logic.
- **Agent**: The AI system instance (e.g., `dummy`, `claude_code`) configured to execute the task.
- **Trajectory**: The sequence of actions, observations, and model responses generated during a task execution.
- **Validation Report**: The final artifact summarizing the reproduction results and comparing them to the paper.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Task execution success rate is measured against the paper's claim of "[deferred] average full pass rate" for the hardest tier (See FR-005, US-3).
- **SC-002**: Artifact completeness is measured against the requirement that every executed task must produce a `trajectory.json` and `summary.json` (See FR-003, US-2).
- **SC-003**: Execution time per task is measured against the CI constraint of ≤ 6 hours total job time and ≤ 60 minutes per task (See FR-006, US-2).
- **SC-004**: Error handling efficacy is measured by the absence of unhandled exceptions (Python tracebacks) during the runner's lifecycle (See FR-004, FR-007, US-1).
- **SC-005**: Validation report fidelity is measured by the presence of a direct, explicit comparison statement between observed results and paper claims (See FR-005, US-3).
- **SC-006**: Compute feasibility is measured by the successful completion of the run on a GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) without GPU allocation errors (See FR-008, US-2).

## Assumptions

- **Assumption about API Access**: The reproduction assumes that a valid API key for at least one supported model provider (e.g., Anthropic, OpenAI) is available via environment variables; if not, the system will run in "dummy" or "dry-run" mode to validate the pipeline without consuming tokens.
- **Assumption about Sandbox Environment**: The system assumes the GitHub Actions runner has sufficient privileges to spawn Docker containers or QEMU instances as required by the `ale_run` sandbox providers.
- **Assumption about Task Selection**: The reproduction assumes that running a single representative task (e.g., `ar_full_300`) is sufficient to validate the codebase's execution logic, as running the full 1K+ task suite is computationally infeasible on free-tier CI.
- **Assumption about Paper Claims**: The validation report assumes the paper's stated "[deferred] pass rate" applies to the specific "hardest tier" of tasks, and the reproduction will focus on tasks within that tier if identifiable.
- **Assumption about Compute Limits**: The analysis assumes that the `ale_run` codebase is compatible with CPU-only execution for the sandbox and agent orchestration layers, as the project is constrained to free-tier GitHub Actions resources (no GPU).
- **Assumption about Network**: The system assumes the runner has outbound internet access to clone the git submodule and pull Docker images, but does not require access to external proprietary databases beyond what is provided in the task definitions.
