# Research: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

## Executive Summary

This research plan outlines the computational investigation of the 1D Anderson model. The primary objective is to verify the theoretical prediction that all eigenstates in a 1D chain with uncorrelated disorder are localized, and to quantify the scaling of the localization length $\xi$ with disorder strength $W$. We employ two independent numerical methods: **Participation Ratio (PR) Finite-Size Scaling** and the **Transfer Matrix Method (TM)**. The study is designed to run on CPU‑only infrastructure, utilizing sparse linear algebra for large systems and rigorous statistical methods (Bonferroni correction for pairwise comparisons only) to handle multiple hypothesis testing.

## Dataset Strategy

Since this is a synthetic physics simulation, no external datasets are used. Instead, we generate "datasets" of Hamiltonian matrices and eigenstates.

| Dataset Name | Description | Source/Loader | Verification |
|--------------|-------------|---------------|--------------|
| **Synthetic 1D Anderson Hamiltonians** | 1D tight‑binding matrices with random on‑site potentials $U(-W/2, W/2)$. Generated in‑place via `numpy.random.Generator`. | `code/generate_hamiltonian.py` | Provenance logged in `data/metadata/provenance.json` with seed, $W$, $L$, and realization index. |
| **Reference Theoretical Values** | Theoretical scaling exponent $\nu$ (slope of $\log \xi$ vs $\log W$) for weak disorder. | Anderson (1958), *Phys. Rev.* | Verified via citation in `research.md` and `paper/`. |

*Note: No external URLs are cited for datasets as the data is generated procedurally. The "Verified datasets" block in the prompt is N/A for synthetic generation, but the code adheres to the "Verified Accuracy" principle by logging provenance.*

## Methodological Approach

### 1. Hamiltonian Generation (FR‑001)
We construct the Hamiltonian $H$ for a chain of length $L$:
$$
H_{ij} = \begin{cases}
\epsilon_i & i=j \\
t & |i-j|=1 \\
0 & \text{otherwise}
\end{cases}
$$
where $t=1$ and $\epsilon_i \sim U(-W/2, W/2)$. Open boundary conditions are used.
*   **Implementation**: `numpy` for matrix construction.
*   **Constraints**: Double precision (`float64`).

### 2. Participation Ratio (PR) Method (FR‑002, FR‑003)
For each disorder realization we compute eigenstates $\psi_n$ with energies $E_n$ near the band centre ($|E_n| < 0.1$). The participation ratio is
$$
\text{PR}_n = \frac{\bigl(\sum_i |\psi_{n,i}|^2\bigr)^2}{\sum_i |\psi_{n,i}|^4}.
$$
**Finite‑size scaling**: PR is measured for a set of system sizes $L \in \{100, 200, 400, 800\}$. We fit the saturation form
$$
\text{PR}(L) = a\bigl[1 - \exp(-L/\xi)\bigr] + b,
$$
where $\xi$ is the localization length and $a,b$ are shape parameters. The fit is performed via non‑linear least squares for each disorder width $W$, yielding $\xi_{\text{PR}}(W)$ and its standard error. This procedure replaces the invalid direct proportionality $\xi = C \times \text{PR}$. The scaling exponent is then extracted from the global regression of $\log \xi$ vs $\log W$.

### 3. Transfer Matrix Method (FR‑004, FR‑009)
To validate the PR results we compute the Lyapunov exponent $\gamma = 1/\xi$ using transfer matrices
$$
T_i = \begin{pmatrix}
(E - \epsilon_i)/t & -1 \\
1 & 0
\end{pmatrix}.
$$
We form the product $M_L = T_L \cdots T_1$ while **orthogonalizing after each multiplication** using QR decomposition:
1. Multiply current $M$ by $T_i$.
2. Perform QR on the result: $M = Q R$.
3. Accumulate $\log|R_{11}|$ (the logarithm of the leading R‑diagonal element).
The Lyapunov exponent is then
$$
\gamma = \frac{1}{L}\,\frac{1}{2}\sum_{i=1}^{L}\log|R_{11}^{(i)}|.
$$
This QR‑based scheme guarantees numerical stability and convergence to the true exponent per Oseledec’s theorem. Convergence is monitored by recording $\gamma(L)$ for increasing $L$ (e.g., $L=100,200,400,800$); the relative change $\Delta\gamma/\gamma$ must fall below $5\%$ at the largest $L$ (see FR‑011). All intermediate $\gamma(L)$ values are stored in `data/metadata/convergence_trace.json`.

### 4. Statistical Analysis (FR‑005, FR‑010)
*   **Scaling Fit**: Linear regression of $\log\xi$ vs $\log W$ using the $\xi_{\text{PR}}$ estimates. The slope $\hat{\beta}$, intercept, $R^2$, and 95 % confidence interval are reported.
*   **Hypothesis Testing**: Null hypothesis $H_0\!:\,\beta = -2$. A two‑sided $t$‑test is performed on the regression slope **for the weak-disorder subset ($W < 1.0$)** where the theoretical prediction holds.
*   **Bonferroni Correction**: Applied **only to pairwise comparisons** of localization lengths (e.g., testing $\xi(W_1)=\xi(W_2)$ for each of the $\binom{10}{2}$ width pairs) to control the family‑wise error rate at $\alpha=0.05$. The global slope test is a single parameter test and does not require Bonferroni correction.
*   **Power Analysis**: An *a priori* power calculation based on literature variance (estimated coefficient of variation for $\xi$ in 1D Anderson models) shows that 100 disorder realizations per $W$ yield >80 % power to detect a deviation of ±0.2 from the theoretical slope at $\alpha=0.05$. This is documented before data generation.
*   **Uncertainty Propagation**: Standard errors from the PR scaling fits are propagated through the regression using weighted least squares.

## Computational Feasibility & Resource Constraints

The implementation must run on GitHub Actions free tier (2 CPU, 7 GB RAM, 6 h limit).

| Component | Strategy | Resource Impact |
|-----------|----------|-----------------|
| **Diagonalization** | `scipy.linalg.eigh` for $L \le 800$. `scipy.sparse.linalg.eigsh` (targeting $E\approx0$) for $L=1600$. | Dense $1600\times1600$ fits comfortably in RAM; sparse fallback guarantees safety. |
| **Parallelization** | `joblib` or `multiprocessing` to parallelize disorder realizations across the two CPU cores. | Wall‑clock time roughly halved; essential for meeting the 6 h limit. |
| **Data Storage** | HDF5 (`h5py`) for raw matrices/eigenstates; CSV/Parquet for processed statistics. | Efficient I/O, prevents RAM overflow. |
| **TM Method** | QR orthogonalization with log‑accumulation; only scalar $\gamma$ stored per step. | $O(1)$ memory per iteration, negligible CPU overhead. |

**Risk Mitigation**:
*   *Risk*: $L=1600$ diagonalization exceeds 6 h. *Mitigation*: Use sparse eigensolver; if still slow, limit PR scaling to $L\le800$ and use TM for $L=1600$ only as a convergence check.
*   *Risk*: Underflow in TM product. *Mitigation*: QR + log‑accumulation (FR‑009) eliminates underflow.

## Addressing Reviewer Comments (Feynman)

**Request**: "Tell me what the electron is doing… point to a specific site."
**Response**: User Story 3 (FR‑006) is fulfilled by visualizing $|\psi_i|^2$ for a single eigenstate at $E\approx0$. The script fits $\ln|\psi_i|^2$ vs distance from the peak; the extracted decay length $\lambda$ is compared to $\xi$ from PR/TM. The resulting figure explicitly marks the localization centre, satisfying the reviewer’s interpretability demand.

## Success Criteria & Metrics

| Metric | Target | Method |
|--------|--------|--------|
| **Scaling Exponent** | 95 % CI of slope includes $-2$ for $W < 1.0$ | Linear regression on $\log\xi$ vs $\log W$ (weighted by SE) on weak-disorder subset. |
| **Method Agreement** | $|\xi_{\text{PR}}-\xi_{\text{TM}}|/\xi_{\text{PR}} \le 10\%$ for ≥80% of realizations | Pairwise comparison per realization; Bonferroni‑corrected for multiple tests. |
| **Visual Decay** | $R^2 \ge 0.95$ for log‑linear fit of $|\psi|^2$ vs distance | Regression on plotted data. |
| **Statistical Power** | ≥80 % power to detect a slope deviation of ±0.2 from $-2$ | A priori power analysis (see Section 4). |
| **FWER Control** | Bonferroni‑corrected pairwise $p$‑values ≤ 0.05 | Applied to $\binom{10}{2}$ width comparisons. |
| **Compute Feasibility** | All 1000 realizations complete ≤ 6 h, peak RAM < 7 GB | Parallel execution, sparse fallback, QR TM. |

## References

1. Anderson, P. W. (1958). "Absence of Diffusion in Certain Random Lattices". *Physical Review*.
2. Mott, N. F., & Twose, W. D. (1961). "The Theory of Impurity Conduction". *Advances in Physics*.
3. Economou, E. N. (2006). *Green’s Functions in Quantum Physics*. Springer. (For Transfer Matrix formulation)
4. Oseledec, V. I. (1968). "A multiplicative ergodic theorem. Lyapunov characteristic numbers for dynamical systems". *Transactions of the Moscow Mathematical Society*.