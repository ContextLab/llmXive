# Feature Specification: llmXive follow-up: extending "AutoResearchClaw"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI C' - Investigating structural features of autonomous agent failure modes to determine viability of deterministic rule extraction vs. probabilistic context retrieval."

## User Scenarios & Testing

### User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1)

The researcher needs to ingest the ARC-Bench failure transcripts, annotate them with structural features (syntactic vs. semantic), and generate a deterministic rule library using a CPU-tractable small model. This is the foundational step; without the rule set, no comparison can be made.

**Why this priority**: This implements the core hypothesis: that specific failure structures can be distilled into rules. If this pipeline fails, the entire comparative study is impossible.

**Independent Test**: The pipeline can be tested by running it on a small, held-out subset of 10 known failure cases and verifying that the output is a valid JSON/YAML rule set containing "If-Condition-Then-Action" structures corresponding to the annotated features.

**Acceptance Scenarios**:

1. **Given** a CSV of 50 failure transcripts with error logs, **When** the annotation and distillation script is executed, **Then** a `rules_library.json` file is generated containing at least 45 rules mapping specific error patterns to pivot actions, including an "Unstructured" category for non-matching cases.
2. **Given** a failure transcript annotated as "syntactic error", **When** the distillation process runs, **Then** the generated rule explicitly contains a deterministic pattern match for the syntax error (e.g., regex or exact string match) rather than a probabilistic instruction.
3. **Given** a failure transcript annotated as "semantic ambiguity", **When** the distillation process runs, **Then** the generated rule reflects a probabilistic retrieval instruction or a flag indicating the rule is insufficient for deterministic resolution.

---

### User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

The researcher needs to execute the distilled rule engine on a held-out test set and compare its performance (Time-to-Pivot, Success Rate) against the full baseline agent under identical resource constraints for the rule engine, but standard resources for the baseline.

**Why this priority**: This provides the empirical data required to answer the research question. It validates whether the distilled rules actually work in practice compared to the full baseline.

**Independent Test**: The engine can be tested by running it on 10 unseen tasks and logging the "Time-to-Pivot" and binary success/failure, then comparing these metrics against a pre-recorded baseline log of the same tasks.

**Acceptance Scenarios**:

1. **Given** a held-out set of 100 experimental tasks, **When** the rule engine processes them, **Then** the system logs a "Time-to-Pivot" value (in seconds) for every task where a pivot was attempted.
2. **Given** a task where the baseline agent succeeded via multi-agent debate, **When** the rule engine attempts the same task, **Then** the system records a binary "Success" or "Failure" for the first pivot attempt.
3. **Given** a task classified as "syntactic error", **When** the rule engine runs, **Then** the average Time-to-Pivot is recorded and logged separately from tasks classified as "semantic ambiguity".

---

### User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

The researcher needs to perform mixed-effects logistic regression to determine the interaction between failure type and method, and manually inspect failed pivots to categorize them as coverage gaps or distillation errors.

**Why this priority**: This transforms raw metrics into scientific insight, distinguishing between "rules don't work" and "rules work for X but not Y."

**Independent Test**: The analysis can be tested by running the statistical script on the logged metrics and verifying that a regression model is output with coefficients for the interaction term (Failure Type * Method).

**Acceptance Scenarios**:

1. **Given** the collected metrics (Time-to-Pivot, Success Rate) and failure annotations, **When** the statistical analysis script runs, **Then** a mixed-effects logistic regression model is generated with "Task ID" as a random effect.
2. **Given** a set of failed pivots from the rule engine, **When** the error analysis script runs, **Then** the failures are categorized into "Missing Heuristic (Coverage Gap)" and "Incorrect Rule Application (Distillation Error)".
3. **Given** the regression results, **When** the report is generated, **Then** the output explicitly states whether the interaction term is statistically significant, indicating that the method's success depends on the failure type.

---

### Edge Cases

- **What happens when** the distillation model hallucinates a rule that matches a valid error log but triggers an incorrect pivot action? (Handled by the "Incorrect Rule Application" error category in US-3).
- **How does system handle** a failure transcript that does not fit any of the pre-defined structural categories (syntactic, logical, semantic)? (Handled by the "Unstructured" category in the annotation phase, which defaults to the baseline retrieval method).
- **What happens when** the CPU memory limit (7 GB) is exceeded during the baseline agent simulation? (The system must implement aggressive sampling or context truncation to stay within limits, documented as a constraint).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the ARC-Bench 25-topic subset and output a labeled dataset where each failure case is annotated with exactly one structural feature (Syntactic Error, Logical Loop, Semantic Ambiguity, Missing Context, or Unstructured) (See US-1).
- **FR-002**: System MUST utilize a CPU-tractable small language model (e.g., Llama-3-8B-INT4 or smaller) to generate a rule library from the labeled dataset, where the rule set covers ≥90% of annotated failure patterns in a [deferred] held-out validation split (See US-1).
- **FR-003**: System MUST implement a lightweight Python rule-matching engine that parses error logs and executes pivot actions without invoking a large language model or multi-agent debate (See US-2).
- **FR-004**: System MUST execute both the distilled rule engine (on 2-core CPU, ~7 GB RAM, 6-hour limit) and the full AutoResearchClaw baseline agent (on standard resources: 4 cores, 16 GB RAM) on a stratified random sample of 100 unseen tasks from the ARC-Bench 25-topic subset (See US-2).
- **FR-005**: System MUST record "Time-to-Pivot" (seconds) and "Success Rate of First Pivot" (binary) for every task, stratified by the annotated failure feature type (See US-2).
- **FR-006**: System MUST apply a mixed-effects logistic regression model to predict "Success Rate" based on "Failure Type," "Method," and their interaction, using "Task ID" as a random effect, tested on the held-out set to verify generalization (See US-3).
- **FR-007**: System MUST categorize every failed pivot from the rule engine into either "Coverage Gap" (no rule matches the error log) or "Distillation Error" (a rule matches but the executed pivot action differs from the ground-truth resolution) (See US-3).

### Key Entities

- **FailureCase**: Represents a single error event from ARC-Bench, containing raw error logs, the ground-truth resolution, and the annotated structural feature.
- **DistilledRule**: Represents a single heuristic derived from a failure case, containing a condition pattern and a prescribed pivot action.
- **PivotAttempt**: Represents a single execution instance where an agent attempts to correct an error, recording the method used, time taken, and success outcome.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in "Time-to-Pivot" between the distilled rule engine and the baseline agent is measured against the baseline's observed latency for each failure type using a paired t-test (or Wilcoxon signed-rank test if normality fails) with 95% confidence intervals (See US-2).
- **SC-002**: The "Success Rate of First Pivot" for the distilled engine is measured against the baseline agent's success rate, stratified by failure type to test the structural dichotomy hypothesis (See US-2).
- **SC-003**: The statistical significance of the interaction term (Failure Type * Method) in the mixed-effects logistic regression is measured against a standard alpha threshold, where significance is determined if the p-value < 0.05, to determine if failure structure dictates method viability (See US-3).
- **SC-004**: The proportion of failed pivots attributed to "Coverage Gap" vs. "Distillation Error" is measured against the total number of failures to determine the primary source of rule-engine limitations, using the ground-truth resolution as the arbiter (See US-3).
- **SC-005**: The total compute time and peak memory usage of the entire experiment (data processing, distillation, execution, analysis) are measured against the GitHub Actions free-tier limits (6 hours, 2 cores, 7 GB RAM) (See US-2).

## Assumptions

- The ARC-Bench dataset (25-topic subset) is accessible via the official repository linked in the *Claw AI Lab* paper and contains sufficient failure-resolution pairs for the analysis.
- The "full-mode" baseline agent can be executed on standard resources (4 cores, 16 GB RAM) without exceeding hardware limits.
- The small language model used for distillation (e.g., Llama-3-8B-INT4) will run within the 7 GB RAM limit on a 2-core CPU runner; if it exceeds this, the dataset will be sampled further to ensure feasibility.
- The structural features (syntactic vs. semantic) are mutually exclusive and can be reliably annotated with high inter-rater agreement using the defined taxonomy.
- The "Time-to-Pivot" metric is measurable within the CI environment without requiring external network latency or GPU acceleration.
- The mixed-effects logistic regression model can be fitted using standard Python libraries (e.g., `statsmodels` or `lme4` equivalent) within the 6-hour time limit for the given sample size.