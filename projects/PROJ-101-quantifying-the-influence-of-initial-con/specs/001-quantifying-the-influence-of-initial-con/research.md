# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary

This research investigates the bias introduced by observational noise in Finite-Time Lyapunov Exponent (FTLE) estimates for high-dimensional chaotic systems. The core hypothesis is that noise induces a systematic positive bias in FTLE estimates that scales with noise amplitude ($\sigma$) and system dimension ($N$), deviating from the asymptotic baseline established by the clean system.

## Methodology

### 1. System Definition
The study utilizes a system of $N$ coupled Lorenz oscillators. The state vector $X \in \mathbb{R}^{3N}$ evolves according to:
$$ \dot{x}_i = \sigma_L (y_i - x_i) + C \sum_{j} A_{ij} (x_j - x_i) $$
$$ \dot{y}_i = x_i (\rho_L - z_i) - y_i $$
$$ \dot{z}_i = x_i y_i - \beta_L z_i $$
Where standard parameters $\sigma_L=10, \rho_L=28, \beta_L=8/3$ are used. Coupling is implemented via a diffusive term with strength $C$ and adjacency matrix $A$ (ring topology).

### 2. Data Generation Strategy
- **Generator**: `scipy.integrate.solve_ivp` with method `'DOP853'`, tolerances `rtol=1e-9`, `atol=1e-12`.
- **Noise Injection**: Additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ applied at every integration step to the observed state.
- **Noise Levels**: Broad range from negligible ($\sim 10^{-4}$) to significant ($\sim 2.0$). Exact values deferred to implementation to allow for iterative refinement, but must include levels where trajectories become unphysical ($\sigma > 0.1$).
- **Trajectory Length**: $T_{total} = 10,000$ steps (sufficient for FTLE convergence checks).
- **Trials**: Minimum $k=30$ independent trials per noise level (exact counts deferred). Random seeds are pinned for reproducibility.

### 3. FTLE Computation
- **Algorithm**: Benettin et al. QR-decomposition method for general FTLE calculation.
- **Baseline Validation**: Asymptotic exponent $\lambda_{\infty}$ computed on the noise-free trajectory using **Rosenstein's algorithm** (as mandated by Constitution Principle VI) to ensure the baseline is numerically converged and specific to the coupled configuration.
- **Sliding Window**: FTLE calculated over windows $T \in \{500, 1000, 5000\}$.
- **Variance**: Calculated across **independent trials** ($k$), **not** across sliding windows of the same trial, to avoid autocorrelation inflation.

### 4. Analysis & Validation
- **Deviation Metric**: $\Delta \lambda = \lambda_{FTLE}(\sigma, T) - \lambda_{\infty}$.
  - **Validity**: Only computed for trajectories that remain bounded (physical). **Unphysical trajectories are explicitly excluded from $\Delta \lambda$ regression** before the metric is computed. For unphysical trajectories, the deviation value is set to `null`.
  - **Survivorship Bias**: The probability of escape $P(\text{escape} | \sigma)$ is reported separately. The bias analysis is explicitly conditional on "bounded trajectories only".
- **Regression**: Linear and power-law models fitted to $\Delta \lambda \sim f(\sigma, N)$.
- **Statistical Tests**:
  - **Primary**: **One-sample t-test** comparing the distribution of noisy FTLE estimates against the fixed deterministic baseline $\lambda_{\infty}$. (Z-test is not applicable as population variance is unknown).
  - **Regression Inference**: P-values and confidence intervals for the regression slope (bias term).
  - **Effect Size**: Cohen's d reported for the bias term.
  - **Multiple Comparisons**: **Bonferroni/FDR corrections are explicitly NOT applied.** The analysis relies solely on the regression model's inference and one-sample t-tests. No pairwise comparisons across noise levels will be conducted.
- **Measure Shift**: The analysis distinguishes between small-noise bias (observational) and large-noise regime shifts (dynamical measure change). A threshold $\sigma_c$ will be determined empirically (e.g., where the residual of the linear fit significantly increases) to separate the "observational noise bias" regime ($\sigma < \sigma_c$) from the "dynamical measure shift" regime ($\sigma > \sigma_c$). Separate regression models will be fitted for each regime if distinct behavior is detected.
- **Edge Case Handling**:
  - **High Noise**: If $\sigma > 0.1$, trajectory boundedness is checked. If unbounded (leaves attractor), data is flagged "unphysical" and excluded from $\Delta \lambda$ regression (deviation set to null).
  - **Non-Chaotic**: If $\rho < 24.74$ or max exponent $\le 0$, analysis aborts.
  - **Measure Shift**: For high $\sigma$, the analysis distinguishes between observational noise bias and potential shifts in the dynamical measure.

## Dataset Strategy

**Note**: This project uses **synthetic data generation** (no external datasets). The "Verified datasets" block in the input is irrelevant as the data is generated via `code/simulation/generator.py`.

| Dataset/Source | Type | Access Method | Verification Status |
| :--- | :--- | :--- | :--- |
| **Coupled Lorenz System** | Synthetic | Generated via `scipy.integrate.solve_ivp` | **Verified**: Algorithm is standard numerical integration; parameters are fixed constants. |
| **FTLE Baseline** | Derived | Computed from clean trajectory (Rosenstein) | **Verified**: Convergence check required before proceeding. |

*No external URLs are cited as this is a simulation study.*

## Statistical Rigor & Feasibility

### Statistical Rigor
- **One-Sample Test**: Correctly uses **one-sample t-test** against the deterministic baseline, avoiding the methodological error of a two-sample test or z-test against a fixed scalar.
- **Regression Focus**: Prioritizes regression coefficient inference (slope p-value) as the primary test. **Bonferroni/FDR corrections are explicitly excluded** to avoid redundancy and misleading inference in a regression framework.
- **Survivorship Bias**: Explicitly models and reports escape probability; bias analysis is conditional on bounded trajectories. Unphysical trajectories have `null` deviation.
- **Variance**: Calculated across independent trials to avoid autocorrelation inflation from sliding windows.
- **Measure Shift**: Distinguishes between observational noise bias and dynamical measure shift for high noise levels by defining an empirical threshold $\sigma_c$.

### Compute Feasibility (CPU-First)
- **CPU-First Strategy**: The entire pipeline (integration + QR decomposition + regression) is computationally light for $N \le 5$ and large $T$.
  - **Memory**: Trajectory storage for $N=5$ is $\approx 10^4 \times 15 \times 8$ bytes $\approx 1.2$ MB per trial. A substantial number of trials fit easily in RAM.
  - **Time**: `DOP` integration of 15 ODEs for 10k steps takes $\approx 0.1$s per trial. trials $\approx 100$s. Total pipeline < 1 hour on 2 cores.
- **No GPU Required**: The QR decomposition for $15 \times 15$ matrices is negligible on CPU. CPU-only strategy ensures strict reproducibility on GitHub Actions.

## Decision/Rationale

1.  **Why Synthetic Data?** The research question requires precise control over noise amplitude and system dimension, which is impossible with real-world observational data where noise is uncontrolled and parameters are unknown.
2.  **Why DOP853?** High-order explicit Runge-Kutta is optimal for non-stiff chaotic systems and provides the necessary accuracy (`rtol=1e-9`) to distinguish numerical error from noise-induced bias.
3.  **Why QR Decomposition?** Standard Gram-Schmidt is numerically unstable for long integrations. QR re-orthonormalization preserves the tangent space geometry required for accurate Lyapunov exponent estimation.
4.  **Why Rosenstein for Baseline?** Constitution Principle VI mandates Rosenstein's algorithm for the baseline validation step to ensure convergence and numerical stability.
5.  **Why CPU-First?** The problem size ($N \le 5$) is trivial for modern CPUs. Using CPU avoids the complexity of CUDA environment setup in CI and ensures results are reproducible on any standard machine.
6.  **Why One-Sample Test?** The baseline is a deterministic scalar, not a random variable. A one-sample t-test correctly compares the noisy distribution against this fixed value. (Z-test is not applicable).
7.  **Why Conditional Bias Analysis?** To avoid survivorship bias, the bias analysis is restricted to bounded trajectories, with escape probability reported separately. Unphysical trajectories have null deviation.
8.  **Why Regime Separation?** To distinguish between observational noise bias (linear scaling) and dynamical measure shift (non-linear or structural change), an empirical threshold $\sigma_c$ is used to separate the regimes for analysis.
9.  **Why No Bonferroni?** The primary hypothesis is tested via regression coefficient inference. Pairwise comparisons are not performed, making multiple comparison corrections irrelevant and potentially misleading.
