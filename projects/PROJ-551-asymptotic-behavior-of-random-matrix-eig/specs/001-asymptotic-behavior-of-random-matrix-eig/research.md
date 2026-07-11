# Research: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Scientific Background

The project investigates the **Bai-Yin / BBP (Baik-Ben Arous-Péché) phase transition** in the context of sparse perturbations. Classical random matrix theory (RMT) states that for a Wigner matrix $W_N$ (symmetric, entries $N(0, 1/N)$), the empirical spectral distribution (ESD) converges to the **Wigner Semicircle Law** with support $[-2, 2]$. When a deterministic finite-rank perturbation $P_N$ of spectral norm $\theta$ is added ($A_N = W_N + P_N$), the eigenvalues of $P_N$ that satisfy $|\theta| > 1$ emerge as **outliers** outside the bulk $[-2, 2]$, converging to $\lambda = \theta + 1/\theta$.

The central research question is whether **sparsity** in $P_N$ alters this critical threshold $\theta_c = 1$. While dense perturbations strictly follow $\theta_c=1$, sparse structures (where non-zero entries are confined to a subset of indices) may exhibit different asymptotic behaviors, potentially shifting the threshold or altering the convergence rate of outliers.

## Dataset Strategy

Since the study relies on synthetic data with controlled parameters, no external dataset is used. The "dataset" is the collection of generated matrix instances and their computed eigenvalues.

| Variable | Source | Description |
| :--- | :--- | :--- |
| `WignerMatrix` | Generated (`code/generators/wigner.py`) | Symmetric $N \times N$ matrix with $N(0, 1/N)$ entries (Dense). |
| `PerturbationMatrix` | Generated (`code/generators/perturbation.py`) | Rank-$k$ deterministic matrix with specified sparsity pattern. |
| `Eigenvalues` | Computed (`code/analysis/eigen_solver.py`) | Top 10 eigenvalues of $A_N = W_N + P_N$. |
| `OutlierFlag` | Derived (`code/analysis/outlier_detect.py`) | Boolean: $\lambda > \text{empirical\_bulk\_edge} + \text{tol}$. |
| `PerturbationNorm` | Input Parameter | $\theta \in [1.0, 3.0]$. |
| `SparsityPattern` | Input Parameter | "diagonal", "block-sparse", "random-sparse". |
| `SupportDensity` | Input Parameter | $p \in \{0.1, 0.2, 0.3\}$ for sensitivity analysis. |

**Verification**: The dataset is self-contained. The "variables" are constructed directly from the mathematical definitions in the spec, ensuring the dataset contains exactly what is needed (predictors: $N, \theta, k, p, \text{pattern}$; outcome: outlier presence).

## Methodology

### 1. Matrix Generation (FR-001, FR-002)
- **Wigner Matrices**: Generated as $W_N = \frac{1}{\sqrt{N}} (X + X^T)/2$ where $X_{ij} \sim N(0, 1)$. **Crucially, $W_N$ is stored as a dense NumPy array.** It is never converted to sparse format, as this would destroy the Wigner ensemble properties.
- **Perturbations**: Constructed to ensure **exact rank $k$**.
  - **Diagonal**: $P_N = \text{diag}(v)$ where $v$ has $k$ non-zero entries.
  - **Block-Sparse**: $P_N$ has a dense $k \times k$ block embedded in an $N \times N$ zero matrix.
  - **Random Sparse**: A dense $k \times k$ core matrix $C$ (with spectral norm $\theta$) is generated. A binary support mask $M$ (size $N \times N$) is generated with density $p$. The perturbation is $P_N = M \odot (U C U^T)$ where $U$ is a random embedding, ensuring the rank remains $k$ while the support is sparse. The spectral norm is re-normalized to $\theta$ after masking to ensure precision.
- **Constraint**: $k \in \{1, 2, 5\}$ (finite rank).

### 2. Eigenvalue Computation (FR-003, FR-010)
- **Solver**: `scipy.sparse.linalg.eigsh` (ARPACK) with `which='LA'` (Largest Algebraic).
- **Implementation**: Since $W_N$ is dense, the matrix $A_N$ is stored as a dense array. The solver is invoked via a `LinearOperator` or the dense interface to compute the top 10 eigenvalues. This avoids the overhead of converting a dense matrix to sparse (which would be nearly full anyway) while leveraging the iterative method's efficiency for extracting a small number of eigenvalues.
- **Parameters**: `k=10`, `tol=1e-10`, `maxiter=10000`.
- **Memory Safety**: For $N=2000$, the dense matrix requires $\approx 32$ MB. This is well within the 7 GB RAM limit. No sparse storage of $W_N$ is attempted.

### 3. Outlier Detection (FR-004)
- **Threshold Definition**: An eigenvalue $\lambda$ is flagged as an outlier if $\lambda > \lambda_{\text{bulk}} + \epsilon$, where $\lambda_{\text{bulk}}$ is the **empirical bulk edge** (e.g., the 99th percentile of the computed spectrum) and $\epsilon = 0.05$.
- **Rationale**: The theoretical edge (2.0) is used as a reference, but the empirical edge accounts for finite-size fluctuations (Tracy-Widom distribution). This avoids circular validation against the dense BBP theory.
- **Reference Value**: The theoretical BBP location $\lambda_{\text{BBP}} = \theta + 1/\theta$ is recorded as a reference but **not** used as the boolean criterion for `is_outlier`. This allows the study to empirically determine if the threshold shifts without assuming the dense theory is correct.
- **Ambiguity Handling**: If $\theta \approx 1$, the result is flagged as "boundary" with a confidence interval derived from the variance of the bulk edge.

### 4. Parameter Sweep (FR-005, FR-006)
- **Grid**: $\theta \in \{1.0, 1.1, \dots, 3.0\}$, $N \in \{100, 500, 1000, 2000\}$.
- **Iterations**: 100 Monte Carlo runs per configuration.
- **Sensitivity**: Support density $p \in \{0.1, 0.2, 0.3\}$ swept for random sparse patterns.
- **Metric**: Probability of outlier emergence $P(\text{outlier} | \theta, p)$.
- **Analysis**: The empirical probability curve $P(\text{outlier}|\theta)$ is fitted with a sigmoid function to estimate the inflection point $\theta_c$ and its confidence interval, increasing statistical power over simple binary counts.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since we are testing multiple $\theta$ values, we report the full curve $P(\text{outlier}|\theta)$ and the estimated $\theta_c$ with confidence intervals. If binary thresholds are derived, we will apply a Bonferroni correction or False Discovery Rate (FDR) control.
- **Power Analysis**: The sample size (100 runs) is a community standard, but the phase transition is sharp. To detect small shifts (e.g., 0.1) with high confidence, we employ **sigmoid curve fitting** on the probability data. This method leverages the shape of the transition to estimate $\theta_c$ more precisely than a simple count. A sensitivity analysis on sample size (e.g., 50 vs 200 runs) will be performed to quantify the power limitations.
- **Causal Claims**: All findings are framed as **associational**. The "perturbation" is a controlled input, not a randomized treatment in a physical sense. We do not claim sparsity *causes* a shift, but rather that it is *associated* with a different threshold in the simulation.
- **Collinearity**: The rank $k$ and norm $\theta$ are orthogonal inputs. However, the number of non-zeros in sparse patterns is correlated with the norm if not normalized; we explicitly normalize $P_N$ to have spectral norm $\theta$ regardless of sparsity.
- **Measurement Validity**: The "outlier" definition relies on the empirical bulk edge to account for finite-size effects (Tracy-Widom fluctuations), ensuring robustness. The theoretical edge (2.0) is used only as a sanity check.

## Compute Feasibility

- **Memory**: $N=2000$ dense matrix $\approx 32$ MB. 7 GB RAM is sufficient for 100 runs of $N=2000$ sequentially.
- **Time**: ARPACK for $N=2000$ takes $\approx 0.1-0.5$ seconds per run. [deferred] runs $\approx 1000-5000$ seconds ($\approx 0.3-1.4$ hours). Well within the 6-hour limit.
- **No GPU**: All operations are CPU-bound and use standard `numpy`/`scipy` which are optimized for CPU.

## Decision/Rationale

- **Why Dense Storage?** Wigner matrices are dense by definition. Sparse storage would be mathematically incorrect. Memory is not a constraint for $N=2000$.
- **Why LinearOperator?** Allows the use of iterative solvers on dense matrices without converting to sparse format, preserving the dense structure while maintaining efficiency.
- **Why Sigmoid Fitting?** The phase transition is a step function. Fitting a sigmoid to the empirical probabilities provides a robust estimator for the inflection point ($\theta_c$) and its uncertainty, addressing the power limitations of simple binary counts.
- **Why Synthetic Data?** Real-world matrices do not offer the precise control over rank and sparsity required to isolate the "sparsity effect" on the BBP threshold.
- **Why 100 Iterations?** Balances statistical power with the 6-hour runtime constraint. The curve-fitting approach maximizes the information extracted from these runs.

