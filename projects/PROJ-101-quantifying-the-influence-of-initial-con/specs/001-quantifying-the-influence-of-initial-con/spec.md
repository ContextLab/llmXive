# Feature Specification: Quantifying the Influence of Initial Conditions on Chaotic Systems

**Feature Branch**: `001-quantify-initial-conditions`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Quantifying the Influence of Initial Conditions on Chaotic Systems"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Noisy High-Dimensional Chaotic Trajectories (Priority: P1)

The researcher needs to generate synthetic time-series data from a high-dimensional chaotic system (coupled Lorenz oscillators) with controllable levels of observational noise to serve as the ground truth for analysis.

**Why this priority**: This is the foundational data source. Without a reproducible, noise-injected trajectory that mimics real-world observational constraints, no analysis of FTLE deviation can occur. It is the single point of failure for the entire study.

**Independent Test**: Can be fully tested by running the simulation script and verifying that the output trajectory dimensions match the system definition and that the noise amplitude statistics (mean/variance) match the injected parameters within a 1% tolerance.

**Acceptance Scenarios**:

1. **Given** a system dimension of $N$ coupled Lorenz oscillators, **When** the simulation runs with noise level $\sigma_{noise} = 0.01$, **Then** the output trajectory contains $N \times T$ data points where the added noise has a standard deviation of $0.01 \pm 0.0001$.
2. **Given** a clean trajectory (noise $\sigma_{noise} = 0$), **When** the simulation runs, **Then** the generated data matches the deterministic integration of the coupled Lorenz equations within numerical precision limits ($< 10^{-9}$).
3. **Given** a requested trajectory length of [deferred] time steps, **When** the simulation completes, **Then** the output file size is less than 100 MB and the process completes within 30 seconds on a standard CPU.

---

### User Story 2 - Compute Finite-Time Lyapunov Exponents and Asymptotic Baselines (Priority: P2)

The researcher needs to calculate the Finite-Time Lyapunov Exponents (FTLE) over sliding windows and establish a robust asymptotic baseline for the clean system to quantify the deviation.

**Why this priority**: This implements the core mathematical logic of the research question. It transforms raw trajectory data into the specific metrics (FTLE vs. Asymptotic) required to answer the hypothesis.

**Independent Test**: Can be fully tested by running the calculation module on the clean (noise-free) trajectory and verifying that the FTLE converges to the known theoretical asymptotic value (approx. 0.905 per dimension for standard Lorenz parameters) as the time window $T$ increases.

**Acceptance Scenarios**:

1. **Given** a noise-free trajectory of length [deferred], **When** the FTLE algorithm runs with window sizes $T \in \{100, 500, 1000, 5000\}$, **Then** the calculated $\lambda_{FTLE}$ approaches the asymptotic limit with an error $< 5\%$ at $T=5000$.
2. **Given** a noisy trajectory, **When** the FTLE is computed for a specific window $T$, **Then** the output includes the exponent value, the time window used, and the noise level applied.
3. **Given** a system with $N$ dimensions, **When** the asymptotic baseline is computed, **Then** the result is a vector of $N$ exponents, with the maximum exponent matching the theoretical expectation within 2% error.

---

### User Story 3 - Analyze Deviation Scaling and Generate Visualizations (Priority: P3)

The researcher needs to perform regression analysis on the deviation $\Delta \lambda$ and generate visualizations showing how the bias scales with noise amplitude and system dimension.

**Why this priority**: This delivers the final scientific output (the "answer" to the research question) and allows for the validation of the scaling laws hypothesized in the idea.

**Independent Test**: Can be fully tested by running the analysis script on pre-computed data and verifying that the output includes a plot of deviation vs. noise level and a table of regression coefficients.

**Acceptance Scenarios**:

1. **Given** a dataset of FTLE deviations across varying noise levels, **When** the regression analysis runs, **Then** the output identifies a statistically significant non-zero bias term (p-value $< 0.05$) for noise levels $\ge 10^{-3}$.
2. **Given** the analysis results, **When** the visualization module runs, **Then** it generates a plot with noise amplitude on the x-axis and deviation magnitude on the y-axis, including error bars representing the standard error of the mean.
3. **Given** multiple system dimensions, **When** the scaling analysis runs, **Then** the output explicitly reports the scaling exponent relating system dimension to the magnitude of the FTLE bias.

### Edge Cases

- What happens if the noise level is so high ($\sigma_{noise} > 1.0$) that the trajectory effectively leaves the attractor? The system MUST clamp the analysis or flag the data as "unphysical" rather than producing garbage FTLE values.
- How does the system handle numerical instability when $T$ (window size) approaches the total trajectory length? The algorithm MUST ensure $T$ is strictly less than the total trajectory length by at least 10 time steps to allow for tangent vector propagation.
- What happens if the coupled Lorenz system parameters are set to non-chaotic values (e.g., $\rho < 24.74$)? The system MUST detect the lack of chaos (negative or zero Lyapunov exponent) and abort the deviation analysis with a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic time-series data for coupled Lorenz oscillators with user-specified noise amplitude $\sigma_{noise} \in [10^{-4}, 10^{-1}]$ (See US-1)
- **FR-002**: System MUST compute Finite-Time Lyapunov Exponents (FTLE) using a sliding window algorithm with window sizes $T \in \{100, 500, 1000, 5000\}$ (See US-2)
- **FR-003**: System MUST calculate the asymptotic Lyapunov exponent for the clean system using Rosenstein's algorithm over a trajectory of length $\ge [deferred]$ steps (See US-2)
- **FR-004**: System MUST perform regression analysis to model the deviation $\Delta \lambda(T, \sigma_{noise})$ as a function of time window and noise level (See US-3)
- **FR-005**: System MUST generate a convergence plot showing FTLE estimates vs. time window for at least three distinct noise levels (See US-3)
- **FR-006**: System MUST validate numerical stability by confirming the clean system's asymptotic exponent is within 2% of the theoretical value (0.905) before proceeding to noisy analysis (See US-2)

### Key Entities

- **Trajectory**: A time-ordered sequence of state vectors representing the system's evolution in phase space, containing both the deterministic path and injected noise.
- **FTLE Estimate**: A calculated scalar value representing the average exponential rate of divergence over a specific finite time window $T$.
- **Deviation Metric**: The difference $\Delta \lambda$ between a finite-time estimate and the asymptotic baseline, used as the primary dependent variable for regression.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The convergence of the clean-system FTLE to the theoretical asymptotic limit is measured against the known analytical value of 0.905 (See FR-006, US-2)
- **SC-002**: The magnitude of the FTLE bias under noise is measured against the injected noise amplitude to verify a monotonic scaling relationship (See FR-004, US-3)
- **SC-003**: The statistical significance of the noise-induced deviation is measured against a null hypothesis of zero bias using a t-test (p-value $< 0.05$) (See FR-004, US-3)
- **SC-004**: The computational runtime of the full analysis pipeline (generation + calculation + regression) is measured against the 6-hour CI limit, targeting completion in $\le 45$ minutes (See FR-001, US-1)

## Assumptions

- The standard Lorenz system parameters ($\sigma=10, \rho=28, \beta=8/3$) are sufficient to represent the high-dimensional chaotic behavior required, with dimensionality increased by coupling $N$ oscillators rather than changing parameters.
- Observational noise can be accurately modeled as additive Gaussian white noise $\mathcal{N}(0, \sigma_{noise}^2)$ without requiring complex measurement error models or colored noise.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to handle the memory footprint of a coupled Lorenz system with $N \le 10$ oscillators and a trajectory length of [deferred] steps.
- The theoretical asymptotic Lyapunov exponent of the clean Lorenz system is approximately 0.905, serving as the ground truth for validation.
- The deviation between FTLE and asymptotic values is primarily driven by the interaction of noise and finite window size, with higher-order effects (e.g., non-Gaussian noise) being negligible for this scope.
- The `scipy.integrate.odeint` solver provides sufficient numerical accuracy for the trajectory generation without requiring adaptive step-size control or higher-precision arithmetic.
