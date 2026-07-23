# Research: Network Topology Energy Transfer in Spin Systems

## Summary

This research investigates how network topology (Erdős-Rényi, Scale-Free, Small-World) influences the rate of energy diffusion in a non-equilibrium spin system. We generate synthetic graphs using a **stratified generation strategy** to decouple topological metrics, simulate localized energy perturbations using a simplified Ising model, and statistically correlate topological metrics (clustering, path length) with diffusion rates using **Ridge Regression** and **Partial Correlation** to isolate independent effects.

## Dataset Strategy

**Data Source**: Synthetic Generation (No external download required).
**Strategy**: All data is generated algorithmically using `networkx` and `numpy` on the CI runner. This ensures reproducibility, avoids access-gated data issues, and fits within the 14GB disk limit.

**Stratified Generation for Coverage (SC-005)**:
To ensure the sensitivity sweep (SC-005) has data at ≥5 distinct clustering coefficient cutoffs, we will not generate random graphs blindly. Instead, we will use a **stratified sampling** approach:
- Define target clustering coefficient bins across a range of low to moderate values.
- For each bin, generate a fixed number of graphs (e.g., 20 per bin) by iterating Watts-Strogatz `k` (neighbors) and `p` (rewiring) parameters until the target bin is hit.
- This guarantees that `sensitivity_sweep.json` will have non-empty bins for all 5 thresholds, avoiding the "empty bin" failure mode.

| Dataset Component | Source/Method | Verification |
|-------------------|---------------|--------------|
| **Network Graphs** | `networkx.generators.random_graphs` (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) with **stratified sampling** by clustering coefficient. | Validated against target clustering/degree distribution in `test_generators.py`. |
| **Spin States** | `numpy` arrays initialized with localized perturbation (seed node). | Checked for monotonic spatial variance increase. |
| **Simulation Logs** | Generated in-memory, serialized to `data/analysis/simulation_results.json`. | Validated against `contracts/simulation_results.schema.yaml`. |

**Feasibility Note**: 
- **CPU-First**: The Ising simulation uses vectorized `numpy` operations. No GPU is required.
- **Memory**: A 500-node graph uses <1MB RAM for the adjacency matrix and state vectors. Even 100 simultaneous simulations fit easily within 7GB RAM.
- **Time**: A moderate number of steps on a substantial number of nodes is estimated at a few minutes per graph on 2 vCPU. 100 graphs will take <6 hours.
- **Dynamic Time Budget**: If the Pilot Variance Estimation (T002) indicates high variance and low power, the batch size will be increased up to the 6-hour limit. If the limit is reached before sufficient power, the report will explicitly state the "Achieved Power Limitation".

## Statistical Rigor & Methodological Design

### 1. Multiple-Comparison Correction (FR-006)
- **Method**: Benjamini-Hochberg (BH) procedure for False Discovery Rate (FDR) control.
- **Application**: Applied when testing correlations between diffusion rate and >1 topological metric (degree, clustering, path length).
- **Fallback**: Bonferroni correction available if family-wise error rate (FWER) is strictly required.
- **Implementation**: `scipy.stats.multipletests` with `method='fdr_bh'`.

### 2. Sample Size & Power (SC-003)
- **Target**: Detect effect size $r \ge 0.3$ at $\alpha = 0.05$ with 80% power.
- **Calculation**: Based on standard power analysis for Pearson correlation.
- **Plan**: 
    - **Pilot Phase (T002)**: Run a small batch (N=20) to estimate variance within topology classes.
    - **Dynamic Adjustment**: If pilot power < 0.8, increase batch size (up to 6h limit).
    - **Limitation Reporting**: If the 6h limit prevents reaching the target sample size, the report will explicitly state the achieved power and the resulting limitation on detecting small effects.
- **Limitation**: If the 6h limit prevents reaching the target sample size, the report will explicitly state the achieved power and the resulting limitation on detecting small effects.

### 3. Causal Inference & Associational Framing (ROC-001)
- **Design**: Observational simulation. Network topologies are generated, not randomly assigned to a "treatment" in a causal sense (topology is the independent variable, but not randomized in a clinical trial sense).
- **Framing**: All claims will be framed as **associational** (e.g., "Higher clustering is associated with slower diffusion") rather than causal.
- **Assumptions**: 
    - No unmeasured confounders (synthetic data allows full control).
    - Linearity (for linear regression) or appropriate non-linear model specification.
- **Confounding Control**: We will use **stratified generation** to decouple metrics (e.g., high clustering with varying path length) and **Partial Correlation** to control for degree distribution, addressing the "confounding by topology class" issue.

### 4. Measurement Validity & Collinearity
- **Metrics**: 
    - **Clustering Coefficient**: Standard definition (transitivity).
    - **Average Path Length**: Shortest path average (for connected components).
    - **Degree Distribution**: Power-law exponent (for SF) or mean degree (for ER).
- **Collinearity Handling**: 
    - **VIF Check**: Calculate Variance Inflation Factor (VIF).
    - **Resolution Strategy**: If VIF > 5, we will:
        1. Report multicollinearity.
        2. Perform **Ridge Regression** as a robustness check.
        3. Perform **Partial Correlation** analysis to control for degree distribution and isolate the effect of clustering vs. path length.
    - **Descriptive Statistics**: Prioritize descriptive statistics for highly correlated pairs, but do not stop there; use Ridge/Partial Correlation to attempt disentangling effects.
- **Instrument Validation**: `networkx` implementations are standard and validated in literature.

### 5. Robustness & Sensitivity (FR-008, SC-005)
- **Sensitivity Sweep**: 
    - Clustering coefficient thresholds will be swept over a range of distinct values.
    - **Guaranteed Coverage**: The generation strategy ensures at least 20 graphs per bin to prevent empty bins.
    - Output: `data/analysis/sensitivity_sweep.json`.
- **Robustness Checks**: 
    - **Divergence Detection**: If energy values exceed a substantial multiple of the initial excitation, the run is flagged `[SIMULATION_DIVERGENCE]` and excluded.
    - **Connectivity**: Disconnected graphs are retried multiple times. If still disconnected, flagged `[CLUSTERING_DEVIATION]` or excluded.

## Decision Rationale: CPU vs. GPU

- **Choice**: **CPU-First**.
- **Rationale**: 
    - The Ising model is a simple spin-flip dynamics simulation. It does not require deep learning or massive parallelism.
    - `numpy` vectorization on a 500-node graph is highly efficient on CPU.
    - No CUDA kernels or transformer models are involved.
    - **GPU Escape Hatch**: Not needed. If the simulation were scaled to 100k+ nodes, a GPU might be considered, but for the current scope (≤1000 nodes), CPU is sufficient and preferred for simplicity and cost (free-tier runner).

## References

- **NetworkX**: https://networkx.org/documentation/stable/
- **Ising Model (Non-equilibrium)**: Standard statistical physics literature (e.g., Glauber dynamics).
- **Small-World Networks**: Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. *Nature*.
- **Power Analysis**: Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*.