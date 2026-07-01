# Feature Specification: Reproduce & Validate OpenComputer

**Feature Branch**: `607-reproduce-opencomputer`  
**Created**: 2026-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: OpenComputer: Verifiable Software Worlds for Computer-Use Agents"

## User Scenarios & Testing

### User Story 1 - Execute Smoke Test on Local Docker Backend (Priority: P1)

**Describe this user journey**: A researcher initiates the OpenComputer reproduction pipeline using the local Docker backend to verify that the environment provisioning, task execution, and verification loops function correctly on a standard CPU-only CI runner.

**Why this priority**: This is the "smoke test" required to confirm the vendored code is not broken by the submodule integration. If the basic execution loop fails, no further validation of the paper's claims is possible. It establishes the baseline viability of the reproduction.

**Independent Test**: Run the provided smoke loop script against a single, simple task (e.g., `audacity_export_wav_440`) within a Docker container. Success is defined by the script exiting with code 0 and generating a valid JSON report artifact.

**Acceptance Scenarios**:
1. **Given** the Docker daemon is running and the `external/OpenComputer` submodule is cloned, **When** the user executes `python -m smoke.smoke_loop --task audacity_export_wav_440 --backend docker`, **Then** the system provisions a container, runs the task, and outputs a `smoke_report.json` with a `status` field of "success" or "partial_success".
2. **Given** the Docker daemon is running, **When** the user runs the smoke test with `--backend docker` but the required base image is missing, **Then** the system attempts to build the image via `build_image.sh` and proceeds to execution, or fails explicitly with a "build_failed" status and error log.

---

### User Story 2 - Validate Verifier Alignment on a Sample Set (Priority: P2)

**Describe this user journey**: A researcher executes a small batch of tasks (e.g., 5 tasks across 3 different applications) using a specific agent (e.g., `claude_agent`) and compares the OpenComputer verifier's pass/fail judgment against the "human adjudication" logic described in the paper to confirm the verifier's fidelity.

**Why this priority**: The core claim of the paper is that OpenComputer's verifiers align better with human adjudication than LLM-as-judge. Validating this alignment on a sample set is the primary scientific contribution of the reproduction.

**Independent Test**: Run multiple distinct tasks. Manually inspect the generated artifacts (e.g., the exported audio file or the modified document) and compare the result against the verifier's JSON output. The test passes if the verifier correctly identifies the success/failure state as confirmed by manual inspection of the artifact.

**Acceptance Scenarios**:
1. **Given** a set of 5 tasks with known ground-truth outcomes (success/failure), **When** the `run_eval.py` script executes these tasks with `--agent claude_agent` and `--verifier hardcode`, **Then** the `verification_report.json` contains a `verifier_accuracy` metric that matches the manual inspection of the artifacts within a 10% margin of error (allowing for edge-case ambiguity).
2. **Given** a task that fails mid-execution, **When** the system runs the verification step, **Then** the verifier correctly flags the task as "failed" and records the specific state mismatch (e.g., "file_not_found" or "format_mismatch") in the `failure_reason` field.

---

### User Story 3 - Generate Reproduction Report Against Paper Claims (Priority: P3)

**Describe this user journey**: The system aggregates the results from the smoke tests and validation runs to generate a final `reproduction_report.md` that explicitly states whether the paper's claims regarding "33 desktop applications" and "[deferred] finalized tasks" are reproducible within the constraints of the free-tier CI environment.

**Why this priority**: This synthesizes the technical execution into the final deliverable required for the project to reach `research_complete`. It answers the "So what?" question for the reproduction effort.

**Independent Test**: Execute the `generate_report.py` script (or equivalent aggregation logic) which reads the JSON artifacts from US-01 and US-02. The test passes if the generated markdown file contains a "Conclusion" section that explicitly references the success rate and compares it to the paper's abstract claims.

**Acceptance Scenarios**:
1. **Given** successful JSON artifacts from US-01 and US-02, **When** the report generation script runs, **Then** the output `reproduction_report.md` contains a table summarizing the `tasks_attempted`, `tasks_passed`, and `verifier_alignment_rate`, and explicitly states "Claims Reproduced" or "Claims Partially Reproduced" based on the data.
2. **Given** a runtime error occurs during the batch execution (e.g., container timeout), **When** the report generation script runs, **Then** the report includes a "Limitations" section detailing the specific error and the number of tasks skipped, rather than failing to generate the file.

### Edge Cases

- **Given** the Docker backend runs out of disk space (limit ~ GB) during image build, **When** the provisioning step occurs, **Then** the system fails gracefully with a "disk_quota_exceeded" error and does not attempt to run the task.
- **Given** an agent (e.g., `gemini_agent`) requires an API key that is not provided in the environment, **When** the agent initialization occurs, **Then** the system skips that agent and logs a "missing_credentials" warning rather than crashing the entire pipeline.
- **Given** a task requires a specific GUI application (e.g., GIMP) that is not installed in the Docker base image, **When** the task runner attempts to launch the app, **Then** the verifier records a "dependency_missing" failure and the task is marked as "skipped" in the report.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the OpenComputer `smoke_loop.py` script against at least one task from the `task_generator` directory using the local Docker backend to validate the end-to-end pipeline. (See US-1)
- **FR-002**: The system MUST run a batch of ≥ 5 tasks using the `run_eval.py` script and generate a JSON verification report containing pass/fail status and failure reasons for each task. (See US-2)
- **FR-003**: The system MUST compute a `verifier_alignment_rate` metric by comparing the hard-coded verifier's judgment against the manual inspection of the generated artifacts for the batch in FR-002. (See US-2)
- **FR-004**: The system MUST generate a `reproduction_report.md` that aggregates execution logs, success rates, and explicitly compares the results to the claims made in the paper's abstract (e.g., "a specific number of applications", "[deferred] tasks"). (See US-3)
- **FR-005**: The system MUST handle container provisioning failures (e.g., image build errors, disk quota exceeded) by logging the specific error and marking the affected tasks as "failed" without crashing the entire batch process. (See Edge Cases)

### Key Entities

- **Task**: A JSON-defined unit of work consisting of an `env_manifest.json`, `task.json`, and expected outcome.
- **Verifier**: The component that inspects the final state of the application environment and outputs a boolean pass/fail decision.
- **Agent**: The LLM-driven controller that executes the task steps (e.g., `claude_agent`, `dart_agent`).
- **Reproduction Report**: The final Markdown artifact summarizing the validation results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The `verifier_alignment_rate` is measured against the manual inspection of the generated artifacts for the 5-task sample set to confirm the verifier's accuracy. (See FR-003)
- **SC-002**: The `task_success_rate` is measured against the expected outcome defined in the `task.json` for the batch of 5 tasks to validate the agent's capability. (See FR-002)
- **SC-003**: The `reproduction_report.md` completeness is measured against the requirement to include a direct comparison to the paper's abstract claims (a representative set of applications and tasks). (See FR-004)
- **SC-004**: The `pipeline_reliability` is measured by the percentage of tasks in the batch that complete without a system-level crash (e.g., OOM, container timeout). (See FR-005)
- **SC-005**: The `execution_time` for the smoke test (US-1) is measured against the 6-hour free-tier CI limit to ensure feasibility. (See FR-001)

## Assumptions

- The local Docker daemon is available and functional on the CI runner, allowing for the build and execution of the OpenComputer environment images.
- The `external/OpenComputer` submodule is correctly cloned and contains all necessary dependencies as listed in `requirements.txt` without modification.
- The free-tier CI runner (multiple CPU cores, adequate RAM) is sufficient to run the Docker containers for the selected sample tasks, assuming no heavy GPU-accelerated models are invoked.
- The `hardcode` verifiers provided in the `evaluation/apps/specs/` directory are sufficient to validate the tasks in the sample set without requiring additional configuration.
- Network access is available to pull base Docker images if they are not locally cached.
- The paper's claim of a "large corpus of finalized tasks" refers to the total corpus, but the reproduction scope is limited to a representative sample (e.g., a small number of tasks) due to compute constraints.
