# Feature Specification: llmXive Follow-up: Trace Compressibility Analysis

**Feature Branch**: `001-trace-compressibility`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "What structural properties of multi-turn tool-execution traces determine their compressibility into symbolic rules without degrading the fidelity of persona-aligned agent behavior?"

## User Scenarios & Testing

### User Story 1 - Synthetic Trace Generation (Priority: P1)

The system must generate a synthetic dataset of multi-turn revision sessions based on the MemSlides benchmark schema, recording tool-execution traces and resulting slide states. This is the foundational data source required for all subsequent analysis.

**Why this priority**: Without a consistent, high-volume dataset of execution traces, no structural metrics can be computed, and no compression models can be trained. This is the prerequisite for the entire research pipeline.

**Independent Test**: Can be fully tested by verifying the generation of a substantial set of unique session files where each file contains a valid sequence of tool calls and a corresponding ground-truth slide state.

**Acceptance Scenarios**:

1. **Given** the MemSlides benchmark schema is loaded, **When** the generation script runs, **Then** a dataset of [deferred] distinct multi-turn revision sessions is created in the output directory.
2. **Given** a generated session, **When** the trace is parsed, **Then** it contains valid tool-execution steps (e.g., `insert_chart`, `format_text`) and a valid final slide state representation.
3. **Given** the generated dataset, **When** a random sample is inspected, **Then** the sequence entropy and tool-repetition frequencies vary across sessions, ensuring dataset diversity.

---

### User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

The system must compute structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance) for each trace and train a lightweight, CPU-based rule-induction model (e.g., Decision Tree or RuleFit) to learn symbolic rules from these traces. The definition of "compressibility" is operationalized as the ability of the induced rules to reproduce the final slide state of the trace within a defined fidelity tolerance.

**Why this priority**: This step operationalizes the core research question by transforming raw traces into quantifiable predictors and a compressed symbolic representation. It is the primary mechanism for testing the "compressibility" hypothesis.

**Independent Test**: Can be fully tested by running the extraction and induction pipeline on a subset of the data and verifying that the output includes a computed feature matrix and a trained model file with non-zero accuracy on a hold-out validation split.

**Acceptance Scenarios**:

1. **Given** a set of generated traces, **When** the feature extraction module runs, **Then** a CSV file is produced containing the structural metrics (entropy, repetition, variance) for each trace.
2. **Given** the feature matrix and ground-truth actions, **When** the rule-induction model is trained, **Then** the resulting model file is generated and can be loaded without errors.
3. **Given** a new, unseen trace, **When** the trained model predicts the rule, **Then** the output is a compact set of symbolic rules (e.g., `IF tool==insert_chart AND arg_variance<0.2 THEN rule=chart_insertion`) that, when executed, reproduce the final slide state within the defined fidelity tolerance.

---

### User Story 3 - Fidelity & Latency Benchmarking (Priority: P3)

The system must replace the raw memory module in the reference agent with the generated symbolic rule bank and compare the Edit Accuracy and Retrieval Latency against the original baseline on a held-out test set.

**Why this priority**: This step provides the empirical evidence required to answer the research question. It measures the trade-off between compression and behavioral fidelity, determining if structural properties predict successful compression.

**Independent Test**: Can be fully tested by executing the benchmark script on a held-out set of requests and verifying that the output includes a comparative report of Edit Accuracy and Retrieval Latency for both the baseline and compressed agents.

**Acceptance Scenarios**:

1. **Given** the original agent and the compressed agent, **When** both process the same [deferred] held-out revision requests, **Then** the system outputs a JSON report containing the Edit Accuracy for both systems.
2. **Given** the same [deferred] held-out requests, **When** the retrieval latency is measured, **Then** the system reports the mean latency for the baseline vs. the compressed agent.
3. **Given** the comparative results, **When** the statistical analysis runs (as defined in FR-006), **Then** a regression output is generated indicating which structural metrics significantly correlate with the Edit Accuracy difference between the baseline and compressed agents.

### Edge Cases

- What happens when a generated trace has zero tool repetitions (high entropy)? The system must handle this without crashing and record it as a data point with high complexity.
- How does the system handle a trace where the argument semantic variance is undefined (e.g., empty arguments)? The system must impute a default value or exclude the trace with a warning log.
- What happens if the rule-induction model achieves [deferred] compression but [deferred] fidelity? The system must still report these metrics accurately to support the "null result" hypothesis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate [deferred] synthetic multi-turn revision sessions using the MemSlides schema, ensuring variation in sequence length and tool types (See US-1).
- **FR-002**: System MUST compute sequence entropy, tool-repetition frequency, and argument semantic variance for every generated trace (See US-2).
- **FR-003**: System MUST train a CPU-tractable rule-induction model (e.g., Decision Tree, RuleFit) on the extracted features to produce a compact symbolic rule set that reproduces the final slide state within a defined fidelity tolerance (See US-2).
- **FR-004**: System MUST execute both the baseline agent (raw memory) and the compressed agent (symbolic rules) on a held-out test set of [deferred] revision requests (See US-3).
- **FR-005**: System MUST calculate and report Edit Accuracy (fraction of edits matching ground truth) and Retrieval Latency (time to context-ready) for both agents (See US-3).
- **FR-006**: System MUST apply Beta regression, logistic regression, or non-parametric Spearman correlation to correlate structural metrics with the Edit Accuracy difference measured on a held-out test set independent of the model training data (See US-3).
- **FR-007**: System MUST implement a sensitivity analysis sweeping the compression threshold over a set of representative thresholds to report how fidelity rates vary (See US-3).

### Key Entities

- **Execution Trace**: A sequence of tool calls and arguments representing a single interaction session.
- **Structural Metrics**: Quantitative descriptors of a trace (entropy, repetition, variance).
- **Symbolic Rule Bank**: A compact set of IF-THEN rules derived from traces.
- **Edit Accuracy**: The fraction of agent-generated edits that match the ground-truth instruction.
- **Retrieval Latency**: The time elapsed between an instruction and the agent having the necessary context.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between structural metrics (predictors) and Edit Accuracy difference (outcome) is measured against the results of the Beta regression or non-parametric analysis on a held-out test set (See FR-006, US-3).
- **SC-002**: The trade-off between compression ratio and fidelity loss is measured against the baseline agent's performance on the held-out test set (See FR-005, US-3).
- **SC-003**: The stability of fidelity rates under threshold variation is measured against the sensitivity analysis sweep (See FR-007, US-3).
- **SC-004**: The computational feasibility of the analysis is measured against the resource constraints of the target CI runner (See Methodology).

## Assumptions

- **Assumption about data synthesis**: The synthetic dataset generator can produce [deferred] sessions that statistically mimic the distribution of real-world multi-turn tool usage without requiring access to a private production database.
- **Assumption about computational resources**: The rule-induction model (Decision Tree/RuleFit) and the statistical analysis will complete within the time and memory limits of the target CI runner, as these methods are known to be CPU-tractable for this dataset size.
- **Assumption about baseline availability**: A reference implementation of the MemSlides agent (or a functional equivalent) is available in the codebase to serve as the "raw memory" baseline for comparison.
- **Assumption about metric validity**: The computed structural metrics (entropy, repetition, variance) are sufficient proxies for the "structural properties" of interest in the research question, and no additional unmeasured latent variables are required.
- **Assumption about ground truth**: The "ground-truth" slide states required for calculating Edit Accuracy can be deterministically generated or derived from the synthetic session definitions.