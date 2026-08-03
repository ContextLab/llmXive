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
3. **Given** the statistical failure point (smallest $N$ where $p < 0.05$), **When** the system compares this to the distance to the true Pareto frontier (calculated per FR-017), **Then** the failure point coincides (within a small objective count tolerance) with the point where the distance to the true Pareto frontier exceeds 5%.

---

### User Story 4 - Validation Independence & Construct Validity (Priority: P4)

As a scientific reviewer, I want the system to generate a held-out set of reward functions with a different noise distribution (e.g., heavy-tailed) and verify the scaling law holds across diverse reward landscapes, so that I can confirm the results are not artifacts of the specific synthetic distribution used.

**Why this priority**: This satisfies Constitution Principle VI (Validation Independence) and addresses the construct validity risk of using only linear reward combinations. It ensures the scaling law is robust to the specific nature of the reward noise.

**Independent Test**: The system successfully generates a held-out dataset with non-Gaussian noise and reports that the scaling law deviation remains within 10% of the theoretical bound.

**Acceptance Scenarios**:

1. **Given** the base synthetic environment, **When** the system generates a held-out set with heavy-tailed noise, **Then** the system reports the specific noise distribution parameters used.
2. **Given** the held-out set, **When** the heuristic is applied, **Then** the system compares the empirical sample complexity to the theoretical bound derived for independent noise.
3. **Given** the comparison, **Then** the system reports if the deviation exceeds a significant threshold, flagging a potential construct validity failure.

---

### User Story 5 - Sensitivity Analysis on Noise Correlation (Priority: P5)

As a researcher, I want the system to perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations ($\rho \in \{\text{zero}, 0.2, 0.5\}$) and verifying if the scaling law holds, so that I can confirm the robustness of the independence assumption.

**Why this priority**: This is essential rigor to prove the 'independence' assumption. If the goal is to find the *lower bound* under independence, testing correlated noise is a secondary robustness check, not a primary requirement for the bound itself, but it is necessary to justify the assumption.

**Independent Test**: The system outputs a report showing the results of a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N for each $\rho$ value, with a pass criterion of $p > 0.05$ for $\rho=0$.

**Acceptance Scenarios**:

1. **Given** a target correlation $\rho$, **When** the system generates the synthetic environment with correlated noise, **Then** it logs the actual correlation achieved.
2. **Given** the generated environment, **When** the system runs the training and validation, **Then** it calculates the slope of sample complexity vs N and performs a Kolmogorov-Smirnov goodness-of-fit test against the theoretical bound.
3. **Given** the test results, **Then** the system reports if the scaling law holds (p > 0.05) for $\rho=0$ and flags deviations for $\rho > 0$.

---

### User Story 6 - Resource Constraint Enforcement (Priority: P6)

As a system administrator, I want the system to enforce strict resource constraints (2 CPU cores, ≤ 7 GB RAM) and implement graceful degradation for N > 50, so that the experiments remain feasible within the GitHub Actions free-tier limits.

**Why this priority**: This ensures the experiments can actually run within the available infrastructure. Without enforcement and degradation logic, the experiments may fail or exceed resource limits.

**Independent Test**: The system successfully completes a training run for N=50 within the specified resource limits and logs the effective N and state space size if degradation occurs.

**Acceptance Scenarios**:

1. **Given** a training run, **When** the system monitors resource usage, **Then** it ensures the total memory footprint remains ≤ 7 GB RAM and CPU usage is limited to 2 cores.
2. **Given** a target objective count N > 50, **When** the system detects the limit, **Then** it reduces the state space size by a significant factor and logs the effective N and state space size used.
3. **Given** the degradation logic, **When** the system completes the run, **Then** it outputs the effective N and reduced state space size in the final report.

---

### Edge Cases

- What happens when the number of objectives $N$ exceeds 50, causing the synthetic state space to become too large for the 7GB RAM limit? (System MUST detect $N > 50$, reduce the state space size by a significant factor, log the effective $N$ and state space size used, and output these values in the final report).
- How does the system handle the case where the Moving-Window Heuristic window size $k$ is smaller than the minimum required for a stable variance estimate? (System must enforce a minimum $k$ or report a convergence failure).
- What occurs if the noise distribution is non-Gaussian (e.g., heavy-tailed), violating the independence assumption? (The theoretical bound may not hold; the system must log this deviation and report it in the final analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST derive a closed-form mathematical equation for the variance of the weighted advantage function as a function of the number of objectives $N$ and independent noise $\epsilon_i$ (See US-1).
- **FR-002**: System MUST calculate the theoretical lower bound on sample complexity required to identify a Pareto-optimal policy based on the derived variance equation, explicitly stating the assumption of independent, identically distributed noise (See US-1).
- **FR-003**: System MUST generate synthetic tabular MDPs with a varying number of objectives, starting from a small scale. using random linear combinations of state features (See US-2).
- **FR-004**: System MUST implement the "Moving-Window Heuristic" to estimate variance using only the last $k$ steps, where $k$ is configurable and strictly less than the rollout group size (See US-2).
- **FR-005**: System MUST execute training runs on a CPU-only environment with exactly 2 CPU cores and a maximum memory footprint of ≤ 7 GB RAM (See US-6).
- **FR-006**: System MUST count the number of episodes required to reach a Pareto-optimal reward threshold and compare this empirical sample count against the theoretical lower bound derived in FR-002, performing a one-sample t-test on the mean of multiple runs (≥ 30) against the theoretical bound at $\alpha = 0.05$ (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis by sweeping the window size $k$ over a concrete set of values (e.g., a range of fractions of the rollout size) and reporting the variation in convergence rates and the deviation from the theoretical bound (See US-3).
- **FR-008**: System MUST log the distance of the final policy from the theoretical Pareto frontier for each configuration (See US-2).
- **FR-009**: System MUST perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations (e.g., $\rho \in \{, 0.2, 0.5\}$) and verifying if the scaling law holds (p > 0.05 in a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N) for the $\rho=0$ case, with $\rho > 0$ cases being exploratory (See US-5).
- **FR-010**: System MUST perform a sensitivity analysis on the reward generation distribution by testing at least three distinct distributions (Linear, Sparse, Non-Convex) to validate construct validity (See US-4).
- **FR-012**: System MUST generate a held-out set of reward functions with a different noise distribution (e.g., heavy-tailed) to satisfy validation independence (See US-4).
- **FR-013**: System MUST calculate the theoretical variance of the injected noise parameters ($\sigma^2$) and use this known value as the ground truth for validating the heuristic, rather than an empirical estimator (See US-3).
- **FR-014**: System MUST perform a sanity check to verify that the empirical variance of the injected noise matches the theoretical noise variance ($\sigma^2$) before any advantage function analysis begins (See US-3).
- **FR-015**: System MUST perform a one-sample t-test comparing the mean of the heuristic's error (Heuristic Estimate - Known $\sigma^2$) against zero to validate accuracy (See US-3).
- **FR-016**: System MUST detect if $N > 50$ and, if so, reduce the state space size by a factor of 2, log the effective $N$ and state space size used, and output these values in the final report (See US-6).
- **FR-017**: System MUST calculate the distance of the final policy from the theoretical Pareto frontier for each configuration using a defined oracle or approximation method (See US-3).

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
- **SC-002**: The empirical convergence failure point is defined as the smallest $N$ in the sweep $\{5, 10, 20, 50\}$ (with ≥ 30 independent runs) where the empirical sample count exceeds the theoretical bound by a factor of 1.5, and this point must coincide (within $\pm 1$) with the point where the distance to the true Pareto frontier (calculated per FR-017) exceeds 5% (See FR-006, FR-008, FR-017).
- **SC-003**: The stability of the Moving-Window Heuristic is confirmed if the ratio of heuristic variance to known injected noise variance ($\sigma^2$) remains within [0.9, 1.1] for ≥ 95% of steps across the post-burn-in phase (steps to end) of the training trajectory (See FR-013).
- **SC-004**: The sensitivity of the heuristic to window size $k$ is measured by the variation in false-positive rates, where a false positive is defined as the heuristic reporting stable (ratio $\in [0.9, 1.1]$) while the deviation from the theoretical bound > 5% (See FR-007).
- **SC-005**: The computational feasibility is measured by the successful completion of the full experiment suite within the GitHub Actions free-tier limit on a minimal CPU core configuration (See FR-005).
- **SC-006**: The construct validity is confirmed if the scaling law holds (deviation < 10%) across all three tested reward distributions (Linear, Sparse, Non-Convex) (See FR-010).

## Assumptions

- The synthetic multi-objective environments generated using random linear combinations of state features are sufficient to approximate the complexity of real-world LLM reward spaces for the purpose of noise scaling analysis, provided that a sensitivity analysis (FR-010) confirms robustness to noise correlations and distribution types.
- The noise in each reward objective is independent and identically distributed (i.i.d.), allowing for the derivation of the theoretical scaling law; if the real-world data violates this, the theoretical bound serves as a lower limit.
- The "Moving-Window Heuristic" with a small $k$ is a valid proxy for real-time variance estimation in high-dimensional spaces, provided the window is large enough to capture local dynamics.
- The GitHub Actions free-tier runner (limited CPU, standard memory) is sufficient to run the synthetic MDPs and training loops if the state space is kept tabular and the number of objectives is capped at a predefined upper limit.
- The theoretical lower bound derived assumes a standard optimization landscape; non-convexities or specific LLM architecture constraints are out of scope for this theoretical derivation.
- The sensitivity analysis window sweep values $\{0.01, 0.05, 0.1\}$ are representative of the community-standard range for moving-window parameters in similar RL literature.
- **Code as Truth**: The `src/derivation/sample_complexity.py` module is the Single Source of Truth for the theoretical derivation; `docs/theoretical_derivation.md` is a generated report and may diverge if not regenerated.
- **Validation Independence**: The held-out set generated in FR-012 is distinct from the training set and uses a different noise distribution to satisfy Constitution Principle VI.
- **Module Structure**: The separation of derivation and empirical logic is enforced by the module structure (`code/src/derivation/` vs `code/src/analysis/`), with `src/derivation/sample_complexity.py` as the primary source of truth.