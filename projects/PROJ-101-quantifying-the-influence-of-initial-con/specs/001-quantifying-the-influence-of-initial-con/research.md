# Research: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Scientific Context

### Theoretical Background
The Lorenz system, defined by $\dot{x} = \sigma(y-x)$, $\dot{y} = x(\rho-z)-y$, $\dot{z} = xy-\beta z$, exhibits deterministic chaos for $\sigma=10, \rho=28, \beta=8/3$ (Lorenz, 1963). The maximum Lyapunov exponent $\lambda_{max}$ quantifies the rate of divergence of nearby trajectories. In high-dimensional coupled systems, the spectrum of Lyapunov exponents becomes complex, and the asymptotic limit depends on coupling strength and topology.

Observational noise $\mathcal{N}(0, \sigma_{noise}^2)$ introduces bias in Finite-Time Lyapunov Exponent (FTLE) estimates. The deviation $\Delta \lambda(T, \sigma_{noise}) = \lambda_{FTLE}(T, \sigma_{noise}) - \lambda_{asymptotic}$ is expected to scale monotonically with noise amplitude and decrease with window size $T$. This project quantifies this scaling law.

### Key References
- **Lorenz, E. N. (1963)**. "Deterministic Nonperiodic Flow". *Journal of the Atmospheric Sciences*. (Primary source for Lorenz equations).
- **Rosenstein, M. T., Collins, J. J., & De Luca, C. J. (1993)**. "A practical method for calculating largest Lyapunov exponents from small data sets". *Physica D*. (Algorithm for FTLE estimation).
- **Wolf, A., et al. (1985)**. "Determining Lyapunov exponents from a time series". *Physica D*. (Foundational method for spectrum calculation).

## Dataset Strategy

**Dataset Type**: Synthetic (Generated).  
**Source**: No external dataset is used. Trajectories are generated in-situ using `scipy.integrate.solve_ivp`.  
**Rationale**: External datasets do not exist for "coupled Lorenz oscillators with controllable noise levels" in the required format. Synthetic generation ensures full control over parameters ($N$, $\sigma_{noise}$, $T$) and reproducibility.

**Generation Parameters**:
- **System**: $N$ coupled Lorenz oscillators (default $N=3$).
- **Coupling**: Linear diffusive coupling with strength $\epsilon$.
- **Noise**: Additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ applied at each time step.
- **Range**: $\sigma_{noise} \in \{10^{-4}, 10^{-3}, 10^{-2}, 0.05, 0.1, 0.2, 0.5, 0.8, 1.0, 1.5, 2.0\}$. Note: The range explicitly includes the (0.1, 1.0] interval required by FR-007 and the edge cases >1.0.
- **Trials**: Variable sample size $k(\sigma)$. $k=50$ for $\sigma < 0.01$ (low-noise regime) to ensure power; $k=30$ for $\sigma \ge 0.01$.
- **Trajectory Length**: $T_{total} = 5000$ steps for noisy analysis; $T_{baseline} = 50,000$ steps for baseline computation.

**Data Availability**:
- **Download**: Not applicable (generated).
- **Storage**: `data/raw/trajectories_*.npz` (compressed, checksummed).
- **Size Estimation**: For $N=5$, $T=5000$, $k=50$: $\approx 5 \times 5000 \times 50 \times 8$ bytes $\approx 10$ MB (well within CI limits).

## Methodology

### Phase 1: Baseline Validation (Constitution VI)
1. **Ultra-Long Integration**: Generate a noise-free trajectory ($\sigma_{noise}=0$) for the specific coupled configuration with $T_{baseline} = 50,000$ steps.
2. **Richardson Extrapolation**: Compute $\lambda_{max}$ for $T=25,000$ and $T=50,000$. Use Richardson extrapolation to estimate the asymptotic limit $\lambda_{asymptotic}$.
3. **Validation**: Confirm the convergence error (difference between $T=50,000$ and extrapolated limit) is $< 5\%$.
4. **Gate**: If convergence fails, abort noisy analysis (T028). **Note**: The baseline is the *numerically computed* limit for the specific configuration, not a theoretical value.

### Phase 2: FTLE Calculation with Noise (Controlled Causal Experiment)
1. **Experimental Design**: This is a **controlled causal experiment** where $\sigma_{noise}$ is the treatment variable. We assign $\sigma_{noise}$ levels via randomization (seeded) to estimate the causal effect of noise on FTLE bias.
2. **Generation**: Generate $k(\sigma)$ trials for each $\sigma_{noise} \in \{10^{-4}, \dots, 2.0\}$.
3. **Boundedness/Escape Time Check**: For each trial, compute the time $t_{escape}$ at which the trajectory exits the known basin of attraction (if it does). Record $t_{escape}$ as a metric. Do **not** discard trials based on "shadowing failure" (deterministic lemma invalid for SDEs). Instead, include $t_{escape}$ as a covariate in the analysis.
4. **FTLE Calculation**: Compute FTLE for each window $T \in \{500, 1000, 5000\}$.
5. **Deviation**: Calculate $\Delta \lambda = \lambda_{FTLE} - \lambda_{asymptotic}$ (where $\lambda_{asymptotic}$ is the independent baseline from Phase 1).

### Phase 3: Deviation Analysis (Non-Linear Scaling)
1. **Model Selection**: Fit candidate models (Linear, Power-law, Logarithmic) to $\Delta \lambda(T, \sigma_{noise})$. Select the best model using AIC/BIC.
2. **Regression**: Perform regression using the selected model: $\Delta \lambda = f(\sigma_{noise}, T) + \epsilon$.
3. **Statistical Test**: Perform a t-test on the coefficient corresponding to $\sigma_{noise}$ (the bias term). Report p-value and effect size (Cohen's d).
4. **Visualization**: Plot $\Delta \lambda$ vs. $\sigma_{noise}$ with error bars (SE) and the fitted non-linear curve.

## Statistical Rigor

- **Multiple Comparisons**: Adjusted via Bonferroni correction if multiple models are tested.
- **Power Analysis**: Variable $k(\sigma)$ ensures $\ge 0.8$ power to detect small effects ($d=0.2$) in the low-noise regime.
- **Causal Inference**: Controlled experiment with $\sigma_{noise}$ as treatment. Claims are causal regarding the noise-induced bias mechanism.
- **Measurement Validity**: FTLE algorithm validated against known theoretical limits for single Lorenz (Rosenstein, 1993).
- **Collinearity**: $T$ and $\sigma_{noise}$ are orthogonal experimental factors; non-linear interaction modeled explicitly.
- **Survivorship Bias**: Addressed by recording $t_{escape}$ and including it as a covariate, rather than discarding "unphysical" trials.

## Compute Feasibility

**Strategy**: CPU-first.
- **ODE Integration**: `scipy.integrate.solve_ivp` (DOP853) is highly optimized for CPU.
- **FTLE**: Rosenstein's algorithm is $O(N \cdot T)$ and runs in seconds for $T=5000$.
- **Memory**: Fits comfortably within 7 GB RAM (max $\approx 10$ MB for raw data).
- **Time**: $50 \text{ trials} \times 10 \text{ noise levels} \times 3 \text{ windows} \approx 1500$ computations. Estimated runtime: < 60 minutes on 2-core CPU.
- **GPU Escape Hatch**: Not required. No transformer or diffusion models involved.

## Decision Rationale

- **Why Synthetic?** No open dataset exists for "coupled Lorenz with controlled noise". Synthetic generation is the only feasible path.
- **Why Variable k?** SC-003 requires t-test; $k=30$ is underpowered for low noise. Variable $k$ ensures power across the range.
- **Why No Shadowing?** Deterministic Shadowing Lemma does not apply to stochastic trajectories (SDEs). Boundedness/Escape time is the correct metric for high noise.
- **Why Ultra-Long Baseline?** To avoid circular validation, the baseline must be an independent ground truth derived from a distinct, longer integration.
- **Why Non-Linear Model?** The physics of FTLE bias is non-linear; linear regression is a misspecification.
- **Why CPU?** The problem is ODE-based, not deep learning. GPU offers no advantage and adds complexity.