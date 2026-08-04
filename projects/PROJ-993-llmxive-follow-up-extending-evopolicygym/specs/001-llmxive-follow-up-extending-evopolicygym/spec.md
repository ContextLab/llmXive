# Feature Specification: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

**Feature Branch**: `001-llmxive-counterfactual-extension`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Extending EvoPolicyGym to test if counterfactual failure explanations improve robust policy discovery under dynamic shifts."

## User Scenarios & Testing

### User Story 1 - Environment Extension and Dynamic Shift Injection (Priority: P1)

The system MUST programmatically extend the 16 existing EvoPolicyGym environments to include "dynamic-shift" modes where reward functions or transition probabilities change after **50%** (default) of the total interaction budget.

**Why this priority**: Without a dynamic environment that shifts mid-task, the core hypothesis (that counterfactuals help generalization to OOD dynamics) cannot be tested. This is the foundational prerequisite for all subsequent data collection and analysis.

**Independent Test**: Can be fully tested by running a static agent on the modified environment and verifying that the environment state or reward function changes exactly at the configured step N (default N = 50% of total interaction budget), causing a measurable performance drop for non-adaptive agents.

**Acceptance Scenarios**:

1. **Given** an initialized EvoPolicyGym environment, **When** the simulation reaches 50% of the total interaction budget, **Then** the reward function or transition probabilities MUST change according to the pre-defined "shift" configuration, and the agent MUST receive a new reward signal reflecting the new dynamics.
2. **Given** an agent evolved on the static version of the environment, **When** tested on the dynamic-shift version, **Then** the system MUST detect a statistically significant performance drop (p < 0.05, one-tailed) in the non-adaptive agent's post-shift score compared to its pre-shift score, confirming the shift is impactful.

---

### User Story 2 - Counterfactual Explanation Generation Module (Priority: P2)

The system MUST implement a module that generates natural language counterfactual failure explanations for agent failures. This module must take agent trajectory logs and ground-truth environment rules as input and output a textual explanation (e.g., "You failed because X, but the environment requires Y") using a lightweight, CPU-tractable model. The output MUST be validated against a machine-readable rule schema to ensure the "explicitly state" requirement is verifiable.

**Why this priority**: This is the independent variable of the study. The quality and availability of these explanations directly determine whether the "counterfactual feedback" condition can be compared against the "scalar reward" baseline.

**Independent Test**: Can be fully tested by feeding a synthetic failure trajectory (where the ground truth is known) into the module and verifying that the output text explicitly identifies the structural flaw and the required correction without hallucinating non-existent rules, validated against the environment's JSON rule schema.

**Acceptance Scenarios**:

1. **Given** a trajectory where the agent failed due to a specific rule violation, **When** the counterfactual module processes the log, **Then** the generated text MUST explicitly state the violated rule (identified by a unique Rule ID from the environment's JSON schema) and the counterfactual action that would have succeeded, within a token limit of 200 tokens. If the output exceeds 200 tokens, the test MUST fail and the output MUST be flagged as "exceeds limit".
2. **Given** a trajectory where the agent succeeded, **When** the module processes the log, **Then** the system MUST NOT generate a failure explanation (or MUST generate a neutral "Success" indicator), ensuring no noise is introduced for successful runs.
3. **Given** a set of 100 generated explanations, **When** a separate Oracle (deterministic rule checker or human expert) validates them, **Then** ≥90% of the explanations MUST correctly identify the violated Rule ID and the required correction, ensuring the module is not tautological.

---

### User Story 3 - Evolutionary Harness and Statistical Analysis Pipeline (Priority: P3)

The system MUST execute the evolutionary agents on both the baseline (scalar reward) and the extended (counterfactual feedback) conditions, parse the resulting policy code for structural metrics (cyclomatic complexity, branch count), and perform a mixed-effects model analysis (or cluster-robust test) to compare generalization scores between the two groups, controlling for complexity as a confound.

**Why this priority**: This delivers the final research output. It connects the experimental conditions to the quantitative results required to answer the research question.

**Independent Test**: Can be fully tested by running a small-scale simulation (e.g., 5 runs per group) and verifying that the pipeline produces a CSV of metrics and a p-value from the mixed-effects model, confirming the statistical comparison logic works end-to-end.

**Acceptance Scenarios**:

1. **Given** two sets of evolved policies (one from baseline, one from counterfactual), **When** the analysis pipeline runs, **Then** it MUST calculate the cyclomatic complexity and conditional branch count for each policy using `radon` or equivalent static analysis.
2. **Given** the collected performance and complexity metrics, **When** the statistical test runs, **Then** the system MUST output a p-value and effect size comparing the two groups using a mixed-effects model (or cluster-robust standard errors) that accounts for nested runs within seeds. The result MUST be flagged as "statistically significant" only if p < 0.05 (one-tailed) AND the effect size indicates the counterfactual group performed *better* than the baseline.

---

### Edge Cases

- **What happens when** the lightweight LLM used for counterfactual generation times out or fails to produce a valid explanation? The system MUST fallback to a deterministic template-based explanation or a scalar reward for that specific step to prevent the evolutionary run from crashing.
- **How does system handle** an environment shift that is too subtle to cause a performance drop? The system MUST log a warning if the performance drop on the dynamic shift is not statistically significant (p ≥ 0.05), indicating the shift configuration may need adjustment.
- **What happens when** the evolved policy code is syntactically invalid (e.g., due to LLM hallucination)? The system MUST catch the syntax error, discard the policy, and record the failure as a "generation error" rather than a performance metric.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extend the 16 existing EvoPolicyGym environments to include a "dynamic-shift" mode that alters reward functions or transition probabilities after a configurable step N (default N = 50% of total interaction budget) (See US-1).
- **FR-002**: System MUST generate natural language counterfactual explanations for agent failures using a lightweight, CPU-tractable model, ensuring the output explicitly identifies the violated rule (by Rule ID from a JSON schema) and the required correction, and MUST validate this output against the schema (See US-2).
- **FR-003**: System MUST execute the evolutionary harness on both the baseline (scalar reward) and counterfactual conditions with fixed random seeds to ensure reproducibility (See US-3).
- **FR-004**: System MUST parse evolved policy code to calculate cyclomatic complexity and count conditional branches (if/else) using a static analysis tool like `radon`, treating these metrics as control variables rather than direct proxies for robustness (See US-3).
- **FR-005**: System MUST perform a mixed-effects model analysis (or cluster-robust test) to compare generalization scores between the baseline and counterfactual groups, accounting for nested data structures (e.g., runs within seeds), and MUST test for a positive effect size (counterfactual > baseline) (See US-3).
- **FR-006**: System MUST implement a fallback mechanism for the counterfactual generator that defaults to a template-based explanation or scalar reward if the model fails to generate valid text within 30 seconds (See US-2).

### Key Entities

- **DynamicShiftEnvironment**: An extension of the standard EvoPolicyGym environment that includes a state flag for "shifted" and logic to modify rewards/transitions at the configured step N (default [deferred]).
- **CounterfactualExplanation**: A text string generated by the LLM module, containing the failure reason (Rule ID) and the hypothetical correct action, validated against a JSON schema.
- **EvolvedPolicy**: The Python code artifact generated by the agent, which will be analyzed for structural metrics (complexity, branch count) as control variables.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in generalization performance (retention of score after dynamic shift) between the counterfactual group and the baseline group is measured against the baseline group's performance drop-off rate (See US-3).
- **SC-002**: The structural complexity (cyclomatic complexity and branch count) of policies evolved under counterfactual feedback is measured against the structural complexity of policies evolved under scalar rewards, to be used as a control variable in the statistical analysis (See US-3).
- **SC-003**: The statistical significance (p-value from mixed-effects model) of the difference in generalization metrics is measured against the standard alpha threshold of 0.05 (one-tailed), with a requirement for a positive effect size (See US-3).
- **SC-004**: The rate of successful counterfactual explanation generation (valid text output vs. total failures) is measured against the total number of agent failures encountered during evolution (See US-2).

## Assumptions

- **Assumption about compute constraints**: The analysis and LLM inference will run on a GitHub Actions free-tier runner (limited CPU cores, limited RAM, NO GPU), requiring the LLM to be a lightweight, quantized model (e.g., a model running in 4-bit/8-bit on CPU) or a local API that does not require CUDA.
- **Assumption about data availability**: The source code and environment suite for EvoPolicyGym are accessible from the provided arXiv repository and can be programmatically modified without violating license terms.
- **Assumption about threshold justification**: The interaction budget threshold for the dynamic shift is based on a standard midpoint intervention strategy to ensure sufficient data is collected both before and after the shift; a sensitivity analysis will sweep this threshold over a range of values to verify robustness.
- **Assumption about statistical power**: Given the CPU constraints, the number of evolutionary runs per group will be limited; the study will acknowledge this as a power limitation and rely on mixed-effects models or cluster-robust tests which are robust to smaller sample sizes and nested structures.
- **Assumption about measurement validity**: The `radon` tool (or equivalent) provides a valid and consistent measure of cyclomatic complexity for the Python code generated by the agents, serving as a structural control variable, NOT as a direct proxy for robustness.