# Data Model: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

This project primarily generates data programmatically. The key data structures are outlined below.

## Synthetic Environment

*   **State Space:** Discrete, represented as integers. Size is variable, but capped to ensure feasibility within resource constraints.
*   **Action Space:** Discrete, represented as integers.
*   **Reward Functions:** A vector of $N$ reward functions, each mapping state-action pairs to scalar rewards. Each reward function is a linear combination of state features.
*   **Transition Dynamics:** Deterministic, based on a simple tabular model.

## Empirical Results

*   **Objective Count (N):** Integer representing the number of reward objectives.
*   **Window Size (k):** Integer representing the size of the moving window for variance estimation.
*   **Empirical Variance:** Float representing the variance of the advantage function.
*   **Theoretical Bound:** Float representing the theoretical lower bound on sample complexity.
*   **Deviation:** Float representing the difference between empirical variance and the theoretical bound.
*   **p-value:** Float representing the p-value from the one-sample t-test.

## Noise Properties

*   **Noise Distribution:** String describing the noise distribution (e.g., Gaussian, heavy-tailed).
*   **Noise Parameters:** Dictionary containing the parameters of the noise distribution (e.g., mean, standard deviation).
*   **Actual Correlation:** Float representing the achieved correlation between reward objectives.

These data structures will be represented in CSV and JSON files for storage and analysis.
