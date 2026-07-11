# Feature Specification: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Feature Branch**: `001-policy-compression-tradeoff`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Foundation Protocol: A Coordination Layer for Agentic Society'"

## User Scenarios & Testing

### User Story 1 - Generate Synthetic Workflow Baselines (Priority: P1)

The system MUST generate a deterministic set of synthetic multi-agent workflows with varying delegation depths and policy complexities to serve as the ground truth for the study. This is the foundational step; without a reproducible set of workflows and their expected "full context" outcomes, no compression analysis can be performed.

**Why this priority**: This is the data generation engine. If this fails, the entire experiment has no input. It establishes the "Full Context" baseline against which all compression variants are measured.

**Independent Test**: Can be fully tested by running the generator script and verifying that the output JSON contains exactly 500 unique workflow definitions with non-zero variance in depth and complexity, and that a separate "ground truth" state machine execution log is produced for each.

**Acceptance Scenarios**:

1. **Given** a request to generate 500 workflows, **When** the generator runs, **Then** it produces 500 unique workflow IDs with varying delegation depths (range 1-20) distributed uniformly (at least 25 workflows per depth level) and policy complexities (varying numbers of constraints).
2. **Given** a generated workflow, **When** the "Full Context" baseline engine executes it, **Then** it produces a ground-truth log of all required policy nodes and identifies any policy violations against the independent Oracle Policy Engine.
3. **Given** a workflow with a specific budget cap policy, **When** the generator creates the workflow, **Then** the budget cap value is explicitly recorded in the workflow metadata for later validation.

---

### User Story 2 - Execute Compressed Context Variants (Priority: P2)

The system MUST execute the generated workflows using a "Compressed Context" variant that applies graph-traversal algorithms (BFS/DFS) to extract minimal policy subgraphs, varying the traversal depth to simulate different compression levels.

**Why this priority**: This implements the core experimental variable (compression ratio). It directly tests the hypothesis that reduced context leads to specific error patterns.

**Independent Test**: Can be fully tested by running the execution engine with a fixed compression parameter (e.g., depth=2) on a subset of workflows and verifying that the output contains a reduced token count and a log of any policy violations compared to the ground truth.

**Acceptance Scenarios**:

1. **Given** a workflow and a compression depth of 2, **When** the compressed engine executes the workflow, **Then** the transmitted policy context size is strictly less than the full context size, and the execution log records any steps where the agent lacked necessary policy data.
2. **Given** a workflow with a complex "data sovereignty" rule, **When** the compression algorithm truncates the graph before reaching the sovereignty node, **Then** the system records a specific "policy-violation" error for that step.
3. **Given** 100 runs at a specific compression level, **When** the batch completes, **Then** the system aggregates the total token usage (via standard tokenizer) and the count of policy violations for that level.

---

### User Story 3 - Analyze Trade-off and Threshold (Priority: P3)

The system MUST perform statistical analysis to model the relationship between context reduction percentage and error rate, identifying the specific "safe operating zone" where efficiency gains do not breach a target error bound.

**Why this priority**: This delivers the scientific insight (the "answer" to the research question). It transforms raw execution logs into the functional relationship curve.

**Independent Test**: Can be fully tested by feeding pre-generated execution logs (with known context reduction percentages and error counts) into the analysis module and verifying that it outputs a regression curve and a specific threshold value where error rates spike.

**Acceptance Scenarios**:

1. **Given** a dataset of 500 runs across 5 compression levels, **When** the analysis runs, **Then** it outputs a non-linear regression curve showing the functional relationship between context reduction percentage and policy-violation error rate.
2. **Given** a target error bound of ≤ 1% policy-violation error rate, **When** the analysis identifies the safe zone, **Then** it reports the maximum context reduction percentage (e.g., [deferred]) that satisfies this bound.
3. **Given** multiple hypothesis tests (comparing different depths), **When** the analysis runs, **Then** it applies a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to the p-values before declaring significance.

---

### Edge Cases

- What happens when a workflow has a policy graph that is a single node (no compression possible)? The system must handle this gracefully and record a [deferred] context reduction percentage.
- How does the system handle a compression depth of 0 (no context passed)? The system must record a [deferred] context reduction percentage and the resulting policy-violation error rate.
- What happens if the deterministic generator produces a workflow that is impossible to satisfy even with full context? The system must flag these as "invalid workflows" and exclude them from the error rate calculation to avoid skewing results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 500 synthetic multi-agent workflows with varying delegation depths (1-20) and policy complexities (1-10 constraints) using a deterministic seed to ensure reproducibility. (See US-1)
- **FR-002**: System MUST implement a "Full Context" baseline engine that executes workflows with complete policy graphs and produces a ground-truth log of required policy nodes and violations against the Oracle Policy Engine. (See US-1)
- **FR-003**: System MUST implement a "Compressed Context" engine that uses constrained BFS/DFS to extract minimal policy subgraphs based on a configurable traversal depth parameter. (See US-2)
- **FR-004**: System MUST record the total token count (calculated via standard tokenizer) and the frequency of policy-violation error rate for every execution run against the Oracle Policy Engine ground truth. (See US-2)
- **FR-005**: System MUST perform a regression analysis to model the functional relationship between context reduction percentage and policy-violation error rate, and apply a multiple-comparison correction to statistical significance tests. (See US-3)
- **FR-006**: System MUST identify and report the specific context reduction percentage threshold where the policy-violation error rate exceeds the 1% threshold, rounded to 2 decimal places. (See US-3)
- **FR-007**: System MUST execute the entire simulation and analysis pipeline on a CPU-only environment without requiring GPU acceleration or large model inference. (See US-2)
- **FR-008**: System MUST implement an independent Oracle Policy Engine that defines the ground-truth validity of workflow steps, separate from the Full Context or Compressed Context execution engines, to prevent circular validation. (See US-1)
- **FR-009**: System MUST simulate actual token usage by applying a standard tokenizer (e.g., tiktoken cl100k_base) to the policy subgraph text before counting, rather than using node count as a proxy. (See US-2)

### Key Entities

- **Workflow**: A directed graph representing a multi-agent task chain, containing nodes for agents, actions, and attached policy constraints.
- **PolicyGraph**: The full set of policy rules and provenance nodes required to validate a specific workflow step.
- **ExecutionLog**: A record of a single workflow run, containing the compression level used, token count, and a list of any policy violations detected against the Oracle Policy Engine.
- **TradeOffCurve**: The aggregated statistical model mapping context reduction percentages to policy-violation error rates.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The policy-violation error rate is measured against the ground-truth "Full Context" execution log (validated by the Oracle Policy Engine) to determine the deviation caused by compression. (See FR-004)
- **SC-002**: The token reduction percentage is measured against the baseline token count of the "Full Context" variant (calculated via standard tokenizer) to quantify efficiency gains. (See FR-004)
- **SC-003**: The statistical significance of the difference in policy-violation error rates between compression levels is measured against a corrected p-value threshold (α < 0.05 after multiplicity adjustment). (See FR-005)
- **SC-004**: The "safe operating zone" boundary is measured as the specific context reduction percentage where the policy-violation error rate first exceeds 1%, interpolated from the regression curve and verified with a 95% confidence interval via bootstrapping (1000 resamples). (See FR-006)
- **SC-005**: The total compute time for multiple runs and analysis is measured as wall-clock time on a GitHub Actions ubuntu-latest runner (including I/O and CPU overhead) against the free-tier runner time limit. (See FR-007)

## Assumptions

- The "Foundation Protocol" graph structure can be accurately simulated using a deterministic Python state machine without requiring interaction with a live agent network.
- Token usage is simulated using a standard tokenizer (e.g., tiktoken cl100k_base) to ensure accurate measurement of context size, replacing the previous node-count proxy.
- A sufficient number of synthetic workflows will be generated to achieve statistical power for detecting a non-linear threshold effect, assuming a medium effect size.
- The CPU-only environment (2 cores, ~7GB RAM) is sufficient to store the graph structures and run the simulation 500 times within 6 hours, provided no large language models are loaded.
- The Oracle Policy Engine logic is assumed to be the "correct" definition of a policy violation, and any deviation by the compressed agent is a true error, not a valid alternative interpretation.
- The relationship between context reduction percentage and policy-violation error rate is assumed to be monotonic and non-linear (diminishing returns on context removal).