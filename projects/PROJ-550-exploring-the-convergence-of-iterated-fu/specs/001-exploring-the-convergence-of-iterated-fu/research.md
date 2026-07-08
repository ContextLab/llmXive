# Research: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

## Executive Summary

This research investigates the behavior of Iterated Function Systems (IFS) when the contractivity condition (Lipschitz constant < 1) is relaxed. While classical IFS theory guarantees a unique attractor and invariant measure for contractive maps, the non-contractive regime (Lipschitz ≥ 1) presents a complex landscape of potential divergence, chaotic filling, or stable non-contractive attractors. This study generates a controlled dataset of synthetic IFS to empirically map the transition thresholds and validate topological descriptors against known benchmarks. The methodology has been refined to distinguish between true mathematical divergence, bounded chaos, and uniform filling, and to avoid circular definitions in statistical modeling.

## Dataset Strategy

The project relies on two sources of data:
1.  **Synthetic Data**: Generated programmatically via `code/generators.py` to ensure precise control over Lipschitz constants and map geometry.
2.  **Benchmarks**: Hardcoded implementations of Sierpinski Triangle, Barnsley Fern, and a specific expanding map from da Cunha et al. (2019) to validate the methodology.

*Note on External Datasets*: The "Verified datasets" list provided in the input contains references to IFS-adjacent datasets (e.g., `ifstruct-v1.0`), but these do not provide the specific controlled synthetic IFS instances with known Lipschitz constants required for this specific hypothesis testing. Therefore, the primary dataset is **synthetically generated** to satisfy the strict experimental design (FR-001). The verified URLs are noted for potential future expansion but are not used for the core validation of the Lipschitz transition.

**Benchmark Sources**:
-   **Sierpinski Triangle**: Standard mathematical definition (affine maps).
-   **Barnsley Fern**: Standard mathematical definition (affine maps with probabilities).
-   **Expanding Map**: Referenced from da Cunha et al. (2019) (Exact citation to be verified in code).

## Methodology

### 1. Synthetic IFS Generation (FR-001, FR-002)
-   **Approach**: Generate a set of IFS instances with 2-4 affine maps.
-   **Control**: Target Lipschitz constants ($L$) are sampled uniformly from [0.5, 2.0] in 0.1 increments.
-   **Validation**: Numerical Lipschitz constant is computed via gradient estimation.
    -   **Grid Resolution**: 1000 points for contractive maps ($L < 1.0$); 5000 points for non-contractive maps ($L \ge 1.0$) to reduce measurement error and regression dilution.
    -   **Adaptive Refinement**: For non-contractive maps, the grid is adaptively refined near high-gradient regions to capture the true supremum.
-   **Filter**: Instances where the computed $L$ deviates > 0.05 from the target are flagged and regenerated.

### 2. Invariant Measure Approximation (FR-003, FR-004)
-   **Algorithm**: Chaos Game (Random Iteration Algorithm).
-   **Iterations**: $10^6$ steps per instance (default). Extended to $5 \times 10^6$ for borderline cases.
-   **Convergence Criterion (Multi-Stage)**:
    1.  **Escape Check**: Immediate termination if points leave $[-1, 2]^2$. Classified as "Divergent".
    2.  **Transient Stability**: For bounded points, compute Wasserstein-2 ($W_2$) distance between 10 iteration windows.
    3.  **Long-Run Verification**: If $W_2$ remains high but points are bounded, extend simulation to $5 \times 10^6$ steps to distinguish slow convergence from transient chaos.
    4.  **Lyapunov Estimation**: Approximate Lyapunov exponents via finite differences to confirm stability.
-   **Classification**:
    -   **Converged**: Bounded, $W_2 < 0.01$ (stable), and Lyapunov exponent $\le 0$.
    -   **Bounded-Chaotic**: Bounded, but $W_2$ high and Lyapunov $> 0$ (no invariant measure).
    -   **Uniform Filling**: Bounded, density uniform (Lebesgue measure), distinct from Divergent.
    -   **Divergent**: Points escape bounding box.

### 3. Topological Analysis (FR-005)
-   **Metric**: Minkowski-Bouligand (Box-counting) dimension.
-   **Method**: Overlay grid scales on the point cloud; compute slope of $\log(N(\epsilon))$ vs $\log(1/\epsilon)$.
-   **Scales**: 50 logarithmically spaced scales.
-   **Transient Dimension**: For "Divergent" or "Bounded-Chaotic" sets, compute the dimension of the transient cloud before escape or over the observation window, avoiding the category error of comparing fractal vs. trivial dimensions.

### 4. Sensitivity & Modeling (FR-006, FR-007)
-   **Sensitivity**: Sweep Lipschitz threshold over {, 1.1, 1.2}. Measure standard deviation of "convergence stability" rates.
-   **Modeling**: Fit Logistic Regression (or Multinomial if needed) to predict **Existence of Invariant Measure**.
    -   **Target**: Binary (Invariant Measure Exists vs. Does Not Exist) derived from the multi-stage convergence check, not the simulation escape alone.
    -   **Features**: **Target Lipschitz** (theoretical parameter), map overlap geometry. *Note: Computed Lipschitz is NOT used as a feature to avoid circularity.*
    -   **Validation**: AUC score and permutation test ($p < 0.05$). The model is first validated on multiple benchmark instances (comparing predicted class vs. known theoretical class) before generalizing to synthetic data.

## Decision & Rationale

**Decision**: Use numerical gradient estimation with adaptive refinement for Lipschitz validation.
**Rationale**: Analytical derivation for arbitrary non-affine or complex affine combinations is intractable for a general generator. Numerical estimation on a dense grid (5000 points for non-contractive) provides a robust approximation sufficient for the ±0.05 tolerance required by the spec (SC-001) and reduces regression dilution bias.

**Decision**: Use a multi-stage convergence check (Escape, W2, Long-Run, Lyapunov).
**Rationale**: Standard point-wise convergence or fixed-window W2 is insufficient for chaotic systems. The multi-stage approach distinguishes slow convergence, transient chaos, and true divergence, providing a statistically robust metric for the existence of an invariant measure.

**Decision**: Process instances sequentially in small batches.
**Rationale**: The GitHub Actions free-tier has sufficient RAM for standard development workflows. Storing a large batch of $10^6$ point clouds simultaneously would exceed memory. Sequential processing ensures feasibility within the -hour runtime and memory constraints.

## Statistical Rigor

-   **Multiple Comparisons**: The sensitivity analysis involves three thresholds. A Bonferroni correction will be applied if multiple hypothesis tests are performed on the same dataset, though the primary metric (standard deviation of stability) is descriptive.
-   **Power Analysis**: With 500 instances, the logistic regression model has sufficient power to detect moderate effect sizes (Cohen's $d \approx 0.5$) with $p < 0.05$.
-   **Causal Inference**: The study is observational regarding the synthetic data generation. Claims of "causality" between Lipschitz constant and divergence are framed as strong associations derived from controlled generation.
-   **Collinearity**: Lipschitz constant and map overlap geometry may be correlated. Variance Inflation Factor (VIF) will be checked; if high, the model will report the relationship descriptively rather than claiming independent effects.
-   **Independence**: The model uses **Target Lipschitz** (independent theoretical parameter) to predict **Observed Behavior**, avoiding the circularity of using the **Computed Lipschitz** (derived from the map) to predict the map's own simulation outcome.

## Risks & Mitigations

-   **Risk**: Non-contractive maps may diverge too quickly to compute $W_2$.
    -   **Mitigation**: Immediate escape detection (bounding box check) terminates the simulation early, saving compute resources.
-   **Risk**: Numerical instability in gradient estimation.
    -   **Mitigation**: Grid resolution fixed at 5000 points for non-contractive maps; adaptive refinement and smoothing applied.
-   **Risk**: Runtime exceeding 6 hours.
    -   **Mitigation**: Iteration count ($10^6$) is the primary variable. If runtime is too high, the plan allows for reducing iterations for the sensitivity sweep, documented as a limitation.