# Research: Network Topology Energy Transfer in Spin Systems

## Research Question
How do specific topological metrics (clustering coefficient, average path length, degree distribution) correlate with the rate of energy diffusion in non-equilibrium spin systems?

## Dataset Strategy
This project utilizes **synthetic data** generated algorithmically. No external datasets are downloaded.

| Dataset Name | Source/Method | Verification Status | Usage |
| :--- | :--- | :--- | :--- |
| **Synthetic ER Graphs** | `networkx.generators.random_graphs.erdos_renyi` | Verified (Algorithmic) | Baseline random topology. |
| **Synthetic SW Graphs** | `networkx.generators.random_graphs.watts_strogatz` | Verified (Algorithmic) | Small-world topology with controlled clustering. |
| **Synthetic SF Graphs** | `networkx.generators.random_graphs.barabasi_albert_graph` | Verified (Algorithmic) | Scale-free topology. |

**Constraint Check**: The spec requires controlled clustering coefficients for SW graphs. `networkx`'s `watts_strogatz` allows tuning `beta` (rewiring probability) to target clustering ranges (0.3–0.5). If the generated `beta` does not yield the exact target, the plan includes a retry loop (up to 10 attempts) or a rejection-sampling strategy to ensure the final batch meets SC-001 (≥90% success rate).

## Methodology & Statistical Rigor

### 1. Graph Generation (FR-001)
*   **Algorithm**: Standard `networkx` implementations.
*   **Validation**: For every generated graph, compute `clustering_coefficient` and `is_connected`.
*   **Handling Mismatches**: If a graph fails connectivity, retry generation with a bounded number of attempts. If clustering deviates >5% from target, flag as `[CLUSTERING_DEVIATION]` but include in analysis with a covariate, unless the deviation is extreme (per Edge Cases).
*   **Variable Fit**: The generated graphs *contain* the required variables (degree sequence, clustering, path length) by definition. No missing data issue.
*   **Sample Size Strategy**: Target **150+ total graphs** (50 per class) to ensure sufficient power for both Regression (N=150) and ANOVA (N=50/group). If rejection sampling reduces the valid count below a sufficient threshold, the batch generation will automatically scale up to compensate.

### 2. Simulation (FR-002, FR-003)
*   **Model**: **Glauber dynamics** with a localized energy source and no heat bath (microcanonical-like relaxation) to model non-equilibrium diffusion.
    *   State: $S_i \in \{-1, +1\}$ (or energy density $E_i$).
    *   Dynamics: Probabilistic spin flips weighted by local energy gradient (neighbor alignment). This ensures energy propagation rather than simple thermal equilibration.
    *   Initialization: Localized perturbation at a seed node ($E_{seed}=1.0$, others $0.0$).
*   **Metric Definition (Diffusion Rate)**:
    *   **Problem**: In a closed system, spatial variance of energy ($Var(E_t)$) rises then falls (unimodal). A derivative over the full time course is ambiguous.
    *   **Solution**: Define **Diffusion Rate** as the **linear regression slope of spatial variance over the Transient Phase** (first 20% of simulation steps, $t \in [0, 20]$). This captures the initial propagation speed before equilibration artifacts dominate.
 * **Alternative Metric**: **Time-to-Saturation** (time step to reach [deferred] of total network energy spread) to avoid fixed-step ceiling effects.
*   **Stability**: Monitor max energy. If $E_{max} > \text{threshold}$ (indicating numerical blow-up), abort and log `[SIMULATION_DIVERGENCE]`.
*   **Compute Feasibility**:
    *   **CPU**: Pure `numpy` vectorized operations. No GPU.
    *   **Memory**: 500 nodes $\times$ 100 steps $\approx$ 50k floats per run. Negligible for 7GB RAM.
    *   **Time**: 100 steps on 500 nodes is estimated < 1 minute per graph on 2 CPU cores. 150+ graphs will complete well within 6 hours.

### 3. Statistical Analysis (FR-005, FR-006)
*   **Hypothesis**: Network metrics predict diffusion rates.
*   **Tests**:
    *   **ANOVA (Primary)**: Compare mean diffusion rates across topology classes (ER vs. SW vs. SF). With N=50/group, power is estimated >0.80 for medium effect sizes (f=0.25).
    *   **Regression (Secondary)**: Correlate continuous metrics with diffusion rates.
*   **Multicollinearity Handling**:
    *   In Watts-Strogatz and Barabási-Albert, clustering and path length are functionally coupled.
    *   **Strategy**: For regression, apply **Principal Component Analysis (PCA)** to topological metrics to create orthogonal predictors before regression. Alternatively, report **Variance Inflation Factors (VIF)** to diagnose instability and interpret coefficients cautiously.
*   **Multiple Comparison Correction (FR-006)**:
    *   Since multiple metrics are tested simultaneously, apply **Benjamini-Hochberg (BH)** procedure to control False Discovery Rate (FDR) at $\alpha=0.05$. Bonferroni available as an alternative.
*   **Power Analysis (SC-003)**:
    *   Target: Detect effect size $r \ge 0.3$.
    *   Sample Size: With 150+ realizations, power is adequate for both ANOVA (50/group) and Regression (N=150). If power is insufficient, the plan will document the limitation (observational design) but proceed with the available data.
*   **Causal Framing (ROC-001)**:
    *   The design is **observational** (simulations are run on generated graphs, not randomly assigned in a physical experiment). All claims in the final report will be **associational** (e.g., "Clustering is associated with diffusion rate," not "Clustering causes...").

### 4. Sensitivity Analysis (FR-008, SC-005)
*   **Method**: Sweep clustering coefficient cutoffs (multiple distinct thresholds) to test robustness of correlation findings.
*   **Output**: Plot of Diffusion Rate vs. Cutoff Threshold.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `networkx` for generation** | Standard, CPU-efficient, reproducible. |
| **Glauber Dynamics (Non-equilibrium)** | Models energy propagation via local gradients, distinct from simple thermal equilibration. |
| **Transient Phase Metric (t=0-20)** | Avoids the unimodal ambiguity of full-time variance derivatives; isolates the diffusion speed. |
| **PCA for Regression Predictors** | Addresses multicollinearity inherent in topological generators (clustering vs. path length). |
| **Benjamini-Hochberg for correction** | Less conservative than Bonferroni, better for exploratory research with multiple metrics. |
| **Associational Framing** | Adheres to ROC-001 and the observational nature of synthetic topology studies. |
| **CPU-only Execution** | Mandatory for GitHub Actions free-tier (no GPU available). |
| **Target N=150** | Ensures adequate power for ANOVA subgroups (50 each) while maintaining regression power. |