# Research: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-rewar"

## Executive Summary

This research project investigates the theoretical limits of Multi-Objective Reinforcement Learning (MORL) under noise. We derive a closed-form lower bound on sample complexity as a function of the number of objectives $N$, assuming independent noise. We then validate this bound using synthetic tabular MDPs and a "Moving-Window Heuristic" for variance estimation, ensuring all experiments run within strict CPU constraints (2 cores, ≤7 GB RAM).

## Theoretical Background

### The Noise Scaling Law
In Multi-Objective RL, the advantage function $A(s, a)$ is often a weighted sum of $N$ objective-specific advantages. If each objective $i$ has independent noise $\epsilon_i \sim \mathcal{N}(0, \sigma^2)$, the variance of the weighted advantage scales with $N$.
The core hypothesis is that the sample complexity $S$ required to identify a Pareto-optimal policy scales as $O(N \cdot \sigma^ / \epsilon^2)$, where $\epsilon$ is the desired error tolerance.
This project aims to derive the exact constant factor for this scaling law and empirically verify it.

**Convergence Criterion & Distinction**:
1.  **Derivation Target**: The theoretical lower bound is derived specifically for a policy whose distance to the theoretical Pareto frontier is **less than 5%**. This defines the "truth" the bound approximates.
2.  **Failure Criterion**: The empirical validation defines "failure" as the point where the **empirical sample count exceeds the theoretical bound by a factor of 1.5**.
3. **Non-Tautological Design**: The bound is a function of the 5% threshold. The failure test (1.5x factor) is an independent margin of error applied to the *result* of the bound. They are mathematically distinct: the bound predicts the sample count for [deferred] error; the test checks if the actual count is significantly higher (1.5x) than that prediction.

### Moving-Window Heuristic
To estimate variance in high-dimensional spaces without storing full batches (memory constraint), we employ a Moving-Window Heuristic. This calculates variance using only the last $k$ steps of a rollout.
*   **Hypothesis**: The heuristic remains accurate for $k \geq k_{min}$, but fails as $N$ increases due to noise accumulation.
*   **Validation**: We will compare the heuristic estimate against the known theoretical noise variance $\sigma^2$ injected into the synthetic environment.

## Dataset Strategy

Since this project relies on **synthetic** data generated from first principles (tabular MDPs), no external datasets are required. This ensures:
1.  **Reproducibility**: The data generation process is deterministic given a seed.
2.  **Control**: We have exact knowledge of the ground truth noise variance $\sigma^2$ and the theoretical Pareto frontier.
3.  **Feasibility**: Data generation happens in-memory, avoiding I/O bottlenecks and storage limits.

**Synthetic Data Generation Strategy**:
*   **Environment**: Tabular MDPs with state space $S$ and action space $A$.
*   **Rewards**: $N$ reward functions generated via random linear combinations of state features.
*   **Noise**: Independent Gaussian noise $\epsilon_i$ added to each reward objective.
*   **Variations**:
    *   **Objective Count**: $N \in \{5, 10, 20, 50\}$.
    *   **Noise Correlation**: $\rho \in \{0, 0.2, 0.5\}$ (Sensitivity Analysis).
    *   **Distribution Types**: Linear, Sparse, Non-Convex, and Heavy-tailed (for construct validity).
    *   **Held-Out Set**: A distinct generation pass with `heavy_tailed` noise and a different seed is performed to ensure independence.

## Methodology

### 0. Pre-Implementation Verification (Phase 0)
*   **Citation Audit**: Verify all theoretical assumptions (MORL, Pareto) against primary sources listed in `docs/citations.md`.

### 1. Theoretical Derivation (Phase 1)
*   **Method**: Symbolic mathematics using `sympy`.
*   **Input**: Model of independent noise $\epsilon_i$.
*   **Output**: Closed-form equation for $Var(A_{weighted})$ and the sample complexity bound $S_{theoretical}(N)$ **for the 5% distance threshold**.
*   **Numerical Evaluation**: The symbolic expression is converted to a numerical function for empirical comparison. **This function is evaluated using `N` from the experiment configuration and `sigma_injected` from `noise_properties.json` to ensure direct comparability.**
*   **Verification**: Automated check via `src/derivation/verify_symbolic.py` comparing algebraic steps.

### 2. Synthetic Environment Generation (Phase 2)
*   **Implementation**: `src/environment/synthetic_mdp.py`.
*   **Logic**:
    *   Generate state features.
    *   Create $N$ reward weight vectors.
    *   Inject noise with specified $\sigma^2$ and correlation $\rho$.
    *   **Constraint**: If $N > 50$, automatically reduce state space size by factor of 2 using `reduce_state_space()` (FR-016) and log the effective parameters.
    *   **Held-Out Set**: A separate execution pass with `--distribution heavy_tailed` and a distinct seed generates the held-out set.
*   **Validation**: Log achieved correlation matrix to `data/processed/noise_properties.json`.

### 3. Heuristic Implementation & Training (Phase 3)
*   **Implementation**: `src/analysis/heuristic.py`.
*   **Logic**:
    *   Execute training episodes.
    *   Calculate variance using a window of size $k$.
    *   Compare heuristic estimate to known $\sigma^2$.
*   **Resource Control**: Enforce 2 CPU cores and 7 GB RAM limit.

### 4. Statistical Validation (Phase 4)
*   **Tests**:
    *   **Noise Sanity Check (FR-014)**: Verify empirical noise matches theoretical $\sigma^2$.
    *   **Stability Significance (SC-003)**: Binomial test on heuristic stability rate.
    *   **Held-Out Set Validation (FR-012)**: Apply heuristic to the distinct heavy-tailed set.
    *   **Pareto Frontier Distance (FR-017)**: Compute true frontier via **Exhaustive Enumeration** to ensure independent ground truth.
    *   **Scaling Law Validation (SC-002)**: **Linear Regression** of `log(Sample Count)` vs `log(N)` with a **t-test on the slope coefficient**. (Replaces the incorrect KS test).
        *   **Data Flow**: Uses `pareto_frontier_distance` from the Pareto Oracle to identify the failure point.
        *   **Failure Definition**: Empirical samples > 1.5 * theoretical_bound.
    *   **Variance Estimator Validation (FR-015)**: One-sample t-test on mean deviation (Heuristic - $\sigma^2$).
    *   **Sensitivity Sweep**: Vary $k \in \{0.01, 0.05, 0.1\}$ of rollout size.
    *   **Correlation Sensitivity (FR-009)**: Sweep $\rho$ and apply **t-test on slope** (replacing KS test).
*   **Construct Validity**: Test across Linear, Sparse, Non-Convex distributions (FR-010).

## Decision / Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-First Approach** | The project involves tabular MDPs and symbolic math, which are computationally light. A GPU is unnecessary and would complicate the CI pipeline. The -core/7GB constraint is sufficient for $N \le 50$. |
| **Synthetic Data** | Real-world MORL datasets with known ground-truth noise and Pareto frontiers do not exist. Synthetic data allows precise control over $N$, $\sigma^2$, and $\rho$, which is essential for validating a theoretical bound. |
| **Moving-Window Heuristic** | Full-batch variance estimation is memory-intensive ($O(N \cdot \text{rollout\_size})$). The moving window reduces memory to $O(N \cdot k)$, enabling high $N$ within 7 GB RAM. |
| **Dynamic State Reduction** | To satisfy FR-016 and ensure feasibility for $N > 50$, the state space is reduced dynamically via `reduce_state_space()`. This is a necessary trade-off to study the scaling law at higher dimensions without OOM errors. |
| **Linear Regression for Slope** | The KS test is inappropriate for validating a regression slope. Linear regression with a t-test on the slope coefficient is the standard statistical method for this hypothesis. This applies to both the primary scaling law and the correlation sweep. |
| **Citation Audit** | Version pinning is insufficient to verify theoretical assumptions. A manual audit of primary sources (MORL, Pareto) is required to satisfy Constitution Principle II. |
| **Exhaustive Enumeration Oracle** | For the small state spaces of synthetic MDPs, Exhaustive Enumeration is computationally feasible and provides a truly independent ground truth, avoiding circular validation. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Memory Overflow at N=50** | High | Implement FR-016: Reduce state space by factor of 2 if $N > 50$ via `reduce_state_space()`. Log effective parameters. |
| **Heuristic Instability for Small k** | Medium | Enforce minimum $k$ in `heuristic.py`. If $k$ is too small, report convergence failure. |
| **Non-Gaussian Noise Violation** | Medium | FR-012 and FR-014 explicitly test heavy-tailed noise. If the bound fails, it is logged as a construct validity finding, not a failure of the code. |
| **Correlation Assumption Failure** | Low | FR-009 and US-5 explicitly test correlated noise. The theoretical bound is defined for independent noise; deviations under correlation are expected and documented. |
| **Tautology Risk** | Medium | **Mitigation**: The bound is derived for "distance < 5%". The failure is defined as "empirical > 1.5 * bound". These are distinct. |
| **Spec Contradiction** | High | **Mitigation**: Proceed with t-test (correct method) for all slope validations and file Spec Amendment for FR-009. |
| **Circular Validation** | High | **Mitigation**: The Pareto Oracle uses Exhaustive Enumeration (independent of the heuristic) to compute the true frontier. |