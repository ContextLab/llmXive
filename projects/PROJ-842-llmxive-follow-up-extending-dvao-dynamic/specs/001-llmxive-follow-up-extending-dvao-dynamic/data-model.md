# Data Model: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

This document defines the data models used in this project.  All data is generated programmatically and stored in files.

## Synthetic Environment Data

*   **`state`**: Integer representing the state of the environment.
*   **`action`**: Integer representing the action taken in the environment.
*   **`reward[i]`**: Float representing the reward received for objective $i$.
*   **`N`**: Integer representing the number of objectives.
*   **`transition_probability[state, action, next_state]`**: Float representing the probability of transitioning from `state` to `next_state` given `action`.
*   **`noise_std`**: Float representing the standard deviation of the noise in each reward objective.

**Storage**: These values will be stored in NumPy arrays and written to CSV files for analysis.  The format will be:

```csv
state,action,reward_1,reward_2,...,reward_N
0,0,0.1,0.2,...,0.5
0,1,0.3,0.4,...,0.6
...
```

## Heuristic Variance Estimation Data

*   **`window_size`**: Integer representing the size of the moving window.
*   **`advantage_estimate`**: Float representing the estimated advantage.
*   **`empirical_variance`**: Float representing the estimated variance of the advantage.
*   **`theoretical_variance`**: Float representing the theoretical variance (calculated from the derivation).

**Storage**: These values will be stored in NumPy arrays and written to CSV files for analysis.

## Statistical Analysis Data

*   **`p_value`**: Float representing the p-value from the t-test.
*   **`deviation`**: Float representing the deviation of the heuristic's variance from the theoretical bound.
*   **`correlation`**: Float representing the correlation between reward objectives.

**Storage**: These values will be stored in JSON files for reporting.

```json
{
  "p_value": 0.02,
  "deviation": 0.05,
  "correlation": 0.1
}
```
