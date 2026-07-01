# Feature Specification: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

**Feature Branch**: `795-opid-reproduction`  
**Created**: 2024-06-15  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning. Source: arXiv. Code vendored at external/OPID. Task is to run, validate, and reproduce end-to-end on CPU-only CI."

## User Scenarios & Testing

### User Story 1 - Verify End-to-End Execution on CPU-Only CI (Priority: P1)

A researcher or CI runner must be able to execute the vendored OPID codebase on a standard GitHub Actions free-tier runner with limited CPU resources, substantial RAM capacity, and no GPU. and observe the system complete at least one full training/evaluation cycle without hardware errors (e.g., CUDA not found, OOM).

**Why this priority**: This is the foundational "smoke test." If the code cannot run on the target infrastructure, no validation or scientific claims can be made. It validates the compute feasibility constraints immediately.

**Independent Test**: Trigger the CI job; verify the logs show successful initialization of the ALFWorld environment, generation of trajectories, and completion of the first optimization step without GPU-related exceptions.

**Acceptance Scenarios**:

1. **Given** the repository is checked out on a GitHub Actions runner with CPU-only resources, **When** the `quickstart` script is executed, **Then** the process initializes the ALFWorld environment and generates the first batch of on-policy trajectories without raising `ImportError` or `RuntimeError` related to CUDA/GPU.
2. **Given** the training loop has started, **When** the first optimization step completes, **Then** the logs explicitly record a valid loss value and the process continues to the next step rather than crashing due to memory exhaustion (RAM > 7GB) or unsupported hardware calls.

---

### User Story 2 - Validate Artifact Generation and Data Integrity (Priority: P2)

A researcher must be able to confirm that the execution produces the expected output artifacts (logs, trajectory data, model checkpoints) and that these artifacts contain valid data reflecting the OPID mechanism (e.g., skill injection, log-probability shifts).

**Why this priority**: Execution alone is insufficient; the system must produce scientifically valid artifacts that can be analyzed. This ensures the code is not just "running" but actually performing the OPID algorithm as described.

**Independent Test**: Inspect the generated output directory for specific files (e.g., `trajectory_logs.json`, `opid_metrics.csv`) and verify they contain non-empty data structures matching the expected schema (skill IDs, step-level rewards).

**Acceptance Scenarios**:

1. **Given** a completed training run, **When** the output directory is inspected, **Then** a `trajectory_logs` file exists containing at least 100 recorded steps with fields for `step_id`, `skill_type` (episode/step), and `log_prob_shift`.
2. **Given** the output metrics file, **When** the data is parsed, **Then** the "outcome advantage" and "distillation advantage" columns contain numerical values with a variance > 0, indicating the model is actually learning from the dual-advantage signal.

---

### User Story 3 - Reproduce Baseline Performance Trends (Priority: P3)

A researcher must be able to compare the OPID implementation's performance against the paper's reported baseline trends (e.g., improvement over outcome-only RL) on a small subset of tasks to confirm the algorithm behaves as hypothesized.

**Why this priority**: This validates the scientific claim. While full-scale reproduction might take too long for CI, a small-scale trend check confirms the method isn't broken or degenerate.

**Independent Test**: Run the evaluation script on a subset of ALFWorld tasks (e.g., a small number of instances) and compare the success rate against a simple "outcome-only" baseline configuration.

**Acceptance Scenarios**:

1. **Given** the evaluation script is configured for a a subset of ALFWorld tasks, **When** the OPID agent is evaluated, **Then** the success rate is recorded and logged.
2. **Given** the baseline (outcome-only) configuration is run on the same tasks, **When** the results are compared, **Then** the OPID success rate is within ±10% of the baseline (allowing for stochastic variance on small N) and does not show a catastrophic failure (e.g., < 10% success rate).

---

### Edge Cases

- **Memory Exhaustion**: What happens if the trajectory buffer grows beyond the 7 GB RAM limit? The system must implement a sampling strategy to drop old trajectories or limit buffer size to prevent OOM crashes.
- **Environment Timeout**: What happens if an ALFWorld episode exceeds the maximum step limit? The system must gracefully mark the episode as failed and record a negative reward rather than hanging indefinitely.
- **Skill Routing Failure**: What happens if the "critical-first routing" mechanism fails to identify a critical step? The system must default to episode-level skills (as per the paper's fallback logic) rather than crashing or skipping the distillation step.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the OPID training loop on CPU-only hardware without invoking any CUDA, GPU, or mixed-precision operations (See US-1).
- **FR-002**: The system MUST generate on-policy trajectories in the ALFWorld environment and record them with step-level metadata including `skill_type` and `log_prob_shift` (See US-2).
- **FR-003**: The system MUST implement the critical-first routing mechanism to select between episode-level and step-level skills, defaulting to episode-level skills when no critical step is detected (See US-2).
- **FR-004**: The system MUST compute a combined policy update advantage using both the outcome advantage and the token-level self-distillation advantage (See US-2).
- **FR-005**: The system MUST produce evaluation artifacts (success rates, logs) for at least 5 ALFWorld task instances to allow for trend comparison (See US-3).

### Key Entities

- **Trajectory**: A sequence of states, actions, and rewards generated by the agent in the ALFWorld environment, annotated with skill supervision signals.
- **Skill**: A hierarchical supervision signal (Episode-level or Step-level) extracted from completed trajectories to guide the policy.
- **Advantage**: A scalar value representing the benefit of an action, computed as a weighted sum of outcome-based and skill-based components.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The training job MUST complete at least 100 optimization steps within the Time-limited CI execution

The research question is: How does the duration of the continuous integration window impact the detection rate of concurrency bugs? The method involves running a comparative analysis of CI pipelines with varying time constraints across multiple open-source projects, as described in Smith et al. (2023) and the approach outlined in arXiv:2105.01234. on a Multi-CPU runner

The research question remains: How does the runner's performance scale with the number of CPU cores? The method involves benchmarking the runner across varying CPU configurations to assess scalability. References: [DOI/arXiv/author-year]., measured against the GitHub Actions job timeout (See US-1).
- **SC-002**: The generated trajectory logs MUST contain non-zero variance in the `log_prob_shift` column, measured against the baseline of "no change" (See US-2).
- **SC-003**: The evaluation success rate on the subset of tasks MUST be within ±10% of the baseline outcome-only RL performance, measured against the paper's reported baseline trends (See US-3).
- **SC-004**: The system MUST NOT raise any `ImportError` or `RuntimeError` related to missing GPU libraries (e.g., `torch.cuda`, `bitsandbytes`), measured against the CI error logs (See US-1).
- **SC-005**: The critical-first routing mechanism MUST fallback to episode-level skills in at least 10% of steps (estimated), measured against the total number of steps processed (See US-2).

## Assumptions

- The ALFWorld environment can be simulated entirely in CPU mode without requiring the Thor physics engine's GPU acceleration (assumed based on standard text-based ALFWorld setups).
- The dataset (ALFWorld tasks) is small enough to fit within the available disk limit. when caching layouts and logs, assuming a subset of tasks is used for the CI run.
- The vendored code in `external/OPID` is a faithful implementation of the paper and does not contain hardcoded paths to external datasets or models that are not included in the repository.
- The "critical-first routing" heuristic in the code uses a deterministic rule or a lightweight classifier that runs efficiently on CPU, avoiding the need for a heavy external skill-retrieval model.
- The GitHub Actions free-tier runner provides sufficient network bandwidth to clone the repository and download any required lightweight dependencies (e.g., `transformers`, `gym`) if not vendored.
