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
3. **Given** a system with $N=5$ oscillators and a trajectory length of $T=10,000$ time steps, **When** the simulation completes, **Then** the trajectory generation completes successfully on the CI runner. No explicit timeout or batch‑processing fallback is mandated.

---

### User Story 2 - Compute Finite-Time Lyapunov Exponents and Asymptotic Baselines (Priority: P2)

The researcher needs to calculate the Finite-Time Lyapunov Exponents (FTLE) over sliding windows and establish a robust asymptotic baseline for the clean system to quantify the deviation.

**Why this priority**: This implements the core mathematical logic of the research question. It transforms raw trajectory data into the specific metrics (FTLE vs. Asymptotic) required to answer the hypothesis.

**Independent Test**: Can be fully tested by running the calculation module on the clean (noise‑free) trajectory and verifying that the FTLE converges to the numerically computed asymptotic baseline for the specific coupled configuration as the time window $T$ increases.

**Acceptance Scenarios**:

1. **Given** a noise‑free trajectory of length $\ge 50{,}000$ steps, **When** the FTLE algorithm runs with window sizes $T \in \{50, 500, 1000, 5000\}$, **Then** the calculated $\lambda_{FTLE}$ approaches the asymptotic limit (numerically computed baseline for the specific coupled configuration) with an error $< 5\%$ at $T=5000$. The reference baseline is defined as the asymptotic exponent computed at $T=20{,}000$ (or when successive window change $<10^{-6}$). This validation applies strictly to the clean trajectory; noisy trajectories are expected to deviate.
2. **Given** a noisy trajectory, **When** the FTLE is computed for a specific window $T$, **Then** the output includes the exponent value, the time window used, and the noise level applied.
3. **Given** a system with $N$ dimensions, **When** the asymptotic baseline is computed, **Then** the result is a single scalar Lyapunov exponent (the maximum exponent of the specific coupled system) used as the baseline for deviation analysis.

---

### User Story 3 - Analyze Deviation Scaling and Generate Visualizations (Priority: P3)

The researcher needs to perform regression analysis on the deviation $\Delta \lambda$ and generate visualizations showing how the bias scales with noise amplitude and system dimension, explicitly conditioning on bounded trajectories and modeling escape probability.

**Why this priority**: This delivers the final scientific output (the "answer" to the research question) and allows for the validation of the scaling laws hypothesized in the idea.

**Independent Test**: Can be fully tested by running the analysis script on pre‑computed data and verifying that the output includes a plot of deviation vs. noise level, a table of regression coefficients with standard significance testing, and a censored‑regression model only if required by the escape‑probability condition.

**Acceptance Scenarios**:

1. **Given** a dataset of FTLE deviations across varying noise levels (with at least $k=30$ independent trials per noise level) for **bounded trajectories only** (state norm $||x|| < 20.0$), **When** the regression analysis runs, **Then** the system performs a Multiple Linear Regression (MLR) modeling $\Delta \lambda$ as a function of noise level and system dimension. The system MUST apply a standard significance threshold ($p < 0.05$) to all regression coefficients. If the escape probability (fraction of trials where $||x|| > 20.0$) exceeds 5 %, the system MAY report this metric but does NOT fit a Tobit model.
2. **Given** the analysis results, **When** the visualization module runs, **Then** it generates a plot with noise amplitude on the x‑axis and deviation magnitude on the y‑axis, including error bars representing the standard error of the mean.
3. **Given** multiple system dimensions, **When** the scaling analysis runs, **Then** the output explicitly reports the scaling exponent relating system dimension to the magnitude of the FTLE bias.

### Edge Cases

- What happens if the noise level is so high ($\sigma_{noise} > 1.0$) that the trajectory effectively leaves the attractor? The system MUST flag the data as "unphysical" if the state vector norm $||x|| > 20.0$ rather than producing garbage FTLE values.
- How does the system handle numerical instability when $T$ (window size) approaches the total trajectory length? The algorithm MUST ensure $T$ is strictly less than the total trajectory length by at least 10 time steps to allow for tangent vector propagation.
- What happens if the coupled Lorenz system parameters are set to non‑chaotic values (e.g., $\rho < 24.74$)? The system MUST detect the lack of chaos (negative or zero Lyapunov exponent) and abort the deviation analysis with a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic time-series data for coupled Lorenz oscillators with user‑specified noise amplitude $\sigma_{noise}$ ∈ [0, 0.5] in increments of 0.05, using `scipy.integrate.solve_ivp` with method 'DOP853' and tolerances `rtol=1e-9`, `atol=1e-12` (See User Story 1)
- **FR-002**: System MUST compute Finite‑Time Lyapunov Exponents (FTLE) using a sliding window algorithm with window sizes $T$ spanning short to long temporal horizons. (See User Story 2)
- **FR-003**: System MUST calculate the asymptotic Lyapunov exponent for the clean system by numerical integration of the ODEs over a trajectory of length sufficient to achieve convergence (defined as relative error ≤ 5 % at $T=5000$ compared to the asymptotic baseline at $T=20{,}000$) and measure convergence against that baseline for the specific coupled configuration (See User Story 2)
- **FR-004**: System MUST perform regression analysis to model the deviation $\Delta \lambda(T, \sigma_{noise})$ as a function of time window and noise level, explicitly conditioning the dataset on **bounded trajectories only** (state norm $||x|| < 20.0$) and using the difference between noisy FTLE and the clean finite‑time baseline as the dependent variable (See User Story 3)
- **FR-005**: System MUST generate a convergence plot showing FTLE estimates vs. time window for at least three distinct noise levels (See User Story 3)
- **FR-006**: System MUST validate numerical stability by confirming the clean system's maximum Lyapunov exponent is stable (converged) before proceeding to noisy analysis, ensuring the baseline is separated from noise‑induced bias. Stability is defined as a relative change < 1 % across three consecutive windows of ΔT = 500. (See User Story 2)
- **FR-007**: System MUST flag trajectories where the state vector norm $||x|| > 20.0$ as "unphysical" and exclude them from the primary bounded‑only regression analysis, while still recording the escape probability for reporting. (See User Story 3)
- **FR-008**: System MUST record and report the probability of escape (fraction of trials where $||x|| > 20.0$) as a function of noise level $\sigma_{noise}$ to account for selection bias and model the full noise regime (See User Story 3)
- **FR-010**: System MUST compute a "clean finite‑time baseline" for every window size $T$ used in the analysis, defined as the mean FTLE of at least five independent noise‑free trajectories for that $T$, and propagate the baseline variance into $\Delta \lambda$ calculations. (See User Story 3)

### Key Entities

- **Trajectory**: A time‑ordered sequence of state vectors representing the system's evolution in phase space, containing both the deterministic path and injected noise.
- **FTLE Estimate**: A calculated scalar value representing the average exponential rate of divergence over a specific finite time window $T$.
- **Deviation Metric**: The difference $\Delta \lambda$ between a noisy finite‑time estimate and the *mean* clean finite‑time baseline for the same window $T$, used as the primary dependent variable for regression.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, percentages) to the implementation/research phase.

- **SC-001**: Convergence of the *clean‑system* FTLE to the numerically computed asymptotic baseline is considered achieved when the relative error ≤ 1 % and the 95 % confidence‑interval width ≤ 0.01, validated using an independent RK45 integration with tolerances `rtol=1e-10`, `atol=1e-13`. (See FR‑003, User Story 2)
- **SC-002**: Monotonic scaling of FTLE bias with noise amplitude is confirmed when Pearson correlation coefficient $r ≥ 0.8$ with $p < 0.05$ across the examined noise levels. (See FR‑004, User Story 3)
- **SC-003**: The statistical significance of the noise‑induced deviation is measured by reporting the p‑value and effect size from the Multiple Linear Regression (with standard $p<0.05$ threshold) and the escape probability. (See FR‑004, FR‑008, User Story 3)
- **SC-004**: The computational runtime of the full analysis pipeline (generation + calculation + regression) is measured against the CI environment, targeting completion within 45 minutes on the standard runner. (See FR‑001, User Story 1)

## Assumptions

- The standard Lorenz system parameters ($\sigma=10, \rho=28, \beta=8/3$) are sufficient to represent the high‑dimensional chaotic behavior required, with dimensionality increased by coupling $N$ oscillators rather than changing parameters.
- Observational noise can be accurately modeled as additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ without requiring complex measurement error models or colored noise.
- The `scipy.integrate.solve_ivp` solver with method 'DOP853' and tolerances `rtol=1e-9`, `atol=1e-12` provides sufficient numerical accuracy for the trajectory generation and FTLE calculation without requiring additional adaptive step‑size control.
- The deviation between FTLE and asymptotic values is primarily driven by the interaction of noise and finite window size, with higher‑order effects (e.g., non‑Gaussian noise) being negligible for this scope.
- The asymptotic Lyapunov exponent of a *coupled* system is determined by the specific coupling strength and topology, and is not necessarily identical to the single‑oscillator value; the baseline must be computed numerically for the specific configuration.
- The primary research question regarding noise‑induced bias is scoped to **bounded trajectories** (state norm $||x|| < 20.0$); escape probability is treated as a separate metric (FR‑008) to avoid selection bias in the regression model.
