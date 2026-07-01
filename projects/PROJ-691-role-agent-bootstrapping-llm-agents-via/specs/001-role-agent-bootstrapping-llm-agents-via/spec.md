# Feature Specification: Reproduce & validate: Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

**Feature Branch**: `001-reproduce-role-agent`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution. The code that implements this paper has been vendored, unchanged, as a git submodule at `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/`. The task is to run, validate, and reproduce the shipped implementation end-to-end and confirm it executes and produces real artifacts."

## User Scenarios & Testing

### User Story 1 - Environment Setup and Sanity Verification (Priority: P1)

The user (researcher/engineer) MUST be able to initialize the vendored `roleagent` repository, install its dependencies, and run a minimal sanity check to confirm the Python environment, Ray cluster (if applicable), and core modules are functional without GPU acceleration.

**Why this priority**: This is the foundational step. If the environment cannot be initialized or the basic dependencies (Python, Ray, PyTorch CPU) fail to load, no further reproduction is possible. It validates the "CPU-only" constraint immediately.

**Independent Test**: Execute the repository's minimal test suite or a "hello world" style script provided in the `tests/` or `scripts/` directory. The test must complete within 5 minutes on a standard CI runner.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner (2 CPU, 7GB RAM), **When** the user runs `pip install -r requirements.txt` and executes `python tests/test_protocol.py`, **Then** the script exits with code 0 and outputs "All sanity checks passed" without CUDA import errors.
2. **Given** the environment is set up, **When** the user attempts to import `role_agent.wia_utils` and `role_agent.aiw_curriculum`, **Then** the import succeeds without missing dependency errors.

---

### User Story 2 - World-In-Agent (WIA) Execution (Priority: P1)

The user MUST be able to execute the World-In-Agent (WIA) component of the Role-Agent framework on a small, sampled subset of the ALFWorld environment. The execution must run entirely on CPU and produce a log file containing state predictions and alignment metrics.

**Why this priority**: WIA is the core "dual-role" mechanism described in the abstract (LLM acting as agent and environment). Validating this specific path confirms the primary innovation of the paper works in the CPU-constrained context.

**Independent Test**: Run the WIA script with a configuration limiting the number of episodes to 5 and the model to a small, CPU-tractable LLM (e.g., a quantized small model or a local API mock if the real model is too heavy). The test verifies the existence of output artifacts (JSON logs) and the absence of GPU memory errors.

**Acceptance Scenarios**:

1. **Given** a valid configuration file pointing to a CPU-tractable model and a 5-episode subset of ALFWorld, **When** the user runs `python role_agent/wia_utils.py --episodes 5`, **Then** the process completes within 30 minutes, and a `wia_results.json` file is generated containing at least 5 entries with `predicted_state` and `actual_state` fields.
2. **Given** the WIA execution, **When** the log is inspected, **Then** no error messages related to "CUDA", "GPU", or "Device mismatch" appear in the standard output.

---

### User Story 3 - Agent-In-World (AIW) and Reproduction Report (Priority: P2)

The user MUST be able to execute the Agent-In-World (AIW) component to retrieve similar failure patterns and generate a final reproduction report that compares the observed metrics against the paper's claims (e.g., the >4% gain) or documents the specific performance on the sampled dataset.

**Why this priority**: This validates the second half of the dual-role evolution and fulfills the project's ultimate goal: confirming the implementation produces real artifacts and can be reported against the paper's claims.

**Independent Test**: Run the AIW script using the failure logs from US-2. Verify the generation of a summary report (Markdown or JSON) that explicitly states the sample size, the specific metrics measured, and whether the observed behavior aligns with the paper's qualitative description (even if quantitative gains differ due to sampling).

**Acceptance Scenarios**:

1. **Given** the `wia_results.json` from US-2, **When** the user runs `python role_agent/aiw_curriculum.py --input wia_results.json`, **Then** the script completes within 15 minutes and generates `aiw_analysis_report.md`.
2. **Given** the `aiw_analysis_report.md`, **When** the file is read, **Then** it contains a section "Reproduction Summary" that explicitly lists: (a) the number of tasks attempted, (b) the number of failures retrieved, and (c) a qualitative statement on whether the "dual-role" mechanism was successfully observed.

---

### Edge Cases

- **What happens when the LLM model size exceeds RAM?** The system MUST detect memory pressure and fail gracefully with a clear error message suggesting a smaller model or dataset subset, rather than crashing with a segmentation fault.
- **How does the system handle missing ALFWorld data?** If the vendored `alfworld` environment data is incomplete, the system MUST raise a `FileNotFoundError` with a specific path to the missing file during the initialization phase, not during execution.
- **What happens if the Ray cluster fails to start?** The system MUST fallback to a single-process mode (if supported) or exit with a clear diagnostic message regarding Ray installation, rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the WIA component on a CPU-only environment using a sampled subset of the ALFWorld dataset (See US-2).
- **FR-002**: System MUST generate a JSON log file containing state predictions and actual states for every episode run in the WIA phase (See US-2).
- **FR-003**: System MUST execute the AIW component to retrieve and analyze failure patterns from the WIA logs (See US-3).
- **FR-004**: System MUST produce a final reproduction report (Markdown) summarizing the execution results and comparing them to the paper's qualitative claims (See US-3).
- **FR-005**: System MUST detect and report any attempt to use CUDA/GPU accelerators, failing the job with a clear error if GPU is detected but not available (See US-1).

### Key Entities

- **WIA_Log**: A JSON record containing `episode_id`, `action`, `predicted_state`, `actual_state`, and `alignment_score`.
- **AIW_Report**: A Markdown document containing `sample_size`, `failure_patterns_identified`, `reproduction_summary`, and `limitations`.
- **Environment_Instance**: A simulated instance of the ALFWorld environment configured for CPU execution.

## Success Criteria

- **SC-001**: The WIA execution MUST complete successfully on a standard multi-CPU, 7GB RAM runner without out-of-memory errors (Measured against: CI runner resource limits) (See FR-001).
- **SC-002**: The generated `wia_results.json` MUST contain at least 5 valid entries with non-null `predicted_state` and `actual_state` fields (Measured against: File content validation) (See FR-002).
- **SC-003**: The final `aiw_analysis_report.md` MUST explicitly state the total number of tasks processed and confirm the presence of the "dual-role" mechanism in the logs (Measured against: Report content audit) (See FR-004).
- **SC-004**: The entire reproduction pipeline (Setup + WIA + AIW) MUST complete within 2 hours on the free-tier CI runner (Measured against: CI job duration) (See FR-001, FR-003).
- **SC-005**: The system MUST NOT import any CUDA-specific libraries or attempt to allocate GPU memory during execution (Measured against: Runtime logs for "CUDA" or "GPU" keywords) (See FR-005).

## Assumptions

- The vendored `roleagent` repository contains a CPU-tractable model configuration or a mechanism to substitute a smaller model (e.g., a distilled version or a mock) for the reproduction run, as the original paper likely used larger models requiring GPUs.
- The ALFWorld environment dependencies within the submodule are compatible with the Python version available on the standard GitHub Actions runner (typically recent stable releases).
- The "reproduction" is defined as validating the *mechanism* (WIA/AIW execution flow) and generating artifacts, not necessarily replicating the exact quantitative performance gains (e.g., >4% improvement) on a small sample, which may require larger compute resources.
- The `external/roleagent` submodule is fully populated and accessible at the start of the workflow; no network access is required to fetch the code itself.
- The Ray framework, if used, can operate in a single-node, single-machine mode for this reproduction scope.
