# Research: The Impact of Bounded Confidence on Opinion Polarization Speed

## Executive Summary

This research investigates the relationship between network topology and the scaling of convergence time in the Hegselmann-Krause (HK) bounded confidence model. We hypothesize that the power-law exponent $\gamma$ in $T \propto (\epsilon - \epsilon_c)^{-\gamma}$ is not universal but depends on structural metrics like assortativity and average path length. The study uses synthetic networks ($N=500$) to ensure controlled comparison.

## Theoretical Background

### Bounded Confidence Models
The HK model (Hegselmann & Krause, 2002) describes opinion dynamics where agents $i$ update their opinion $x_i$ by averaging the opinions of neighbors $j$ within a confidence bound $\epsilon$:
$$ x_i(t+1) = x_i(t) + \frac{1}{|N_i(t)|} \sum_{j \in N_i(t)} (x_j(t) - x_i(t)) $$
where $N_i(t) = \{j : |x_i(t) - x_j(t)| \le \epsilon\}$.

### Critical Phenomena and Scaling
Near a critical threshold $\epsilon_c$, the convergence time $T$ diverges. Previous studies suggest a power-law scaling $T \sim (\epsilon - \epsilon_c)^{-\gamma}$. This research tests whether $\gamma$ is invariant across topologies (universality) or sensitive to network structure (topological dependence).

### Network Topologies
1.  **Erdős-Rényi (ER)**: Random graphs with fixed edge probability $p$. Baseline for "no structure."
2.  **Barabási-Albert (BA)**: Scale-free networks with preferential attachment. High heterogeneity in degree.
3.  **Watts-Strogatz (WS)**: Small-world networks with high clustering and short path lengths.

## Methodology

### Phase 1: Network Generation
Generate 50 independent instances for each topology ($N=500$).
-   **ER**: $p$ chosen to match average degree of BA ($\langle k \rangle \approx 10$).
-   **BA**: $m=5$ (edges added per new node).
-   **WS**: $k=10$ (initial neighbors), $p \in \{0.05, 0.1, 0.2\}$ (rewiring).

### Phase 2: Simulation
Execute discrete-time HK dynamics for $\epsilon$ over a representative range of values.
-   **Initial Conditions**: Uniform random $x_i \in [0, 1]$.
-   **Stopping Criterion**: $\max_i |x_i(t+1) - x_i(t)| < 10^{-4}$.
- **Non-convergence**: If $t > T_{max}$ (e.g., [deferred] iterations), mark as non-convergent.
-   **Repetition**: 50 seeds per configuration.

### Phase 3: Analysis (Revised for Statistical Rigor)

1.  **Critical Threshold Detection ($\epsilon_c$)**:
    -   For each of the network instances across the different topologies, we will not assume a fixed $\epsilon_c$.
    -   **Algorithm**: We will perform a grid search over candidate $\epsilon_c$ values in the range $[, 0.45]$ with step 0.01.
    -   For each candidate $\epsilon_c$, we fit the power-law model $T = A(\epsilon - \epsilon_c)^{-\gamma}$ to the convergence times for $\epsilon$ in a range slightly above $\epsilon_c$ and up to 0.50 using non-linear least squares (scipy.optimize.curve_fit).
    -   The $\epsilon_c$ that minimizes the Residual Sum of Squares (RSS) is selected as the estimate for that specific network instance. This ensures the fit is robust and $\gamma$ is estimated from the optimal critical regime.

2.  **Power-Law Fitting**:
    -   Once $\epsilon_c$ is estimated, we calculate $\gamma$ for that specific network instance using the optimal $\epsilon_c$.
    -   This process is repeated for **all network instances**, resulting in a corresponding set of $\gamma$ values (one per topology).
    -   We will report the mean and standard deviation of $\gamma$ for each topology, but the regression uses the individual 150 values.

3.  **Regression Analysis**:
    -   **Hypothesis**: $\gamma$ is predicted by structural metrics (Assortativity, PathLength).
    -   **Challenge**: Topology type (ER, BA, WS) determines the distribution of these metrics, creating perfect or near-perfect multicollinearity if included together.
    -   **Strategy**:
        -   **Model A (Topology Effect)**: Regress $\gamma \sim \text{Topology}$ (Categorical). This tests if the *type* of network matters.
        -   **Model B (Structural Effect)**: Regress $\gamma \sim \text{Assortativity} + \text{PathLength}$ *within* each topology group (separate regressions for ER, BA, WS). This tests if *variations* in structure *within* a topology affect $\gamma$.
        -   **Model C (Descriptive)**: Report the correlation between $\epsilon_c$ and $\gamma$ descriptively. We will *not* include $\epsilon_c$ as a covariate in the main regression to avoid measurement error bias, as $\epsilon_c$ is estimated from the same data used to derive $\gamma$.
    -   **Limitations**: We explicitly acknowledge that for synthetic networks, Assortativity and PathLength are deterministic functions of the Topology generation algorithm. Model B isolates the effect of structural variance *conditional* on topology, but cannot claim independence from the generation method.

## Dataset Strategy

Since this is a synthetic study, no external dataset is required. All data is generated programmatically using `networkx`.

| Component | Source | Loading Method |
|-----------|--------|----------------|
| Network Topologies | Synthetic (NetworkX) | `networkx.erdos_renyi_graph`, `barabasi_albert_graph`, `watts_strogatz_graph` |
| Opinion Dynamics | Synthetic (Custom Code) | `simulate_hk.py` |
| Structural Metrics | Calculated | `networkx` built-ins (`assortativity`, `average_path_length`) |

*Note: No external URLs are cited as the data is self-generated.*

## Statistical Rigor & Feasibility

### Multiple Comparison Correction
The regression analysis involves multiple predictors. We will apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR) for the p-values of the structural metrics in Model B.

### Power Analysis
With 50 network instances per topology (N=150 total $\gamma$ values), we have sufficient samples to estimate the mean convergence time with a standard error $< 5\%$ for the critical regime. The power to detect a correlation between $\gamma$ and assortativity (expected $r \approx 0.4$) with $N=150$ is $> 0.95$ at $\alpha=0.05$.

### Computational Feasibility
-   **Memory**: $N=500$ agents $\times$ [deferred] steps $\times$ 3 topologies $\times$ 50 seeds. We process one seed at a time and stream results to disk to stay under a fixed memory budget.
-   **Runtime**: A large number of simulations. Estimated time per simulation is on the order of seconds (CPU). Total duration is expected to be approximately several hours. Well within the established time limit.
-   **No GPU**: The algorithm is $O(N^2)$ per step but $N=500$ is small enough for CPU vectorization (NumPy).

## Decision Rationale

### Why Static HK?
The spec (FR-002) mandates the "discrete-time Hegselmann-Krause update rule." While adaptive variants exist in literature, implementing them would violate the spec's explicit constraint. The "adaptive" suggestion from the reviewer (T033) is noted for future work but excluded from this plan to ensure deterministic execution against the current spec.

### Why $N=500$?
This size balances the need for structural metrics (assortativity, path length) to be stable estimates while keeping the $O(N^)$ computation per step tractable on a 2-core CPU.

### Why Power-Law Fit in Critical Regime?
The scaling behavior is theoretically predicted to emerge only near $\epsilon_c$. Fitting over the entire range would dilute the signal. We will use a grid-search to identify $\epsilon_c$ and fit only for $\epsilon \in [\epsilon_c + 0.05, 0.50]$.

### Why Separate Regression Models?
Including Topology and its deterministic structural metrics in a single regression leads to multicollinearity and uninterpretable coefficients. Separating the analysis (Model A vs. Model B) allows us to test both the "type" effect and the "structural variance" effect without statistical invalidity.