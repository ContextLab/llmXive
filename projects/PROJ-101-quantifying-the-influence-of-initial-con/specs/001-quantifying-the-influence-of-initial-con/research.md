# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Problem Statement

Chaotic systems are characterized by sensitive dependence on initial conditions, quantified by Lyapunov exponents. In practice, these exponents are estimated from finite-time trajectories that are often contaminated by observational noise. This research quantifies the bias introduced by this noise and the finite-time window length $T$ on the estimation of the maximum Lyapunov exponent in high-dimensional coupled Lorenz systems.

## Theoretical Background

### Coupled Lorenz Oscillators
The system consists of $N$ Lorenz oscillators coupled via a diffusive term. The equations for the $i$-th oscillator ($i=1..N$) are:

$$
\begin{aligned}
\dot{x}_i &= \sigma(y_i - x_i) + \frac{D}{N} \sum_{j=1}^N (x_j - x_i) \\
\dot{y}_i &= x_i(\rho - z_i) - y_i \\
\dot{z}_i &= x_i y_i - \beta z_i
\end{aligned}
$$

Standard parameters: $\sigma=10, \rho=28, \beta=8/3$. Coupling strength $D$ is a parameter to be explored (default $D=0.2$).

### Finite-Time Lyapunov Exponents (FTLE)
The FTLE $\lambda_T$ over a window $T$ is defined as:
$$ \lambda_T = \frac{1}{T} \ln \left( \frac{\| \delta \mathbf{x}(T) \|}{\| \delta \mathbf{x}(0) \|} \right) $$
where $\delta \mathbf{x}(t)$ is the evolution of a perturbation vector governed by the tangent linear equations. **Crucially, for this study, the tangent linear equations are integrated using the *noisy* observed trajectory states.** Specifically, **the Jacobian matrix $J(\mathbf{x})$ is evaluated at the noisy state $\mathbf{x}_{obs}(t)$ at each step** to simulate the realistic scenario of estimating chaos from noisy data.

### Noise Model
Observational noise is modeled as additive Gaussian white noise:
$$ \mathbf{x}_{obs}(t) = \mathbf{x}_{true}(t) + \boldsymbol{\epsilon}(t), \quad \boldsymbol{\epsilon}(t) \sim \mathcal{N}(0, \sigma_{noise}^2 \mathbf{I}) $$

## Dataset Strategy

This project generates **synthetic data**. No external datasets are used.
- **Source**: `code/data/generator.py` (Coupled Lorenz ODE solver).
- **Verification**: The generator is validated against the numerically computed asymptotic Lyapunov exponent for the specific coupled configuration.
- **Data Volume**:
  - Trajectories: $N \le $ dimensions, $T_{total} \approx 10^5$ steps.
  - Trials: $k=30$ independent trials per noise level.
  - Noise levels: $\sigma_{noise}$ will be varied across a range of magnitudes from very low to high to assess sensitivity.
  - Window sizes: $T \in \{\text{small}, 500, 1000, 5000\}$.
  - Estimated total data size: < 500 MB (fits within CI limits).

## Methodology

### Phase 0: Solver Sanity Check (Constitution Principle VI - N=1)
1. Generate a long, noise-free trajectory for $N=1$ (single oscillator).
2. Compute FTLE for increasing $T$.
3. Verify convergence to the theoretical asymptotic value ($\lambda_{max} \approx 0.905$) within 5% error at $T=5000$.
4. **Gate**: If convergence fails, abort and tune solver tolerances. *Note: This is a sanity check for the solver, not the baseline for the coupled system study.*

### Phase 1: High-Dimensional Asymptotic Baseline (Scientific Soundness)
1. For each configuration ($N \in \{3, 5, 10\}$, $D=0.2$):
   - Generate a **very long** noise-free trajectory ($T_{long} \approx 2 \times 10^5$ steps).
   - Compute the full spectrum of Lyapunov exponents using the tangent-linear method.
   - **Extrapolate to $T \to \infty$** using **Richardson extrapolation** on the sequence of FTLE estimates from the long trajectory (using windows $T \in \{5000, 10000, 20000\}$) to establish the **true numerical asymptotic baseline** for that specific configuration.
   - *Note: This baseline is NOT $N \times 0.905$; it is the numerically converged max exponent for the specific coupled system, determined solely by $N$ and $D$.*
2. **Gate**: If the max exponent $\le 0$, abort (system is not chaotic).

### Phase 2: Noisy Trajectory Generation & FTLE
1. For each $N$ and $\sigma_{noise}$:
   - Generate $k=30$ independent noisy trajectories.
   - **Do NOT discard** trajectories that leave the attractor. Instead, record the time of escape (if any) as a distinct event.
   - Compute FTLE for each window size $T$ using the **noisy states** for both the trajectory and the tangent linear propagation (simulating real-world estimation bias).
   - If a trajectory leaves the attractor, record the FTLE up to the escape time (truncated window) and flag the event as `escape_event=True`.

### Phase 3: Statistical Analysis
1. Calculate deviation $\Delta \lambda = \lambda_{FTLE} - \lambda_{asymptotic}$ (where $\lambda_{asymptotic}$ is the baseline from Phase 1).
2. **Model Selection**: Fit multiple candidate models for $\Delta \lambda(T, \sigma_{noise})$:
   - Additive: $\Delta \lambda = \alpha + \beta_1 \sigma_{noise} + \beta_2 T^{-1}$
   - Multiplicative (Power-law): $\Delta \lambda = \alpha \cdot \sigma_{noise}^\gamma \cdot T^{-\beta}$
   - Saturation (Michaelis-Menten style): $\Delta \lambda = \frac{A \cdot \sigma_{noise}}{K + \sigma_{noise}}$
   - Select the best model using **AIC/BIC**.
3. **Robust Statistics**:
   - Perform a Shapiro-Wilk test on residuals.
   - If normality is violated, use **bootstrapped confidence intervals** (sufficient resamples for stability) and non-parametric tests (Wilcoxon) instead of t-tests.
   - If normality holds, report t-test p-values and effect sizes.
4. **Escape Analysis**: Model the probability of escape as a function of $\sigma_{noise}$ (logistic regression or simple proportion) to characterize system stability limits.
5. Generate visualizations: $\Delta \lambda$ vs. $\sigma_{noise}$ (with error bars), $\Delta \lambda$ vs. $T$, and the probability of escape vs. $\sigma_{noise}$.

## Statistical Rigor

- **Multiple Comparisons**: Since multiple noise levels and window sizes are tested, a Bonferroni correction or False Discovery Rate (FDR) control will be applied to p-values if the number of comparisons is substantial.
- **Power Justification**: $k=30$ trials per condition is a standard heuristic. However, due to the heavy-tailed nature of chaotic systems, **bootstrapping** is mandated to ensure robust confidence intervals regardless of distribution shape.
- **Causal Inference**: This is a controlled simulation study. The "cause" (noise level) is explicitly manipulated. Claims are strictly about the *simulation model*, not real-world physical systems.
- **Collinearity**: $T$ and $\sigma_{noise}$ are orthogonal experimental factors. No collinearity issues expected.
- **Selection Bias Mitigation**: Escape events are modeled as a distinct outcome (probability of escape) rather than discarded, preventing bias in the continuous FTLE estimates.

## Compute Feasibility

- **CPU-First**: The entire pipeline (ODE integration, Jacobian propagation, regression) is computationally light enough for the GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Memory**: Storing $N=10$ trajectories of $10^5$ steps requires $\approx 10 \times 10^5 \times 30 \times 8$ bytes $\approx 240$ MB. Well within limits.
- **Runtime**:
  - ODE Integration: $\approx 2$ seconds per trajectory.
  - FTLE Calculation: $\approx 5$ seconds per trajectory.
  - Total for multiple trials $\times$ 5 noise levels $\times$ 4 dimensions $\approx 6000$ trajectories.
  - Estimated total time: approximately a moderate duration on a single core.
  - **Optimization**: The plan will parallelize trials across the 2 available cores (using `multiprocessing`) to reduce runtime to $\approx 5$ hours, safely within the 6-hour CI limit. If needed, $k$ will be reduced to 15 or $N$ limited to 5 to guarantee completion.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Trajectory divergence for high noise | Loss of data | Model "escape" as a distinct event (probability analysis) rather than discarding. |
| Numerical instability in Jacobian | Biased FTLE | Use `DOP853` with strict tolerances; validate on clean baseline first. |
| CI timeout (h) | Incomplete results | Parallelize trials; reduce $k$ or $N$ if necessary; report power limitation. |
| Coupling strength non-chaotic | Invalid baseline | Scan coupling range; abort if max $\lambda \le 0$. |
| Model Misspecification | Invalid coefficients | Use AIC/BIC to select the best functional form (linear, power-law, saturation). |