# Research: Influence of Network Topology on Thermal Conductivity in Nanomaterials

## Scientific Background

The effective thermal conductivity ($k_{eff}$) of nanowire networks is governed by the percolation of heat flow paths and the thermal resistance at wire junctions. Unlike bulk materials, where $k$ is an intrinsic property, network $k_{eff}$ depends heavily on topology (connectivity, path length) and nanoscale effects (surface scattering). The Fuchs-Sondheimer model is the standard approach for correcting bulk conductivity ($k_{bulk}$) for nanowires with diameter $d < 100$ nm:
$$ k_{eff} = k_{bulk} \left( 1 - \frac{3}{8} \frac{\lambda}{d} (1-p) \right) $$
where $\lambda$ is the phonon mean free path and $p$ is the specularity parameter. For this study, we assume a simplified size-correction factor $F(d)$ applied to the bulk value to calculate edge resistance $R = L / (k_{eff} \cdot A)$.

**Construct Validity Note**: This study assumes a **homogeneous** network (constant wire diameter $d$) to isolate the effect of *topology*. In realistic networks, diameter heterogeneity and contact (Kapitza) resistance are significant. These are treated as limitations; the current model focuses on the topological contribution. Contact resistance is omitted as a first-order approximation to isolate the connectivity effect, though this may overestimate $k_{eff}$ in real heterogeneous networks.

## Dataset Strategy

This project generates **synthetic data** via simulation; no external static dataset is required. The "dataset" is the set of generated graphs and their computed properties.

| Dataset Name | Source Type | URL / Loader | Verification Status |
| :--- | :--- | :--- | :--- |
| Synthetic Nanowire Networks | Generated | `networks.generate_random_geometric_graph(N, p)` | **Verified**: Generated at runtime via NetworkX. No external download. |
| Material Properties (NIST) | Internal Default | `code/config.py` (Hardcoded NIST 300K values) | **Verified**: Values match NIST standard references for Si, CNT, Ag, Au. |

**Note**: No external datasets (e.g., Hugging Face, UCI) are used because the research question requires controlled variation of topology parameters ($N$, $p$) that do not exist in static observational datasets. The "data" is the output of the simulation engine itself.

## Methodology

### 1. Graph Generation
- **Algorithm**: Random Geometric Graph (RGG) in a **unit square domain [0,1]x[0,1]**.
- **Parameters**: Node count $N=1000$, Target Average Degree $\langle k \rangle \in [2, 10]$.
- **Mapping**: Connection probability $p$ is derived from target degree to ensure density remains constant while topology varies.
- **Validation**: Ensure measured $\langle k \rangle$ is within $\pm 5\%$ of target. If not, regenerate.
- **Spatial Constraint**: Fixed domain size ensures that varying $p$ changes connectivity without changing node density.

### 2. Thermal Resistance Assignment
- **Edge Weight**: $R_{ij} = \frac{L}{k_{material} \cdot F(d) \cdot A}$.
- **Size Correction**: Apply Fuchs-Sondheimer factor for $d < 100$ nm.
- **Defaults**: Si (149), CNT (3500), Ag (429), Au (318) W/(m·K).
- **Error Handling**: If material not in defaults, raise `ValueError` requiring user input via `--k-value`.
- **Limitation**: Assumes homogeneous diameter; contact resistance is neglected.

### 3. Heat Flow Solver
- **Method**: Solve $G \cdot T = I$ where $G$ is the conductance matrix (Laplacian), $T$ is node temperature, $I$ is current source/sink.
- **Boundary Conditions**: **Source and Sink are the pair of nodes with the maximum Euclidean distance** in the graph. $T=1$ at source, $T=0$ at sink.
- **Convergence**: Iterative solver (CG) or direct solver (sparse LU) with residual $\le 10^{-6}$.
- **Edge Case**: If graph disconnected, $k_{eff} = 0$.

### 4. Statistical Analysis
- **Metrics**: Average degree ($\langle k \rangle$), Average Path Length ($L_{avg}$), Clustering Coefficient ($C$).
- **Percolation Threshold**: Identify $\langle k \rangle_c$ as the smallest average degree where $P(\text{connected})$ reaches a high probability threshold (operational definition for N=1000). Error bars on this estimate will be reported via bootstrapping.
- **Scaling Law**:
  1.  Exclude disconnected graphs ($k_{eff}=0$) from regression.
  2.  Fit critical scaling law: $k_{eff} \propto (\langle k \rangle - \langle k \rangle_c)^t$ for $\langle k \rangle > \langle k \rangle_c$.
  3.  Report scaling exponent $t$, 95% CI, and p-value.
- **Power Analysis**: A sufficient number of samples per level is used as a heuristic minimum based on typical percolation transition widths. Bootstrapping will be used to estimate confidence intervals for the exponent and validate the power assumption.
- **Robustness**: Sensitivity sweep on resistance scaling factor $\{0.9, 1.0, 1.1\}$.

## Compute Feasibility & Decision Rationale

**Decision**: CPU-First Implementation.

**Rationale**:
1.  **Algorithm Nature**: The core operations (graph generation, sparse matrix factorization, OLS regression) are classical linear algebra and combinatorial problems. They do not require GPU acceleration.
2.  **Scale**: The grid (1,000 simulations) involves small matrices ($N=1000$). Sparse solvers in `scipy` handle this efficiently on a limited number of CPU cores.
3.  **Constraints**: A reasonable time limit and memory capacity are sufficient for this workload. The research question, method, and references remain as specified in the planning document. No transformer or diffusion models are involved.
4.  **No GPU Escape Hatch Needed**: A scaled-down GPU version is unnecessary and would add complexity without performance benefit. The plan explicitly avoids GPU libraries.

## Statistical Rigor

- **Multiple Comparisons**: Only one primary metric ($\langle k \rangle$) is used for regression to avoid family-wise error inflation. Correlation matrix is reported for other metrics ($L_{avg}, C$) but not used for hypothesis testing.
- **Sample Size**: 1,000 simulations (100 per connectivity level) provide sufficient power to detect scaling exponents with $p < 0.05$, assuming typical percolation transition widths. Bootstrapping will be used to verify.
- **Causal Claims**: The study reports **associational** relationships. No random assignment of physical parameters occurs; the "cause" is the synthetic topology parameter.
- **Collinearity**: $L_{avg}$ and $C$ are often correlated with $\langle k \rangle$. The plan uses $\langle k \rangle$ as the primary predictor and reports the correlation matrix to acknowledge this dependency, avoiding claims of independent effects for derived metrics.
- **Measurement Validity**: The Fuchs-Sondheimer model is the standard for nanowire thermal transport; validation is assumed based on literature consensus.