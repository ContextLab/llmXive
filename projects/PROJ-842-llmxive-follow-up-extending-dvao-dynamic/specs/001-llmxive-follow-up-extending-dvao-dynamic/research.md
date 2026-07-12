# Research: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Executive Summary

This research investigates the theoretical limits of Multi-Objective Reinforcement Learning (MORL) as the number of objectives $N$ increases. We derive a closed-form lower bound on sample complexity based on the accumulation of independent noise in the advantage function. We then validate this bound empirically using synthetic tabular MDPs and a "Moving-Window Heuristic" for variance estimation, constrained to run on CPU-only hardware.

**Methodological Revision**: To address concerns regarding statistical validity and circular logic, the validation strategy has been updated. The primary statistical test is now a **Paired T-Test** comparing the Moving-Window Heuristic variance against the **Full-Batch Empirical Variance** (calculated over the same trajectory). The theoretical bound serves as a reference curve for expected scaling, but is not the subject of the t-test. The success criterion regarding the "coincidence" of statistical failure and Pareto distance has been revised to measure **correlation** rather than exact coincidence.

## Theoretical Derivation Strategy

### Noise Scaling Law (FR-001, FR-002)
The core hypothesis is that the variance of the weighted advantage function, $Var(A_{\text{weighted}})$, scales linearly with the number of objectives $N$ under the assumption of independent, identically distributed (i.i.d.) noise $\epsilon_i$.

1. **Model**: Let the advantage for objective $i$ be $A_i = \mu_i + \epsilon_i$, where $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$.
2. **Weighted Advantage**: $A_{\text{weighted}} = \sum_{i=1}^N w_i A_i$, where $\sum w_i = 1$.
3. **Variance Derivation**:
 $$Var(A_{\text{weighted}}) = Var\left(\sum_{i=1}^N w_i (\mu_i + \epsilon_i)\right) = \sum_{i=1}^N w_i^2 Var(\epsilon_i) = \sigma^2 \sum_{i=1}^N w_i^2$$
 Assuming uniform weights ($w_i = 1/N$):
 $$Var(A_{\text{weighted}}) = \sigma^2 \sum_{i=1}^N \left(\frac{1}{N}\right)^2 = \frac{\sigma^2}{N}$$
 *Revised Hypothesis*: The sample complexity $S$ required to identify a policy within $\delta$ of the Pareto frontier scales as $S \propto \frac{N \cdot \sigma^2}{\delta^2}$. This will be derived symbolically using `sympy` in `code/derivation/`.

### Assumptions & Validity (Scope Correction)
- **Independence**: Noise $\epsilon_i$ is independent across objectives.
- **Gaussianity**: Noise is Gaussian (will be tested via sensitivity analysis in FR-009 against heavy-tailed noise).
- **Linearity**: Reward functions are linear combinations of state features.
- **Scope Limitation**: The derived "fundamental limits" apply strictly to **MORL under i.i.d. Gaussian noise in tabular MDPs**. **We explicitly do NOT claim that synthetic tabular MDPs approximate the complexity of real-world LLM reward spaces**, which may exhibit heavy tails, non-stationarity, and complex correlations. Extrapolation to LLMs is a hypothesis for future work, not a current claim.

## Dataset Strategy

### Synthetic Data Generation
Since no external verified dataset exists for "MORL noise scaling laws" (and the provided `` has no URL), this project generates its own data.

| Dataset Name | Source/Generation Method | Variables | Rationale |
|:--- |:--- |:--- |:--- |
| **SyntheticMDP** | `code/simulation/synthetic_mdp.py` | State features, Actions, $N$ Reward vectors, Trajectories | Generates tabular MDPs with $N \in \{5, 10, 20, 50\}$ objectives. Ensures full control over noise correlation and variance. |

**Note**: No external URLs are cited as no verified source for this specific theoretical benchmark exists in the provided list.

## Experimental Design

### Ground Truth Definition
To ensure statistical validity and avoid circular logic:
1. **Analytical Ground Truth**: The true variance of the reward generation process, known from the generator parameters ($\sigma^2/N$).
2. **Full-Batch Empirical Variance**: Calculated by averaging the squared deviations over the **entire** generated trajectory for a specific configuration. This serves as the **Ground Truth Proxy** for the variance of the sample, as it minimizes sampling noise compared to the heuristic.
3. **Moving-Window Heuristic**: The estimator being tested.

The validation strategy compares the **Heuristic** against the **Full-Batch Empirical** (to test estimator bias) and the **Full-Batch Empirical** against the **Analytical Ground Truth** (to validate the noise model). The primary statistical test (Paired T-Test) is performed on the Heuristic vs. Full-Batch Empirical comparison.

### Environment Setup
- **State Space**: Small tabular grid (e.g., $10 \times 10$) to ensure RAM < 7GB.
- **Objectives**: $N \in \{5, 10, 20, 50\}$.
- **Noise**: $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$ with configurable correlation $\rho$.
- **Validation Independence**: The "Training Set" uses noise distribution $D_1$ (e.g., Gaussian). The "Validation Set" (held-out) uses a different distribution (e.g., $D_2$: Laplace or scaled Gaussian) to ensure the theoretical bound is not circularly validated against the training data generation process.

### Heuristic Implementation (FR-004)
- **Moving-Window Heuristic**: Estimates variance using the last $k$ steps of a rollout.
- **Window Size $k$**: Configurable. Sweep values: $k \in \{0.01, 0.05, 0.1\} \times \text{Rollout Size}$.
- **Constraint**: $k < \text{Rollout Size}$. Minimum $k$ enforced to ensure stability.

### Statistical Validation (FR-006, FR-007)
1. **Paired T-Test**: Compare the distribution of Heuristic Variance estimates against the Full-Batch Empirical Variance estimates for the same trajectory segments.
 - $H_0$: Mean difference (Heuristic - Full-Batch) = 0.
 - $\alpha = 0.05$.
 - *Correction*: This tests if the heuristic is an unbiased estimator of the empirical variance (ground truth proxy).
2. **Sensitivity Analysis**: Sweep $k$ and measure convergence rates and false-positive rates.
3. **Correlation Sweep**: Test $\rho \in \{0, 0.2, 0.5\}$ to verify robustness of the independence assumption.
4. **Heavy-Tailed Sensitivity**: Test noise distributions with heavy tails (e.g., Laplace) to assess construct validity beyond Gaussian assumptions.

### Success Metrics Alignment (Revised)
- **SC-001**: Symbolic derivation verified by `sympy` simplification.
- **SC-002**: **Correlation Analysis**: Measure the correlation between the variance estimation error (Heuristic vs. Full-Batch) and the distance to the Pareto frontier. We do not require them to coincide at a specific N, but expect a positive correlation as N increases.
- **SC-003**: Stability ratio heuristic/full-batch $\in [0.9, 1.1]$ for $\ge 95\%$ of steps.
- **SC-004**: False-positive rate variation across $k$ sweep.
- **SC-005**: Runtime < 6h on GitHub Actions free-tier.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
|:--- |:--- |:--- |
| **RAM Exceeds 7GB** | Critical (Job Failure) | Use tabular MDPs; limit state space size; process trajectories in batches; avoid storing full history. |
| **Non-Gaussian Noise** | Medium (Theory Invalid) | FR-009 sensitivity analysis will detect deviation; report as "bound holds only for Gaussian/Independent noise". |
| **Heuristic Instability** | Medium (False Negatives) | Enforce minimum $k$; implement fallback to full-batch if $k$ is too small; report convergence failure. |
| **CPU Time Limit** | High (Incomplete Results) | Optimize loops with `numpy`; limit episodes per $N$; use parallel processing for independent $N$ runs (if CI allows). |
| **Construct Validity Gap** | Medium (Generalizability) | Explicitly scope claims to tabular MDPs; use heavy-tailed noise tests to probe the limits of the model. |

## Decision Rationale (Compute Feasibility)
The plan explicitly avoids deep neural networks or large LLMs. The "Moving-Window Heuristic" is chosen over full-batch variance estimation to reduce memory footprint from $O(T \cdot N)$ to $O(k \cdot N)$, where $k \ll T$. This ensures the experiment fits within the 7GB RAM limit even for $N=50$. The use of `sympy` for derivation ensures the theoretical bound is mathematically rigorous without requiring runtime compute.