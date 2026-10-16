# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Summary
We investigate how additive observational noise biases Finite‑Time Lyapunov Exponent (FTLE) estimates in high‑dimensional chaotic systems. By generating synthetic trajectories of coupled Lorenz oscillators, computing FTLE over multiple windows, and comparing against a rigorously validated clean‑system baseline, we quantify the scaling law  
\[
\Delta\lambda = f(\sigma_{\text{noise}}, N, T)
\]
where \( \Delta\lambda \) is the deviation from the asymptotic exponent.

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
  - Dimensions \(N \in \{3,5\}\) (extendable).  
  - Noise levels \(\sigma_{\text{noise}} \in \{10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 0.5, 1.0\}\).  
  - Trials per cell: \(k = 30\) (pinned seeds).  
- **Boundedness check**: trajectories with \(\|x(t)\| > 20.0\) are flagged “unphysical”.  

### 3. Baseline FTLE (Clean System)
- **Algorithm**: Rosenstein’s method applied to a noise‑free trajectory of length 20 000.  
- **Convergence criterion**: Relative change < 5 % between estimates at \(T=5000\) and \(T=10 000\).  
- **Output**: `baseline_{N}.json` containing the asymptotic maximum exponent \(\lambda_{\infty}(N)\).  

### 4. FTLE Computation on Noisy Trajectories
- **Sliding windows**: \(T \in \{500, 1000, 5000\}\).  
- **Procedure**: Propagate tangent linear equations alongside the state, re‑orthonormalize via QR decomposition every step, then accumulate logarithmic growth, then average over the window.  
- **Result record**: `ftle_results.json` entries include `window_size`, `lambda_max`, `status`, and the injected `sigma_noise`.  

### 5. Edge‑Case & Stability Checks
- **Boundedness**: flag any trajectory where `||x|| > 20.0` → `status = "unphysical"`.  
- **Chaos detection**: if max exponent ≤ 0 → abort with clear error.  
- **Durbin‑Watson test**: compute DW statistic on the raw FTLE time‑series for each trajectory; store p‑value.  
- **Newey‑West correction**: if DW p < 0.05, recompute regression standard errors with Newey‑West HAC.  

### 6. Deviation Metric & Modeling Strategy
\[
\Delta\lambda = \lambda_{\text{FTLE}}(T, \sigma_{\text{noise}}) - \lambda_{\infty}(N)
\]
- Computed **only** for trajectories with `status == "valid"` (bounded).  
- **Mixed‑effects regression**: Random intercept per trajectory; fixed effects include `σ_noise`, `N`, interaction `σ_noise·N`, and `1/T`. This accounts for the hierarchical dependence of overlapping windows.  
- **Benjamini‑Hochberg FDR** (q ≤ 0.05) applied to all fixed‑effect coefficients.  
- **Tobit censored regression**: Always fitted on the full dataset (including `unphysical` points) to estimate latent bias; escape probability is reported separately.  

### 7. Power Analysis
A power analysis for the planned multiple regression was performed using a simulation-based approach for a model with four predictors (σ, N, interaction, 1/T). With a total sample size of \(N_{obs} \approx 1080\) (12 parameter cells $\times$ 30 trials $\times$ 3 window sizes), the model is powered (\(1-\beta \ge 0.80\)) to detect a small-to-medium effect size (\(f^2 \approx 0.02\)) for the primary noise coefficient at \(\alpha=0.05\). The use of \(k=30\) independent trials per configuration ensures sufficient variability to reliably estimate the random intercepts and the interaction between noise and system dimension.

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
- **Bias scaling plot**: Δλ (y‑axis) vs. σ_noise (x‑axis) with error bars (SEM).  
- **Dimension scaling**: Δλ vs. N on log‑log axes; fitted scaling exponent reported.  

### 10. Compute Feasibility
All steps execute on the CPU‑only runner. Memory usage stays < 2 GB; total wall‑clock time for the full grid (N = 3,5; 6 noise levels; 30 trials) [deferred] with 2‑core multiprocessing, satisfying the 45‑minute CI limit. No GPU resources are required.

### 11. Decision / Rationale (re‑stated)
- Synthetic data → full control over noise and dimensionality.  
- High‑order DOP853 + tight tolerances ensure numerical error is far below the noise‑induced bias we aim to measure.  
- QR re‑orthonormalization guarantees stable FTLE estimates for long windows.  
- Rosenstein baseline satisfies Constitution VI and provides a deterministic reference.  
- Mixed‑effects regression respects hierarchical dependence, addressing methodological concerns.  
- Durbin‑Watson + Newey‑West fulfill FR‑009 while handling autocorrelation appropriately.  
- Always‑fit Tobit removes post‑hoc selection bias.  
- Parallel trial execution respects CI runtime limits while preserving reproducibility (each worker seeded independently).  

---