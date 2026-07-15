# Feature Specification: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-AgentWorld: Language World Models for General Agents'"

## User Scenarios & Testing

### User Story 1 - Ground Truth Oracle Construction (Priority: P1)

As a researcher, I need to parse the Qwen-AgentWorld environment source code to generate a deterministic state-transition oracle so that I have a mathematically independent ground truth against which to measure LLM hallucinations.

**Why this priority**: Without a verified ground truth derived from the environment's actual logic, any comparison to LLM traces is circular or unverifiable. This is the foundational requirement for the entire study.

**Independent Test**: Can be fully tested by running the parser on a known subset of the environment code and verifying that the generated oracle produces identical state transitions as the original environment simulator for a representative set of random input sequences.

**Acceptance Scenarios**:

1. **Given** the Qwen-AgentWorld environment source code, **When** the oracle parser processes the code, **Then** it outputs a deterministic state-transition function that covers all defined interaction types (spatial, temporal, causal).
2. **Given** a stratified random sample of N=1,000 initial states and actions (uniform distribution over interaction types, seed=42), **When** the oracle function is executed, **Then** the resulting state trajectory matches the trajectory produced by the original environment simulator with ≥99.9% accuracy (allowing ≤1 discrepancy per [deferred] transitions due to floating-point tolerance).

---

### User Story 2 - Rule Extraction from Reasoning Traces (Priority: P2)

As a researcher, I need to apply an Inductive Logic Programming (ILP) or decision tree algorithm to the LLM's Chain-of-Thought (CoT) traces to extract a set of explicit, deterministic logical rules so that I can compare the "learned" logic against the ground truth.

**Why this priority**: This step transforms the unstructured, probabilistic LLM output into a structured format that can be systematically compared against the ground truth oracle. It directly addresses the "implicit logical rules" aspect of the research question.

**Independent Test**: Can be fully tested by feeding a known set of CoT traces (N=500 synthetic traces with pre-determined logical patterns) into the extraction algorithm and verifying that the output rules correctly reproduce the known patterns with ≥95% precision, citing community standard for ILP benchmarks.

**Acceptance Scenarios**:

1. **Given** a dataset of LLM CoT traces for 500 planning tasks, **When** the rule extraction algorithm processes the traces, **Then** it outputs a set of explicit transition rules (e.g., "If A and B, then C") that are syntactically valid and logically consistent.
2. **Given** a subset of traces where the LLM reasoning contains a specific logical error (hallucination), **When** the rules are extracted, **Then** the resulting rule set either fails to cover the valid transition (rule gap) or includes a transition that contradicts the ground truth (hallucination), provided the rule was logically inferable from the context.

---

### User Story 3 - Divergence Quantification and Classification (Priority: P3)

As a researcher, I need to run the extracted rules and the original LLM model on a standardized set of long-horizon tasks and classify the resulting errors into "hallucination" and "rule gap" categories to quantify where and why the probabilistic model diverges from deterministic physics.

**Why this priority**: This is the core analysis step that produces the answer to the research question. It requires the outputs of US-01 and US-02 to be operationalized and compared.

**Independent Test**: Can be fully tested by executing the comparison pipeline on a small, manually verified dataset of tasks and confirming that the error classification (hallucination vs. rule gap) matches manual human annotation with Cohen's Kappa ≥ 0.8.

**Acceptance Scenarios**:

1. **Given** the ground truth oracle, the extracted rule set, and the LLM model, **When** all three are run on 500 standardized planning tasks, **Then** the system outputs a divergence report classifying each state transition as "Match", "Hallucination", or "Rule Gap", while recording "Extraction Uncertainty" separately for transitions where the rule was not inferable.
2. **Given** a specific interaction class (e.g., spatial constraints), **When** the analysis is filtered for that class, **Then** the system calculates the divergence rate and identifies if it is statistically significantly higher than other classes (e.g., temporal) using a bootstrapped permutation test over entire trajectories (N=1,000 resamples) to account for Markovian dependencies, with α ≤ 0.05.

### Edge Cases

- **Ambiguous Reasoning**: What happens when the LLM CoT traces are ambiguous or contain contradictory reasoning within a single trace? (System MUST flag these as "Extraction Uncertainty" and exclude them from the "Rule Gap" count, reporting them separately to prevent conflation of extraction failure with model ignorance).
- **Cold Start**: How does the system handle interaction types in the environment that were never visited in the LLM traces? (System MUST report these as "Coverage Gap (Cold Start)" with [deferred] certainty, distinguishing them from "Rule Gaps" which require a logically inferable rule that the LLM failed to execute).
- **Code Drift**: What if the environment source code changes between the generation of the dataset and the oracle construction? (System MUST verify code checksums and fail if mismatched).

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse the Qwen-AgentWorld environment source code to generate a deterministic state-transition oracle that covers all defined interaction types (See US-01).
- **FR-002**: System MUST apply an ILP or decision tree induction algorithm to LLM CoT traces to extract explicit logical rules, treating the output as a "Hypothesized Rule Set" subject to "Extraction Uncertainty" (See US-02).
- **FR-003**: System MUST execute a standardized set of long-horizon planning tasks using the extracted rules, the original LLM, and the ground truth oracle simultaneously (See US-03).
- **FR-004**: System MUST classify state trajectory deviations into exactly two categories for analysis: "Hallucination" (LLM deviates from ground truth on a logically inferable rule) and "Rule Gap" (LLM fails to execute a valid ground-truth transition that is logically inferable from context). Match transitions are excluded from the deviation count. "Extraction Uncertainty" and "Coverage Gap (Cold Start)" must be recorded separately and excluded from the Hallucination/Rule Gap counts (See US-03).
- **FR-005**: System MUST perform a bootstrapped permutation test over entire trajectories (N=1,000 resamples) to determine if divergence rates differ significantly between interaction classes, accounting for trajectory dependence, with α ≤ 0.05 (See US-03).
- **FR-006**: System MUST report the boundary conditions (e.g., step count, state complexity) under which the LLM's accuracy drops below an adherence threshold of ≥95% (See US-03).

### Key Entities

- **State Transition Oracle**: A deterministic function derived from environment source code representing ground-truth physics.
- **Hypothesized Rule Set**: A set of explicit, deterministic logical rules derived from LLM CoT traces, subject to extraction uncertainty.
- **Divergence Report**: A structured output containing error classifications (Hallucination, Rule Gap, Match) and statistical significance metrics, with separate fields for Extraction Uncertainty and Coverage Gap.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The rate of "Hallucination" errors is measured against the total number of state transitions in the benchmark (excluding Extraction Uncertainty and Coverage Gap). (See FR-004).
- **SC-002**: The rate of "Rule Gap" errors is measured against the total number of valid ground-truth transitions that were logically inferable but not executed by the LLM (excluding Extraction Uncertainty and Coverage Gap). (See FR-004).
- **SC-003**: The statistical significance of divergence differences between interaction classes is measured against α ≤ 0.05 using a bootstrapped permutation test over trajectories. (See FR-005).
- **SC-004**: The accuracy drop-off boundary is measured as the step count or state complexity at which LLM adherence falls below [deferred]. (See FR-006).
- **SC-005**: The correlation between extracted rule precision and LLM CoT quality is measured using Pearson's correlation coefficient (r), with a successful correlation defined as r ≥ 0.7. (See FR-002).

## Assumptions

- The Qwen-AgentWorld dataset and environment source code are publicly accessible and remain static during the analysis period.
- The environment source code logic is mathematically independent of the LLM's generated traces. To ensure semantic independence, the analysis will filter out any LLM traces containing verbatim code snippets or documentation phrases from the environment source.
- The ILP or decision tree algorithm selected for rule extraction is CPU-tractable and can complete the induction process on the available dataset within the GitHub Actions time limit.
- A representative benchmark set of interaction tasks is designed to reflect the full distribution of interaction types in the environment.
- The ground truth oracle can be generated automatically without manual intervention or heuristic patching.
- The LLM model used for the "original model" comparison is accessible via an API or local inference engine that fits within the free-tier CPU constraints (no GPU required).
- The statistical power for the bootstrapped permutation test is sufficient with N=500 tasks to detect medium effect sizes; if not, the limitation will be explicitly noted in the final report.