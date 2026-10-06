# Feature Specification: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Feature Branch**: `001-quantify-initial-conditions`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Quantifying the Influence of Initial Conditions on Chaotic Systems"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Noisy High-Dimensional Chaotic Trajectories (Priority: P1)

The researcher needs to generate synthetic time-series data from a high-dimensional chaotic system (coupled Lorenz oscillators) with controllable levels of observational noise to serve as the ground truth for analysis.

**Why this priority**: This is the foundational data source. Without a reproducible, noise-injected trajectory that mimics real-world observational constraints, no analysis of FTLE deviation can occur. It is the single point of failure for the entire study.

**Independent Test**: Can be fully tested by running the simulation script and verifying that the output trajectory dimensions match the system definition and that the noise amplitude statistics (mean/variance) match the injected parameters within a 5% tolerance.

**Acceptance Scenarios**:

1. **Given** a system dimension of $N$ coupled Lorenz oscillators, **When** the simulation runs with noise level $\sigma_{noise} = 0.01$, **Then** the output trajectory contains $N \times T$ data points where the added noise has a standard deviation within 5% of the injected $\sigma_{noise}$ (measured via sample standard deviation).
2. **Given** a clean trajectory (noise $\sigma_{noise} = 0$), **When** the simulation runs, **Then** the generated data matches the deterministic integration of the coupled Lorenz equations within numerical precision limits ($< 10^{-9}$).
3. **Given** a system with $N=5$ oscillators and a trajectory length of $T=10,000$ time steps, **When** the simulation completes, **Then** the trajectory generation phase completes within 30 seconds on a GitHub Actions ubuntu-latest runner (2-core, 7GB RAM). For $T > 10,000$, the system MUST enter batch processing mode where each trial completes within 5 minutes.

---

### User Story 2 - Compute Finite-Time Lyapunov Exponents and Asymptotic Baselines (Priority: P2)

The researcher needs to calculate the Finite-Time Lyapunov Exponents (FTLE) over sliding windows and establish a robust asymptotic baseline for the clean system to quantify the deviation.

**Why this priority**: This implements the core mathematical logic of the research question. It transforms raw trajectory data into the specific metrics (FTLE vs. Asymptotic) required to answer the hypothesis.

**Independent Test**: Can be fully tested by running the calculation module on the clean (noise-free) trajectory and verifying that the FTLE converges to the numerically computed asymptotic baseline for the specific coupled configuration as the time window $T$ increases.

**Acceptance Scenarios**:

1. **Given** a noise-free trajectory of length $\ge [deferred]$ steps, **When** the FTLE algorithm runs with window sizes $T \in \{50, 500, 1000, 5000\}$, **Then** the calculated $\lambda_{FTLE}$ approaches the asymptotic limit (numerically computed baseline for the specific coupled configuration) with an error $< 5\%$ at $T=5000$. The reference baseline is defined as the numerically computed limit where the difference between successive windows ($T$ and $T+1000$) is $< 10^{-6}$. This validation applies strictly to the clean trajectory; noisy trajectories are expected to deviate.
2. **Given** a noisy trajectory, **When** the FTLE is computed for a specific window $T$, **Then** the output includes the exponent value, the time window used, and the noise level applied.
3. **Given** a system with $N$ dimensions, **When** the asymptotic baseline is computed, **Then** the result is a vector of exponents proportional to the number of degrees of freedom, with the maximum exponent of the *specific coupled system* (numerically computed for the given coupling) used as the baseline for deviation analysis, not the single-oscillator theoretical value.

---

### User Story 3 - Analyze Deviation Scaling and Generate Visualizations (Priority: P3)

The researcher needs to perform regression analysis on the deviation $\Delta \lambda$ and generate visualizations showing how the bias scales with noise amplitude and system dimension, explicitly conditioning on bounded trajectories and modeling escape probability.

**Why this priority**: This delivers the final scientific output (the "answer" to the research question) and allows for the validation of the scaling laws hypothesized in the idea.

**Independent Test**: Can be fully tested by running the analysis script on pre-computed data and verifying that the output includes a plot of deviation vs. noise level, a table of regression coefficients with FDR correction, and a censored regression model if escape rates are high.

**Acceptance Scenarios**:

1. **Given** a dataset of FTLE deviations across varying noise levels (with at least $k=30$ independent trials per noise level) for **bounded trajectories only** (state norm < 20.0), **When** the regression analysis runs, **Then** the system performs a Multiple Linear Regression (MLR) modeling $\Delta \lambda$ as a function of noise level and system dimension. The system MUST apply the Benjamini-Hochberg FDR correction ($q \le 0.05$) to the set of regression coefficients (slopes and interaction terms). The deviation $\Delta \lambda$ is defined as the difference between the noisy FTLE and the *clean finite-time baseline* computed for the same window size $T$. If the escape probability (fraction of trials where $||x|| > 20.0$) exceeds 5%, the system MUST ALSO fit a Tobit censored regression model using the full dataset (including censored points) to estimate the latent bias.
2. **Given** the analysis results, **When** the visualization module runs, **Then** it generates a plot with noise amplitude on the x-axis and deviation magnitude on the y-axis, including error bars representing the standard error of the mean.
3. **Given** multiple system dimensions, **When** the scaling analysis runs, **Then** the output explicitly reports the scaling exponent relating system dimension to the magnitude of the FTLE bias.

### Edge Cases

- What happens if the noise level is so high ($\sigma_{noise} > 1.0$) that the trajectory effectively leaves the attractor? The system MUST flag the data as "unphysical" if the state vector norm $||x|| > 20.0$ rather than producing garbage FTLE values.
- How does the system handle numerical instability when $T$ (window size) approaches the total trajectory length? The algorithm MUST ensure $T$ is strictly less than the total trajectory length by at least 10 time steps to allow for tangent vector propagation.
- What happens if the coupled Lorenz system parameters are set to non-chaotic values (e.g., $\rho < 24.74$)? The system MUST detect the lack of chaos (negative or zero Lyapunov exponent) and abort the deviation analysis with a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic time-series data for coupled Lorenz oscillators with user-specified noise amplitude $\sigma_{noise}$ spanning a broad range from negligible to significant levels, using `scipy.integrate.solve_ivp` with method 'DOP853' and tolerances `rtol=1e-9`, `atol=1e-12` (See US-1)
- **FR-002**: System MUST compute Finite-Time Lyapunov Exponents (FTLE) using a sliding window algorithm with window sizes $T$ spanning short to long temporal horizons. (See US-2)
- **FR-003**: System MUST calculate the asymptotic Lyapunov exponent for the clean system by numerical integration of the ODEs over a trajectory of length sufficient to achieve convergence (defined as $<5\%$ error at $T=5000$) and measure convergence against the numerically computed baseline for the specific coupled configuration (See US-2)
- **FR-004**: System MUST perform regression analysis to model the deviation $\Delta \lambda(T, \sigma_{noise})$ as a function of time window and noise level, explicitly conditioning the dataset on **bounded trajectories only** (state norm $||x|| < 20.0$) and using the difference between noisy FTLE and the clean finite-time baseline as the dependent variable (See US-3)
- **FR-005**: System MUST generate a convergence plot showing FTLE estimates vs. time window for at least three distinct noise levels (See US-3)
- **FR-006**: System MUST validate numerical stability by confirming the clean system's maximum Lyapunov exponent (calculated from the full spectrum of $3N$ exponents for the specific coupled configuration) is stable (converged) before proceeding to noisy analysis, ensuring the baseline is separated from noise-induced bias (See US-2)
- **FR-007**: System MUST flag trajectories where the state vector norm $||x|| > 20.0$ as "unphysical" and exclude them from the primary bounded-only regression analysis, but MUST retain them as censored observations for the secondary Tobit model (See Edge Cases)
- **FR-008**: System MUST record and report the probability of escape (fraction of trials where $||x|| > 20.0$) as a function of noise level $\sigma_{noise}$ to account for selection bias and model the full noise regime (See US-3)
- **FR-009**: System MUST perform a Durbin-Watson test on the residuals of the *time-series FTLE calculation* (within a single trajectory) to check for autocorrelation; if autocorrelation is detected (p < 0.05), the system MUST apply Newey-West standard errors to the regression coefficients to handle heteroscedasticity across trials (See US-3)
- **FR-010**: System MUST compute a "clean finite-time baseline" for every window size $T$ used in the analysis, defined as the FTLE of the noise-free system over that specific window $T$, to serve as the reference for calculating noise-induced bias (See US-3)

### Key Entities

- **Trajectory**: A time-ordered sequence of state vectors representing the system's evolution in phase space, containing both the deterministic path and injected noise.
- **FTLE Estimate**: A calculated scalar value representing the average exponential rate of divergence over a specific finite time window $T$.
- **Deviation Metric**: The difference $\Delta \lambda$ between a noisy finite-time estimate and the *clean finite-time baseline* for the same window $T$, used as the primary dependent variable for regression.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The convergence of the *clean-system* FTLE to the numerically computed asymptotic baseline for the specific coupled configuration is measured against the stable limit achieved at large $T$; this validates numerical stability, not the noisy results (See FR-003, US-2).
- **SC-002**: The magnitude of the FTLE bias under noise is measured against the injected noise amplitude to verify a monotonic scaling relationship for bounded trajectories (See FR-004, US-3)
- **SC-003**: The statistical significance of the noise-induced deviation is measured by reporting the p-value and effect size from the Multiple Linear Regression (with FDR correction) and the escape probability (See FR-004, FR-008, US-3)
- **SC-004**: The computational runtime of the full analysis pipeline (generation + calculation + regression) is measured against the specified CI limit, targeting completion within 45 minutes (See FR-001, US-1)

## Assumptions

- The standard Lorenz system parameters ($\sigma=10, \rho=28, \beta=8/3$) are sufficient to represent the high-dimensional chaotic behavior required, with dimensionality increased by coupling $N$ oscillators rather than changing parameters.
- Observational noise can be accurately modeled as additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ without requiring complex measurement error models or colored noise.
- The GitHub Actions free-tier runner (limited CPU, constrained RAM) is sufficient to handle the memory footprint of a coupled Lorenz system with $N=5$ oscillators and a trajectory length of $T=10,000$ steps within 30 seconds; for larger $T$, batch processing is assumed.
- The `scipy.integrate.solve_ivp` solver with method 'DOP853' and tolerances `rtol=1e-9`, `atol=1e-12` provides sufficient numerical accuracy for the trajectory generation and FTLE calculation without requiring adaptive step-size control beyond these defaults.
- The deviation between FTLE and asymptotic values is primarily driven by the interaction of noise and finite window size, with higher-order effects (e.g., non-Gaussian noise) being negligible for this scope.
- The asymptotic Lyapunov exponent of a *coupled* system is determined by the specific coupling strength and topology, and is not necessarily identical to the single-oscillator value.; the baseline must be computed numerically for the specific configuration.
- The primary research question regarding noise-induced bias is scoped to **bounded trajectories** (state norm $||x|| < 20.0$); escape probability is treated as a separate metric (FR-008) and a censored variable (FR-010) to avoid selection bias in the regression model.