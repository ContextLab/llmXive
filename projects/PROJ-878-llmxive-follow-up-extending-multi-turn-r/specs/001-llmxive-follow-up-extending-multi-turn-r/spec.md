# Feature Specification: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Feature Branch**: `001-llmxive-topological-limits`  
**Created**: 2026-07-18  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode' - investigating how topological complexity of logical dependency graphs limits convergence in generative models."

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation with Controlled Topology (Priority: P1)

The system MUST generate a synthetic dataset of logical puzzles where the nesting depth and branching factor are explicitly controlled and recorded as metadata for every instance.

**Why this priority**: This is the foundational requirement. Without a dataset where the independent variables (topology) are known and systematically varied, no correlation with convergence behavior can be established. The research question hinges entirely on the ability to isolate these structural metrics.

**Independent Test**: The generation script can be executed in isolation to produce a JSONL file. A validation script can parse this file and verify that the distribution of `nesting_depth` and `branching_factor` matches the requested ranges, and that the ground-truth solution is derivable from the graph structure.

**Acceptance Scenarios**:

1. **Given** a request to generate 500 puzzles with `nesting_depth` between 3 and 6, **When** the generation script runs, **Then** the output file contains exactly 500 valid instances where every instance's recorded `nesting_depth` is an integer between 3 and 6.
2. **Given** a specific puzzle instance, **When** the dependency graph is reconstructed from the puzzle text, **Then** the calculated maximum nesting depth matches the `nesting_depth` metadata field exactly.
3. **Given** a puzzle with `branching_factor` set to 4, **When** the logical deduction steps are parsed by reconstructing the graph and calculating the mean in-degree of non-root nodes, **Then** the calculated average branching factor matches the target `branching_factor` within a tolerance of ±0.1.

---

### User Story 2 - CPU-Feasible Baseline Execution (Priority: P2)

The system MUST execute the Reflective Masking (RM) loop on the generated dataset using a pre-trained Mask Diffusion Model, constrained to CPU-only execution, and record the number of turns until convergence or failure for each instance.

**Why this priority**: This implements the core experimental loop. It transforms the theoretical question into empirical data. It must be CPU-feasible to align with the project's constraint of running on free-tier CI (no GPU).

**Independent Test**: The execution script can be run on a standard CPU environment. It must complete within the CI limit for the full dataset. The output must be a log file containing `instance_id`, `turns_to_converge` (or `failure`), and `final_accuracy`.

**Acceptance Scenarios**:

1. **Given** a dataset of 100 puzzles, **When** the RM execution script runs on a CPU-only environment, **Then** the process completes without OOM (Out of Memory) errors and generates a results log within 6 hours.
2. **Given** a puzzle that converges successfully, **When** the execution finishes, **Then** the log records the exact integer number of turns taken to reach the ground-truth solution, verified by graph-traversal match.
3. **Given** a puzzle that fails to converge within 50 turns, **When** the execution finishes, **Then** the log records the instance as a "failure" with the final turn count capped at 50.

---

### User Story 3 - Statistical Correlation & Threshold Analysis (Priority: P3)

The system MUST perform non-parametric regression (Spearman correlation) and Generalized Linear Modeling to correlate topological metrics with convergence metrics, and execute a sensitivity analysis on the convergence threshold.

**Why this priority**: This delivers the scientific answer. It transforms raw execution logs into the "non-linear degradation" and "tipping point" insights described in the expected results. The sensitivity analysis is required to validate any observed thresholds.

**Independent Test**: The analysis script can be run on the results log. It must produce a report containing correlation coefficients, p-values, and a plot/table showing how convergence rates change when the success threshold is varied (e.g., 40 turns vs 50 turns vs 60 turns).

**Acceptance Scenarios**:

1. **Given** the execution results log, **When** the analysis script runs, **Then** it outputs a Spearman correlation coefficient between `nesting_depth` and `turns_to_converge` and the corresponding p-value, regardless of the result value.
2. **Given** a specific convergence threshold (e.g., 50 turns), **When** the sensitivity analysis runs, **Then** the output includes a table showing the failure rate for thresholds of 40, 50, and 60 turns.
3. **Given** the statistical model, **When** the script identifies a "tipping point" (e.g., depth > 7), **Then** the report explicitly states the depth value where the degradation rate exceeds a defined slope change.

---

### Edge Cases

- **What happens when** the generated logical graph is cyclic or invalid? The generator must detect and discard such instances, ensuring the dataset is acyclic and solvable.
- **How does the system handle** a model that enters an infinite loop of masking/unmasking without converging? The execution loop must enforce a hard maximum turn limit and mark the instance as "non-convergent" rather than hanging indefinitely.
- **What happens when** the dataset size exceeds available RAM on the CI runner? The execution script must process the dataset in batches to ensure memory usage stays within acceptable system limits.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a synthetic logical deduction dataset where every instance includes explicit metadata for `nesting_depth` and `branching_factor` derived from a directed acyclic dependency graph. (See US-1)
- **FR-002**: System MUST implement the Reflective Masking (RM) inference loop using a pre-trained Mask Diffusion Model, constrained to run exclusively on CPU (no CUDA/GPU), with a termination condition after a bounded number of turns per instance. (See US-2)
- **FR-003**: System MUST record the outcome for every dataset instance, capturing the exact number of turns to solution for successful cases and a binary "failure" flag for cases exceeding the turn limit. (See US-2)
- **FR-004**: System MUST perform a Spearman rank correlation analysis between the `nesting_depth` predictor and the `turns_to_converge` outcome variable. (See US-3)
- **FR-005**: System MUST execute a sensitivity analysis on the convergence threshold by re-evaluating success rates at three specific cutoffs (40, 50, and 60 turns) to verify the stability of the identified "tipping point." (See US-3)
- **FR-006**: System MUST validate that every generated puzzle instance is acyclic and has a unique ground-truth solution derivable from its dependency graph before inclusion in the dataset. (See US-1)
- **FR-007**: System MUST implement a randomized path perturbation mechanism during generation that selects a valid ground-truth solution path different from the longest path in the dependency graph to prevent tautological validation. (See US-1)
- **FR-008**: System MUST execute an extended budget validation run on a subset of the dataset with a 1000-turn limit to distinguish between budget exhaustion and reasoning failure. (See US-2)

### Key Entities

- **LogicalPuzzle**: A structured instance containing the text prompt, the ground-truth solution, and metadata (`nesting_depth`, `branching_factor`, `target_path_id`).
- **ExecutionLog**: A record of a single inference run, containing `instance_id`, `turns_to_converge` (integer or null), `convergence_status` (success/failure), and `final_token_sequence`.
- **TopologicalMetric**: A derived value representing the structural complexity of a puzzle, specifically `max_nesting_depth` (longest chain of implications) and `avg_branching_factor` (mean in-degree of non-root nodes).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The correlation coefficient between `nesting_depth` and `turns_to_converge` is measured against the null hypothesis of zero correlation to determine statistical significance (p < 0.05). (See FR-004)
- **SC-002**: The failure rate at the identified "tipping point" depth is measured against the failure rates at adjacent depths (depth-1 and depth+1) to enable analysis of non-linear degradation patterns. (See FR-005)
- **SC-003**: The total execution time for the full dataset (N=500) is measured against the 6-hour CI job limit to confirm CPU-feasibility. (See FR-002)
- **SC-004**: The sensitivity analysis results (failure rates at 40/50/60 turns) are measured against the primary result to verify that the observed threshold is not an artifact of the specific 50-turn cutoff. (See FR-005)
- **SC-005**: The dataset generation process is measured against the requirement that no instances contain cyclic dependencies or unsolvable states; the validation script must return a [deferred] cycle rate. (See FR-006)
- **SC-006**: The system must measure the divergence between the model's output path and the longest path in the graph to confirm the model is reasoning over alternative paths rather than simply traversing the longest chain. (See FR-007)
- **SC-007**: The extended budget validation (1000 turns) must report the percentage of "failures" (at 50 turns) that eventually converge at 1000 turns, quantifying the rate of budget exhaustion vs. reasoning failure. (See FR-008)

## Assumptions

- The pre-trained Mask Diffusion Model weights referenced in the "Multi-Turn Reflective Masking" paper are available via Hugging Face or a local repository and can be loaded into a CPU-only inference environment without requiring 8-bit quantization (which requires CUDA).
- The GSM8K dataset is used solely as a seed for the *structure* of the logical puzzles; the specific mathematical content is replaced by synthetic logical deduction problems to ensure topological control, so the original GSM8K answer keys are not used for validation.
- The "50 turn" limit for convergence is a community-standard default for iterative reasoning loops; if the model requires >50 turns, it is assumed to be in a non-convergent state for the purpose of this study.
- The synthetic dataset generation script can produce 500 valid, acyclic logical puzzles with controlled topology within 30 minutes of CPU time.
- The `nesting_depth` metric is defined as the length of the longest path in the dependency graph, and `branching_factor` is the average in-degree of non-root nodes; these definitions are assumed to be the standard for this specific research context.
- The GitHub Actions free-tier runner provides sufficient disk space to store the model weights, the generated dataset, and the execution logs simultaneously.