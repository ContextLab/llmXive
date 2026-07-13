# Research: The Impact of Bounded Confidence on Opinion Polarization Speed

## 1. Problem Statement & Literature Context

The Hegselmann-Krause (HK) model describes how agents with bounded confidence ($\epsilon$) update their opinions based on neighbors within that threshold. A critical phenomenon occurs near a threshold $\epsilon_c$, where the convergence time $T$ diverges.

The core research question is whether this scaling exponent $\gamma$ is universal or if it is disrupted by network topology. Specifically, we investigate:
1.  **Scale-Free Networks (Barabási-Albert)**: Do hubs accelerate or decelerate consensus compared to random graphs?
2.  **Small-World Networks (Watts-Strogatz)**: How does the rewiring probability (and resulting path length/clustering) modulate the critical regime?

**Finite-Size Context**: We explicitly acknowledge that for a fixed network size $N=500$, the observed "divergence" is a finite-size scaling effect. We do not claim to measure a thermodynamic limit exponent, but rather compare the *relative* finite-size scaling exponents across topologies to determine structural influence. The extracted $\gamma$ is a descriptor of the critical regime width for $N=500$, not a universal constant.

## 2. Dataset Strategy

As this is a computational study using synthetic data, no external datasets are required. The "dataset" is the ensemble of generated networks and simulation runs.

**Verified Datasets**: None (Synthetic Generation).

**Generation Strategy**:
-   **Networks**: Generated using `networkx` algorithms:
    -   `erdos_renyi_graph(N=500, p)`
    -   `barabasi_albert_graph(N=500, m)`
    -   `watts_strogatz_graph(N=500, k, p_rewire)`
-   **Parameters**:
    -   $N = 500$ (fixed).
    -   Topology parameters tuned to match theoretical expectations (e.g., average degree $\approx 10$).
    -   Multiple independent seeds per topology type (Total multiple instances).
-   **Opinion Initialization**: Uniform random distribution $x_i \sim U[0, 1]$.

## 3. Methodology & Statistical Rigor

### 3.1 Simulation Protocol
-   **Update Rule**: Discrete-time HK: $x_i(t+1) = \frac{1}{|N_i|} \sum_{j \in N_i(t)} x_j(t)$ where $N_i(t) = \{j : |x_i(t) - x_j(t)| \le \epsilon\}$.
-   **Convergence Criteria**: Max change $\max_i |x_i(t+1) - x_i(t)| < 10^{-4}$.
- **Hard Limit**: [deferred] iterations (FR-007). Non-convergent runs are flagged as `non_converged`.
-   **Sweep**: $\epsilon \in [0.05, 0.50]$ step 0.05.

### 3.2 Scaling Analysis (FR-005) - Non-Circular Two-Stage Estimation
To avoid circularity in estimating $\epsilon_c$ and $\gamma$, we employ a strictly deterministic, two-stage procedure:

1.  **Stage 1: Critical Region Identification (Independent of Fit)**:
    *   For each network instance, compute the mean convergence time $\bar{T}(\epsilon)$ across the 50 seeds.
    *   Identify $\epsilon_{peak}$ as the $\epsilon$ bin where $\bar{T}(\epsilon)$ is maximized. This peak represents the point of maximum divergence for that specific network instance.
    *   Define the **Critical Regime** as the range $[\epsilon_{peak} + 0.05, 0.50]$. This range is determined *independently* of the power-law fit parameters.

2.  **Stage 2: Model Fitting & Comparison**:
    *   Fit a Power-Law model: $T = A(\epsilon - \epsilon_{peak})^{-\gamma}$.
    *   Fit an Exponential model: $T = A \exp(-k(\epsilon - \epsilon_{peak}))$.
    *   **Model Selection**: Compare models using Akaike Information Criterion (AIC).
        *   If $\Delta AIC > 10$ favoring Power-Law, report $\gamma$ and $R^2$.
        *   If $\Delta AIC > 10$ favoring Exponential, report that the power-law hypothesis is rejected for this topology.
        *   If inconclusive, report both parameters.
    *   **Validity & Bias**: We do *not* discard low $R^2$ fits. A low $R^2$ is a valid result indicating the absence of power-law scaling. All fit results (regardless of $R^2$) are reported to validly test the universality claim.

3.  **Uncertainty**: Bootstrap resampling (1,000 iterations) to estimate standard error of $\gamma$.

### 3.3 Correlation Analysis (FR-006) - Hierarchical Approach with Fixed Effects
To address confounding between topology and structural metrics:

-   **Unit of Analysis**: We perform the power-law fit for **each of the 150 network instances** individually (50 networks × 3 topologies). This yields 150 distinct $\gamma$ values, providing $N=150$ data points for regression.
-   **Model**: Multiple Linear Regression with Topology as a fixed effect:
    $$ \gamma_i = \beta_0 + \beta_1(\text{Assortativity}_i) + \beta_2(\text{Path Length}_i) + \sum_{k} \beta_k(\text{Topology}_k) + \beta_{cov}(\epsilon_{c,i}) + \eta_i $$
    where $\text{Topology}_k$ represents categorical dummy variables for ER, BA, and WS.
-   **Significance**: P-values $< 0.05$ required for structural metrics (SC-002).
-   **Collinearity Check**: Variance Inflation Factor (VIF) will be calculated. If VIF > 5, we will report the partial correlation of the metric *within* each topology type to isolate effects from the topology-level confounding.

### 3.4 Multiple Comparisons & Power
-   **Multiple Comparisons**: We will apply a False Discovery Rate (FDR) correction (Benjamini-Hochberg) to the p-values of the regression coefficients to account for testing multiple metrics.
-   **Power**: With $N=150$ data points (individual network instances) and 5 predictors (2 metrics + 3 topology dummies + covariate), the power to detect medium effect sizes ($f^2 \approx 0.15$) at $\alpha=0.05$ is $>0.95$. This is sufficient to detect structural correlations.

## 4. Compute Feasibility & Constraints

-   **Hardware**: GitHub Actions Free Tier (multi-core CPU, standard RAM).
-   **Memory Management**:
    -   Network generation: negligible memory usage.
    -   Simulation: We will run simulations sequentially or in small batches to avoid holding all state matrices in memory. Results will be streamed to disk (CSV/Parquet) immediately after each run.
    -   Expected RAM peak: < 1GB.
-   **Runtime**:
    -   Estimated time per simulation: < 0.5s on CPU.
 - Total time: $150 \times 10 \times 50 \times 0.5s \approx [deferred]s$ (10.4 hours) is too high. **Correction**: We will parallelize the 50 seeds per configuration using `multiprocessing` on the 2 available cores (batching 25 seeds per core) or optimize the inner loop. The target is < 5 hours.
    -   Optimized vectorized NumPy operations are critical.
-   **No GPU**: All operations are CPU-native. No PyTorch/TensorFlow heavy lifting; pure NumPy/NetworkX.

## 5. Decision Rationale

-   **Why NetworkX?**: It is the standard for Python graph analysis, supports all required topologies, and is CPU-efficient.
-   **Why Vectorized NumPy?**: Essential for meeting the 6-hour runtime limit. Naive Python loops would exceed the time budget.
-   **Why $N=500$?**: A balance between network realism (sufficient for scale-free properties) and computational tractability.
-   **Why Two-Stage Estimation?**: Prevents the circular dependency where $\epsilon_c$ is chosen to maximize $R^2$, ensuring the extracted $\gamma$ is not an artifact of the fitting procedure.
-   **Why Per-Instance Fitting?**: Provides $N=150$ data points for regression, enabling robust statistical inference of structural effects, unlike aggregating to $N=3$.
