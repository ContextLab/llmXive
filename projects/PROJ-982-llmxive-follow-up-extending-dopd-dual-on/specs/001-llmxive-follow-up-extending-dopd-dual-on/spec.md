# Feature Specification: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

**Feature Branch**: `001-dopd-discrete-mdp`  
**Created**: 2026-07-23  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'DOPD: Dual On-policy Distillation' - Does the 'privilege illusion' phenomenon emerge in discrete, non-differentiable MDPs, and can DOPD mitigate it without neural optimization?"

## User Scenarios & Testing

### User Story 1 - Construct Discrete Privilege Illusion MDP Environment (Priority: P1)

As a researcher, I need a synthetic, discrete-state MDP environment where a "Teacher" agent has access to a hidden privileged signal (state variable) that a "Student" agent cannot observe, so that I can isolate the "privilege illusion" failure mode without the confounding variables of neural network training dynamics.

**Why this priority**: This is the foundational prerequisite. Without a controlled environment that explicitly simulates information asymmetry (privileged signal available to Teacher, masked from Student), the phenomenon cannot be observed or tested. This is the MVP for the entire research question.

**Independent Test**: The environment can be instantiated and queried to confirm that the Student's observation space strictly excludes the privileged variable while the Teacher's does not, and that optimal policy requires the privileged variable.

**Acceptance Scenarios**:

1. **Given** a grid-world MDP with hidden state `H` and observable state `O`, **When** the environment generates a state, **Then** the Teacher receives `(O, H)` and the Student receives only `O`, ensuring information asymmetry.
2. **Given** a specific state where `H` dictates the optimal action, **When** the Student acts based solely on `O`, **Then** the Student's greedy action (without privileged info) leads to a suboptimal reward, confirming the necessity of `H` for optimality.
3. **Given** the environment is run with 10 independent random seeds, **When** the state generation process is reset, **Then** the distribution of states and hidden variables remains consistent across seeds, ensuring reproducibility.

---

### User Story 2 - Implement DOPD vs. Uniform Supervision Training Loops (Priority: P2)

As a researcher, I need to implement two distinct training regimes: (1) Uniform On-Policy Distillation (Student mimics Teacher actions regardless of confidence) and (2) DOPD (Student dynamically weights Teacher vs. self-supervision based on the advantage gap), so that I can compare their ability to learn the underlying rules versus mimicking the privileged signal.

**Why this priority**: This implements the core intervention (DOPD) and the baseline (Uniform) required to test the hypothesis. It allows for the direct comparison of algorithmic logic without neural artifacts.

**Independent Test**: The training loops can be executed on the discrete MDP, logging the Student's policy updates and action distributions to verify that DOPD reduces reliance on the Teacher's actions when the advantage gap is low, unlike the Uniform regime.

**Acceptance Scenarios**:

1. **Given** a trained Student under the Uniform regime, **When** the privileged signal `H` is masked during evaluation, **Then** the Student's performance drops significantly (simulating the "illusion" of competence), confirming the baseline failure mode.
2. **Given** a trained Student under the DOPD regime, **When** the privileged signal `H` is masked during evaluation, **Then** the Student's performance remains robust, defined as: `drop = (accuracy_unmasked - accuracy_masked) / R_max`, where `R_max` is the maximum possible reward in the MDP; the DOPD regime's `drop` must be ≤ 20% of the Uniform regime's `drop`.
3. **Given** the training logs, **When** analyzing the Student's action distribution during training, **Then** the DOPD Student shows higher entropy or self-correction when the Teacher's advantage is low, whereas the Uniform Student blindly mimics.

---

### User Story 3 - Execute Statistical Generalization Analysis (Priority: P3)

As a researcher, I need to run a statistical comparison (Mann-Whitney U test) of the generalization accuracy between the DOPD and Uniform regimes across multiple independent random seeds, so that I can determine if the improvement is statistically significant and not due to chance.

**Why this priority**: This validates the research claim. Without statistical rigor, the observed differences could be noise. This is the final step to produce a publishable result.

**Independent Test**: The analysis script can take the accuracy logs from the training runs and output a p-value and effect size, confirming or refuting the hypothesis that DOPD mitigates the privilege illusion.

**Acceptance Scenarios**:

1. **Given** generalization accuracy scores from 50 seeds for both Uniform and DOPD regimes, **When** the statistical test is run, **Then** the output includes a p-value and the observed direction of the difference (e.g., "DOPD > Uniform" or "Uniform > DOPD").
2. **Given** the test environment is constructed with a distinct random seed from the training environment, **When** the evaluation is performed, **Then** the results reflect true generalization capability rather than overfitting to the training distribution.
3. **Given** the data is collected from 50 independent seeds, **When** the analysis is run, **Then** the system uses the Mann-Whitney U test to ensure valid inference given the sample size.

### Edge Cases

- What happens if the "privileged signal" `H` is completely uncorrelated with the optimal action (i.e., the signal is noise)? The DOPD mechanism should still function, but the advantage gap might behave differently; the system must handle this without crashing.
- How does the system handle a scenario where the Student's self-supervision (reinforcement) signal is extremely sparse or zero? The DOPD logic must default safely to the Teacher's signal without causing division-by-zero errors in the advantage calculation.
- What if the grid-world size is increased beyond the available RAM limit? The system MUST enforce a maximum grid size of a tractable dimension to ensure CPU tractability and memory usage remains within the available limit.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a discrete grid-world MDP where the Student's observation space is strictly a projection of the full state, excluding at least one "privileged" variable required for optimal navigation (See US-1).
- **FR-002**: System MUST implement a DOPD training loop where the Teacher computes an advantage gap (defined as the difference between the Teacher's state-action value Q(s,a) and a baseline value function V_baseline(s), where V_baseline(s) is the state-value of a random policy). If the dynamic range of this gap is < 0.1, the system MUST switch to a min-max normalized advantage baseline to ensure meaningful weighting. This gap is passed as a scalar weighting signal to the Student to dynamically weight the distillation loss against self-supervision (See US-2).
- **FR-003**: System MUST implement a Uniform On-Policy Distillation training loop where the Student mimics the Teacher's actions with fixed, equal weighting regardless of the advantage gap (See US-2).
- **FR-004**: System MUST execute a generalization test where the privileged signal is artificially removed from the input during evaluation to measure the performance drop (See US-2).
- **FR-005**: System MUST perform a one-tailed Mann-Whitney U test on the generalization accuracy of DOPD vs. Uniform regimes across ≥50 independent random seeds, testing the null hypothesis H0: mean(DOPD) <= mean(Uniform). The study must explicitly state that if the observed effect size is < 0.5, the study is exploratory and underpowered for moderate effects (See US-3).
- **FR-006**: System MUST log training accuracy, convergence steps, and action entropy for every training step to enable post-hoc analysis of learning dynamics (See US-2).
- **FR-007**: System MUST ensure the test environment uses a distinct random seed and state generation process from the training environment to guarantee evaluation independence (See US-3).
- **FR-008**: System MUST enforce a maximum grid dimension to ensure memory usage remains within available RAM limits (See Edge Cases).

### Key Entities

- **MDP Environment**: A discrete state-space grid with observable and hidden (privileged) variables, defining transitions and rewards.
- **Teacher Policy**: An oracle policy that has full access to the state (including privileged variables) and provides optimal actions.
- **Student Policy**: A tabular Q-table or simple linear classifier that learns from the Teacher and self-reinforcement but lacks access to privileged variables.
- **Training Regime**: A configuration defining the distillation logic (Uniform vs. DOPD) used to update the Student policy.
- **Generalization Metric**: A scalar value (accuracy/reward) measuring Student performance on a test set where privileged signals are masked.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The drop in generalization accuracy for the Uniform regime (when privileged signal is masked) is measured against the drop in generalization accuracy for the DOPD regime (See US-2).
- **SC-002**: The statistical significance (p-value) of the difference in mean generalization accuracy between DOPD and Uniform regimes is measured against a fixed alpha threshold of 0.05. (See US-3).
- **SC-003**: The convergence steps required for DOPD to reach a stable policy are measured against the convergence steps of the Uniform regime to determine computational efficiency (See US-2).
- **SC-004**: The action entropy of the Student policy during training is measured against a baseline of random action to verify that DOPD encourages exploration/self-correction when the advantage gap is low (See US-2).
- **SC-005**: The reproducibility of results is measured by running the experiment with multiple independent random seeds; the coefficient of variation (CV) of generalization accuracy is calculated and reported.

## Assumptions

- The discrete MDP environment can be fully simulated in memory (RAM < 7 GB) using pure Python data structures (e.g., dictionaries or lists) without requiring external databases or large datasets.
- The "privileged signal" is a discrete variable that can be explicitly masked during evaluation to simulate the real-world deployment scenario where the signal is unavailable.
- The Student policy is implemented as a tabular Q-table or a simple linear classifier, ensuring that training and inference can be completed on a CPU-only GitHub Actions runner within the allotted time limit.
- The "advantage gap" calculation in DOPD relies on the existence of a baseline value function that can be estimated or approximated without neural network backpropagation. If the baseline is degenerate, the system switches to a normalized baseline.
- The statistical power of the experiment (with 50 seeds) is targeted to be sufficient for moderate effect sizes; however, if the observed effect size is < 0.5, the study is explicitly considered exploratory and underpowered for moderate effects.
- The environment generation process is deterministic given a random seed, ensuring that training and test sets can be reproduced exactly for debugging and verification.
- The "privilege illusion" phenomenon is defined as the Student achieving high training accuracy by mimicking the Teacher's actions (which use the privileged signal) but failing to generalize when that signal is removed.