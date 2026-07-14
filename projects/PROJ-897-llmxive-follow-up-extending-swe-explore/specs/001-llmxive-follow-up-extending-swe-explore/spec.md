# Feature Specification: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Feature Branch**: `001-iterative-exploration-benchmark`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does an iterative, feedback-driven exploration strategy yield higher line-level coverage and repair success on ambiguous or unsolvable issues compared to the static, one-shot exploration evaluated in the original SWE-Explore benchmark?"

## User Scenarios & Testing

### User Story 1 - Data Curation and Hard Instance Selection (Priority: P1)

The researcher must be able to download the SWE-Explore dataset, filter for the bottom [deferred] of issues based on initial coverage scores to identify "hard" instances, and generate a set of synthetic ambiguous issues by mutating variable names, removing comments, and applying structural obfuscations. This forms the foundational dataset for the comparative study.

**Why this priority**: Without a curated, reproducible set of "hard" and synthetic ambiguous issues, the comparative analysis between static and iterative strategies cannot proceed. This is the prerequisite for all downstream agent execution and metric calculation.

**Independent Test**: The system can be tested by verifying the existence of the curated dataset subset and confirming the synthetic mutation logic produces valid, ambiguous code instances that differ from the originals but retain structural validity.

**Acceptance Scenarios**:

1. **Given** the full SWE-Explore dataset is downloaded, **When** the system filters for the bottom [deferred] of initial coverage scores, **Then** a subset of "hard" instances is produced with a count matching 20% of the total.
2. **Given** a set of solvable tasks, **When** the system mutates variable names, removes comments, and applies structural obfuscations, **Then** 50 synthetic ambiguous issues are generated that are syntactically valid but semantically obscured.
3. **Given** the curated dataset, **When** a researcher inspects the synthetic issues, **Then** the issues must be verifiable as ambiguous versions of the original tasks without introducing syntax errors that prevent parsing.

---

### User Story 2 - Iterative Agent Execution Loop (Priority: P2)

The researcher must be able to execute a multi-turn exploration loop using a lightweight, CPU-tractable LLM wrapper. The agent must accept a query, retrieve top-k code regions, perform static analysis (via `pylint` or `ast`), detect errors/missing dependencies, and reformulate the query based on these signals, limited to a maximum of 3 turns per issue.

**Why this priority**: This implements the core experimental condition (iterative feedback) being tested. It directly addresses the research question regarding the efficacy of dynamic adaptation versus static retrieval.

**Independent Test**: The system can be tested by running a single "hard" issue through the iterative loop and verifying that the agent performs exactly 3 turns (or terminates early if a solution is found), producing a sequence of reformulated queries and static analysis logs.

**Acceptance Scenarios**:

1. **Given** a "hard" issue from the curated dataset, **When** the iterative agent is invoked, **Then** the agent performs up to 3 exploration turns, updating its context based on static analysis feedback after each turn.
2. **Given** a static analysis error is detected in turn 1, **When** the agent reformulates the query for turn 2, **Then** the new query string must contain the exact error message text from the previous turn (e.g., "missing import" or "undefined variable").
3. **Given** the 3-turn limit is reached, **When** the agent finishes, **Then** the system must output the final retrieved context and a log of all reformulated queries for auditability.

---

### User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

The researcher must be able to compute line-level coverage and ranking efficiency for both the iterative and static baselines on the paired issues, and apply the Wilcoxon signed-rank test (or exact permutation test if ties dominate) to determine statistical significance (p < 0.05) of the difference.

**Why this priority**: This delivers the final scientific result. Without the statistical comparison, the execution of the agents yields only raw data, not the empirical evidence required to answer the research question.

**Independent Test**: The system can be tested by providing pre-computed coverage metrics for both agents on a small test set and verifying the statistical test returns a p-value and a clear conclusion (significant vs. non-significant) at the 0.05 threshold.

**Acceptance Scenarios**:

1. **Given** coverage metrics for the iterative and static agents on the same set of issues, **When** the statistical test is run, **Then** the Wilcoxon signed-rank test is applied to the paired differences, or an exact permutation test is used if ties exceed a non-negligible proportion of the data.
2. **Given** a p-value of 0.03, **When** the result is evaluated against the threshold, **Then** the system reports a statistically significant improvement for the iterative agent.
3. **Given** a p-value of 0.15, **When** the result is evaluated, **Then** the system reports no statistically significant difference between the two strategies.

### Edge Cases

- What happens when a synthetic ambiguous issue becomes unsolvable due to over-mutation (syntax errors preventing parsing)? The system must skip the issue and log a warning rather than crashing the entire batch.
- How does the system handle a static analysis tool (e.g., `pylint`) returning no output or an unexpected error? The agent must treat this as a neutral signal and proceed to the next turn or terminate if the limit is reached, logging the anomaly.
- What if the 3-turn limit is reached but the agent is in a loop (repeating the same query)? The system must detect repeated queries and terminate the loop early, recording the reason for termination.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the SWE-Explore dataset and filter for the bottom [deferred] of initial coverage scores to identify "hard" instances (See US-1).
- **FR-002**: System MUST generate 50 synthetic ambiguous issues by mutating variable names, removing comments, and applying structural obfuscations in a subset of solvable tasks (See US-1).
- **FR-003**: System MUST implement a multi-turn exploration loop that limits execution to a maximum of 3 turns per issue to ensure CPU feasibility (See US-2).
- **FR-004**: System MUST integrate a static analysis tool (e.g., `pylint` or `ast`) to detect errors and missing dependencies after each retrieval turn (See US-2).
- **FR-005**: System MUST compute line-level coverage (percentage of ground-truth relevant lines retrieved) and ranking efficiency (position of the first relevant line) for both iterative and static runs (See US-3).
- **FR-006**: System MUST apply the Wilcoxon signed-rank test to compare coverage and efficiency metrics between the iterative and static approaches on paired issues; if ties exceed a substantial proportion of the data, the system MUST use an exact permutation test or apply a continuity correction (See US-3).
- **FR-007**: System MUST frame all comparative findings as associational differences in performance, avoiding causal claims unless randomization is explicitly part of the experimental design (See US-3).
- **FR-008**: System MUST derive ground-truth relevant lines for synthetic ambiguous issues from the original solution code *before* mutation, ensuring the oracle is independent of the mutation process (See US-1).
- **FR-009**: System MUST apply structural obfuscations (e.g., control flow reordering or API signature changes) in addition to variable renaming to ensure synthetic issues are actually harder for AST-based retrieval (See US-1).
- **FR-010**: System MUST validate the "hard" instance proxy by manually inspecting a [deferred] random subset to confirm that low coverage correlates with genuine ambiguity or unsolvability (See US-1).

### Key Entities

- **Hard Instance**: A repository issue from the SWE-Explore dataset falling in the bottom [deferred] of initial coverage scores.
- **Synthetic Ambiguous Issue**: A mutated version of a solvable task where variable names are changed, comments are removed, and structural obfuscations are applied to obscure intent.
- **Exploration Turn**: A single cycle of query, retrieval, static analysis, and query reformulation within the iterative agent loop.
- **Coverage Metric**: The percentage of ground-truth relevant code lines successfully retrieved by the agent.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Line-level coverage improvement is measured against the static one-shot baseline on the "hard" and synthetic issue subset (See FR-005).
- **SC-002**: Ranking efficiency (position of first relevant line) is measured against the static one-shot baseline to determine retrieval speed (See FR-005).
- **SC-003**: Statistical significance of the difference in coverage is measured against the p < 0.05 threshold using the Wilcoxon signed-rank test (with tie-handling as defined in FR-006) (See FR-006).
- **SC-004**: Multiplicity correction is applied using the Bonferroni method to the family of hypothesis tests (coverage and ranking) to control the family-wise error rate (See US-3).
- **SC-005**: Computational feasibility is measured against the constraint of running the full analysis on a 2-core, 7GB RAM, CPU-only runner within 6 hours (See FR-003).
- **SC-006**: Threshold sensitivity is measured by sweeping turn limits to verify result stability (See FR-003, See US-2).

## Assumptions

- The SWE-Explore dataset contains the necessary ground-truth relevant lines and initial coverage scores required to identify the bottom [deferred] "hard" instances.
- The "hard" instances identified by low initial coverage are representative of retrieval failures that iterative strategies can address.
- A lightweight LLM (e.g., Qwen or similar) can run inference on a CPU-only environment within a feasible time limit for the specified dataset size and turn count.
- The static analysis tools (`pylint` or `ast`) are sufficient to detect the types of errors and missing dependencies relevant to the exploration loop.
- The 3-turn limit per issue is sufficient to capture the majority of the adaptive benefit of an iterative strategy without exceeding compute constraints.
- The Wilcoxon signed-rank test is an appropriate non-parametric test for the distribution of coverage and ranking metrics observed in this dataset, provided tie-handling corrections are applied when necessary.
- The SWE-Explore dataset does not explicitly label "unsolvable" issues; "hard" instances (defined as the bottom [deferred] of initial coverage scores) are used as the operational proxy for retrieval failures in this study.