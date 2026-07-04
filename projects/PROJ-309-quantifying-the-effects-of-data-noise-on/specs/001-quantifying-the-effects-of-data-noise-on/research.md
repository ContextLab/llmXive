# Research: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

## Objective

To determine the critical Signal-to-Noise Ratio (SNR) threshold at which phase space reconstruction metrics (Correlation Dimension, Lyapunov Exponents, False Nearest Neighbors) for chaotic systems (Lorenz, Rössler) degrade beyond a statistically significant error margin (defined as mean error >30% or FNN saturation >50% across N=50 realizations).

## Dataset Strategy

Since this study relies on synthetic ground-truth data with known analytical properties, no external dataset URLs are required. The "dataset" is generated programmatically to ensure exact parameter control (σ=10, ρ=28, β=8/3 for Lorenz).

| Dataset Name | Source / Generation Method | Variables Available | Validation Status |
| :--- | :--- | :--- | :--- |
| Synthetic Lorenz Trajectory | `scipy.integrate.solve_ivp` (Standard params) | Time, x, y, z | **Verified**: Ground-truth Lyapunov exponent and Correlation Dimension are established in literature. |
| Synthetic Rössler Trajectory | `scipy.integrate.solve_ivp` (Standard params) | Time, x, y, z | **Verified**: Ground-truth metrics established in literature. |
| Noisy Variants | Programmatic injection (Gaussian/Quantization) | Time, x, y, z, SNR, NoiseType | **Derived**: Generated from Synthetic Trajectories. |

**Rationale**: Using synthetic data eliminates the uncertainty of real-world measurement noise characteristics and ensures the "ground truth" is mathematically defined by the differential equations. This aligns with the project's goal of quantifying *degradation* relative to a known baseline.

## Methodology

### 1. Data Generation (FR-001)
- **System**: Lorenz and Rössler attractors.
- **Integration**: `scipy.integrate.solve_ivp` with `RK45` method.
- **Parameters**: 
  - Lorenz: σ=10, ρ=28, β=8/3.
  - Rössler: a=0.2, b=0.2, c=5.7.
- **Duration**: ≥10,000 time steps (dt=0.01).
- **Sample Size**: **N=50 independent realizations** per system. This sample size is pre-determined based on a power analysis (α=0.05, effect size d=0.8, power=0.8) which suggests N is sufficient; N=50 provides a safety margin for high-variance metrics at low SNR while remaining computationally feasible.
- **Validation**: 
  1. Verify trajectory length and absence of NaN/Inf.
  2. Compute metrics on the **mean of the 50 clean realizations**. Compare these baseline values against literature values within ±5% tolerance to validate the algorithm implementation.
  3. The **internal baseline** (mean of 50 clean realizations) serves as the "Ground Truth" for the subsequent noise-degradation error calculation, avoiding circular validation against external constants.

### 2. Noise Injection (FR-002, FR-003)
- **Gaussian Noise**: Additive White Gaussian Noise (AWGN). Variance $\sigma_n^2$ calculated from target SNR: $SNR_{dB} = 10 \log_{10}(P_{signal}/P_{noise})$.
- **Quantization Noise**: Uniform distribution $U[-\Delta/2, \Delta/2]$ where $\Delta = \frac{Range}{2^B}$. Tested at 4-bit to 16-bit resolutions.
- **SNR Levels**: {0, 5, 10, 15, 20, 25, 30} dB.
- **Verification**: Post-injection SNR measured and validated to be within ±0.5dB of target.

### 3. Metric Computation (FR-004, FR-005, FR-006)
- **Correlation Dimension ($D_2$)**: Grassberger-Procaccia algorithm. Embedding dimension search range: 2 to 10.
- **Lyapunov Exponent ($\lambda_1$)**: Rosenstein's algorithm. 
  - **Noise-Robustness Protocol**: For SNR < 20dB, apply **Local Projection Denoising** (CPU-tractable implementation) prior to Rosenstein estimation to prevent noise-induced divergence saturation.
  - Maximum evolution time determined by convergence of the divergence curve.
- **False Nearest Neighbors (FNN)**: Embedding dimension=2, threshold=10× standard deviation.
- **Statistical Rigor**:
  - **Multiple Comparisons**: 7 SNR levels × 3 metrics = 21 tests. **Holm-Bonferroni correction** applied to control Family-Wise Error Rate (FWER) for dependent tests, maintaining higher power than standard Bonferroni.
 - **Power Analysis**: Pre-determined sample size N=50 per condition ensures power ≥ 0.8 for detecting a [deferred] error effect size.
  - **Collinearity**: Acknowledged that $D_2$ and $\lambda_1$ are linked by the Kaplan-Yorke conjecture ($D_{KY} \approx 1 + \lambda_1/|\lambda_2|$). While treated as independent signals for the lookup table, the interpretation of "reconstruction failure" will discuss their correlated behavior and potential divergent sensitivity, rather than making independent causal claims.
  - **Ground Truth Reference**: Error is calculated relative to the **mean metric value of the 50 clean realizations** (internal baseline), not external literature values, to isolate noise-induced degradation from algorithmic bias.

### 4. Error Analysis & Threshold Detection (FR-007, FR-008)
- **Error Metric**: $Error\% = \frac{|Computed_{noisy} - Mean_{clean}|}{|Mean_{clean}|} \times 100$.
- **Critical Threshold**: The lowest SNR level where the **mean error** (across N=50 realizations) with 95% confidence intervals exceeds the [deferred] degradation level, OR the mean FNN rate exceeds 50%. This continuous, statistical approach replaces binary single-point checks.
- **Sensitivity Analysis**: Sweep critical threshold definition over {0.01, 0.05, 0.1} absolute error thresholds and report how the identified SNR varies.

## Compute Feasibility Assessment

- **Runtime**: The pipeline involves numerical integration (fast) and $O(N^2)$ distance calculations. With N=10,000 points and N=50 realizations, optimized loops (NumPy vectorization) and the CPU-tractable `nolds` library will keep runtime well [deferred] on CPU cores.
- **Memory**: Storing a large number of points × 3 variables × A sufficient number of iterations (SNR×Noise×System×Realizations) will be conducted to ensure statistical robustness across the experimental configurations. results in a substantial memory footprint. Even with overhead, this is < 1GB, well within the 7GB limit.
- **GPU**: Not required. All algorithms are CPU-native.

## Risks & Mitigations

- **Risk**: Finite-time convergence error in Lyapunov estimation may confound noise-induced error.
  - **Mitigation**: The error metric uses the internal clean-data mean as baseline, isolating noise effects. The study reports "total error" and discusses finite-time bias in the discussion.
- **Risk**: Correlation dimension estimation may be unstable for short time series.
  - **Mitigation**: Enforce minimum 10,000 points. If estimation fails (no plateau), the data point is flagged and excluded from the lookup table.
- **Risk**: Lyapunov estimation saturation at low SNR.
  - **Mitigation**: Implementation of Local Projection Denoising pre-processing for low-SNR data.