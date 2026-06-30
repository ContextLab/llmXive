# Feature Specification: $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

**Feature Branch**: `001-bench-evaluating-proactive-personal-assi`  
**Created**: 2026-05-27  
**Status**: Draft  
**Input**: User description: "$π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows"

## User Scenarios & Testing

### User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1)

The system MUST successfully execute the vendored `Pi-Bench` codebase on a standard CPU-only CI runner, initializing the mock environment, loading a set of multi-turn tasks across 5 personas, and running the evaluation loop to completion without crashing or requiring GPU resources.

**Why this priority**: This is the foundational requirement. Without a successful execution of the existing code, no validation or reproduction of the paper's claims can occur. It verifies the "fit the box" constraint (CPU, 7GB RAM) immediately.

**Independent Test**: Trigger the `quickstart` runbook. The CI job must finish with exit code 0 and produce the `results/` directory containing JSON artifacts for at least one persona (e.g., `Financier`) before the 6-hour job timeout.

**Acceptance Scenarios**:

1. **Given** the `Pi-Bench` submodule is checked out and the The CI runner is equipped with multiple CPU cores and 7GB RAM., **When** the `main.py` entry point is invoked with the `Financier` persona configuration, **Then** the script completes within 6 hours and generates valid JSON result files in `results/Financier/`.
2. **Given** the runner has no GPU available, **When** the evaluation script attempts to load any model configuration, **Then** it defaults to CPU execution (no CUDA errors) and proceeds without requiring `load_in_8bit` or mixed-precision flags.
3. **Given** a fresh CI environment, **When** the `test_server.py` and `docker_launcher.py` components are initialized, **Then** the mock environment starts successfully, and the agent loop processes at least 10 tasks without memory exhaustion (OOM) errors.

---

### User Story 2 - Validate Proactivity Metrics and Distinguish from Retrieval (Priority: P2)

The system MUST compute and report the specific metrics defined in the paper (Proactivity Score, Task Completion Rate) and explicitly calculate a "retrieval entropy" or "action novelty" metric to address the concern that proactivity might be mere complex retrieval, as flagged by the Turing-simulated reviewer.

**Why this priority**: This addresses the core scientific contribution of the paper and the specific methodological objection raised. It ensures the reproduction isn't just a "run script" but a valid scientific validation.

**Independent Test**: Analyze the generated `results/` JSON files. The output must contain a `proactivity_score` field and a `action_entropy` or `novelty_index` field. The system must be able to filter tasks where the agent's action sequence matches a known trajectory vs. a novel one.

**Acceptance Scenarios**:

1. **Given** a completed evaluation run for the `law_trainee` persona, **When** the results are aggregated, **Then** the report includes a `proactivity_score` and a `task_completion_rate` for each of the 20 tasks.
2. **Given** a specific task where the agent performs a hidden-intent action, **When** the trace is analyzed, **Then** the system flags the action as "proactive" only if the action sequence deviates from the baseline retrieval path by a defined threshold (e.g., Levenshtein distance > 0.2 or unique token ratio > 0.1).
3. **Given** the full dataset of 100 tasks, **When** the aggregate metrics are calculated, **Then** the report explicitly distinguishes between "Task Completion" (binary success) and "Proactivity" (anticipation of unstated needs), showing they are not perfectly correlated.

---

### User Story 3 - Reproduce Comparative Baseline Results (Priority: P3)

The system MUST reproduce the comparative analysis between different LLM backends (e.g., MiniMax, Claude, DeepSeek) as presented in the paper, generating a table of results that allows for a direct comparison of the "proactive" vs. "reactive" performance across models.

**Why this priority**: This validates the paper's empirical claims about which models handle long-horizon workflows better, providing the "real artifacts" required for the research phase.

**Independent Test**: Run the evaluation with at least two distinct model configurations (e.g., `MiniMax-M2.5` and `claude-haiku-4-5-20251001`) and generate a comparative report. The report must show statistically distinguishable differences (or lack thereof) in the proactivity scores.

**Acceptance Scenarios**:

1. **Given** two different model configuration YAMLs, **When** the evaluation is run on the same set of `marketer` tasks, **Then** the output includes a comparative table showing `proactivity_score` and `completion_rate` for both models.
2. **Given** the full set of 5 personas, **When** the results are aggregated, **Then** the system produces a summary figure (or data table ready for plotting) showing the performance gap between models on "hidden intent" tasks vs. "explicit instruction" tasks.
3. **Given** the requirement for reproducibility, **When** the run is repeated with the same seed and configuration, **Then** the `proactivity_score` variance is within ±0.05, confirming the stability of the metric.

---

### Edge Cases

- **What happens when** the mock environment fails to simulate a specific API (e.g., Amazon or Gmail) due to a schema mismatch in the `task.yaml`? The system MUST log the error, mark the task as "Environment Failure" (not "Agent Failure"), and exclude it from the proactivity metric calculation to avoid skewing results.
- **How does the system handle** a model that times out on a long-horizon task (>10 turns)? The system MUST record a `timeout` flag, treat the task as a failure for `completion_rate`, and set `proactivity_score` to 0.0 for that specific trajectory, rather than crashing the entire batch.
- **What happens when** the "hidden intent" in a task is ambiguous in the `task.yaml`? The system MUST default to the explicit instructions provided in the `profile.yaml` and flag the task in the results as "Ambiguous Intent" for manual review, rather than guessing the intent.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `Pi-Bench` evaluation loop for all personas across diverse profiles. (Financier, Law Trainee, Marketer, Pharmacist, and one additional) using the provided `task.yaml` and `profile.yaml` files without requiring manual intervention. (See US-1)
- **FR-002**: System MUST compute a `proactivity_score` for each task trajectory by comparing the agent's action sequence against a baseline "explicit-only" trajectory, penalizing high-entropy retrieval paths that lack causal structure. (See US-2)
- **FR-003**: System MUST support CPU-only execution of all configured LLM models, ensuring no CUDA/GPU dependencies are triggered, and defaulting to standard precision floating point operations. (See US-1)
- **FR-004**: System MUST generate a structured JSON artifact for each task containing `task_id`, `model_id`, `completion_status`, `proactivity_score`, `action_trace`, and `latency_ms`. (See US-2)
- **FR-005**: System MUST implement a "novelty check" that flags actions as "retrieval" vs. "planning" based on the deviation from known task templates, addressing the concern that proactivity is merely complex retrieval. (See US-2)
- **FR-006**: System MUST aggregate results across all tasks to produce a summary report comparing `task_completion_rate` and `proactivity_score` across different model backends. (See US-3)
- **FR-007**: System MUST handle environment errors (e.g., API simulation failures) by logging them and excluding affected tasks from the final metric calculation, rather than failing the entire run. (See Edge Cases)

### Key Entities

- **Task**: A single unit of work defined by a `task.yaml` file, containing explicit instructions, hidden intents, and expected outcomes for a specific persona.
- **Trajectory**: The sequence of actions, observations, and thoughts generated by an agent while attempting a Task.
- **Persona**: A user profile (e.g., Financier) defining the context, skills, and typical hidden needs for a set of tasks.
- **Proactivity Metric**: A calculated score (0.0–1.0) representing the degree to which an agent anticipated and acted on unstated user needs, distinct from simple task completion.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The `proactivity_score` distribution is measured against the baseline "explicit-only" trajectory to quantify the agent's ability to anticipate hidden intents. (See US-2)
- **SC-002**: The `task_completion_rate` is measured against the paper's reported baseline for each model to validate the reproduction of the original findings. (See US-3)
- **SC-003**: The `action_entropy` (or novelty index) is measured against a threshold (e.g., 0.2) to distinguish between "planning" and "retrieval" behaviors, addressing the Turing-simulated reviewer's concern. (See US-2)
- **SC-004**: The total runtime for the full 100-task evaluation is measured against the 6-hour CI job limit to ensure compute feasibility on free-tier runners. (See US-1)
- **SC-005**: The memory usage peak is measured against the 7GB RAM limit to confirm the system fits within the "fit the box" constraint. (See US-1)

## Assumptions

- The vendored `Pi-Bench` codebase at `external/Pi-Bench/` is functionally complete and does not require external API keys for the mock environment (e.g., Gmail, Amazon) to simulate task execution.
- The "hidden intents" defined in the `task.yaml` files are unambiguous and sufficient for the evaluation logic to distinguish between proactive and reactive behavior without manual intervention.
- The CPU-only execution of the selected LLM models (via the provided YAML configs) will complete within the 6-hour CI timeout, even for the longest-horizon tasks, provided the batch size is limited to 1 task per run or small batches.
- The `proactivity_score` calculation logic implemented in the codebase aligns with the paper's definition (anticipation of unstated needs) and does not require re-implementation of the metric from scratch.
- The mock environment (simulated APIs) provides deterministic responses for the same input, ensuring that repeated runs produce consistent results for the purpose of validation.
