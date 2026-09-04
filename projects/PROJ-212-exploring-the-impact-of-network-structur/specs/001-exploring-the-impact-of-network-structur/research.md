# Research: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## 1. Research Question
Does the static topological structure of a network (specifically degree distribution, clustering coefficient, and average path length) predict the robustness of synchronization (critical coupling strength $K_c$) in a system of N=200 Kuramoto oscillators?

## 2. Dataset Strategy

The project relies on network datasets that are **open, directly downloadable, and verified** for programmatic access. The spec mentions "SNAP and Network Repository datasets".

### Verified Datasets
Based on the input verification block, the following sources are available for direct programmatic loading. **Priority is given to real-world graph datasets** to ensure the research question about "complex physical systems" remains valid.

| Dataset Name | Source URL | Programmatic Loader | Status |
|:--- |:--- |:--- |:--- |
| SNAP (email-EuAll) | ` (Direct `.mtx` via `datasets` or `urllib`) | `datasets.load_dataset("csv",...)` (if converted) or `networkx.read_matrix_market` | **Verified** (Real Graph) |
| SNAP (ca-AstroPh) | ` (Direct `.mtx`) | `networkx.read_matrix_market` | **Verified** (Real Graph) |
| SNAP (web-Stanford) | ` (Direct `.mtx`) | `networkx.read_matrix_market` | **Verified** (Real Graph) |
| Network Repository (Random Regular) | `https://networkrepository.com/random-regular.php` | `networkx.read_graphml` (if available) or synthetic generation | **Verified** (Synthetic Ground Truth) |

**Note on Dataset Fit**: The verified URLs for SNAP (email-EuAll, ca-AstroPh, web-Stanford) point to **real-world graph edge lists** (Matrix Market format). These are the primary data sources.
* **Action Plan**: The `loader.py` module will download these files and convert them to `networkx.Graph` objects.
* **Fallback**: If the real-world datasets yield fewer than 30 networks, the pipeline will generate synthetic graphs (Barabási-Albert, Erdős-Rényi, Random Regular) to meet the **N>=30** requirement. This is explicitly noted in the results to maintain transparency.

**Constraint**: No access-gated datasets (e.g., ADNI, HCP) are planned. The focus is on open, programmatic access to ensure CI feasibility.

## 3. Methodological Rigor

### 3.1 Topological Feature Extraction (FR-001)
* **Metrics**: Degree distribution (histogram), Clustering Coefficient ($C$), Average Path Length ($L$).
* **Handling Disconnected Graphs**: If a graph has $>1$ connected component, $L$ is set to `null` (infinity). This aligns with the physical reality that global synchronization is impossible in disconnected systems (US-1).
* **Collinearity Check**: Topological metrics are often correlated (e.g., high degree often implies high clustering). We will compute the Variance Inflation Factor (VIF) prior to regression.

### 3.2 Kuramoto Simulation (FR-002, FR-003)
* **Model**: $N=200$ oscillators.
* **Integration**: `scipy.integrate.solve_ivp` with `method='RK45'`.
* **Parameters**:
 * Natural frequencies $\omega_i$ drawn from a **Lorentzian distribution with width $\gamma=1.0$**.
 * Coupling strength $K$ swept across a broad range in discrete steps.
 * **Threshold Definition**: Minimum $K$ where order parameter $r(t) > 0.8$ sustained for $t \in [t_{end}-100, t_{end}]$.
* **Numerical Stability**: Random seeds pinned. Tolerances set to `rtol=1e-6` to prevent drift.
* **Theoretical Validation**: For a Lorentzian distribution with $\gamma=1.0$, the theoretical critical coupling is $K_c = 2\gamma = 2.0$. This is the ground truth for validation.

### 3.3 Statistical Analysis (FR-004, FR-005, FR-006)
* **Regression**: Linear and Polynomial (degree 2) models.
* **Cross-Validation**: **5x5-Fold Cross-Validation** is used for **all** dataset sizes (replacing LOOCV/10-fold conditional logic) to ensure robust stability estimates and align with Constitution Principle VII.
* **Multicollinearity**: VIF calculated. If $VIF > 5$, the predictor is removed or Ridge Regression is applied.
* **ANOVA**: An ANOVA test is performed on the regression model to confirm feature significance (p < 0.05) as required by Constitution Principle VII.
* **Success Criteria**:
 * **R² > 0.6**: The model must explain at least 60% of the variance.
 * **p < 0.05**: At least one predictor must be statistically significant.
* **Decoupling Target Variable**: To avoid tautology (since $K_c$ is theoretically linked to spectral properties), the analysis will also regress the **residual** ($K_{c,empirical} - K_{c,spectral}$) against topology. This tests for *additional* predictive power beyond the spectral definition.

### 3.4 Validation Strategy
* **Analytical Check (SC-006)**: A Ring Graph (N=200) will be simulated. The detected $K_c$ must match the theoretical value of **2.0** (derived from $\gamma=1.0$) within 5% tolerance.
* **Synthetic Ground Truth**: Networks with known analytical $K_c$ (e.g., Random Regular Graphs) will be generated and used to validate the regression model's predictive power on non-trivial topologies.
* **Manual Verification (SC-003)**: First 5 networks (alphabetically) will have their $r(t)$ curves manually inspected in the logs to confirm the $r>0.8$ threshold logic.

## 4. Compute Feasibility
* **CPU-First**: Kuramoto simulation for N=200 over 100 time units with RK45 is computationally light (~seconds per K-step). A full sweep (50 steps) per network will take < 2 minutes per network on a 2-core CPU.
* **Memory**: NetworkX graphs for N=200 are negligible in size. Pandas DataFrames for < 100 samples fit easily in 7GB RAM.
* **No GPU Required**: The method does not require deep learning or massive matrix operations that necessitate CUDA. The "GPU escape hatch" is not needed for this specific scientific pipeline.

## 5. Decision Rationale
The choice of **real-world graph datasets** (email-EuAll, ca-AstroPh, web-Stanford) is driven by the need to answer the research question about "complex physical systems" with empirical validity. Synthetic graphs are used only to ensure statistical power (N>=30). The **5x5-Fold Cross-Validation** is chosen to provide stable error estimates for small samples, aligning with the Constitution. The **decoupling of the target variable** via residual analysis addresses the tautology risk, ensuring the regression tests for genuine topological predictive power.
