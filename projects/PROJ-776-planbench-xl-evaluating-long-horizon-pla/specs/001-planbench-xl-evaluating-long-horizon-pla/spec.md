# Feature Specification: PlanBench-XL Reproduction & Validation

**Feature Branch**: `001-planbench-xl-reproduction`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents in Large-Scale Tool Ecosystems (arXiv:2606.22388) using vendored code."

## User Scenarios & Testing

### User Story 1 - Execute Baseline Reproduction (Priority: P1)

**Journey**: A researcher initiates the reproduction pipeline to run the PlanBench-XL benchmark on a small, representative subset of tasks (e.g., 5 tasks) using a single default model configuration (e.g., `gpt-5.4-mini` in default mode) to verify the codebase executes without errors and produces the expected output artifacts (JSON logs, evaluation metrics).

**Why this priority**: This is the critical path. If the vendored code cannot be executed end-to-end on a small scale, the entire project fails. It validates the environment setup, dependency installation, and basic script functionality.

**Independent Test**: Run `scripts/run_retail_batch.py` with a configuration restricting the task count to 5 and the model to `gpt-5.4-mini`. Verify the script exits with code 0 and generates a `results/` directory containing `eval_results.json` and `task_logs/`.

**Acceptance Scenarios**:

1. **Given** the project is initialized and dependencies are installed, **When** the user executes the baseline batch script with a 5-task limit, **Then** the script completes successfully, and a valid JSON results file is generated with non-empty metrics.
2. **Given** the script runs, **When** the output logs are inspected, **Then** they show successful tool retrieval and execution steps for the sampled tasks without uncaught exceptions.
3. **Given** the run completes, **When** the `eval_results.json` is parsed, **Then** it contains the expected keys (e.g., `accuracy`, `task_id`, `success`) matching the paper's reported schema.

---

### User Story 2 - Validate Blocking & Noise Conditions (Priority: P2)

**Journey**: A researcher expands the reproduction to include the "blocking" and "noise" conditions described in the abstract (e.g., `retail_gpt5.4_blocker.yaml` and `retail_gpt5.4_noise_ratio_0p4.yaml`) to confirm the environment correctly simulates missing tools and distracting information, resulting in the expected drop in agent performance.

**Why this priority**: The core contribution of the paper is the evaluation of agents under imperfect conditions. Validating that the simulation logic (blocking/noise) works as intended is essential to confirm the benchmark's validity.

**Independent Test**: Execute the batch script with the `blocker` and `noise_ratio_0p4` configurations. Compare the resulting accuracy metrics against the baseline (default) run to confirm a statistically significant performance drop, consistent with the paper's claim that "agents are especially vulnerable when failures lack explicit error signals."

**Acceptance Scenarios**:

1. **Given** the baseline accuracy is established, **When** the blocking configuration is run on the same task subset, **Then** the recorded accuracy is strictly lower than the baseline (e.g., < 50% of baseline) and the logs contain specific "tool blocked" or "missing input" events.
2. **Given** the noise configuration is run, **When** the task logs are analyzed, **Then** they contain evidence of the agent interacting with "distracting" or "noisy" tool descriptions, and the final success rate reflects increased failure due to misinterpretation.
3. **Given** multiple runs are performed, **When** the results are aggregated, **Then** the variance in performance under noise conditions is captured and reported in the summary artifacts.

---

### User Story 3 - Generate Comparative Analysis Report (Priority: P3)

**Journey**: A researcher aggregates the results from multiple model configurations (e.g., `gpt-5.4`, `llama3.3-70b`, `qwen3-14b`) and conditions (default, blocker, noise) to generate a summary table and figures that reproduce the "Main Table" and key findings from the paper, explicitly noting any discrepancies.

**Why this priority**: This delivers the final validation artifact. It confirms that the reproduction matches the published claims and highlights any deviations, completing the "reproduce & validate" objective.

**Independent Test**: Run the evaluation script to process all generated JSON logs into a consolidated CSV/JSON report and generate a summary Markdown report. Verify the report contains a table comparing models across conditions and a section titled "Discrepancies" if results differ from the paper.

**Acceptance Scenarios**:

1. **Given** logs from at least 3 different model configurations, **When** the analysis script runs, **Then** it produces a `reproduction_report.md` containing a comparative table of accuracy scores for each model/condition pair.
2. **Given** the paper's reported accuracy for GPT-5.4 ([deferred] block-free, [deferred] severe blocking), **When** the report is generated, **Then** the report explicitly lists the reproduced values and calculates the percentage difference (or flags `[NEEDS CLARIFICATION]` if the difference > 5%).
3. **Given** the analysis is complete, **When** the report is reviewed, **Then** it includes a specific section detailing any methodological differences (e.g., random seed, API version) that might explain result variations.

---

### Edge Cases

- **What happens when** an API key is missing or expired? The system must fail gracefully with a clear error message indicating which model configuration failed and the specific authentication error, rather than crashing the entire batch.
- **How does the system handle** a tool call that hangs indefinitely? The executor must enforce a strict timeout (e.g., a bounded duration per tool call) and mark the task as "failed due to timeout" rather than blocking the entire pipeline.
- **What happens when** the external repository submodule is corrupted or missing files? The entry script must detect missing critical files (e.g., `database.json`, `tasks.json`) at startup and exit with a descriptive error code, preventing partial execution.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `scripts/run_retail_batch.py` entry point with configurable parameters for `task_count`, `model_config`, and `condition_type` (default/blocker/noise) to support the reproduction workflow (See US-1).
- **FR-002**: The system MUST simulate the "blocking" mechanism by intercepting tool calls defined in `blocker_tools.json` and returning specific error states (e.g., "tool unavailable") without crashing the agent loop (See US-2).
- **FR-003**: The system MUST inject "noisy" or "misleading" tool descriptions into the context window according to the `noise_ratio` parameter defined in the YAML configs, ensuring the agent receives the altered data (See US-2).
- **FR-004**: The system MUST enforce a hard timeout of 60 seconds per individual tool invocation and 300 seconds per total task execution to ensure the analysis fits within the 6-hour CI job limit (See US-1, US-2).
- **FR-005**: The system MUST persist all execution traces, tool call logs, and final evaluation metrics into structured JSON files (`.json`) in the `results/` directory for downstream analysis (See US-3).
- **FR-006**: The system MUST automatically detect and skip models that require external API keys not present in the environment, logging a warning but continuing execution for available models (See US-1).
- **FR-007**: The system MUST generate a `reproduction_report.md` that aggregates results from all completed runs, calculating accuracy percentages and comparing them against the paper's baseline values (See US-3).

### Key Entities

- **Task**: A single retail query from `tasks.json` requiring a sequence of tool calls to solve.
- **Tool**: An atomic function defined in `baseline_tools.json` (or variants) that the agent can invoke.
- **ModelConfig**: A YAML definition specifying the LLM endpoint, parameters, and specific environment conditions (e.g., noise ratio).
- **ExecutionLog**: A JSON record capturing the step-by-step interaction (prompt, tool call, response, error) for a single task.
- **EvaluationMetric**: A summary statistic (e.g., accuracy, success rate) derived from the ExecutionLogs.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reproduction pipeline MUST successfully complete a full run of 5 tasks on at least one model configuration within 30 minutes, producing valid `eval_results.json` artifacts (Measured against: CI job duration and file existence) (See US-1).
- **SC-002**: The accuracy metric for the "blocker" condition MUST be demonstrably lower than the "default" condition for the same model on the same task subset (Measured against: Internal comparison of `eval_results.json` from different runs) (See US-2).
- **SC-003**: The `reproduction_report.md` MUST contain a comparison table where every cell is populated with a numeric accuracy value or a `[DEFERRED]` flag if the run failed, with no empty cells (Measured against: Report validation script) (See US-3).
- **SC-004**: The system MUST reject any configuration requiring GPU-accelerated models (e.g., local Llama3-70b with CUDA) and log a specific error, ensuring the run remains CPU-tractable (Measured against: Error log content) (See US-1).
- **SC-005**: The total disk usage for all generated logs and results for a multi-task run MUST remain within a constrained footprint, ensuring it fits within the available disk limit. (Measured against: File system size check) (See US-3).

## Assumptions

- **Assumption about API Access**: The reproduction assumes that the CI environment has valid, rate-limited access to the required external LLM APIs (e.g., OpenAI, Anthropic) via environment variables. If keys are missing, those specific models are skipped.
- **Assumption about Data Integrity**: The vendored `external/PlanBench-XL` submodule is assumed to be a complete and uncorrupted clone of the source repository, containing all necessary `database.json`, `tasks.json`, and configuration files.
- **Assumption about Compute Limits**: The analysis assumes that the "small-scale" reproduction (a limited number of tasks per model) is sufficient to validate the codebase's functionality without needing to reproduce the full benchmark, which would exceed the 6-hour CI time limit.
- **Assumption about Model Availability**: The `gpt-5.4` and `gpt-5.4-mini` models referenced in the paper are assumed to be available via the standard OpenAI API endpoints used in the provided YAML configs; if the API version has changed, the config will need manual adjustment (recorded as a discrepancy).
- **Assumption about Determinism**: The analysis assumes that the LLM API responses may vary slightly between runs due to non-determinism; therefore, the success criteria focus on the *trend* (blocker < default) rather than exact numeric replication of the paper's percentages.
