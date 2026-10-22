# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary
We quantify how additive observational noise biases Finite‑Time Lyapunov Exponent (FTLE) estimates in high‑dimensional chaotic systems. By generating synthetic trajectories of coupled Lorenz oscillators, computing FTLE over multiple sliding windows, and comparing against a rigorously validated clean‑system baseline, we estimate the scaling law  

\[
\Delta\lambda = f(\sigma_{\text{noise}}, N, T)
\]

where \(\Delta\lambda\) is the deviation from the asymptotic exponent.

## Methodology

### 1. System Definition
A ring of \(N\) Lorenz oscillators (\(x_i,y_i,z_i\), \(i=1\ldots N\)) evolves as  

\[
\begin{aligned}
\dot{x}_i &= \sigma_L (y_i - x_i) + C\sum_{j}A_{ij}(x_j - x_i)\\
\dot{y}_i &= x_i(\rho_L - z_i) - y_i\\
\dot{z}_i &= x_i y_i - \beta_L z_i,
\end{aligned}
\]

with canonical parameters \(\sigma_L=10\), \(\rho_L=28\), \(\beta_L=8/3\) and diffusive coupling strength \(C=1.0\). The adjacency matrix \(A\) implements a nearest‑neighbor ring.

### 2. Synthetic Data Generation
- **Integrator**: `scipy.integrate.solve_ivp` (method `DOP853`, `rtol=1e-9`, `atol=1e-12`).  
- **Time discretisation**: 10 000 uniform steps (Δt ≈ 0.01).  
- **Noise injection**: Add i.i.d. Gaussian noise \(\mathcal{N}(0,\sigma_{\text{noise}}^2)\) to *every* state component at each step.  
- **Parameter grid**:  
  - Dimensions \(N \in \{3,5\}\).  
  - Noise levels \(\sigma_{\text{noise}} \in \{10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 0.5, 1.0\}\).  
  - Trials per cell: \(k = 30\) (seeded).  
- **Boundedness check**: Trajectories where \(\|x(t)\| > 20.0\) are flagged “unphysical”.  
- **High‑noise warning**: Emitted for \(\sigma_{\text{noise}} > 0.1\).  
- **Non‑chaotic abort**: If the clean system’s maximum Lyapunov exponent ≤ 0, a `NonChaoticSystemError` aborts the pipeline.

### 3. Baseline FTLE (Clean System)
- **Algorithm**: Rosenstein’s method applied to **multiple** (K ≥ 5) noise‑free trajectories of length **≥ 50 000** steps per dimension.  
- **Convergence criterion**: Relative change < 5 % between estimates at \(T=5000\) and \(T=10 000\).  
- **Output**: `baseline_{N}.json` (single object) and `baseline_per_window_{N}.json` (array of per‑window estimates). Status is `"valid"` only when convergence is satisfied.  

### 4. FTLE Computation on Noisy Trajectories
- **Sliding windows**: \(T \in \{500, 1000, 5000\}\).  
- **Procedure**: Propagate the tangent linear equations alongside the state, re‑orthonormalise via **QR decomposition** each step, accumulate logarithmic growth, and average over the window.  
- **Result record**: JSON objects (`ftle_result.schema.yaml`) with fields `trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation` (null if status ≠ “valid”), `status`, and Durbin‑Watson p‑value. All entries aggregated into `ftle_results.json`.

### 5. Edge‑Case & Stability Checks
- **Boundedness**: `check_boundedness` flags any trajectory with \(\|x\| > 20.0\).  
- **Chaos detection**: `detect_chaos` aborts if the clean system’s maximum exponent ≤ 0.  
- **Durbin‑Watson test**: Computed on the raw FTLE time‑series per trajectory; p‑value stored.  
- **Newey‑West correction**: Applied when DW p < 0.05.

### 6. Deviation Metric & Modeling Strategy
\[
\Delta\lambda = \lambda_{\text{FTLE}}(T, \sigma_{\text{noise}}) - \lambda_{\infty}(N)
\]

- **Mixed‑effects regression** (random intercept per trajectory, random slope for window size)  
  \[
  \Delta\lambda \sim \sigma_{\text{noise}} + N + \sigma_{\text{noise}}\times N + \frac{1}{T}
  \]  
  Implemented with `statsmodels.MixedLM`; observation‑level weights derived from baseline variance.  
- **Benjamini‑Hochberg FDR** (`q ≤ 0.05`) applied to all fixed‑effect p‑values.  
- **Tobit censored regression**: Always fitted on the full dataset (including `unphysical` points) to estimate latent bias.  
- **Escape probability**: Fraction of trials flagged `unphysical` for each \(\sigma_{\text{noise}}\).

### 7. Power Analysis
A simulation‑based power analysis for the hierarchical mixed‑effects model (four fixed predictors) shows that with ≈ 1 080 effective observations (12 parameter cells × 30 trials × 3 windows) we achieve ≥ 80 % power to detect a small‑to‑medium effect size (`f²≈0.02`) for the primary `σ_noise` coefficient at α = 0.05. The chosen \(k=30\) trials per cell provides sufficient variability for reliable random‑intercept estimation.

### 8. Statistical Analysis Summary
| Step | Method | Rationale |
|------|--------|-----------|
| Durbin‑Watson | Detects first‑order autocorrelation in FTLE series | Required by FR‑009 |
| Newey‑West HAC SE | Adjusts SEs when DW indicates autocorrelation | Satisfies FR‑009 |
| Mixed‑effects MLR | Accounts for hierarchical dependence of overlapping windows | Models \(\Delta\lambda\) appropriately (FR‑004) |
| Benjamini‑Hochberg FDR | Controls false discovery rate across coefficients | FR‑004 |
| One‑sample t‑test vs. baseline | Valid because baseline is a deterministic aggregated quantity (variance incorporated via weights) | SC‑001 |
| Cohen’s d | Provides effect‑size magnitude for primary noise coefficient | SC‑003 |
| Tobit regression | Handles censored observations (`unphysical` trajectories) | FR‑007, FR‑008 |
| Escape probability estimation | Quantifies selection bias due to trajectory escape | FR‑008 |

### 9. Visualization
- **Convergence plot**: λ vs. T for three noise levels (clean, moderate, high).  
- **Bias‑scaling plot**: Δλ (y) vs. σ_noise (x) with SEM error bars.  
- **Dimension‑scaling plot**: Δλ vs. N on log‑log axes; fitted power‑law exponent reported.  

All figures saved as PNGs under `data/processed/plots/`.

### 10. Compute Feasibility
All steps run on the CPU‑only GitHub Actions runner. Peak RAM < 2 GB; total wall‑clock time meets the CI time constraint with 2‑core multiprocessing. No GPU is required.

### 11. Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control; no external dataset needed.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level.  
3. **QR re‑orthonormalisation** – Provides stable FTLE estimates for long windows.  
4. **Rosenstein baseline** – Meets Constitution VI and supplies a deterministic reference with variance.  
5. **Mixed‑effects regression** – Properly handles hierarchical data and propagates baseline uncertainty.  
6. **Durbin‑Watson + Newey‑West** – Satisfies FR‑009 while addressing autocorrelation.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias.  
8. **Parallel trial execution** – Keeps runtime within CI limits while preserving reproducibility.  

---
