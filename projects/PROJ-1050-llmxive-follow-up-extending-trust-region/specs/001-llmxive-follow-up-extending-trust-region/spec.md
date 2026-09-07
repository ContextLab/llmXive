# Feature Specification: llmXive follow-up: extending "Trust Region Policy Distillation"

**Feature Branch**: `001-llmxive-topd-extension`  
**Created**: 2026-09-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Trust Region Policy Distillation' - investigating the collapse of reasoning strategies into shallow heuristics due to teacher-student capacity mismatches."

## User Scenarios & Testing

### User Story 1 - Synthetic Reasoning Environment & Teacher Policy (Priority: P1)

**Description**: As a researcher, I need a deterministic synthetic "Reasoning MDP" environment where a "Teacher" policy generates optimal, deep reasoning paths, so that I can establish a ground-truth baseline for distillation experiments.

**Why this priority**: Without a valid environment and a reliable teacher policy, no student training or collapse analysis can occur. This is the foundational data source.

**Independent Test**: The environment can be instantiated, and the teacher policy can be queried to produce a valid, optimal path of a specified depth without external dependencies.

**Acceptance Scenarios**:
1. **Given** a requested logical problem of depth `D`, **When** the Teacher Policy is invoked, **Then** it returns a sequence of `D` valid inference rules that solve the problem deterministically.
2. **Given** a problem with a known ground-truth path, **When** the environment state is advanced by one valid inference step, **Then** the environment correctly transitions to the next state without error.
3. **Given** an invalid inference rule attempt, **When** the environment processes it, **Then** it returns a terminal failure state or invalid action penalty.

---

### User Story 2 - Capacity-Constrained Student Policy & TOP-D Training Loop (Priority: P2)

**Description**: As a researcher, I need a student policy implementation with a configurable "cognitive horizon" (max steps) and a TOP-D training loop that interpolates between the student and teacher distributions using a variable coefficient $\alpha$, so that I can simulate the learning dynamics under capacity constraints.

**Why this priority**: This implements the core hypothesis mechanism. It allows the researcher to vary the interpolation strength and student capacity to observe the emergence (or collapse) of reasoning strategies.

**Independent Test**: The training loop can run for a fixed number of epochs with a specific $\alpha$ and horizon, producing a trained student model and loss logs without GPU acceleration.

**Acceptance Scenarios**:
1. **Given** a student horizon limit of `H` steps and a teacher path of length `D > H`, **When** the TOP-D loss is calculated with interpolation coefficient $\alpha = 0.5$, **Then** the loss function correctly blends the student's probability distribution with the teacher's target distribution.
2. **Given** a training run with $\alpha \in \{0.1, 0.3, 0.5, 0.7, 0.9\}$, **When** the training completes, **Then** the system outputs a distinct convergence stability metric (loss variance) for each $\alpha$ value, where "distinct" means statistically distinct (p < 0.05) across configurations.
3. **Given** a student policy with a configurable horizon constraint, **When** the policy attempts to exceed this constraint during inference, **Then** the system truncates the path or penalizes the action as defined by the horizon limit.

---

### User Story 3 - Interaction Analysis & Collapse Detection (Priority: P3)

**Description**: As a researcher, I need an automated analysis pipeline that performs a censored regression (Tobit model) on the "effective reasoning depth" across different $\alpha$ and horizon configurations, and detects the "collapse" into shallow heuristics (defined as effective depth ≤ 0.5 × teacher depth), so that I can validate the non-monotonic relationship hypothesis.

**Why this priority**: This transforms raw training data into the scientific result required to answer the research question. It identifies the specific conditions where reasoning collapses using a statistically sound method for censored data.

**Independent Test**: The analysis script can ingest the training logs, run the Tobit regression, and output a report indicating whether a significant interaction effect exists.

**Acceptance Scenarios**:
1. **Given** a dataset of "effective reasoning depth" for all combinations of $\alpha$ and student horizons, **When** the Tobit regression is executed, **Then** the system reports the likelihood ratio test statistic and p-value for the interaction term ($\alpha \times \text{horizon}$).
2. **Given** a configuration where $\alpha$ is high (e.g., 0.9) and the horizon is short, **When** the collapse detection logic runs, **Then** it flags the student's performance as "shallow heuristic" if the effective depth is ≤ 0.5 × teacher depth.
3. **Given** the full experimental grid results, **When** the non-monotonicity check runs, **Then** it identifies the peak effective reasoning depth at an intermediate $\alpha$ value (if the hypothesis holds) or reports a null result.

---

### Edge Cases

- **What happens when the teacher's optimal path is shorter than the student's horizon?** The system must handle this gracefully, treating the student's extra capacity as unused or allowing it to explore sub-optimal paths without crashing.
- **How does the system handle a "zero-interpolation" scenario ($\alpha = 0$)?** The system must correctly default to pure student learning (no teacher signal) to establish a baseline for "no guidance."
- **What if the synthetic environment generates a problem with no valid solution?** The system must detect unsolvable states and exclude them from the statistical analysis to prevent bias.

## Requirements

### Non-Functional Requirements

- **NFR-001**: The system must operate without GPU acceleration, relying solely on CPU computation to ensure compatibility with standard free-tier CI/CD runners (e.g., GitHub Actions).

### Functional Requirements

- **FR-001**: System MUST implement a deterministic synthetic "Reasoning MDP" where states represent partial proofs and actions represent valid inference rules, ensuring the environment is solvable via a known ground-truth path of varying depths (See US-1).
- **FR-002**: System MUST enforce a configurable "cognitive horizon" constraint on the student policy, limiting the maximum number of reasoning steps it can execute in a single trajectory (See US-2).
- **FR-003**: System MUST calculate the Trust Region Policy Distillation (TOP-D) loss using probability-space interpolation with a configurable coefficient $\alpha \in [0, 1]$ (See US-2).
- **FR-004**: System MUST record the "effective reasoning depth" (number of valid inference steps executed until correct solution or stagnation) and "convergence stability" (variance of the loss) for every training episode across the experimental grid (See US-3).
- **FR-005**: System MUST execute a censored regression (Tobit model) statistical test to determine the significance of the main effects ($\alpha$, horizon) and their interaction on the effective reasoning depth (See US-3).
- **FR-006**: System MUST support a sensitivity analysis for the interpolation coefficient $\alpha$, sweeping values over a set $\{0.1, 0.3, 0.5, 0.7, 0.9\}$ and reporting the variation in "collapse rates," where collapse is defined as effective depth ≤ 0.5 × teacher depth (See US-3).
- **FR-007**: System MUST verify that the ground-truth optimal path is accessible to the environment before starting training to ensure failures are due to distillation dynamics, not environment design (See US-1).

### Key Entities

- **ReasoningMDP**: The synthetic environment instance, defined by the problem graph, valid inference rules, and state transitions.
- **TeacherPolicy**: A hard-coded policy that always selects the optimal path, serving as the target distribution.
- **StudentPolicy**: A tabular or tiny fixed-parameter network with a configurable horizon, updated via TOP-D.
- **ExperimentRun**: A record containing the configuration ($\alpha$, horizon), training logs, and final metrics (effective depth, stability).
- **AnalysisResult**: The output of the statistical test, containing likelihood ratio statistics, p-values, and interaction effect flags.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The interaction effect p-value is measured against the standard significance threshold ($\alpha_{sig} = 0.05$) to determine if the teacher-student capacity mismatch significantly impacts effective reasoning depth (See FR-005).
- **SC-002**: The effective reasoning depth is measured against the teacher's ground-truth path length to quantify the "collapse" magnitude for each $\alpha$ configuration (See FR-004).
- **SC-003**: The convergence stability (loss variance) is measured against the baseline of pure student learning ($\alpha=0$) to assess the stabilizing effect of the TOP-D signal (See FR-004).
- **SC-004**: The sensitivity of the collapse rate (fraction of episodes with effective depth ≤ 0.5 × teacher depth) is measured across the $\alpha$ sweep set $\{0.1, 0.3, 0.5, 0.7, 0.9\}$ to verify the non-monotonic relationship hypothesis (See FR-006).
- **SC-005**: The experimental grid design is constrained to complete within 6 hours of CPU runtime on a standard runner to ensure feasibility (See FR-003).

## Assumptions

- The synthetic "Reasoning MDP" environment can be fully implemented in Python using standard libraries (e.g., `numpy`, `scipy`) without requiring external datasets or large model weights.
- The student policy will be implemented as a tabular method or a tiny fixed-parameter network (e.g., <1M parameters) to ensure it fits within the ~7 GB RAM and ~14 GB disk limits of the free-tier runner.
- The "cognitive horizon" is implemented as a hard truncation of the action sequence rather than a learned constraint, simulating a fixed capacity limit.
- The teacher policy is assumed to be perfect and deterministic, serving as an oracle for the ground-truth path.
- The statistical power of the censored regression (Tobit) is sufficient with a sample size of $N=100$ episodes per configuration; if power is low, the result will be noted as a limitation rather than a definitive failure.
- The analysis of "collapse" relies on "effective reasoning depth" (steps until solution or stagnation) as a valid proxy for "reasoning strategy quality," distinct from raw step count, to avoid conflating efficiency with depth in the presence of hard truncation.
- No GPU, CUDA, or mixed-precision training will be used; all operations will run in default precision on CPU cores.