# Research: Influence of Network Topology on Thermal Conductivity in Nanomaterials

## Summary of Research Question

How does the connectivity distribution (average node degree) of randomly assembled nanowire networks modulate effective thermal conductivity? This research synthesizes synthetic data to determine the scaling law between graph-theoretic metrics and thermal transport, identifying the percolation threshold where conductive paths emerge.

## Dataset Strategy

**Note**: This project generates **synthetic data** via simulation. No external datasets are consumed. The "dataset" is the output of the `generate_networks.py` module, which creates random geometric graphs (RGG) based on user-specified parameters ($N$, $p$, material properties).

| Dataset Source | Type | Relevance | Access Method |
| :--- | :--- | :--- | :--- |
| **Synthetic RGG Generator** | Synthetic | Core data source for topology and conductivity. | Programmatic generation via `networkx.random_geometric_graph`. |
| **NIST Standard Values** | Reference | Baseline thermal conductivity for Si, CNT, Ag, Au. | Hardcoded defaults in `material_db.py` (FR-010). |

*Constraint Check*: The spec explicitly defines the data generation process. No external URL is needed or permitted for the primary data, ensuring reproducibility and adherence to the "No GPU/External Heavy Data" constraint.

## Methodology & Statistical Rigor

### 1. Network Generation (FR-001, FR-004)
- **Method**: Random Geometric Graphs (RGG) using `networkx`.
- **Parameters**: Node count $N=1000$; Connection probability $p \in [0.01, 0.10]$ (10 levels).
- **Metric Validation**: For each generated graph, compute average degree $\langle k \rangle$, average path length $L$, and clustering coefficient $C$.
- **Target Fit**: Ensure measured $\langle k \rangle$ is within $\pm 5\%$ of target (SC-001). If not, regenerate with adjusted $p$ or report failure.
- **Independent Variable**: The **measured average degree** $\langle k \rangle$ is used as the independent variable for regression, not the input parameter $p$. While $p$ drives the generation, $\langle k \rangle$ varies stochastically and represents the physical connectivity state of the specific network instance.

### 2. Macroscopic Geometry Definition (FR-003, FR-011)
To convert network conductance (W/K) to effective thermal conductivity (W/(m·K)), a defined macroscopic geometry is required:
- **Domain**: A square domain of side $L_{domain} = 1 \mu m$.
- **Boundaries**: 
  - **Source**: All nodes with $x < 0.1 \mu m$ are connected to a common source node at potential $V=1$.
  - **Sink**: All nodes with $x > 0.9 \mu m$ are connected to a common sink node at potential $V=0$.
  - **Insulation**: No heat flow across top/bottom boundaries ($y=0, y=L_{domain}$).
- **Cross-Section**: The effective cross-sectional area $A_{eff}$ is the sum of the cross-sectional areas of all wires intersecting the mid-plane ($x = 0.5 \mu m$).
- **Calculation**: $k_{eff} = \frac{I_{total} \cdot L_{domain}}{A_{eff} \cdot \Delta V}$, where $I_{total}$ is the total current from source to sink and $\Delta V = 1$.

### 3. Thermal Resistance Assignment (FR-002, FR-011)
- **Model**: $R = \frac{\ell}{k_{eff} \cdot A}$.
- **Size Correction**: Apply Fuchs-Sondheimer model for $d < 100\text{nm}$ to adjust bulk $k$ to $k_{eff}$.
- **Clamping**: If $R \le 0$, clamp to $10^{-9}$ K/W to prevent division by zero (Edge Case).
- **Units**: All values converted to SI (W/(m·K)) before calculation (Constitution Principle VII).

### 4. Heat Flow Solver (FR-003)
- **Method**: Sparse linear system $G \mathbf{V} = \mathbf{I}$, where $G$ is the conductance matrix (Laplacian), $\mathbf{V}$ is node potential, $\mathbf{I}$ is current injection.
- **Algorithm**: `scipy.sparse.linalg.spsolve` (direct solver).
- **Convergence**: Residual norm $\le 10^{-6}$. If failed, log and abort run (Constitution Principle VI).
- **Disconnected Graphs**: If source/sink are disconnected, $k_{eff} = 0.0$ (Edge Case).

### 5. Statistical Analysis (FR-005, FR-006)
- **Percolation Threshold**: Identify $p_c$ as the smallest $\langle k \rangle$ where $\ge 80\%$ of graphs are connected (SC-003).
- **Scaling Law**: 
  - **Sub-critical**: $k_{eff} \approx 0$.
  - **Super-critical**: Fit the critical scaling law $k_{eff} \propto (\langle k \rangle - \langle k \rangle_c)^t$ using non-linear least squares.
  - **Log-Log Form**: For visualization and linearization in the super-critical regime, plot $\log(k_{eff})$ vs $\log(\langle k \rangle - \langle k \rangle_c)$.
- **Primary Metric**: Average degree $\langle k \rangle$ is the sole predictor for the primary scaling exponent to avoid multiple-comparison issues (FR-006).
- **Collinearity**: Report Pearson correlation matrix of $\langle k \rangle$, $L$, and $C$ to demonstrate collinearity (FR-006).
- **Significance**: Calculate 95% confidence intervals and p-values for the critical exponent $t$.
  - **Scientific Rationale**: The "statistical significance" (p < 0.05) tests the hypothesis that the observed data is consistent with the theoretical critical scaling model, not the existence of a relationship (which is physically deterministic). A significant result confirms the numerical solver's accuracy and the model's validity.
- **Multiple Comparisons**: Only one primary regression is performed per grid level. If secondary metrics are tested, Bonferroni correction is applied. *Decision*: Spec mandates using average degree as primary; secondary metrics are descriptive only.

### 6. Sensitivity Analysis (FR-007, SC-004)
- **Sweep**: Resistance scaling factor $S \in \{0.9, 1.0, 1.1\}$.
- **Metric**: Max deviation in $k_{eff}$ relative to baseline ($S=1.0$).
- **Acceptance**: Deviation $\le 10\%$ (SC-004).

## Statistical Rigor & Limitations

- **Power Analysis**: The grid size (A series of simulations $\times$ 10 levels = A substantial dataset) provides high statistical power for regression ($N=1000$).
- **Causal Claims**: Claims are **associational**. The data is synthetic; no random assignment of physical parameters occurs. We describe the relationship, not a causal mechanism.
- **Collinearity**: Acknowledged that $L$ and $C$ are definitionally related to $\langle k \rangle$. The plan explicitly avoids claiming independent effects for these metrics in the primary regression model.
- **Sample Size**: 1000 samples is sufficient to detect scaling exponents with $p < 0.05$ given the low noise expected in synthetic physics simulations.
- **Multiple Testing**: Controlled by restricting the primary hypothesis test to the average degree metric.

## Compute Feasibility

- **Hardware**: Multiple CPU cores, 7GB RAM.
- **Strategy**:
  - Use sparse matrices for the conductance graph ($N=1000 \implies \approx 4000$ edges for $k=4$).
  - Avoid dense matrix operations.
  - Parallelize simulations across the 10 connectivity levels using `multiprocessing` (2 workers).
  - Total runtime estimated: < 2 hours for A series of simulations will be conducted to evaluate the research question using the established method, as supported by relevant literature [Citation]. (well under 6h limit).
- **Memory**: Graph storage $\approx 10$ MB; Solver matrices $\approx 50$ MB. Total memory usage < 500 MB.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `scipy.sparse.linalg.spsolve`** | Direct solver is stable for $N=1000$ and avoids convergence issues of iterative solvers on ill-conditioned sparse matrices. |
| **Fuchs-Sondheimer for size correction** | Standard model for nanowires $d < 100\text{nm}$; required by FR-011. |
| **Critical Scaling Fit** | Replaces global OLS to correctly model the percolation transition physics (methodology concern 90fec831). |
| **Primary Metric = Average Degree** | Required by FR-006 to avoid multiple-comparison inflation; used as the measured independent variable. |
