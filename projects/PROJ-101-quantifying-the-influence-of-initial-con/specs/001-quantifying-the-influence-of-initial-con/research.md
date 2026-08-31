# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary

This research investigates the bias introduced by observational noise in Finite-Time Lyapunov Exponent (FTLE) estimates for high-dimensional coupled Lorenz systems. The core hypothesis is that the deviation $\Delta \lambda = \lambda_{FTLE} - \lambda_{\infty}$ scales monotonically with noise amplitude $\sigma_{noise}$ and inversely with the time window $T$, but the *functional form* (power-law, logarithmic, etc.) is unknown and must be determined via model selection. The study utilizes synthetic data generated via numerical integration, as no open-source dataset exists for *coupled* Lorenz systems with *controllable* observational noise levels and *known* ground-truth asymptotic baselines.

## Dataset Strategy

**Strategy**: Synthetic Data Generation.
**Rationale**: The research question requires precise control over noise amplitude ($\sigma_{noise}$) and system dimension ($N$) to isolate the bias effect. Existing public datasets (e.g., UCI, Hugging Face) contain real-world time series or single-oscillator data, but none offer the specific "coupled Lorenz with additive Gaussian noise" ground truth required for this controlled experiment.
**Implementation**:
- **Generator**: `code/generator.py` implements the coupled Lorenz equations using `scipy.integrate.solve_ivp` (method: 'DOP853', `rtol=1e-9`, `atol=1e-12`).
- **Noise Model**: Additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ injected at each time step.
- **Parameters**:
  - Dimensions: $N \in \{1, 3, 5, 10\}$
  - Noise Levels: $\sigma_{noise} \in \{0.0, 0.01, 0.05, 0.1, 0.5, 1.0\}$
  - Trajectory Length: $T_{total} \ge 5000$ steps (to allow $T_{window} \in \{500, 1000, 5000\}$).
- **Data Availability**: Data is generated on-the-fly during the pipeline execution. No external download is required. The generated data is stored in `data/raw/` and checksummed.

**Note on Verified Datasets**: The provided "Verified datasets" block contains legal text embedding datasets (nyaya-ae) which are irrelevant to this physics simulation. **No external dataset URLs are used.** The study relies entirely on the synthetic generator defined in `code/generator.py`.

## Methodology & Statistical Rigor

### 1. Trajectory Generation (FR-001)
- **Method**: Numerical integration of coupled Lorenz ODEs.
- **Validation**: For $\sigma=0$, the generated trajectory is compared against a reference solution to ensure numerical precision ($< 10^{-9}$).
- **Constraint**: $N=5$ generation must complete within 30 seconds on a standard CPU (verified via `test_runtime_benchmark.py`).

### 2. Asymptotic Baseline Computation (FR-003, FR-006)
- **Method**: The asymptotic Lyapunov spectrum is computed for the *specific* coupled configuration using a long trajectory ($T=10^5$) and the Benettin algorithm (QR-based method) to ensure convergence.
- **Baseline Validation**: The baseline itself is validated for finite-time bias using Richardson extrapolation (comparing $T=10^5$ and $T=2 \cdot 10^5$). The "ground truth" $\lambda_{\infty}$ is only accepted if the relative difference is $< 1\%$.
- **Gating**: The system calculates the maximum exponent $\lambda_{max}$. If the system is non-chaotic ($\lambda_{max} \le 0$) or if $\lambda_{max}$ does not converge (relative change $< 10^{-6}$ over last [deferred] of trajectory), the pipeline halts with `NonChaoticSystemError`.
- **Baseline**: The converged $\lambda_{max}$ is stored as the ground truth $\lambda_{\infty}$.

### 3. FTLE Calculation (FR-002)
- **Method**: Sliding window algorithm. For each window of size $T$, the tangent linear map is computed and the Lyapunov exponent estimated.
- **Shadowing Lemma Check**: Before computing FTLE on a noisy trajectory, the system verifies that the divergence rate does not exceed the theoretical maximum by a significant margin. If the trajectory no longer shadows a true orbit, it is flagged as "unphysical" and discarded.
- **Noise Handling**: For $\sigma > 0$, the FTLE is computed on the noisy trajectory.
- **Edge Case**: If $\sigma > 0.1$, a `HighNoiseWarning` is logged. If the trajectory state exceeds physical bounds (e.g., $|x| > 100$) or $\sigma > 1.0$ causes divergence, an `UnphysicalTrajectoryError` is raised, and the trial is discarded.

### 4. Numerical Error Floor
- **Method**: To distinguish true noise-induced bias from numerical integration artifacts, a "clean-noise" baseline is computed using high-precision arithmetic (via `mpmath`) or Richardson extrapolation.
- **Threshold**: The noise-induced bias is only reported if it exceeds the numerical error floor by a significant margin. If the bias is smaller than the error floor, the result is reported as "indistinguishable from numerical noise".

### 5. Deviation Analysis & Regression (FR-004, FR-005)
- **Metric**: $\Delta \lambda = \lambda_{FTLE} - \lambda_{\infty}$.
- **Regression**: A model selection step is performed. Two models are fitted:
  1. Power-law: $\Delta \lambda \approx \alpha \cdot \sigma^k + \beta \cdot T^{-m}$
  2. Non-parametric: LOESS (Locally Estimated Scatterplot Smoothing)
- **Selection**: The model with the lower AIC/BIC is selected as the primary result. If the LOESS fit is significantly better, the power-law coefficients are not reported as the definitive scaling law.
- **Statistical Tests**:
  - **t-test**: To test the significance of the bias term ($\alpha \neq 0$) in the selected model.
  - **Multiple Comparisons**: If multiple noise levels are tested, a Bonferroni correction is applied to the p-values to control Family-Wise Error Rate (FWER).
  - **Power Analysis**: Acknowledgement that with synthetic data, power is effectively infinite for detecting the bias, but the *magnitude* of the bias relative to the numerical error floor is the primary metric.
- **Visualization**: Plots of $\Delta \lambda$ vs. $\sigma$ (with error bars) and $\Delta \lambda$ vs. $T$.

## Decision/Rationale: CPU vs. GPU

**Decision**: **CPU-First**.
**Rationale**:
- The core computations (ODE integration, QR decomposition for Lyapunov exponents) are highly optimized in `scipy` and `numpy` and run efficiently on CPU.
- The system dimensions ($N \le $) and trajectory lengths ($T \le 10^5$) fit comfortably within the 7GB RAM and 14GB disk limits of the GitHub Actions free tier.
- No deep learning models or large matrix inversions requiring CUDA are used.
- **GPU Escape Hatch**: Not required. If future extensions involve $N > 100$ or $T > 10^7$, the pipeline would be offloaded to a Kaggle GPU, but for the current scope, CPU is sufficient and preferred for reproducibility on standard CI runners.

## Risk Mitigation

- **Numerical Instability**: Mitigated by strict tolerances (`rtol=1e-9`) and the explicit baseline convergence check (Constitution Principle VI).
- **Spec Ambiguity (Noise Threshold)**: Resolved by implementing a two-tier check: warning at 0.1, abort only on divergence (unphysical).
- **Runtime Constraint**: A dedicated benchmark task ensures the $N=5$ generation meets the 30s limit.
- **Non-Chaotic Regime**: Explicit check for $\lambda_{max} > 0$ (numerical) prevents invalid analysis.
- **Model Misspecification**: Model selection (LOESS vs. Power-law) ensures the correct functional form is reported.
- **Numerical Artifacts**: The "Numerical Error Floor" check ensures bias is not confounded with integration error.
- **Shadowing Failure**: The "Shadowing Lemma Check" ensures the validity of FTLE estimates on noisy trajectories.
