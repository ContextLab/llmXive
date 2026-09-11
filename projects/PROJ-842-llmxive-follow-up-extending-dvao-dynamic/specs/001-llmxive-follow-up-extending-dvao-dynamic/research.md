# Research: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Theoretical Derivation of Noise Scaling Law (User Story 1)

**Methodology:** We will derive the theoretical lower bound on sample complexity for Pareto optimality as the number of reward objectives increases, assuming independent noise. The derivation will follow a variance accumulation argument, modeling the weighted advantage function and its variance as a function of the number of objectives ($N$). The theoretical bound will be expressed as a function of $N$ and the desired error tolerance.

**Dataset Strategy:** No dataset is required for this theoretical derivation.

**Decision/Rationale:** This phase focuses on theoretical analysis, hence no dataset is needed. The code will be implemented in `src/derivation/sample_complexity.py`.

## Synthetic Environment Generation & Heuristic Implementation (User Story 2)

**Methodology:** We will generate synthetic multi-objective tabular MDPs with varying objective counts ($N \in \{5, 10, 20, 50\}$). The reward functions will be derived from random linear combinations of state features. We will implement the "Moving-Window Heuristic" for variance estimation, which calculates the estimate using only the last $k$ steps.

**Dataset Strategy:** The synthetic environments themselves constitute the dataset. These are generated programmatically and do not require external data sources.

**Decision/Rationale:** Synthetic environments allow for controlled experimentation and validation of the theoretical bound.  The code will be implemented in `src/environment/synthetic_mdp.py` and `src/heuristics/moving_window.py`.

## Statistical Validation & Sensitivity Analysis (User Story 3)

**Methodology:** We will perform a one-sample t-test comparing the mean deviation of the heuristic's variance from the theoretical bound against zero. We will sweep the window size $k$ to test sensitivity.

**Dataset Strategy:** The empirical variance data from the synthetic environment runs will be used as the dataset.

**Decision/Rationale:** Statistical tests require empirical data to validate the theoretical findings. The code will be implemented in `src/analysis/statistical_tests.py`.

## Validation Independence & Construct Validity (User Story 4)

**Methodology:** We will generate a held-out set of reward functions with a different noise distribution (e.g., heavy-tailed) and verify if the scaling law holds across diverse reward landscapes.

**Dataset Strategy:** The held-out set of reward functions constitutes the dataset.

**Decision/Rationale:** This phase aims to validate the robustness of the findings to different noise distributions.

## Sensitivity Analysis on Noise Correlation (User Story 5)

**Methodology:** We will perform a sensitivity analysis on the noise correlation structure by introducing controlled correlations ($\rho \in \{\text{zero}, 0.2, 0.5\}$) and verifying if the scaling law holds.

**Dataset Strategy:** Synthetic environments with correlated noise will be used as the dataset.

**Decision/Rationale:** This phase assesses the impact of noise correlation on the scaling law.

## Resource Constraint Enforcement (User Story 6)

**Methodology:** We will monitor resource usage during the experiments and implement graceful degradation for $N > 50$.

**Dataset Strategy:** No dataset is required for this phase.

**Decision/Rationale:** This ensures the experiments can be run within the available infrastructure.
