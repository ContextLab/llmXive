# Research: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Theoretical Derivation of Noise Scaling Law (User Story 1)

### Method

We will derive the theoretical lower bound on sample complexity for Pareto optimality as the number of reward objectives ($N$) increases, assuming independent noise.  This involves:

1.  **Modeling Noise**: Define the noise per objective as independent random variables $\epsilon_i$.
2.  **Advantage Function Variance**: Derive the variance of the weighted advantage function as a function of $N$ and the noise variances.
3.  **Sample Complexity Bound**: Invert the variance relationship to solve for the sample complexity required to achieve a desired error tolerance.

### Decision/Rationale

The analysis will be performed analytically using symbolic manipulation. The resulting equations will be verified using a symbolic math engine (e.g., SymPy in Python).  CPU-first approach, reliance on symbolic derivation. No GPU needed.

### Verified datasets

*   N/A - This is a theoretical derivation.

## Synthetic Environment Generation & Heuristic Implementation (User Story 2)

### Method

1.  **Environment Generation**: Create synthetic tabular MDPs with varying objective counts ($N \in \{5, 10, 20, 50\}$). Reward functions will be derived from random linear combinations of state features.
2.  **Heuristic Implementation**: Implement the "Moving-Window Heuristic" for variance estimation, using a window size $k$ much smaller than the rollout group size.

### Decision/Rationale

The environments will be tabular to minimize computational cost and focus on the scaling of variance with $N$. The moving-window heuristic is chosen for its computational efficiency.  CPU-first approach, using NumPy and SciPy for numerical simulations.

### Verified datasets

*   N/A - Synthetic environments are generated programmatically.

## Statistical Validation & Sensitivity Analysis (User Story 3)

### Method

1.  **T-Test**: Perform a one-sample t-test comparing the mean deviation of the heuristic's variance from the theoretical bound against zero.
2.  **Sensitivity Analysis**: Sweep the window size $k$ over a set $\{0.01, 0.05, 0.1\}$ of the rollout size to assess the sensitivity of the heuristic.

### Decision/Rationale

The t-test will provide a statistical measure of the accuracy of the heuristic. The sensitivity analysis will reveal how the performance of the heuristic changes with different window sizes.  CPU-first approach, using SciPy for statistical analysis.

### Verified datasets

*   N/A - Analysis is performed on synthetic data generated in User Story 2.

## Validation Independence & Construct Validity (User Story 4)

### Method

1.  **Held-Out Dataset**: Generate a held-out set of reward functions with a heavy-tailed noise distribution.
2.  **Scaling Law Verification**: Apply the heuristic to the held-out set and verify if the scaling law still holds.

### Decision/Rationale

Using a different noise distribution will assess the robustness of the scaling law and address the construct validity risk of using only linear reward combinations. CPU-first approach.

### Verified datasets

*   N/A - Synthetic environments are generated programmatically.

## Sensitivity Analysis on Noise Correlation (User Story 5)

### Method

1.  **Correlated Noise**: Introduce controlled correlations ($\rho \in \{\text{zero}, 0.2, 0.5\}$) into the noise distribution.
2.  **Kolmogorov-Smirnov Test**: Perform a Kolmogorov-Smirnov goodness-of-fit test for the slope of sample complexity vs N for each $\rho$ value.

### Decision/Rationale

Testing with correlated noise will help understand the impact of the independence assumption and the robustness of the scaling law. CPU-first approach.

### Verified datasets

*   N/A - Synthetic environments are generated programmatically.

## Resource Constraint Enforcement (User Story 6)

### Method

Monitor resource usage during training runs and implement graceful degradation for $N > 50$ by reducing the state space size.

### Decision/Rationale

This ensures the experiments remain feasible within the GitHub Actions free-tier limits. CPU-first approach.

### Verified datasets

*   N/A - Monitoring is done during execution.
