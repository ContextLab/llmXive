# Feature Specification: llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

**Feature Branch**: `001-llmxive-procedural-memory`  
**Created**: 2026-09-02  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending TUA-Bench with procedural memory retrieval for scientific workflows"

## User Scenarios & Testing

### User Story 1 - Execute Baseline Agent on Scientific Workflows (Priority: P1)

The system must execute a standard Llama 3 agent on 24 curated multi-step scientific workflow tasks from TUA-Bench using only standard in-context prompting, recording execution success rates and failure modes without any external memory assistance.

**Why this priority**: This establishes the critical baseline performance. Without a quantified failure rate for the standard agent on these specific tasks, we cannot measure the efficacy of the proposed procedural memory augmentation. It isolates the "synthesis" bottleneck.

**Independent Test**: Can be fully tested by running the baseline agent script against the 24 selected tasks and generating a JSON report of pass/fail outcomes, independent of the memory retrieval module.

**Acceptance Scenarios**:

1. **Given** the 24 multi-step scientific workflow tasks from TUA-Bench are loaded, **When** the baseline agent (Llama 3.1 8B) is executed with standard in-context prompting, **Then** the system records a binary success/fail outcome for each task and logs the specific error type (e.g., syntax error, wrong command, infinite loop) for failed tasks.
2. **Given** a completed baseline run, **When** the results are aggregated, **Then** the system outputs a baseline success rate (e.g., [deferred]) and a breakdown of failure modes to a `baseline_results.json` file.

---

### User Story 2 - Execute Augmented Agent with Procedural Memory (Priority: P2)

The system must execute the same Llama 3.1 8B agent on the same 24 tasks, but this time augmented with a retrieval step that queries a human-curated "Procedural Memory Bank" of 50 verified command sequences and appends relevant patterns to the context before action generation.

**Why this priority**: This tests the core hypothesis: that explicit scaffolding of known patterns improves performance on complex synthesis tasks. It directly addresses the research question regarding the efficacy of retrieval-augmented generation in this domain.

**Independent Test**: Can be fully tested by running the augmented agent script (with retrieval enabled) against the same 24 tasks and generating a separate JSON report, allowing for a direct statistical comparison with the baseline.

**Acceptance Scenarios**:

1. **Given** the 24 tasks and the Procedural Memory Bank (50 sequences) are loaded, **When** the augmented agent receives a task description, **Then** the system retrieves the top-k most relevant command sequences based on semantic similarity and appends them to the prompt context before the agent generates its first action.
2. **Given** the augmented agent completes execution, **When** the results are aggregated, **Then** the system outputs an augmented success rate and a comparison log showing which memory entries were retrieved for each task to `augmented_results.json`.

---

### User Story 3 - Statistical Comparison of Success Rates (Priority: P3)

The system must perform a statistical analysis (McNemar's test or paired t-test) comparing the baseline and augmented success rates to determine if the performance difference is statistically significant, while also analyzing the impact on routine vs. complex tasks.

**Why this priority**: This provides the scientific validation of the hypothesis. It moves from raw data to a defensible conclusion about the intervention's effectiveness, satisfying the research question's requirement for a "statistically significant" finding.

**Independent Test**: Can be fully tested by feeding the two result JSON files into the analysis script and verifying the output contains the test statistic, p-value, and a conclusion regarding the null hypothesis.

**Acceptance Scenarios**:

1. **Given** `baseline_results.json` and `augmented_results.json` containing paired outcomes for the 24 tasks, **When** the statistical analysis module runs, **Then** it computes a McNemar's test statistic and p-value to assess if the difference in success rates is significant (p < 0.05).
2. **Given** the analysis results, **When** the report is generated, **Then** it explicitly distinguishes performance gains on "complex multi-step" tasks versus "routine single-step" tasks, confirming the hypothesis that gains are domain-specific.

---

### Edge Cases

- What happens if the retrieval step returns zero relevant command sequences for a specific task? (System must proceed with standard prompting, logging the "miss").
- How does the system handle a task where the retrieved command sequence is syntactically correct but semantically irrelevant to the specific scientific context? (System must rely on the agent's reasoning to reject or adapt, logging this as a "false positive retrieval").
- How does the system behave if the 6-hour timeout is reached during the execution of a specific batch of tasks? (System must gracefully terminate the batch, record the partial results, and flag the timeout in the log).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load 24 specific multi-step scientific workflow tasks from the TUA-Bench dataset and exclude routine single-command tasks (See US-1).
- **FR-002**: System MUST execute a Llama 3.1 8B model on a CPU-only environment with a hard timeout of 6 hours per task batch to ensure compute feasibility (See US-1).
- **FR-003**: System MUST construct a "Procedural Memory Bank" containing exactly 50 human-verified command sequences for common shell operations (See US-2).
- **FR-004**: System MUST implement a retrieval mechanism that queries the memory bank based on task description and appends the top-k relevant sequences to the agent's context window before action generation (See US-2).
- **FR-005**: System MUST record binary success/fail outcomes and specific failure modes for every task execution in a structured JSON format for both baseline and augmented conditions (See US-1, US-2).
- **FR-006**: System MUST perform a McNemar's test (or paired t-test) on the paired success/fail outcomes to determine statistical significance of the performance difference (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) if the analysis involves testing multiple hypotheses beyond the primary success rate comparison (See US-3).

### Key Entities

- **Task**: Represents a specific scientific workflow from TUA-Bench, containing the description, expected terminal state, and validation script.
- **MemoryEntry**: Represents a single verified command sequence in the Procedural Memory Bank, containing the command string, description, and semantic embedding.
- **ExecutionResult**: Represents the outcome of a single task run, containing the task ID, success status, error message, and retrieval metadata (if augmented).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in success rates between the augmented and baseline agents is measured against the null hypothesis of no difference using a p-value threshold of < 0.05 (See US-3).
- **SC-002**: The absolute increase in success rate on complex tasks is measured against a target of +[deferred] improvement to validate the efficacy of the procedural memory (See US-2).
- **SC-003**: The false-positive rate of the retrieval mechanism (retrieving irrelevant sequences) is measured against a threshold of < 20% to ensure the memory bank does not degrade performance (See US-2).
- **SC-004**: The total compute time for the full experiment (24 tasks x 2 conditions) is measured against the 6-hour limit per batch to ensure CPU-only feasibility (See US-1).
- **SC-005**: The sensitivity of the success rate to the retrieval threshold (top-k value) is measured by sweeping k over the set {1, 3, 5} and reporting the variance in headline success rates (See US-3).

## Assumptions

- The TUA-Bench dataset contains the necessary variables (task descriptions, validation scripts) to define the 24 selected scientific workflow tasks without requiring additional data collection.
- The Llama 3.1 8B model can be loaded and executed on a standard GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) in default precision without requiring GPU acceleration or quantization.
- The 50 command sequences in the Procedural Memory Bank are sufficient to cover the common patterns required for the 24 selected tasks; if a task requires a pattern not in the bank, the system relies on the agent's base reasoning.
- The statistical power of the experiment (n=24) is sufficient to detect a moderate effect size (Cohen's d ≈ 0.5) for the primary hypothesis, acknowledging that a null result may be due to limited sample size.
- The retrieval mechanism uses a standard semantic similarity metric (e.g., cosine similarity on sentence embeddings) that is computationally lightweight enough to run on CPU within the time budget.
