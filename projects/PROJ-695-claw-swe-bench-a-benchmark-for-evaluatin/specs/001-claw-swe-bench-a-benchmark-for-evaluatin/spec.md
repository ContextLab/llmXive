# Feature Specification: Claw-SWE-Bench Reproduction & Validation

**Feature Branch**: `001-reproduce-claw-swe-bench`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Reproduce & validate: Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks"

## User Scenarios & Testing

### User Story 1 - Execute Full Benchmark Pipeline (Priority: P1)

**Description**: As a researcher, I want to execute the `run_eval.py` entry point against the full SWE-bench multilingual dataset using the vendored OpenClaw harness and the default adapter, so that I can reproduce the primary result of the Pass@k metric reported in the paper.

**Why this priority**: This is the core validation step. Without a successful end-to-end execution on the full dataset, the benchmark's primary claims cannot be verified. It establishes the baseline "minimal adapter" performance.

**Independent Test**: The CI runner executes the script, processes all instances (or a representative subset if time-constrained, but aiming for full), and generates a `results/` directory containing the raw execution logs, patch files, and a summary JSON with the Pass@1 metric.

**Acceptance Scenarios**:
1. **Given** the `external/claw-swe-bench` submodule is initialized and dependencies are installed, **When** `run_eval.py` is invoked with the `multilingual.yaml` config, **Then** the process completes within 6 hours and outputs a `results/full_eval_summary.json` containing a `pass@1` metric.
2. **Given** the environment is ready, **When** the script encounters a repository cloning failure for a specific instance, **Then** the script logs the error, skips the instance, and continues processing the remaining instances without crashing the entire pipeline.
3. **Given** a successful run, **When** the output directory is inspected, **Then** it contains a `patches/` subdirectory with `.diff` files for every instance where the agent generated a patch.

---

### User Story 2 - Validate Adapter & Model Sweep (Priority: P2)

**Description**: As a researcher, I want to run a comparative evaluation between the "minimal direct-diff adapter" and the "full adapter" using the GLM backbone on the `Claw-SWE-Bench Lite` subset (80 instances), so that I can validate the reported performance gap ($\text{low}$ vs high Pass@1).

**Why this priority**: This validates the paper's central hypothesis regarding the importance of adapter design. It is a distinct experimental condition from the P1 baseline and requires specific configuration switching.

**Independent Test**: The CI runner executes two separate runs (minimal adapter vs. full adapter) on the 80-instance Lite set and produces a comparative report showing the Pass@1 delta.

**Acceptance Scenarios**:
1. **Given** the `verified.yaml` config is selected for the Lite subset, **When** the evaluation runs with the `full_adapter` flag enabled, **Then** the resulting `pass@1` metric is recorded in `results/lite_full_adapter.json`.
2. **Given** the same Lite subset, **When** the evaluation runs with the `minimal_adapter` flag enabled, **Then** the resulting `pass@1` metric is recorded in `results/lite_minimal_adapter.json`.
3. **Given** both result files exist, **When** a comparison script is run, **Then** it outputs a delta value and flags if the observed delta is within a reasonable tolerance of the paper's reported substantial percentage point difference.

---

### User Story 3 - Cost & Efficiency Accounting (Priority: P3)

**Description**: As a researcher, I want the evaluation pipeline to capture and report the total API cost and runtime duration for each agent run, so that I can verify the paper's claim that systems with similar accuracy can differ substantially in cost.

**Why this priority**: The paper explicitly treats cost accounting as a first-class axis. While P1 and P2 verify accuracy, P3 verifies the economic validity of the benchmark.

**Independent Test**: The evaluation run produces a log file containing per-instance cost estimates (tokens $\times$ price) and total wall-clock time.

**Acceptance Scenarios**:
1. **Given** a successful evaluation run, **When** the `results/` directory is scanned, **Then** a `cost_summary.csv` exists containing columns for `instance_id`, `api_cost_usd`, and `wall_time_seconds`.
2. **Given** the `cost_summary.csv`, **When** the total cost is aggregated, **Then** the value is non-zero and reflects the specific model pricing used in the config (e.g., GLM 5.1).
3. **Given** a run exceeding the 6-hour CI limit, **When** the job is terminated, **Then** the partial results include a `termination_reason: timeout` flag and the cost incurred up to that point is recorded.

---

### Edge Cases

- **What happens when** the API provider (e.g., DashScope, implied by `dashscope_cache_proxy.py`) returns a rate-limit error (HTTP 429)? **Then** the system MUST implement a retry mechanism with exponential backoff (max limited retries, A base delay is established.) before marking the instance as failed.
- **How does the system handle** a generated patch that fails to apply cleanly to the workspace due to context drift? **Then** the `evaluate.py` module MUST log the specific error (e.g., `Hunk failed`) and record the instance as `failed_apply` rather than `pass`.
- **What happens when** a repository in the dataset is private or the clone URL is broken? **Then** the dataset loader MUST skip the instance, log a `data_missing` warning, and ensure the total count of processed instances reflects this exclusion.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `run_eval.py` entry point using the `multilingual.yaml` configuration to process the dataset, ensuring all target languages and repositories are included in the run. (See US-1)
- **FR-002**: The system MUST support configuration switching between the `minimal_adapter` and `full_adapter` modes to reproduce the specific performance comparison claims. (See US-2)
- **FR-003**: The system MUST capture and persist API usage metrics (token counts, estimated cost) and wall-clock time for every instance processed. (See US-3)
- **FR-004**: The system MUST implement a robust error-handling mechanism that allows the evaluation to continue processing subsequent instances if a single instance fails due to network errors, API timeouts, or patch application failures. (See US-1, US-2)
- **FR-005**: The system MUST generate a final summary report in JSON format that aggregates Pass@1 metrics, total cost, and runtime statistics, matching the structure required for comparison with the paper's results. (See US-1, US-2, US-3)
- **FR-006**: The system MUST enforce a hard timeout per CI job, gracefully shutting down and saving partial results if the limit is reached. (See US-1, US-2)
- **FR-007**: The system MUST validate that the vendored submodule `external/claw-swe-bench` is at the correct commit hash before starting execution. (See US-1)

### Success Criteria

- **SC-001**: The Pass@1 metric for the minimal adapter on the full dataset is measured against the paper's reported value of a significant percentage. (See FR-001, US-1)
- **SC-002**: The Pass@1 metric for the full adapter on the Lite subset is measured against the paper's reported value of a high percentage. (See FR-002, US-2)
- **SC-003**: The total API cost and runtime are measured against the paper's qualitative claim that "systems with similar accuracy can differ substantially in total API cost." (See FR-003, US-3)
- **SC-004**: The error recovery rate is measured by the percentage of instances successfully processed after an initial transient failure (target: $>95\%$ recovery of recoverable errors). (See FR-004, US-1)
- **SC-005**: The completeness of the output dataset is measured by the count of successfully processed instances vs. the total 350 (target: $\ge$ a sufficient number of instances processed, excluding known data gaps). (See FR-007, US-1)

## Assumptions

- The `external/claw-swe-bench` submodule is correctly cloned and points to the commit `HEAD` of the repository ` as referenced in the paper.
- The CI runner has access to the necessary API keys for the LLM backends (e.g., GLM 5.1) via environment variables, and the `dashscope_cache_proxy.py` is configured to use a valid proxy endpoint if required.
- The 6-hour CI time limit is sufficient to process the Lite set with a single model; the full -instance set may require a subset or parallelization strategy not explicitly defined in the code but assumed to be handled by the `orchestrator.py` or manual configuration.
- The paper's claim of "future-commit cleanup" implies the dataset used is already static and does not require dynamic fetching of new commits during the evaluation run.
- The `requirements.txt` in the vendored repository is compatible with the standard Python 3.9+ environment provided by the GitHub Actions runner.
- The evaluation metrics (Pass@1) are calculated strictly according to the `evaluate.py` logic in the vendored code, which is assumed to align with the SWE-bench standard.
