# Research: Influence of Network Topology on Thermal Conductivity in Nanomaterials

## Scientific Background

The effective thermal conductivity ($k_{eff}$) of nanowire networks is governed by both the intrinsic properties of the wires and the topological arrangement of the network. As wire diameter decreases into the nanoscale regime, surface scattering becomes significant, reducing thermal conductivity relative to bulk values. This is modeled by the Fuchs-Sondheimer theory. Additionally, the network must be percolated (connected) to conduct heat between boundaries. Near the percolation threshold ($k_c$), $k_{eff}$ follows a power-law scaling: $k_{eff} \propto (k - k_c)^t$, where $t$ is the critical exponent.

## Dataset Strategy

**Data Source**: Synthetic Generation.
No external dataset is required. The study generates its own data via Random Geometric Graphs (RGGs) to precisely control the connectivity parameter ($p$) and node count ($N$). This approach is necessary because existing datasets of nanowire networks rarely provide the ground-truth topology and thermal parameters simultaneously required for this specific scaling analysis.

**Generation Method**:
1.  **Spatial Domain**: Fixed square domain of $10 \mu m \times 10 \mu m$.
2.  **Nodes**: $N=1000$ nodes distributed uniformly at random.
3.  **Edges**: Two nodes are connected if their Euclidean distance $r \le r_c$. $r_c$ is derived from the target average degree $\langle k \rangle$ using the relation $\langle k \rangle = (N-1) \pi r_c^2 / A$, where $A$ is the domain area.
4.  **Reproducibility**: All random seeds are fixed and logged.

## Methodology

### 1. Network Generation (FR-001, FR-014)
Generate RGGs for 10 connectivity levels (target $\langle k \rangle$ ranging from 2.0 to 6.0, step 0.4). For each level, perform a pilot study (N=10) to estimate variance and adjust sample size dynamically (FR-018) up to a maximum of 200 runs per level. The pilot study calculates variance $\sigma^2$ and uses the formula $N = (Z_{\alpha/2} + Z_{\beta})^2 \sigma^2 / \delta^2$ (assuming $\delta$ = 10% deviation from $t=1.3$ i.e., $\delta=0.13$, power=0.8) to determine if the sample size must be doubled.

### 2. Physics Modeling (FR-002, FR-011, FR-012)
-   **Bulk Conductivity ($k_{bulk}$)**: Use NIST values (Si: high thermal conductivity, CNT: significantly higher, etc.).
-   **Size Correction**: Apply Fuchs-Sondheimer model: $k_{eff\_wire} = k_{bulk} [1 - \frac{3}{8}(1-p)\frac{\lambda}{d}]$, where $p=0.5$, $\lambda=40nm$, $d=50nm$.
-   **Junction Resistance**: Add series resistance $R_{junction}$ to each edge. **Sensitivity**: Perform a specific sweep on $R_{junction}$ over $\pm 10\%$ of the nominal value ($10^{-9}$ K/W), in addition to the general scaling factor sweep.
-   **Edge Resistance**: $R_{edge} = \frac{L}{k_{eff\_wire} \cdot A_{cross}} + R_{junction}$.

### 3. Solver (FR-003, FR-013)
-   **Boundary Conditions**: To mitigate systematic bias from fixed X-axis alignment, the simulation is run with **multiple boundary condition pairs**: (MinX, MaxX), (MinY, MaxY), (MinX+MinY, MaxX+MaxY), (MinX+MaxY, MaxX+MinY).
-   **Equation**: Solve $G \mathbf{V} = \mathbf{I}$ for each pair where $G$ is the conductance matrix (Laplacian), $\mathbf{V}$ is node potential, $\mathbf{I}$ is current injection (A).
-   **Method**: `scipy.sparse.linalg.spsolve` (LU decomposition) with tolerance sufficiently small.
-   **Output**: $k_{eff}^{iso} = \text{mean}(k_{eff}^{X}, k_{eff}^{Y}, k_{eff}^{D1}, k_{eff}^{D2})$. If disconnected, $k_{eff}=0$.

### 4. Analysis (FR-005, FR-006, FR-017)
-   **Percolation Threshold ($k_c$)**: Estimate $k_c$ via the inflection point of the giant component size curve ($P_{\infty}$) using a **sigmoid fit** on the *entire* dataset (including disconnected graphs). This step is performed **first** and $k_c$ is **fixed**.
-   **Scaling Law**: Fit $k_{eff} = A (\langle k \rangle - k_c)^t$ using non-linear least squares on the subset of **connected** graphs ($k_{eff} > 0$).
-   **Selection Bias Correction**: To address the bias of excluding disconnected graphs, the analysis employs a **two-part model**:
    1.  Model $P_{\infty}(\langle k \rangle)$ using logistic regression on the binary connected/disconnected outcome.
    2.  The final "effective" conductivity is reported as $k_{eff}^{adj} = k_{eff}^{fitted} \times P_{\infty}$.
-   **Collinearity**: Compute Pearson correlation matrix of $\langle k \rangle$, average path length, and clustering coefficient. Use $\langle k \rangle$ as the primary predictor. Note: In RGGs, $\langle k \rangle$ is a proxy for connection radius $r_c$. The study frames the result as "scaling with connection density" rather than pure topology.
-   **Sensitivity**: Sweep resistance scaling factor $\alpha \in \{0.9, 1.0, 1.1\}$ and $R_{junction} \in \{0.9 \times R_{nom}, 1.1 \times R_{nom}\}$.
-   **Theoretical Comparison**: Calculate the deviation $|t_{fitted} - 1.3|$ and report the p-value for the hypothesis $H_0: t = 1.3$ (using bootstrapped standard errors). Note: The comparison is framed as a consistency check for the RGG model in the finite-size regime (N=1000), acknowledging that finite-size effects may cause deviations from the asymptotic $t \approx 1.3$.

## Statistical Rigor & Feasibility

-   **Multiple Comparisons**: Only one primary regression reported.
-   **Power Analysis**: Pilot study (N=10) estimates variance. If power < 0.80 (alpha=0.05, effect size=0.13), sample size doubles (max 200).
-   **Causal Claims**: None. The study reports associational scaling laws.
-   **Collinearity**: Acknowledged. $\langle k \rangle$ is the sole predictor, but it is a proxy for connection radius $r_c$ in RGGs. The study frames the result as "scaling with connection density" rather than pure topology.
-   **Construct Validity**: The study frames the result as "scaling with connection density" acknowledging that in RGGs, $\langle k \rangle$ is a proxy for geometric radius $r_c$.
-   **Finite-Size Effects**: The comparison to $t \approx 1.3$ is framed as a consistency check. The analysis notes that N=1000 is in the finite-size regime and deviations are expected.
-   **Compute Feasibility**:
    -   **CPU**: All operations CPU-tractable.
    -   **Memory**: Sparse matrices < 1MB.
    -   **Time**: ~1000 graphs * 0.1s/graph = 100s total.
    -   **GPU**: Not required.

## Decision/Rationale

-   **Method Choice**: Random Geometric Graphs are the standard model for nanowire networks.
-   **Solver**: Sparse direct solver chosen for stability. Isotropic averaging (4 directions) mitigates directional bias.
-   **Dataset**: Synthetic generation is the only viable option for controlled topology studies without access to proprietary experimental data.
-   **Bias Correction**: The two-part model (Logistic + Power Law) is selected over simple exclusion to correct the severe selection bias near the percolation threshold.
-   **Threshold Estimation**: Two-stage estimation (Sigmoid for $k_c$ -> Fixed $k_c$ for Power Law) avoids circular validation and overfitting.