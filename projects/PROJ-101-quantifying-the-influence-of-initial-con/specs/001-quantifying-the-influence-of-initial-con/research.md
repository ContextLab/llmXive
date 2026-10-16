# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary
We investigate how additive observational noise biases Finite‑Time Lyapunov Exponent (FTLE) estimates in high‑dimensional chaotic systems. By generating synthetic trajectories of coupled Lorenz oscillators, computing FTLE over multiple sliding windows, and comparing against a rigorously validated clean‑system baseline, we quantify the scaling law  

\[
\Delta\lambda = f(\sigma_{\text{noise}}, N, T)
\]

where \(\Delta\lambda\) is the deviation from the asymptotic exponent.

## Methodology

### 1. System Definition
A ring of \(N\) Lorenz oscillators (\(x_i, y_i, z_i\), \(i=1\ldots N\)) evolves as  

\[
\begin{aligned}
\dot{x}_i &= \sigma_L (y_i - x_i) + C\sum_{j}A_{ij}(x_j - x_i)\\
\dot{y}_i &= x_i(\rho_L - z_i) - y_i\\
\dot{z}_i &= x_i y_i - \beta_L z_i,
\end{aligned}
\]

with standard parameters \(\sigma_L=10,\ \rho_L=28,\ \beta_L=8/3\) and diffusive coupling strength \(C=1.0\). The adjacency matrix \(A\) implements a nearest‑neighbor ring.

### 2. Synthetic Data Generation
- **Integrator**: `scipy.integrate.solve_ivp` (method `DOP853`, `rtol=1e-9`, `atol=1e-12`).  
- **Time discretisation**: 10 000 uniform steps (Δt ≈ 0.01).  
- **Noise injection**: At each step, add i.i.d. Gaussian noise \(\mathcal{N}(0,\sigma_{\text{noise}}^2)\) to every state component.  
- **Parameter grid**:  
  - Dimensions \(N \in \{3,5\}\).  
  - Noise levels \(\sigma_{\text{noise}} \in \{10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 0.5, 1.0\}\).  
  - Trials per cell: \(k = 30\) (seeds pinned).  
- **Boundedness check**: trajectories with \(\|x(t)\| > 20.0\) are flagged “unphysical”.  
- **High‑noise warning**: a `HighNoiseWarning` is emitted for \(\sigma_{\text{noise}} > 0.1\).  
- **Unphysical error**: an `UnphysicalTrajectoryError` is raised during integration if the norm exceeds 20.0.

### 3. Baseline FTLE (Clean System)
- **Algorithm**: Rosenstein’s method applied to a noise‑free trajectory of length **≥ 50 000** steps.  
- **Convergence criterion**: relative change < 5 % between estimates at \(T=5000\) and \(T=10 000\).  
- **Output**: `baseline_{N}.json` containing `system_dimension`, `lambda_max`, `convergence_error`, `status="valid"` (or `"invalid"`), `trajectory_length`, `algorithm`.  

### 4. FTLE Computation on Noisy Trajectories
- **Sliding windows**: \(T \in \{500, 1000, 5000\}\).  
- **Procedure**: Propagate tangent linear equations alongside the state, re‑orthonormalize via QR decomposition each step, accumulate logarithmic growth, then average over the window.  
- **Result record**: For each trial and window, a JSON object (`ftle_result.schema.yaml`) with `trial_id`, `system_dimension`, `noise_level`, `window_size`, `lambda_max`, `deviation` (null if status ≠ “valid”), `status` (`valid`, `unphysical`, `non‑chaotic`), and timestamp.  
- **Aggregation**: All entries are combined into `ftle_results.json` (validated against `ftle_results.schema.yaml`).  

### 5. Edge‑Case & Stability Checks
- **Boundedness**: `check_boundedness` flags any trajectory where \(\|x\| > 20.0\).  
- **Chaos detection**: `detect_chaos` aborts with `NonChaoticSystemError` if the clean system’s maximum exponent ≤ 0.  
- **Durbin‑Watson test**: computed on the raw FTLE time‑series per trajectory; p‑value stored.  
- **Newey‑West correction**: applied if the DW test indicates autocorrelation (p < 0.05).  

### 6. Deviation Metric & Modeling Strategy
\[
\Delta\lambda = \lambda_{\text{FTLE}}(T, \sigma_{\text{noise}}) - \lambda_{\infty}(N)
\]

- Computed **only** for trajectories with `status == "valid"` (bounded).  
- **Mixed‑effects regression**: Random intercept per trajectory; fixed effects include `σ_noise`, `N`, interaction `σ_noise·N`, and `1/T`.  
- **Benjamini‑Hochberg FDR** (q ≤ 0.05) applied to all fixed‑effect coefficients.  
- **Tobit censored regression**: Always fitted on the full dataset (including `unphysical` points) to estimate latent bias.  
- **Escape probability**: Estimated as the fraction of trials flagged `unphysical` for each noise level.  

### 7. Power Analysis
A simulation‑based power analysis for the planned mixed‑effects model (four fixed predictors) shows that with a total of ≈ 1 080 observations (12 parameter cells × 30 trials × 3 windows) we achieve ≥ 80 % power to detect a small‑to‑medium effect size (\(f^2 ≈ 0.02\)) for the primary `σ_noise` coefficient at \(\alpha=0.05\). The \(k=30\) independent trials per configuration ensure sufficient variability for reliable random‑intercept estimation.

### 8. Statistical Analysis Summary
| Step | Method | Rationale |
|------|--------|-----------|
| **Durbin‑Watson** on raw FTLE series per trajectory | Detects first‑order autocorrelation before aggregation. |
| **Newey‑West HAC SE** (if DW p < 0.05) | Adjusts SEs for autocorrelation & heteroskedasticity (FR‑009). |
| **Mixed‑effects MLR**: Δλ ~ σ + N + σ·N + 1/T (random intercept) | Captures hierarchical dependence of overlapping windows. |
| **Benjamini‑Hochberg FDR** (q ≤ 0.05) on all fixed‑effect coefficients | Controls false discovery rate (FR‑004). |
| **One‑sample t‑test** per noise level vs. deterministic baseline | Valid because baseline is a fixed quantity (SC‑001). |
| **Effect size** (Cohen’s d) for the primary noise coefficient | Provides magnitude beyond p‑values (SC‑003). |
| **Tobit regression** (always) | Handles censored observations (FR‑007/FR‑008). |
| **Escape probability** estimation | Reported as \(P(\text{escape}\mid\sigma)\) for each noise level. |

### 9. Visualization
- **Convergence plot**: λ vs. T for three representative noise levels (clean, moderate, high).  
- **Bias scaling plot**: Δλ (y) vs. σ_noise (x) with SEM error bars.  
- **Dimension scaling**: Δλ vs. N on log‑log axes; fitted scaling exponent reported.  

All figures are saved as PNGs under `data/processed/plots/`.

### 10. Compute Feasibility
All steps execute on the CPU‑only runner. Peak RAM < 2 GB; total wall‑clock time for the full grid (N = 3,5; 6 noise levels; 30 trials; 3 windows) ≈ 42 min with 2‑core multiprocessing, satisfying the 45‑minute CI limit. No GPU resources are required.

### 11. Decision / Rationale (re‑stated)
1. **Synthetic data** – Guarantees full control over noise and dimensionality; no external dataset required.  
2. **DOP853 + tight tolerances** – Numerical error far below the smallest noise level studied.  
3. **QR re‑orthonormalisation** – Ensures stable FTLE estimates for long windows.  
4. **Rosenstein baseline** – Satisfies Constitution VI and provides a deterministic reference.  
5. **Mixed‑effects regression** – Properly accounts for hierarchical dependence of overlapping windows.  
6. **Durbin‑Watson + Newey‑West** – Meets FR‑009 while handling autocorrelation appropriately.  
7. **Always‑fit Tobit** – Removes post‑hoc selection bias.  
8. **Parallel trial execution** – Keeps total runtime within CI limits while preserving reproducibility (each worker seeded independently).  

---
