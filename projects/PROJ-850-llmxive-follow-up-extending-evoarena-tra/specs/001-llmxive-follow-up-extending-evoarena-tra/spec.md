# Feature Specification: EvoMem-Conflict Filtering for Robust LLM Agents

**Feature Branch**: `001-evoconflict-filtering`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Does filtering retrieved memory traces in dynamic environments to include only 'conflict-inducing' patches significantly improve agent accuracy and reduce hallucination rates compared to retrieving all recent traces?"

## User Scenarios & Testing

### User Story 1 - Conflict-Detection Heuristic Implementation (Priority: P1)

**User Journey**: As a researcher, I need a lightweight, CPU-tractable heuristic that can ingest a sequence of state patches and a current query, and output a binary flag indicating whether a specific patch contains a semantic contradiction to the current state. This is the foundational mechanism required to differentiate "noise" from "signal" in the memory stream.

**Why this priority**: Without a functioning conflict detector, the "Conflict" agent variant cannot be constructed. This is the core innovation of the study; if this fails, the comparison against the baseline is impossible.

**Independent Test**: Can be fully tested by running the detector on a static dataset of 500 synthetic "contradiction" and "non-contradiction" pairs (e.g., "File X exists" vs. "File X deleted") generated from a predefined JSON file containing labeled examples. The test verifies a precision/recall baseline ≥ 80% against this ground truth before integration with the agent loop.

**Acceptance Scenarios**:
1. **Given** a list of memory patches where Patch A states "File X is required" and Patch B states "File X is deprecated", **When** the heuristic processes the pair, **Then** Patch B is flagged as a conflict.
2. **Given** a list of patches where Patch A states "User role is Admin" and Patch B states "User role is Admin", **When** the heuristic processes the pair, **Then** Patch B is NOT flagged as a conflict.
3. **Given** a patch containing unrelated context (e.g., "The system time is 12:00"), **When** processed against a state requiring a file path, **Then** the patch is NOT flagged as a conflict.

---

### User Story 2 - Dual-Agent Execution Pipeline (Priority: P2)

**User Journey**: As a researcher, I need an execution pipeline that instantiates two distinct agent variants (`EvoMem-All` and `EvoMem-Conflict`) and runs them on the same set of evolving terminal tasks from the `Terminal-Bench-Evo` dataset, logging their context window usage, execution time, and step-level success.

**Why this priority**: This enables the comparative analysis. It ensures that the only variable changing between runs is the memory retrieval strategy, allowing for a controlled experiment.

**Independent Test**: Can be tested by running a subset of 10 tasks on both agents and verifying that `EvoMem-All` retrieves $N$ patches while `EvoMem-Conflict` retrieves $M$ patches (where $M < N$) and that both agents produce a log entry for every task step.

**Acceptance Scenarios**:
1. **Given** a task requiring a file rollback, **When** `EvoMem-All` executes, **Then** it retrieves the last $N$ patches (including non-conflicting history).
2. **Given** the same task, **When** `EvoMem-Conflict` executes, **Then** it retrieves only the latest state and patches flagged as conflicts by the heuristic from User Story 1.
3. **Given** a completed run of 200 tasks, **When** the logs are aggregated, **Then** the system produces a CSV containing columns for `task_id`, `agent_variant`, `context_tokens`, `inference_time`, and `success_status`.

---

### User Story 3 - Statistical Comparison and Reporting (Priority: P3)

**User Journey**: As a researcher, I need a post-processing script that calculates the accuracy and hallucination rates for both agents, performs a Wilcoxon signed-rank test to determine statistical significance, and generates a report highlighting the reduction in irrelevant tokens processed.

**Why this priority**: This transforms raw execution data into the scientific result (the answer to the research question). It validates the hypothesis regarding signal-over-noise filtering.

**Independent Test**: Can be tested by feeding the script a mock CSV with known differences (e.g., Agent A success rate lower than Agent B) and verifying it outputs a p-value < 0.05 and correctly identifies the direction of the effect using the Wilcoxon signed-rank test.

**Acceptance Scenarios**:
1. **Given** the execution logs from both agents, **When** the analysis script runs, **Then** it calculates the chain-level accuracy for each agent.
2. **Given** the accuracy distributions, **When** the Wilcoxon signed-rank test is executed, **Then** the script outputs a p-value and a boolean indicating statistical significance (p < 0.05).
3. **Given** the results, **When** the report is generated, **Then** it explicitly states the percentage reduction in "memory noise" (non-conflict patches) for the `EvoMem-Conflict` agent.

---

### Edge Cases

- **What happens when the conflict detector produces no flags?** The `EvoMem-Conflict` agent must fall back to retrieving the latest state only (or a minimal context window) to ensure the agent does not run with an empty context, which would cause immediate failure.
- **How does the system handle ambiguous contradictions?** If the heuristic cannot determine a contradiction with a softmax probability score > 0.90 (90% confidence), the patch is treated as non-conflicting (conservative approach) to avoid false positives that would discard necessary context.
- **What if the dataset lacks sufficient conflicts?** If a small fraction of the 200 tasks contain detectable conflicts, the system must flag this in the final report as a dataset limitation, preventing invalid statistical conclusions.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a conflict-detection heuristic using a CPU-tractable model (e.g., a compact parameter scale) to identify semantic contradictions between memory patches and the current state. Validation MUST use a dataset of ≥ 500 labeled synthetic pairs. (See US-1)
- **FR-002**: System MUST filter the memory retrieval stream to include only the latest state and patches flagged as conflicts by FR-001 for the `EvoMem-Conflict` variant. (See US-1, US-2)
- **FR-003**: System MUST execute both `EvoMem-All` and `EvoMem-Conflict` agents on a representative set of tasks from the `Terminal-Bench-Evo` dataset. (See US-2)
- **FR-004**: System MUST log the number of retrieved patches, total context tokens, and step-level success status for every task execution. (See US-2)
- **FR-005**: System MUST perform a Wilcoxon signed-rank test on the accuracy distributions of the two agent variants to determine statistical significance. (See US-3)
- **FR-006**: System MUST calculate the "memory noise" reduction rate by comparing the average number of non-conflict patches retrieved in `EvoMem-All` vs. `EvoMem-Conflict`. (See US-3)
- **FR-007**: System MUST handle cases where the conflict detector fails or times out by defaulting to a safe retrieval mode (latest state only) to prevent agent crashes. (See US-2)
- **FR-008**: System MUST perform a sensitivity analysis on the conflict detector's performance across a range of thresholds and model sizes to validate robustness. (See US-1)

### Key Entities

- **Memory Patch**: A discrete record of a state change (e.g., file modification, rule update) containing a timestamp, content, and source instruction.
- **Conflict Flag**: A binary indicator attached to a patch by the heuristic, denoting a semantic contradiction with the current active state.
- **Agent Variant**: A configuration of the LLM agent defined by its retrieval strategy (All vs. Conflict).
- **Task Instance**: A specific terminal command sequence from the `Terminal-Bench-Evo` dataset requiring state tracking.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of `EvoMem-Conflict` is measured against the accuracy of `EvoMem-All` on the `Terminal-Bench-Evo` dataset to determine performance improvement. (See US-3)
- **SC-002**: The hallucination rate (defined as incorrect terminal command execution or state misinterpretation where the LLM's output state description matches the ground truth state description with < 90% string similarity) is measured against the baseline `EvoMem-All` variant. (See US-3)
- **SC-003**: The reduction in context window size (in tokens) is measured against the `EvoMem-All` baseline to quantify efficiency gains. (See US-3)
- **SC-004**: Statistical significance of the accuracy difference is measured against a p-value threshold of 0.05 using a Wilcoxon signed-rank test. (See US-3)
- **SC-005**: The computational feasibility is measured against the constraint of running the full multi-task experiment within a standard GitHub Actions runner time limit on 2 CPU cores. (See US-2)

## Assumptions

- The `Terminal-Bench-Evo` dataset contains a sufficient number of tasks (≥ 200) with explicit version updates and contradictions to yield statistically significant results.
- The "conflict" definition (semantic contradiction) can be reliably captured by a distilled 0.5B parameter model running on CPU without requiring GPU acceleration or 8-bit quantization. If this assumption fails, the sensitivity analysis in FR-008 will trigger a fallback to a larger model or heuristic.
- The `Terminal-Bench-Evo` dataset variables (state patches, command outcomes) are complete and sufficient for the analysis; no external data sources are required.
- The GitHub Actions free-tier runner (standard CPU allocation, sufficient RAM) is sufficient to load a medium-scale model and process a multi-task dataset within the 6-hour job limit.
- The hallucination metric is defined strictly by the failure to execute the correct terminal command or the production of an incorrect state description (with < 90% string similarity to ground truth), independent of the memory retrieval mechanism.
- The conflict detection heuristic is deterministic for a given input, ensuring reproducible results across the two agent variants.
- A power analysis will be conducted to justify an adequate sample size for the Wilcoxon signed-rank test.