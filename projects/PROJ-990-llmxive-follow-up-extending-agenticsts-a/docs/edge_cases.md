# Edge Case Documentation

This document details the edge cases encountered during the llmXive AgenticSTS pipeline execution,
their impact on statistical power and result interpretation, and the mitigation strategies implemented.

## 1. NaN Entropy Values

**Source**: `code/entropy.py` (T006b), `data/processed/edge_case_warnings.log`

**Description**:
During the calculation of Shannon entropy for legal move distributions, certain trajectories or turns
resulted in `NaN` (Not a Number) or `Infinity` values. This typically occurs when:
- The legal move distribution is empty (no valid moves).
- The probability distribution sums to zero due to floating-point underflow.
- The input data for a specific trajectory is malformed or missing move information.

**Impact on Statistical Power**:
- **Data Loss**: Trajectories with NaN entropy are excluded from downstream analyses (e.g., correlation studies, model training) unless imputed or handled. This reduces the effective sample size ($n$), directly lowering statistical power.
- **Bias**: If NaN occurrences are non-random (e.g., correlated with specific agent behaviors or game states), the remaining dataset may be biased, leading to spurious conclusions.

**Mitigation Strategy**:
- **Sentinel Value**: In `code/entropy.py`, if a calculated entropy is `NaN` or `Infinity`, a warning is logged to `data/processed/edge_case_warnings.log`, and a sentinel value (e.g., `-1.0`) is returned.
- **Fallback Logic**: Downstream tasks (e.g., T015b) detect this sentinel value and trigger an "all-layers" fallback selection, ensuring the simulation can proceed without crashing.
- **Exclusion**: For statistical tests requiring valid entropy values, trajectories with the sentinel value are explicitly excluded from the analysis set.

**Example Log Entry**:
```
WARNING: Entropy calculation resulted in NaN for trajectory_id: traj_123, turn: 45. Returning sentinel -1.0.
```

## 2. Small Sample Size (n < 300)

**Source**: `code/splitter.py` (T014a), `data/processed/edge_case_warnings.log`

**Description**:
After splitting the dataset into train/validation/test sets, the training set size ($n$) was found to be less than 300.
This threshold is based on the Central Limit Theorem and standard power analysis assumptions for detecting small-to-medium effect sizes.

**Impact on Statistical Power**:
- **Marginal Power**: With $n < 300$, the power to detect small effect sizes (e.g., Cohen's $d < 0.3$) drops significantly below the standard 0.80 target.
- **Increased Variance**: Estimates of means and variances become less stable, increasing the width of confidence intervals.
- **Generalizability**: Results may be less generalizable to the broader population of trajectories.

**Mitigation Strategy**:
- **Warning Log**: A warning is logged to `data/processed/edge_case_warnings.log` stating "Statistical power marginal (n < 300)".
- **Proceed with Caution**: The pipeline does **not** skip the ablation study or switch to heuristic fallbacks solely due to sample size. Instead, it proceeds but flags the limitation.
- **Explicit Reporting**: The final statistical report (`data/processed/statistical_analysis_report.md`) includes a "Limitations" section explicitly stating the sample size and its implications.
- **Power Analysis**: Task T044/T053 performs a post-hoc power analysis to quantify the achieved power given the observed effect size and sample size.

**Example Log Entry**:
```
WARNING: Training set size (n=250) is below the recommended threshold of 300. Statistical power may be marginal.
```

## 3. Data Homogeneity (Zero Variance in Utility Delta)

**Source**: `code/splitter.py` (T014a), `data/processed/edge_case_warnings.log`

**Description**:
After the ablation study (T008/T008c), the variance of the `utility_delta` column in the training set was found to be zero or near-zero (< 1e-6). This indicates that the ablation layers had no measurable impact on the outcome for the given trajectories, or the data is too uniform.

**Impact on Statistical Power**:
- **No Signal**: If variance is zero, there is no signal to model. Any machine learning model trained on this data will fail to learn meaningful patterns.
- **Invalid Proxy Validation**: Correlation-based validation (T014) becomes undefined or meaningless if one of the variables has zero variance.
- **False Negatives**: The system might incorrectly conclude that no layer is important.

**Mitigation Strategy**:
- **Critical Warning**: A CRITICAL warning is logged: "Data homogeneity detected; ablation labels contain no signal."
- **Heuristic Fallback**: The `USE_HEURISTIC` flag is set to `true` in `data/processed/config_state.json`. This triggers the fallback to a fixed-k heuristic (e.g., selecting top-k layers based on a static rule) instead of relying on the trained model.
- **Investigation**: This condition triggers a review of the ablation study parameters and the quality of the raw trajectory data.

**Example Log Entry**:
```
CRITICAL: Variance of utility_delta in training set is 0.0. Data homogeneity detected; ablation labels contain no signal. Setting USE_HEURISTIC=true.
```

## 4. Trajectory Divergence

**Source**: `code/divergence_checker.py` (T050), `data/processed/divergence_report.json`

**Description**:
During re-simulation (Dynamic vs. Static), some trajectories resulted in different final state hashes compared to the baseline or between runs. This indicates that the agent's behavior diverged, potentially due to non-determinism in the environment or the agent itself.

**Impact on Statistical Power**:
- **Invalid Pairing**: If trajectories diverge, the "paired" statistical tests (e.g., McNemar's, Paired t-test) become invalid because the conditions are no longer comparable.
- **Noise**: Divergence introduces noise into the comparison, potentially masking true effects.

**Mitigation Strategy**:
- **Exclusion**: Trajectories with mismatched initial/final state hashes are excluded from paired tests.
- **Logging**: Excluded trajectories are logged in `data/processed/paired_status.json`.
- **Threshold**: If divergence exceeds 10%, a warning is issued, and the results are interpreted with extreme caution.

## 5. Token Budget Pruning

**Source**: `code/simulator.py` (T015c), `data/processed/token_budget_detailed.csv`

**Description**:
In some cases, the calculated context size exceeded the maximum token budget (4096 tokens), requiring aggressive pruning of layers.

**Impact on Statistical Power**:
- **Information Loss**: Pruning removes potentially useful context, which may degrade agent performance and bias the results against the dynamic policy.
- **Edge Case Bias**: If pruning occurs frequently for specific types of trajectories, the evaluation may not reflect the policy's performance on full-context scenarios.

**Mitigation Strategy**:
- **Detailed Logging**: `data/processed/token_budget_detailed.csv` logs the initial tokens, selected layers, final tokens, and pruning reasons for every trajectory.
- **Analysis**: This data is used to analyze whether pruning is a systemic issue or an edge case, and to tune the `MIN_CONTEXT` and budget parameters.

## Conclusion

The pipeline is designed to "fail loudly" on data integrity issues (e.g., missing files, checksum mismatches) but handles computational edge cases (NaN, homogeneity, sample size) with specific logging, fallback mechanisms, and explicit reporting. All edge cases are documented in `data/processed/edge_case_warnings.log` and summarized in the final report to ensure transparent interpretation of the results.
