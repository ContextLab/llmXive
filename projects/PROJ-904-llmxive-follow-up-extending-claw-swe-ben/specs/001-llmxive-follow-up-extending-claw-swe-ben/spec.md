# Feature Specification: llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs

**Feature Branch**: `001-context-fidelity-scaling-tradeoff`  
**Created**: 2026-08-06  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Claw-SWE-Bench to isolate context compression fidelity as a primary variable against model scaling on CPU-only hardware."

## User Scenarios & Testing

### User Story 1 - Context-Bound Task Filtering and Baseline Execution (Priority: P1)

The system must automatically ingest the Claw-SWE-Bench dataset, filter for instances where the relevant file history exceeds 500 lines to ensure context-bound complexity (determined via static analysis of the issue description), and execute a baseline run using a naive "first-N-lines" truncation strategy with a CPU-runnable 1B-parameter model.

**Why this priority**: This establishes the ground truth for the "low-fidelity context" condition and ensures the dataset actually contains the complexity required to test the research hypothesis. Without this, the experiment lacks a valid control group and appropriate data scope.

**Independent Test**: Can be fully tested by running the filtering script on the raw dataset and executing a single instance with the baseline model, verifying that the model receives only the truncated context and produces a pass/fail result against the unit tests.

**Acceptance Scenarios**:

1. **Given** the raw Claw-SWE-Bench dataset, **When** the filtering script runs, **Then** the output set contains only instances with >500 lines of relevant file history (determined by static analysis), and instances with <500 lines are excluded.
2. **Given** a filtered task instance, **When** the baseline harness runs with the 1B-parameter model, **Then** the model receives a context limited to the first N lines of the file, and the execution completes within the 60-minute runtime budget.
3. **Given** the baseline execution output, **When** the results are aggregated, **Then** the Pass@1 score and token consumption are recorded and stored for comparison.

---

### User Story 2 - High-Fidelity Context Strategy Integration (Priority: P2)

The system must implement and integrate three distinct context compression modules (TF-IDF/BM retrieval, diff-aware sliding window, and rule-based semantic summarization) and execute them against the same filtered dataset using the 1B-parameter model.

**Why this priority**: This enables the core comparison of context fidelity levels. It tests the hypothesis that high-fidelity strategies can improve performance over the naive baseline, which is the primary mechanism being investigated.

**Independent Test**: Can be fully tested by running a single high-fidelity strategy (e.g., TF-IDF) on a subset of tasks and verifying that the retrieved context differs from the baseline and that the model produces a different (ideally improved) output.

**Acceptance Scenarios**:

1. **Given** a task instance, **When** the TF-IDF/BM25 module runs, **Then** the context provided to the model contains snippets ranked by relevance to the issue description, excluding irrelevant lines.
2. **Given** a task instance, **When** the diff-aware sliding window module runs, **Then** the context prioritizes lines adjacent to predicted changes and maintains a sliding window of relevant code.
3. **Given** a task instance, **When** the semantic summarization module runs, **Then** the context contains a rule-based summary of file changes rather than raw code snippets.

---

### User Story 3 - Model Scaling Comparison and Interaction Analysis (Priority: P3)

The system must repeat the baseline and high-fidelity experiments using a larger model to quantify the performance gain from model scaling versus context optimization., and perform a Generalized Linear Model (GLM) analysis to test for interaction effects.

**Why this priority**: This addresses the "trade-off" aspect of the research question. It determines whether context optimization can substitute for model scaling by identifying if a specific strategy exists where the SLM with high-fidelity context outperforms the larger model with low-fidelity context.

**Independent Test**: Can be fully tested by running the 7B-parameter model on the baseline and high-fidelity configurations and comparing the resulting Pass@1 curves to identify if a crossover exists.

**Acceptance Scenarios**:

1. **Given** the filtered dataset, **When** the 7B-parameter model runs with the baseline strategy, **Then** the Pass@1 score is recorded and compared against the 1B-parameter baseline.
2. **Given** the full set of results (1B/7B models × 4 strategies), **When** the statistical analysis runs, **Then** a Generalized Linear Model (GLM) with a binomial link is performed to test for interaction effects between "context strategy" and "model size."
3. **Given** the GLM results, **When** post-hoc pairwise comparisons are executed, **Then** the system identifies the specific configuration where context optimization yields a higher marginal return than parameter scaling.

---

### Edge Cases

- **What happens when** the dataset contains instances where the "relevant file history" logic fails to identify any files exceeding 500 lines?
  - **Handling**: The system must log the count of excluded instances and proceed with the remaining valid set; if the valid set drops below a minimum threshold (e.g., 50 unique issue IDs), the run must fail with a "Insufficient Context-Bound Data" error.
- **How does the system handle** a context compression module that returns zero relevant snippets (e.g., TF-IDF fails to match)?
  - **Handling**: The system must fall back to the naive "first-N-lines" strategy for that specific instance to prevent execution failure, logging the fallback event for audit.
- **What happens when** the 7B-parameter model exceeds the 7GB RAM limit of the free-tier runner?
  - **Handling**: The system must detect the memory pressure and automatically switch to a more aggressive quantization level (e.g., Q4_K_M) or terminate the specific run with a "Resource Constraint" flag, ensuring the job does not hang.

## Requirements

### Functional Requirements

- **FR-001**: System MUST filter the Claw-SWE-Bench dataset to retain only instances where the relevant file history exceeds 500 lines, determined via static analysis of the issue description and dependency graphs (independent of the ground-truth patch) to ensure context-bound complexity (See US-1).
- **FR-002**: System MUST execute a baseline configuration using a naive "first-N-lines" truncation strategy with a CPU-runnable 1B-parameter model (See US-1).
- **FR-003**: System MUST implement and execute three distinct context compression modules: (a) TF-IDF/BM25 relevance retrieval, (b) diff-aware sliding window, and (c) rule-based semantic summarization defined as extracting the first sentence of each paragraph and the last sentence of each function block, concatenated with a '...' separator, limited to 512 tokens (See US-2).
- **FR-004**: System MUST repeat all baseline and high-fidelity experiments using a larger 7B-parameter model to quantify scaling effects (See US-3).
- **FR-005**: System MUST record Pass@1 success rates, total tokens consumed, and specific failure modes (e.g., missing context vs. reasoning error) for every configuration (See US-1, US-2, US-3).
- **FR-006**: System MUST perform a Generalized Linear Model (GLM) with a binomial link to test for interaction effects between "context strategy" and "model size" on Pass@1 scores (See US-3).
- **FR-007**: System MUST enforce a runtime budget of 60 minutes per instance and a total wall-clock duration of ≤72 hours for the full experiment (400 instances total) via parallel batching on the CPU-only runner (See US-1, US-2, US-3).
- **FR-008**: System MUST infer failure modes using a deterministic rule-based classifier: flag "missing context" if the output contains "file not found", "cannot locate", or references a file not in the input context; flag "reasoning error" if the file exists in context but the logic fails (See US-1, US-2, US-3).

### Key Entities

- **Task Instance**: A specific issue from Claw-SWE-Bench containing the issue description, repository state, and ground-truth unit tests.
- **Context Configuration**: A specific combination of a model size (1B or 7B) and a context strategy (Baseline, TF-IDF, Diff-Aware, Summarization).
- **Execution Result**: The outcome of a single task run, including Pass@1 status, token count, and failure classification.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Pass@1 success rates for each (Model Size, Context Strategy) configuration are measured against the ground-truth unit tests provided in the benchmark (See US-1, US-2, US-3).
- **SC-002**: Total tokens consumed per instance are measured against the token budget to calculate cost-efficiency ratios (See US-1, US-2, US-3).
- **SC-003**: Interaction effect significance (p-value) between context strategy and model size is measured against the standard alpha level using Generalized Linear Model (GLM) with a binomial link. (See US-3).
- **SC-004**: The existence of a strategy where the 1B-model outperforms the 7B-model is determined by comparing the Pass@1 rates of the 1B-model (high-fidelity) vs. the 7B-model (baseline) to identify if any strategy exists where the 1B-model's rate exceeds the 7B-model's rate by a margin of ≥5% with p < 0.05 (See US-3).
- **SC-005**: Failure mode distribution (missing context vs. reasoning error) is measured against the annotated failure logs to validate the hypothesis that context loss drives specific breakdowns (See US-1, US-2).

## Assumptions

- The Claw-SWE-Bench dataset contains sufficient instances with >500 lines of relevant history (determined by static analysis of issue text) to support statistical power for a GLM (minimum n=50 per cell is assumed; if not, the study is underpowered).
- The B-parameter model (e.g., Llama-3-1B or similar) and the 7B-parameter model (quantized to Q4_K_M or lower) can both fit within the 7GB RAM limit of the GitHub Actions free-tier runner.
- The "relevant file history" metric can be programmatically determined via static analysis of the issue description and dependency graphs without manual inspection or reliance on the ground-truth patch.
- The ground-truth unit tests in the benchmark are independent of the context compression logic, ensuring that the Pass@1 metric is a valid proxy for reasoning capacity and not an artifact of the retrieval method.
- The dataset variables (issue description, code files, test cases) are sufficient to support the analysis; the system will infer failure modes using the rules defined in FR-008.
- The "diff-aware" strategy can be implemented using standard diff libraries without requiring external LLM calls for change detection, to maintain CPU-only feasibility.