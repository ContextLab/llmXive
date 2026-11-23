# Research: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Research Question

Does the static topological structure of a network (specifically degree distribution, clustering coefficient, and average path length) predict the critical coupling strength required for global synchronization in a system of Kuramoto oscillators?

## Dataset Strategy

### Verified Datasets
The following datasets have been verified for accessibility and format suitability. Per the project constraints, **only** these sources will be used.

| Dataset Name | Verified URL | Format | Notes |
|:--- |:--- |:--- |:--- |
| SNAP Network Collection | ` | Matrix Market (.mtx), Edge List (.csv) | Official SNAP repository. We will programmatically fetch available graphs from this source. |
| Network Repository | `https://networkrepository.com/` | Matrix Market (.mtx), Edge List (.csv) | Official Network Repository. We will fetch graphs from this source. |

**Note on LOOCV**: No external dataset exists for "LOOCV" as it is a statistical method, not a data source. It will be implemented algorithmically.
**Note on NetworkGraph**: This is an internal entity defined in the spec, not an external dataset.

### Data Acquisition Plan
1. **Ingestion**: The `src/loader.py` module will fetch graphs from the verified SNAP and Network Repository URLs.
2. **Filtering**: We will filter for entries that resolve to valid Matrix Market (`.mtx`) or edge-list (`.csv`) files.
3. **Streaming**: Given the potential size of the collections, we will use `datasets.load_dataset(..., streaming=True)` or direct HTTP streaming to iterate through available graphs without loading the entire collection into RAM.
4. **Fallback**: If the verified URLs do not yield sufficient graphs (N < 10), the system will halt regression analysis and output a warning as per FR-004. **No synthetic data will be generated.**

## Methodology

### 1. Network Reduction Strategy
The input datasets (SNAP, Network Repository) contain networks of varying sizes (from hundreds to millions of nodes). The Kuramoto simulation requires exactly N=200 oscillators.
- **For N > 200**: We will extract a connected subgraph of exactly 200 nodes using a Breadth-First Search (BFS) starting from a random seed node. This preserves local clustering and degree distribution better than random truncation.
- **For N < 200**: The network will be used as-is, with a warning logged in `results/sim_results.json` that the network size is below the standard N=200.
- **Disconnected Graphs**: If the largest connected component is < 90% of the total nodes, the graph is flagged as "Disconnected" and excluded from regression analysis (see below).

### 2. Topological Feature Extraction
For each network $G=(V, E)$:
- **Degree Distribution**: Computed as the histogram of node degrees. We will use the *mean degree* and *degree variance* as scalar predictors. **Note**: This reduction discards higher-order information (hubs), but the study explicitly tests the predictive power of these scalar moments against the synchronization threshold, as per FR-001.
- **Clustering Coefficient**: Global clustering coefficient $C$ computed as $3 \times \text{triangles} / \text{connected triplets}$.
- **Average Path Length**: Computed on the largest connected component. **Crucially**, if the graph is disconnected (largest component < 90% of nodes), the path length is set to `null`, and the graph is **excluded** from the regression analysis to prevent bias from arbitrary imputation.

### 3. Kuramoto Synchronization Simulation
- **Model**: $\frac{d\theta_i}{dt} = \omega_i + \frac{K}{N} \sum_{j=1}^{N} A_{ij} \sin(\theta_j - \theta_i)$.
- **Parameters**: $N=200$ oscillators (or subgraph size). Natural frequencies $\omega_i \sim \mathcal{N}(0, 1)$ with a **fixed random seed (seed=42)** to ensure reproducibility. The threshold is the result of this single realization, acknowledging that ensemble averaging is computationally prohibitive for N<30.
- **Integration**: `scipy.integrate.ode` with `method='dop5'` (RK45).
- **Threshold Detection**: We use a **bisection search** on $K \in [0, 5]$ to find the critical coupling strength $K_{crit}$. The search narrows until the interval is < 0.001, minimizing quantization error. The synchronization threshold is the minimum $K$ where the order parameter $r(t) > 0.8$ for a sustained duration of $t \in [T_{end}-100, T_{end}]$.
- **Disconnected Handling**: If the graph is disconnected, $K_{crit} = \text{null}$ (or infinity) and the graph is excluded from regression.
- **Threshold Justification**: The $r=0.8$ cutoff is used as a standard community proxy for the synchronization transition in finite systems. Results are specific to this definition.

### 4. Statistical Analysis
- **Regression**: Fit Linear ($y = \beta_0 + \beta_1 x_1 + \dots$) and Polynomial ($y = \beta_0 + \beta_1 x_1 + \beta_2 x_1^2 + \dots$) models.
- **Multicollinearity**: Calculate Variance Inflation Factor (VIF) for all predictors. If $\text{VIF}_i > 5$, the system will first attempt to remove the highest VIF predictor and re-run. If VIF remains > 5 or N is too small, it will switch to Ridge Regression with alpha=1.0 and log the decision.
- **Cross-Validation**:
 - If $N < 50$: Leave-One-Out Cross-Validation (LOOCV). **Note**: LOOCV has high variance for small N. We will also report a bootstrap confidence interval for R².
 - If $N \ge 50$: 10-fold Cross-Validation.
- **Significance**: Report $R^2$, p-values, and 95% confidence intervals. If $N < 10$, report descriptive statistics only and flag "Insufficient Power".
- **Power Limitations**: If $N < 30$, the study will report the observed R² and p-values but will explicitly flag that the power is insufficient to confirm the R² > 0.6 threshold, treating it as a descriptive limit rather than a pass/fail gate.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Since we are testing multiple predictors (degree, clustering, path length), we will apply a Bonferroni correction to the p-values ($\alpha_{adj} = 0.05 / \text{number of predictors}$).
- **Theoretical Limitations**: While spectral properties (e.g., largest eigenvalue $\lambda_{max}$) are theoretically dominant drivers of synchronization, this study explicitly tests the scalar topological metrics (degree, clustering, path length) as per the Spec. We acknowledge that these metrics may not capture the full predictive power if the true driver is spectral.
- **Causal Inference**: This is an observational study of network structures. We will frame results as "associations" between topology and synchronization, not causal effects.

## Compute Feasibility

- **CPU-First**: All simulations (RK45) and statistical models (scikit-learn) are computationally lightweight for $N=200$ oscillators and typical network sizes (up to 10k nodes). No GPU is required.
- **Memory**: Streaming the dataset and processing one graph at a time ensures RAM usage remains well under the 7 GB limit.
- **Time**: With a 6-hour limit, we can process approximately 15-20 networks (assuming [deferred] per network). If the verified dataset yields more, we will process the first 20. If the pipeline exceeds 6 hours, the run is marked 'TIMEOUT' and the specific network ID causing the delay is logged.

## Verification & Validation

- **SC-003 (Manual Verification)**: The system will select the first 5 networks from the `data/raw/` directory sorted alphabetically by filename, run the simulation, and manually verify that the order parameter $r(t) > 0.8$ condition is met for the reported threshold. Results are saved to `results/verification_report.json`.
- **SC-006 (Ring Graph Validation)**: A synthetic Ring Graph (N=200) will be generated and simulated with K=0.5. The detected threshold must be within 5% of the theoretical value to pass the validation gate.