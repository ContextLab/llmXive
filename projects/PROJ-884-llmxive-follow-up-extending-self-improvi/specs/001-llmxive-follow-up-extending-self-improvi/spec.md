# Feature Specification: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Feature Branch**: `001-symbolic-bes`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Self-Improving Language Models with Bidirectional Evolutionary Search'"

## User Scenarios & Testing

### User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1)

The researcher must be able to instantiate a dataset of logic and arithmetic puzzles (e.g., Sudoku variants, constrained pathfinding) where each item includes a deterministic Python script capable of verifying the solution path and final answer without relying on the LLM.

**Why this priority**: This is the foundational infrastructure. Without a deterministic ground-truth verifier, the core hypothesis (symbolic constraints vs. learned verifiers) cannot be tested, and the entire evolutionary loop lacks a fitness signal.

**Independent Test**: The pipeline can be fully tested by running the verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

**Acceptance Scenarios**:
1. **Given** a puzzle instance and a candidate solution string, **When** the deterministic Python verifier is executed, **Then** it returns a boolean "valid/invalid" and a specific error code if invalid, within 100ms.
2. **Given** a puzzle instance and a solution that violates a specific constraint (e.g., duplicate number in Sudoku row), **When** the verifier runs, **Then** it correctly identifies the violation and rejects the solution.

---

### User Story 2 - Hybrid Evolutionary Search Execution (Priority: P2)

The researcher must be able to execute the Bidirectional Evolutionary Search (BES) framework where the forward step uses a small pre-trained LLM for trajectory recombination, and the backward step is entirely replaced by the symbolic planner to guide goal decomposition.

**Why this priority**: This implements the core experimental condition. It allows the comparison of the symbolic-guided approach against the baseline, directly addressing the research question about the necessity of semantic understanding.

**Independent Test**: The system can be tested by running the evolutionary loop on a subset of puzzles. and verifying that the symbolic planner successfully generates sub-goals for all population members where the constraints are parseable, and that the LLM attempts to satisfy these sub-goals.

**Acceptance Scenarios**:
1. **Given** a population of LLM-generated candidate solutions, **When** the symbolic planner processes the problem constraints, **Then** it outputs a structured decomposition of sub-goals that strictly adhere to the puzzle rules.
2. **Given** the symbolic sub-goals, **When** the LLM attempts to generate a solution trajectory, **Then** the resulting output is formatted in a way that the deterministic verifier can parse and evaluate.

---

### User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

The researcher must be able to record success rates and computational costs (wall-clock time, energy) for both the symbolic-guided and neural-verifier baselines, and apply a two-proportion z-test and t-test to determine statistical significance.

**Why this priority**: This provides the empirical evidence required to answer the research question. It transforms raw execution logs into a defensible scientific conclusion regarding efficiency and efficacy.

**Independent Test**: The analysis module can be tested by feeding it synthetic success rate data with known statistical differences to verify that the z-test correctly identifies significance at p < 0.05 and that the cost comparison accurately calculates overhead.

**Acceptance Scenarios**:
1. **Given** the raw execution logs from both the symbolic and neural baseline runs, **When** the analysis script is executed, **Then** it outputs a success rate difference and a p-value for the two-proportion z-test.
2. **Given** the resource usage logs, **When** the cost analysis runs, **Then** it calculates the total wall-clock time and energy consumption for the symbolic method and compares it against the baseline, reporting the percentage reduction.

### Edge Cases

- What happens when a puzzle constraint is too complex for the symbolic parser to decompose (e.g., non-linear constraints in a logic grid)? The system must log the failure, exclude the item from the symbolic-guided run, and record it as a "symbolic failure" rather than a crash.
- How does the system handle an LLM output that is syntactically valid but semantically nonsensical (e.g., a path that jumps between non-adjacent nodes)? The deterministic verifier must catch this and return "invalid," ensuring the evolutionary pressure remains on validity, not just syntax.
- What happens if the symbolic planner generates a sub-goal that is logically impossible given the puzzle state? The system must detect the logical contradiction in the planner's output and flag the instance for manual review or exclusion.

## Requirements

### Functional Requirements

- **FR-001**: System MUST curate a dataset of [deferred] logic/arithmetic puzzles where each item includes a deterministic Python verification script that independently validates the solution path and answer, and where all puzzle constraints are in a parseable formal language (or the item is excluded) (See US-1).
- **FR-002**: System MUST implement a symbolic planner that parses formal puzzle constraints to generate a decomposition of sub-goals, replacing the neural backward step in the BES framework (See US-2).
- **FR-003**: System MUST execute the BES forward evolution step using a small pre-trained LLM combined with the symbolic planner's sub-goals to guide the search population (See US-2).
- **FR-004**: System MUST record the success rate (percentage of correctly solved puzzles) and computational cost (wall-clock time, energy in Joules) for both the symbolic-guided and neural-verifier baseline variants (See US-3).
- **FR-005**: System MUST apply a two-proportion z-test to compare success rates and a t-test to compare computational overhead, ensuring statistical significance is evaluated at p < 0.05 (See US-3).
- **FR-006**: System MUST exclude any puzzle instance from the symbolic-guided run if the symbolic planner fails to decompose its constraints, logging the exclusion reason (See US-2).

### Key Entities

- **Puzzle Instance**: A specific logic problem defined by constraints, initial state, and target state.
- **Candidate Solution**: A string or structured output generated by the LLM attempting to solve the puzzle.
- **Verification Script**: A deterministic Python function associated with a Puzzle Instance that returns a boolean validity status.
- **Symbolic Planner**: A rule-based module that converts Puzzle Constraints into a sequence of Sub-goals.
- **Evolutionary Population**: A set of Candidate Solutions being evolved over generations.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The success rate of the symbolic-guided BES is measured against the neural-verifier baseline to determine the difference in performance, with the statistical framework (equivalence vs. non-inferiority) pre-registered (See FR-004, FR-005).
- **SC-002**: The computational overhead (wall-clock time, energy in Joules) of the symbolic-guided BES is measured against the neural-verifier baseline to enable statistical comparison of efficiency (See FR-004, FR-005).
- **SC-003**: The validity of the symbolic-guided approach is measured by the success rate of the evolutionary search guided by the planner's sub-goals, ensuring the planner does not introduce logical contradictions that prevent solution finding (See FR-002, FR-003).
- **SC-004**: The statistical significance of the difference in success rates is measured using a two-proportion z-test, with the system outputting the calculated p-value (See FR-005).
- **SC-005**: The scalability of the symbolic-guided approach is measured by characterizing the computational complexity class (e.g., O(n), O(n^2), O(2^n)) of the relationship between problem complexity and computation time (See FR-001, FR-002).

## Assumptions

- The curated dataset of logic puzzles contains sufficient variability in complexity to support a statistically valid comparison (sample size assumed adequate for z-test with p < 0.05).
- The "small pre-trained LLM" selected for the forward step is capable of running on a standard CPU-only environment with minimal resource requirements within the 6-hour CI job limit, without requiring GPU acceleration or 8-bit quantization.
- The symbolic planner's rule set covers all constraint types present in the curated dataset; any puzzle type outside this rule set is excluded from the symbolic-guided run.
- The deterministic Python verification scripts for the puzzles are computationally lightweight (executing in <100ms) to prevent the verification step from becoming the bottleneck in the evolutionary loop.
- The neural-verifier baseline cost is measured as wall-clock time on comparable hardware or energy consumption (Joules) to ensure a valid comparison of computational efficiency, rather than converting GPU-hours to CPU-seconds.
- The research design treats the comparison as associational regarding the "necessity of semantic understanding," as the study does not involve random assignment of the "understanding" variable itself but rather the substitution of the verification mechanism.
- The dataset variables (puzzle constraints, solution paths) are fully contained within the curated puzzle definitions, requiring no external data sources or dynamic variable extraction that might introduce noise.