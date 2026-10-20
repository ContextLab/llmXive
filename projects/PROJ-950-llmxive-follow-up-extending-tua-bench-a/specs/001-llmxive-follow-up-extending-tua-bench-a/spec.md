# Feature Specification: llmXive follow-up: extending "TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents"

**Feature Branch**: `001-llmxive-procedural-memory`  
**Created**: 2026-09-02  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending TUA-Bench with procedural memory retrieval for scientific workflows"

## User Scenarios & Testing

### User Story 1 - Execute Baseline Agent on Scientific Workflows (Priority: P1)

The system must execute a standard **Llama 3.1 8B** agent on 24 curated multi-step scientific workflow tasks from TUA-Bench using only standard in-context prompting, recording execution success rates and failure modes without any external memory assistance.

**Why this priority**: This establishes the critical baseline performance. Without a quantified failure rate for the standard agent on these specific tasks, we cannot measure the efficacy of the proposed procedural memory augmentation. It isolates the "synthesis" bottleneck.

**Independent Test**: Can be fully tested by running the baseline agent script against the 24 selected tasks and generating a JSON report of pass/fail outcomes for each seed, independent of the memory retrieval module.

**Acceptance Scenarios**:

1. **Given** the 24 tasks (12 complex multi-step + 12 routine single-command) from TUA-Bench are loaded, **When** the baseline agent (Llama 3.1 8B) is executed with standard in-context prompting for a single random seed, **Then** the system records a binary success/fail outcome for each task and logs the specific error type (e.g., syntax error, wrong command, infinite loop) for failed tasks.
2. **Given** a completed baseline run for a seed, **When** the results are aggregated across the five independent seeds, **Then** the system outputs a baseline success rate (average proportion of successful runs) and a breakdown of failure modes to a `baseline_results.json` file.

---

### User Story 2 - Execute Augmented Agent with Procedural Memory (Priority: P2)

The system must execute the same Llama 3.1 8B agent on the same 24 tasks, but this time augmented with a retrieval step that queries a human-curated "Procedural Memory Bank" of 50 verified command sequences and appends relevant patterns to the context before action generation.

**Why this priority**: This tests the core hypothesis: that explicit scaffolding of known patterns improves performance on complex synthesis tasks. It directly addresses the research question regarding the efficacy of retrieval-augmented generation in this domain.

**Independent Test**: Can be fully tested by running the augmented agent script (with retrieval enabled) against the same 24 tasks for each of the five seeds and generating a separate JSON report, allowing for a direct statistical comparison with the baseline.

**Acceptance Scenarios**:

1. **Given** the 24 tasks and the Procedural Memory Bank (50 sequences) are loaded, **When** the augmented agent receives a task description, **Then** the system retrieves the top‑k most relevant command sequences based on semantic similarity and appends them to the prompt context before the agent generates its first action. If the retrieval returns zero hits, the system proceeds with standard prompting and logs a “retrieval miss” event.
2. **Given** the augmented agent completes execution for a seed, **When** the results are aggregated across the five seeds, **Then** the system outputs an augmented success rate and a comparison log showing which memory entries were retrieved for each task to `augmented_results.json`.

---

### User Story 3 - Statistical Comparison of Success Rates (Priority: P3)

The system must perform a statistical analysis comparing the baseline and augmented success rates to determine if the performance difference is statistically significant, while also analyzing the impact on routine vs. complex tasks.

**Why this priority**: This provides the scientific validation of the hypothesis. It moves from raw data to a defensible conclusion about the intervention's effectiveness, satisfying the research question's requirement for a "statistically significant" finding.

**Independent Test**: Can be fully tested by feeding the two result JSON files into the analysis script and verifying the output contains the test statistic, p‑value, and a conclusion regarding the null hypothesis.

**Acceptance Scenarios**:

1. **Given** `baseline_results.json` and `augmented_results.json` containing paired outcomes for the 24 tasks across five seeds, **When** the statistical analysis module runs, **Then** it computes McNemar’s exact test statistic and p‑value to assess if the difference in success rates is significant (p < 0.05). A paired t‑test may be reported as a secondary exploratory analysis.
2. **Given** the analysis results, **When** the report is generated, **Then** it explicitly distinguishes performance gains on "complex multi-step" tasks versus "routine single-step" tasks, confirming the hypothesis that gains are domain‑specific (targeted ≥ 10 % improvement on complex tasks and ≤ 5 % improvement on routine tasks).

---

### Edge Cases

- What happens if the retrieval step returns zero relevant command sequences for a specific task? (System proceeds with standard prompting and logs the “retrieval miss”.)
- How does the system handle a task where the retrieved command sequence is syntactically correct but semantically irrelevant to the specific scientific context? (System must rely on the agent's reasoning to reject or adapt, logging this as a “false positive retrieval”.)
- How does the system behave if the 6‑hour timeout is reached during the execution of a specific batch of tasks? (System gracefully terminates the batch, records partial results, and flags the timeout in the log.)

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a set of 24 tasks comprising **12 complex multi-step scientific workflow tasks** and **12 routine single‑command tasks** from the TUA‑Bench dataset (See US-1).
- **FR-002**: System MUST execute the Llama 3.1 8B model on a CPU‑only environment with a hard per‑task timeout of **15 minutes** and a hard per‑batch timeout of **6 hours** (where a batch is the 24 tasks for a single condition and a single random seed) to ensure compute feasibility (See US-1).
- **FR-003**: System MUST construct a "Procedural Memory Bank" containing exactly 50 human‑verified command sequences for common shell operations (See US-2).
- **FR-004**: System MUST implement a retrieval mechanism that queries the memory bank based on task description and appends the top‑k relevant sequences to the agent's context window before action generation. If the retrieval returns zero hits, the system proceeds with standard prompting and logs a “retrieval miss” event (See US-2).
- **FR-005**: System MUST record binary success/fail outcomes and specific failure modes for every task execution in a structured JSON format for both baseline and augmented conditions (See US-1, US-2).
- **FR-006**: System MUST perform McNemar’s exact test on the paired binary outcomes to assess statistical significance of the primary success‑rate difference (p < 0.05). As a secondary analysis, a paired t‑test may be reported for exploratory purposes (See US-3).
- **FR-007**: System MUST apply Holm‑Bonferroni correction across all hypothesis tests performed, including the k‑sweep sensitivity analyses (primary k = 3 designated a priori) (See US-3).
- **FR-008**: System MUST run each task‑condition pair **five independent times** using distinct random seeds, record each run’s binary outcome, and aggregate results as the proportion of successful runs per task (See US-1, US-2).
- **FR-009**: System MUST gracefully terminate a batch when the 6‑hour batch timeout is reached, record partial results obtained up to that point, and flag the timeout event in the log file (See US-1).
- **FR-010**: System MUST maintain a ground‑truth relevance mapping between each task and MemoryEntry; a retrieval is considered a false‑positive if the retrieved entry is not marked relevant for that task (See US-2).
- **FR-011**: System MUST record the false‑positive retrieval rate as the number of false‑positive retrievals divided by total retrievals, using the ground‑truth relevance mapping (See SC-003).
- **FR-012**: System MUST support configurable top‑k retrieval values; for the sensitivity analysis (SC-005) the experiment will run three augmented conditions with k = 1, 3, 5, each respecting the per‑batch timeout (See SC-005).

### Key Entities

- **Task**: Represents a specific scientific workflow from TUA‑Bench, containing the description, expected terminal state, and validation script.
- **MemoryEntry**: Represents a single verified command sequence in the Procedural Memory Bank, containing the command string, description, and semantic embedding.
- **ExecutionResult**: Represents the outcome of a single task run, containing the task ID, success status, error message, and retrieval metadata (if augmented).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in success rates between the augmented and baseline agents is measured against the null hypothesis of no difference using a p‑value threshold of **< 0.05** (See US-3).
- **SC-002**: The absolute increase in success rate on **complex** tasks must be at least **+[deferred]**; the increase on **routine** tasks must not exceed **+[deferred]**, validating domain‑specific efficacy (See US-2, US-3).
- **SC-003**: The false‑positive rate of the retrieval mechanism (retrieving entries not marked relevant in the ground‑truth map) is measured against a threshold of **< 20 %** (See FR-010, FR-011).
- **SC-004**: The total compute time per batch (24 tasks for a single condition and a single seed) must not exceed **6 hours**; the overall experiment across five seeds may use up to **30 hours** total, which is acceptable for the CPU‑only environment (See US-1).
- **SC-005**: The sensitivity of the success rate to the retrieval threshold (top‑k value) is measured by sweeping k over the set **{1, 3, 5}** and reporting the variance in headline success rates. The primary k = 3 is designated a priori; Holm‑Bonferroni correction is applied across the three k‑conditions (See FR-012, FR-007).

## Assumptions

- The TUA‑Bench dataset contains the necessary variables (task descriptions, validation scripts) to define the 24 selected scientific workflow tasks without requiring additional data collection.
- The Llama 3.1 8B model can be loaded and executed on a standard GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM) in default precision without requiring GPU acceleration or quantization.
- The 50 command sequences in the Procedural Memory Bank are sufficient to cover the common patterns required for the 24 selected tasks; if a task requires a pattern not in the bank, the system relies on the agent's base reasoning.
- The statistical power of the experiment (n = 24 tasks × 5 seeds) is sufficient to detect a moderate effect size for the primary McNemar’s test, assuming a discordant‑pair rate of at least 8.
- The retrieval mechanism uses a standard semantic similarity metric (e.g., cosine similarity on sentence embeddings) that is computationally lightweight enough to run on CPU within the time budget.
