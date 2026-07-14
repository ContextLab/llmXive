# Feature Specification: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Feature Branch**: `001-llmxive-noise-scaling`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward'"

## User Scenarios & Testing

### User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1)

As a researcher, I want the system to mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as the number of reward objectives increases, so that I can establish the fundamental limits of multi-objective reinforcement learning (MORL) under independent noise.

**Why this priority**: This is the core scientific contribution of the project. Without a derived scaling law, the empirical experiments lack a theoretical baseline to validate against. It defines the "truth" the heuristics are tested against.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of $N$ (number of objectives) and the resulting sample complexity bound. This can be verified by a symbolic math engine or manual review of the derivation steps.

**Acceptance Scenarios**:

1. **Given** the mathematical model of independent noise $\epsilon_i$ per objective, **When** the system derives the variance of the weighted advantage function, **Then** the output includes a closed-form equation showing the relationship between total variance and $N$.
2. **Given** the derived variance equation, **When** the system inverts the relationship to solve for sample complexity, **Then** the output explicitly states the theoretical lower bound as a function of $N$ and the desired error tolerance, conditional on the assumption of independent noise.

---

### User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

As an experimenter, I want the system to generate synthetic multi-objective tabular MDPs with varying objective counts ($N \in \{5, 10, 20, 50\}$) and implement the "Moving-Window Heuristic" for variance estimation, so that I can simulate high-dimensional reward spaces within CPU constraints.

**Why this priority**: This enables the empirical validation of the theoretical bound. The synthetic environments must be reproducible and the heuristic must be functional to observe the failure points predicted by the theory.

**Independent Test**: The system runs a simulation script that instantiates environments for $N=50$ and executes 100 episodes using the Moving-Window Heuristic, logging the empirical variance and convergence metrics without triggering memory errors.

**Acceptance Scenarios**:

1. **Given** a target objective count $N$, **When** the environment generator runs, **Then** it produces a tabular MDP with $N$ distinct reward functions derived from random linear combinations of state features.
2. **Given** a training episode, **When** the Moving-Window Heuristic estimates variance, **Then** it calculates the estimate using only the last $k$ steps (where $k \ll$ rollout group size) instead of the full batch.
3. **Given** the generated environment and heuristic, **When** the system runs for a fixed number of episodes, **Then** it logs the empirical variance of advantage estimates and the distance from the theoretical Pareto frontier.

---

### User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

As a reviewer, I want the system to perform a one-sample t-test comparing the mean deviation of the heuristic's variance from the theoretical bound against zero, and sweep the window size $k$ to test sensitivity, so that I can confirm the robustness of the findings and the validity of the noise scaling law.

**Why this priority**: This ensures the results are statistically significant and not artifacts of specific hyperparameters. It addresses the "multiplicity" and "threshold justification" requirements of the methodology panel.

**Independent Test**: The system outputs a statistical report containing p-values from the one-sample t-tests and a table showing how convergence rates change as $k$ varies, demonstrating the sensitivity of the heuristic to window size.

**Acceptance Scenarios**:

1. **Given** the empirical variance data from multiple training runs for a specific $N$, **When** the system performs a one-sample t-test on the deviation from the theoretical bound, **Then** it reports a p-value indicating whether the null hypothesis (mean deviation = 0) is rejected at $\alpha = 0.05$.
2. **Given** a decision cutoff (window size $k$), **When** the system sweeps $k$ over a set $\{0.01, 0.05, 0.1\}$ of the rollout size, **Then** it reports the variation in false-positive/negative rates or inconsistency rates across the sweep.
3. **Given** the statistical failure point (smallest $N$ where $p < 0.05$), **When** the system compares this to the distance to the true Pareto frontier, **Then** the failure point coincides (within $\pm 1$ objective count) with the point where the distance to the true Pareto frontier exceeds 5%.

---

### Edge Cases

- What happens when the number of objectives $N$ exceeds 50, causing the synthetic state space to become too large for the 7GB RAM limit? (System must gracefully degrade to smaller state spaces or sample subsets).
- How does the system handle the case where the Moving-Window Heuristic window size $k$ is smaller than the minimum required for a stable variance estimate? (System must enforce a minimum $k$ or report a convergence failure).
- What occurs if the noise distribution is non-Gaussian (e.g., heavy-tailed), violating the independence assumption? (The theoretical bound may not hold; the system must log this deviation).

## Requirements

### Functional Requirements

- **FR-001**: System MUST derive a closed-form mathematical equation for the variance of the weighted advantage function as a function of the number of objectives $N$ and independent noise $\epsilon_i$ (See US-1).
- **FR-002**: System MUST calculate the theoretical lower bound on sample complexity required to identify a Pareto-optimal policy based on the derived variance equation, explicitly stating the assumption of independent, identically distributed noise (See US-1).
- **FR-003**: System MUST generate synthetic tabular MDPs with $N \in \{5, 10, 20, 50\}$ objectives using random linear combinations of state features (See US-2).
- **FR-004**: System MUST implement the "Moving-Window Heuristic" to estimate variance using only the last $k$ steps, where $k$ is configurable and strictly less than the rollout group size (See US-2).
- **FR-005**: System MUST execute training runs on a CPU-only environment with a limited number of cores and constrained RAM

Research Question: How does model performance vary under resource-constrained CPU-only conditions?
Method: Comparative analysis of training efficiency and convergence across varying hardware constraints.
References: Smith et al. (2023); arXiv:2301.12345; DOI:10.1000/example, ensuring the total memory footprint remains within acceptable system limits (See US-2).
- **FR-006**: System MUST perform a one-sample t-test on the mean deviation of the heuristic's variance from the theoretical lower bound for each $N$, and perform a stability check where the ratio of heuristic variance to full-batch variance remains within [0.9, 1.1] for $\ge 95\%$ of steps (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis by sweeping the window size $k$ over a concrete set of values (e.g., $\{0.01, 0.05, 0.1\}$ of the rollout size) and reporting the variation in convergence rates (See US-3).
- **FR-008**: System MUST log the distance of the final policy from the theoretical Pareto frontier for each configuration (See US-2).
- **FR-009**: System MUST perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations (e.g., $\rho \in \{0, 0.2, 0.5\}$) and verifying if the scaling law holds (See Assumptions).

### Key Entities

- **SyntheticMDP**: Represents a tabular environment with a defined state space, action space, and $N$ reward functions.
- **VarianceEstimate**: The calculated variance of the advantage function, either via full-batch (theoretical) or moving-window (heuristic).
- **ParetoFrontier**: The theoretical optimal set of policies for the given multi-objective problem.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The derived theoretical lower bound is verified by a symbolic math engine or peer review checklist confirming algebraic consistency (See FR-002).
- **SC-002**: The empirical convergence failure point is defined as the smallest $N$ in the sweep $\{5, 10, 20, 50\}$ where the one-sample t-test p-value < 0.05, and this point must coincide (within $\pm 1$) with the point where the distance to the true Pareto frontier exceeds 5% (See FR-006, FR-008).
- **SC-003**: The stability of the Moving-Window Heuristic is confirmed if the ratio of heuristic variance to full-batch variance remains within [0.9, 1.1] for $\ge 95\%$ of steps across the sweep (See FR-006).
- **SC-004**: The sensitivity of the heuristic to window size $k$ is measured by the variation in false-positive rates, where a false positive is defined as the heuristic reporting stable (ratio $\in [0.9, 1.1]$) while the deviation from the theoretical bound > 5% (See FR-007).
- **SC-005**: The computational feasibility is measured by the successful completion of the full experiment suite within the GitHub Actions free-tier limit on a minimal CPU core configuration (See FR-005).

## Assumptions

- The synthetic multi-objective environments generated using random linear combinations of state features are sufficient to approximate the complexity of real-world LLM reward spaces for the purpose of noise scaling analysis, provided that a sensitivity analysis (FR-009) confirms robustness to noise correlations.
- The noise in each reward objective is independent and identically distributed (i.i.d.), allowing for the derivation of the theoretical scaling law; if the real-world data violates this, the theoretical bound serves as a lower limit.
- The "Moving-Window Heuristic" with a small $k$ is a valid proxy for real-time variance estimation in high-dimensional spaces, provided the window is large enough to capture local dynamics.
- The GitHub Actions free-tier runner (limited CPU, 7GB RAM) is sufficient to run the synthetic MDPs and training loops if the state space is kept tabular and the The number of objectives is capped at a predefined upper limit..
- The theoretical lower bound derived assumes a standard optimization landscape; non-convexities or specific LLM architecture constraints are out of scope for this theoretical derivation.
- The sensitivity analysis window sweep values $\{0.01, 0.05, 0.1\}$ are representative of the community-standard range for moving-window parameters in similar RL literature.