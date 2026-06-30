# Feature Specification: Reproduce & Validate ResearchClawBench

**Feature Branch**: `001-reproduce-researchclawbench`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Research. The code is vendored; task is to run, validate, and reproduce the shipped implementation end-to-end."

## User Scenarios & Testing

### User Story 1 - Execute Single-Task Reproduction (Priority: P1)

The researcher MUST be able to execute the benchmark evaluation on a single, representative task (e.g., `Astronomy_000` or `Chemistry_000`) using the vendored `ResearchClawBench` codebase to verify that the pipeline initializes, runs the agent loop, and produces a final score artifact without runtime errors.

**Why this priority**: This is the "smoke test" for the entire project. If the vendored code cannot run a single task end-to-end on the target environment (free CPU CI), the entire benchmark validation is impossible. It establishes the baseline feasibility of the reproduction effort.

**Independent Test**: Run the `rcb-eval` CLI command with a specific task ID and a lightweight local or mock agent configuration. Verify the existence of a generated score JSON file and a log file containing the execution trace.

**Acceptance Scenarios**:

1. **Given** the `ResearchClawBench` submodule is cloned and dependencies are installed, **When** the user executes `rcb-eval --task Astronomy_000 --agent mock`, **Then** the system MUST produce a `results/Astronomy_000_score.json` file containing a numeric score and exit with status code 0.
2. **Given** the evaluation environment is configured with a mock API key, **When** the evaluation process encounters a missing dependency in the task data, **Then** the system MUST log a clear error message to `stderr` and exit with a non-zero status code, failing fast without partial artifacts.

---

### User Story 2 - Validate Multimodal Rubric Scoring (Priority: P2)

The researcher MUST be able to verify that the evaluation engine correctly parses the `checklist.json` rubric for a target study and applies the weighted criteria to the generated artifacts (text, figures, data) to produce a reproducible score.

**Why this priority**: The core novelty of ResearchClawBench is the "multimodal rubric" approach. Validating that the scoring logic actually consumes the rubric and produces a score (rather than a hardcoded value) is essential to confirming the benchmark's validity.

**Independent Test**: Manually inspect a target task's `checklist.json` and the corresponding `target_study/paper.pdf`. Run the evaluator and cross-reference the generated score breakdown (if available) or the final score against the expected range defined in the paper's abstract (e.g., a moderate scale for current frontier agents).

**Acceptance Scenarios**:

1. **Given** a task with a defined `checklist.json` containing 5 weighted criteria, **When** the evaluator processes a perfect hypothetical output, **Then** the system MUST assign a score equal to the sum of the weights (e.g., 100.0) within a tolerance of ±0.01.
2. **Given** a task where the generated output is missing a required figure referenced in the rubric, **When** the evaluator runs, **Then** the system MUST deduct the specific weight assigned to that figure in the `checklist.json` and reflect this in the final score.

---

### User Story 3 - Reproduce Cross-Agent Aggregation (Priority: P3)

The researcher MUST be able to execute the evaluation pipeline for a small subset of agents (e.g., 2 distinct agents) across 1 task to verify that the system correctly aggregates individual task scores into a summary report, mimicking the "leaderboard" generation described in the paper.

**Why this priority**: The paper claims to evaluate "seven autonomous research agents." While running all 7 is computationally expensive, reproducing the aggregation logic for a subset validates that the data pipeline can handle multiple runs and produce the comparative statistics (mean, std dev) reported in the abstract.

**Independent Test**: Run the evaluator for two distinct agent configurations on one task. Verify the existence of a summary report (CSV or JSON) that lists scores per agent and calculates the mean score for that task.

**Acceptance Scenarios**:

1. **Given** two successful evaluation runs for `Agent_A` and `Agent_B` on `Astronomy_000`, **When** the aggregation script is executed, **Then** the output MUST contain a record with `mean_score` equal to the arithmetic average of the two individual scores.
2. **Given** a run where one agent fails (non-zero exit), **When** the aggregation script runs, **Then** the system MUST either exclude the failed run from the mean calculation or explicitly mark it as "failed" in the summary report, without crashing the aggregation process.

### Edge Cases

- **What happens when** the `tasks/<ID>/data/` directory is missing required CSV or PDF files? The system MUST fail with a specific `FileNotFoundError` indicating the missing file, rather than silently proceeding with empty data.
- **How does the system handle** a `checklist.json` where the sum of weights does not equal 100 (or 1.0)? The system MUST validate the rubric weights at startup and raise a `ValueError` if the total weight deviates from the expected baseline by more than 0.01.
- **What happens when** the external LLM API returns a rate-limit error during the agent loop? The system MUST implement a retry mechanism (exponential backoff) for up to 3 attempts before marking the task as failed.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `rcb-eval` CLI entry point to initialize the evaluation environment for a specified task ID and agent configuration (See US-1).
- **FR-002**: System MUST parse the `tasks/<ID>/target_study/checklist.json` file to extract weighted evaluation criteria and apply them to generated artifacts (See US-2).
- **FR-003**: System MUST validate that all required data files (CSV, PDF, images) referenced in `task_info.json` exist before starting the evaluation loop (See US-1).
- **FR-004**: System MUST generate a structured JSON artifact containing the final score, rubric breakdown, and execution logs for every completed task (See US-2).
- **FR-005**: System MUST aggregate individual task scores across multiple agent runs to compute mean and standard deviation statistics for a summary report (See US-3).
- **FR-006**: System MUST implement a retry mechanism with exponential backoff (multiple attempts, initial delay of several seconds) for transient network errors during agent inference (See US-1).

### Key Entities

- **Task**: Represents a specific scientific challenge (e.g., `Astronomy_000`), containing `task_info.json`, `data/`, `related_work/`, and `target_study/`.
- **Rubric**: The `checklist.json` artifact defining the weighted criteria for scoring a specific task.
- **Agent**: A configuration defining the autonomous research agent (e.g., `Claude Code`, `ResearchHarness`) used to generate the output.
- **Score**: The numeric result (0-100) derived from applying the Rubric to the Agent's output.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The reproduction run MUST produce a valid JSON score artifact for at least one task, measured against the existence of the file `results/<task_id>_score.json` (See FR-004, US-1).
- **SC-002**: The scoring engine MUST correctly apply the rubric weights, measured by verifying that a perfect synthetic output yields a score equal to the sum of weights in `checklist.json` (See FR-002, US-2).
- **SC-003**: The aggregation logic MUST compute the mean score accurately, measured by comparing the calculated mean in the summary report against the manual average of the input scores (See FR-005, US-3).
- **SC-004**: The system MUST handle missing data gracefully, measured by the system raising a specific `FileNotFoundError` within 5 seconds of detecting the missing file (See FR-003, US-1).
- **SC-005**: The evaluation pipeline MUST complete a single task run within 30 minutes on a standard CPU-only runner, measured against the wall-clock time of the execution (See FR-001, US-1).

## Assumptions

- The vendored `ResearchClawBench` codebase at `external/ResearchClawBench/` is a complete and unmodified clone of the repository referenced in the paper, containing all necessary scripts and task definitions.
- The evaluation environment (GitHub Actions free-tier runner) provides sufficient disk space (~14 GB) to store the `external/` submodule, task data, and generated artifacts without exceeding limits.
- The benchmark evaluation does not require GPU acceleration; all agent inference and scoring logic is assumed to be CPU-tractable or relies on external API calls that do not consume local GPU resources.
- The `mock` agent or lightweight local model referenced in the acceptance scenarios is sufficient to verify the pipeline's structural integrity without requiring expensive API keys or large model downloads.
- The `checklist.json` rubrics provided in the `target_study` directories are valid JSON files with consistent schema (weights summing to 1.0 or 100) as implied by the paper's methodology.
- The external LLM APIs (if used for full reproduction) will be available and rate-limited appropriately; the spec assumes a fallback to a mock agent for structural validation to ensure CI feasibility.
