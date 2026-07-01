# Feature Specification: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

**Feature Branch**: `653-taste-benchmark-reproduction`  
**Created**: 2024-05-20  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks"

## User Scenarios & Testing

### User Story 1 - Execute TASTE Pipeline End-to-End (Priority: P1)

The system MUST successfully execute the vendored TASTE pipeline (Stage 1: N-gram Model, Stage 2: Clustering, Stage 3: Task Synthesis) using the provided `external/TASTE-task-synthesis-from-tool-sequence-evolution` submodule code and pre-seeded artifacts, producing valid JSON task artifacts for at least one domain (e.g., `airline`) without runtime errors.

**Why this priority**: This is the foundational requirement for a reproduction project. Without a successful end-to-end execution, no validation of the paper's claims can occur. It establishes the baseline "runnable" state of the code.

**Independent Test**: Run the entry script with default configuration; verify that output files (e.g., `tasks.json`) are created in the `artifacts/task_sets` directory and contain valid JSON structures matching the schema of the input `tool_spec.json`.

**Acceptance Scenarios**:

1. **Given** the submodule is cloned and dependencies are installed via `pyproject.toml`, **When** the main execution script is invoked with the `airline` domain, **Then** the process completes with exit code 0 and generates a `tasks.json` file containing at least 10 distinct task objects.
2. **Given** a valid `tool_spec.json` exists, **When** the N-gram sampler (Stage 1) executes, **Then** it produces a checkpoint file (`ngram_airline_n3_*.json`) containing probability distributions for tool sequences.
3. **Given** the Stage 1 checkpoint, **When** the clustering and validation (Stage 2) runs, **Then** it outputs a `medoids.json` file identifying representative tool sequences.

---

### User Story 2 - Validate Task Coherence and Tool Usage (Priority: P2)

The system MUST validate that the synthesized tasks are coherent (the tool sequence actually solves the natural language task) and that the tool sequences are valid according to the domain-specific validators (e.g., `airline.py`).

**Why this priority**: The core claim of the paper is that TASTE generates *valid* but *difficult* tasks. Generating syntactically correct JSON that represents nonsense or invalid tool usage would invalidate the reproduction. This ensures the "quality" of the generated artifacts.

**Independent Test**: Run the `task_validator` module against the generated `tasks.json`; the validation rate (percentage of tasks passing) must be ≥ 80% for the initial sample.

**Acceptance Scenarios**:

1. **Given** a generated task object with a `scenario` (text) and `action_sequence` (list of tools), **When** the domain validator (e.g., `src/common/domain_validators/airline.py`) checks the sequence, **Then** the validator returns a `valid: true` status if the sequence logically achieves the scenario goal.
2. **Given** a batch of generated tasks, **When** the `action_sequence_policy` checks for tool coverage, **Then** the output report confirms that at least 3 distinct tools are used across the top [deferred] of generated tasks.
3. **Given** a task with an invalid tool parameter (e.g., non-existent flight ID format), **When** the validator runs, **Then** the task is flagged as invalid and excluded from the final `tasks.json` set, logging the specific error reason.

---

### User Story 3 - Reproduce Difficulty Drop Claim (Priority: P3)

The system MUST execute a simulated evaluation (or report the existing evaluation results if the code includes a "mock" agent runner) to demonstrate that the generated tasks are harder than the baseline `τ²-Bench` tasks, specifically targeting a performance drop in agent success rates.

**Why this priority**: This addresses the primary scientific claim of the paper (that models saturate existing benchmarks but fail on TASTE tasks). While we may not have access to the proprietary LLMs (Gemini-3-Flash) to run live inference, the spec requires the *mechanism* to be present or the *data* to be reproducible from the paper's provided artifacts.

**Independent Test**: If the code includes an agent runner, execute it on a sample of `τ²-Bench` tasks vs. `TASTE` tasks; if not, verify the code can load the paper's provided result metrics and reproduce the reported performance gap (e.g., a significant reduction) via a deterministic script.

**Acceptance Scenarios**:

1. **Given** the `retail_base_tasks` (baseline) and `retail_gemini_3_flash` (TASTE) task sets, **When** the evaluation script runs (using a deterministic heuristic or mock agent), **Then** the output report shows a success rate for TASTE tasks ≤ 60% of the baseline success rate.
2. **Given** the `task_sets` directory, **When** the `partial_coverage_gt_agent` is invoked, **Then** it outputs a CSV/JSON summary comparing tool-combination coverage between baseline and TASTE sets, showing TASTE has >2x unique tool combinations.
3. **Given** the evaluation results, **When** the `adversarial_evolver` is analyzed, **Then** the report confirms that the "difficulty" metric (inverse of success rate) increased by a factor of ≥ 1.5 compared to the baseline.

---

### Edge Cases

- **What happens when** the N-gram sampler converges to a single dominant tool sequence (mode collapse)? The system MUST detect this (via entropy check) and trigger a re-sampling with adjusted temperature parameters.
- **How does the system handle** a domain (e.g., `telecom`) where the `tool_spec.json` references tools not present in the validator logic? The system MUST raise a `ConfigurationError` at initialization, preventing pipeline execution.
- **What happens when** the LLM call (if used for validation) times out or returns malformed JSON? The system MUST implement a retry mechanism (max 3 attempts) with exponential backoff before marking the task as "failed validation" rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the Stage 1 N-gram model initialization using the `pre_seed.json` and `post_seed.json` artifacts to generate valid tool sequence probabilities. (See US-1)
- **FR-002**: System MUST perform clustering on the sampled tool sequences to identify medoids, ensuring at least 5 representative clusters are selected per domain. (See US-1)
- **FR-003**: System MUST invoke domain-specific validators (e.g., `airline.py`, `retail.py`) to verify the logical coherence of every generated task before inclusion in the final artifact set. (See US-2)
- **FR-004**: System MUST generate a final `tasks.json` file for each domain containing the natural language scenario, the tool sequence, and the expected database state. (See US-1)
- **FR-005**: System MUST produce a validation report detailing the pass/fail rate of generated tasks, the distribution of tool combinations, and the entropy of the N-gram model. (See US-2)
- **FR-006**: System MUST handle missing environment variables (e.g., `LLM_API_KEY` if external calls are required) by gracefully exiting with a clear error message rather than a stack trace. (See US-3)
- **FR-007**: System MUST ensure that the generated tasks do not exceed a maximum tool sequence length to maintain CPU tractability. (See US-1)

### Key Entities

- **ToolSequence**: A ordered list of tool invocations (tool name + parameters) representing the ground-truth solution path.
- **Task**: A composite entity containing a natural language `scenario`, a `tool_sequence`, and a `validation_status`.
- **DomainConfig**: Configuration object defining the available tools, constraints, and validator logic for a specific domain (e.g., `airline`).
- **NgramModel**: The statistical model storing $n$-gram probabilities derived from seed sequences.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of generated tasks passing the domain validator is measured against a target threshold of ≥ 80% for the `airline` domain. (See US-2)
- **SC-002**: The number of unique tool combinations in the TASTE-generated set is measured against the baseline `τ²-Bench` set; the target is ≥ 2.0x increase. (See US-3)
- **SC-003**: The average entropy of the N-gram model output is measured against a baseline of random sampling to ensure the model is not degenerate (target entropy > 0.5). (See US-1)
- **SC-004**: The total execution time for the full pipeline (Stage 1-3) on a single CPU core is measured against a limit of ≤ 6 hours. (See US-1)
- **SC-005**: The success rate of a heuristic agent on TASTE tasks is measured against the baseline success rate; the target is a drop of ≥ 30 percentage points (e.g., from [deferred] to <60%). (See US-3)

## Assumptions

- The vendored submodule `TASTE-task-synthesis-from-tool-sequence-evolution` contains a working `main` entry point or a documented `run.sh` script that does not require external LLM API keys for the core N-gram and clustering logic (Stage 1 & 2).
- The pre-seeded artifacts (`artifacts/ngram/checkpoints/`) are sufficient to initialize the model without re-training from raw data, as re-training would exceed the 6-hour CPU limit and require access to the original seed data which may not be public.
- The "evaluation" of agent performance (US-3) relies on the paper's provided result artifacts or a deterministic mock agent, as running actual proprietary LLMs (Gemini-3-Flash) is not feasible in this CI environment.
- The `pyproject.toml` dependencies are compatible with the standard Python 3.9+ environment provided by the GitHub Actions runner and do not require GPU-accelerated libraries (e.g., `torch` with CUDA).
- The domain validators (`airline.py`, etc.) are self-contained and do not require external database connections or network access to validate task coherence.
- The `tool_spec.json` files in the `artifacts/domains` directory are complete and accurate representations of the tool capabilities used in the original paper.
