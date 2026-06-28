# Feature Specification: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do varying levels and types of measurement noise (e.g., Gaussian, quantization) degrade the accuracy of phase space reconstruction metrics (correlation dimension, Lyapunov exponents) for canonical chaotic systems like the Lorenz attractor?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Clean Chaotic Time-Series Data (Priority: P1)

A researcher needs to obtain ground-truth chaotic time-series data from canonical systems (Lorenz, Rössler) with known parameters to serve as the baseline for noise-degradation analysis.

**Why this priority**: This is the foundational data source. Without clean ground-truth trajectories, noise injection and metric comparison cannot proceed. It is the prerequisite for all downstream analysis.

**Independent Test**: Can be fully tested by generating a Lorenz attractor trajectory, computing its known Lyapunov exponent (~0.906 bits/s for standard parameters), and verifying the output matches expected values within ±5% tolerance.

**Acceptance Scenarios**:

1. **Given** standard Lorenz system parameters (σ=10, ρ=28, β=8/3), **When** the system integrates for [deferred] time steps with dt=0.01, **Then** the output trajectory contains ≥3 state variables (x, y, z) with no NaN values.
2. **Given** the generated trajectory, **When** computing the correlation dimension using Grassberger-Procaccia algorithm, **Then** the result falls within [2.0, 2.1] (expected range for Lorenz attractor).

---

### User Story 2 - Inject Controlled Noise at Specified SNR Levels (Priority: P1)

A researcher needs to apply additive Gaussian noise and uniform quantization noise to clean trajectories across a defined SNR range (0dB to 30dB in 5dB increments) to simulate measurement degradation.

**Why this priority**: This creates the experimental condition (predictor variable). The noise levels must be precisely controlled and reproducible to establish the noise→metric-degradation relationship.

**Independent Test**: Can be fully tested by injecting Gaussian noise at 10dB SNR into a signal and verifying the measured SNR (computed as 10·log₁₀(P_signal/P_noise)) matches the target within ±0.5dB.

**Acceptance Scenarios**:

1. **Given** a clean trajectory with known variance, **When** Gaussian noise is injected at 15dB SNR, **Then** the noisy signal's SNR (measured post-injection) is within [14.5, 15.5] dB.
2. **Given** a clean trajectory, **When** uniform quantization noise is applied with 8-bit resolution, **Then** the quantization step size equals 2⁻⁸ of the signal's dynamic range.

---

### User Story 3 - Compute Phase Space Reconstruction Metrics and Compare Against Ground Truth (Priority: P2)

A researcher needs to calculate correlation dimension, Lyapunov exponents, and false nearest neighbors for each noisy trajectory, then compute error rates relative to clean-data ground truth.

**Why this priority**: This produces the outcome variables (reconstruction metrics). Error analysis identifies the SNR threshold where reconstruction fails.

**Independent Test**: Can be fully tested by running the pipeline on 20dB SNR data and verifying Lyapunov exponent error is ≤10% of ground truth, while 0dB SNR data shows error ≥50%.

**Acceptance Scenarios**:

1. **Given** a noisy trajectory at 25dB SNR, **When** computing the largest Lyapunov exponent using Rosenstein's algorithm, **Then** the value deviates from ground truth by ≤15% (absolute error ≤0.14 bits/s).
2. **Given** a noisy trajectory at 5dB SNR, **When** computing false nearest neighbors (embedding dimension=2, threshold=10), **Then** the FNN rate exceeds 50% (indicating reconstruction failure).

---

### User Story 4 - Generate Error-vs-SNR Lookup Table and Visualization (Priority: P3)

A researcher needs to produce a lookup table showing metric error rates across SNR levels, plus plots illustrating the critical threshold where reconstruction quality degrades.

**Why this priority**: This delivers the practical output for experimentalists. While not required for the analysis to complete, it enables the lookup-table use case described in expected results.

**Independent Test**: Can be fully tested by generating the lookup table and verifying it contains ≥6 SNR levels (0, 5, 10, 15, 20, 25, 30dB) with corresponding error rates for all three metrics.

**Acceptance Scenarios**:

1. **Given** completed analysis across all SNR levels, **When** exporting the lookup table as CSV, **Then** the file contains columns for SNR, Lyapunov-error, correlation-dimension-error, and FNN-rate.
2. **Given** the error-vs-SNR data, **When** generating a line plot, **Then** the critical threshold (where error exceeds 30%) is marked with a vertical line at the identified SNR value.

---

### Edge Cases

- What happens when SNR=0dB (noise power equals signal power)? The FNN rate should saturate near [deferred], indicating complete reconstruction failure.
- How does system handle insufficient trajectory length? If clean data contains <10,000 points, the pipeline rejects with error "Insufficient data for reliable correlation dimension estimation (minimum 10,000 points required)".
- What happens when noise type is unsupported? Only Gaussian and uniform quantization noise are supported; any other type triggers error "Unsupported noise type: [type]. Supported: Gaussian, uniform quantization".
- How does system handle numerical overflow during integration? If scipy.integrate.solve_ivp produces NaN/Inf values, the trajectory is discarded and logged with warning "Integration overflow at time step [t]".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate clean chaotic time-series data from Lorenz and Rössler attractors using scipy.integrate.solve_ivp with standard parameters (See US-1)
- **FR-002**: System MUST inject additive Gaussian noise at SNR levels ∈ {0, 5, 10, 15, 20, 25, 30} dB with measured SNR accuracy within ±0.5dB (See US-2)
- **FR-003**: System MUST inject uniform quantization noise with user-specified bit resolution (4-bit to 16-bit) and verify quantization step size equals 2⁻ᵇ of signal dynamic range (See US-2)
- **FR-004**: System MUST compute correlation dimension using Grassberger-Procaccia algorithm with embedding dimension search range [2, 8] (See US-3)
- **FR-005**: System MUST compute largest Lyapunov exponent using Rosenstein's algorithm with maximum evolution time of 50 time steps (See US-3)
- **FR-006**: System MUST compute false nearest neighbors with embedding dimension=2 and threshold=10× standard deviation of signal (See US-3)
- **FR-007**: System MUST calculate absolute error for each metric as |computed_value - ground_truth_value| / |ground_truth_value| × [deferred] (See US-3)
- **FR-008**: System MUST identify critical SNR threshold where any metric error exceeds 30% and record this threshold value (See US-4)
- **FR-009**: System MUST export results as CSV with columns: SNR_dB, noise_type, metric_name, computed_value, ground_truth_value, error_percent (See US-4)
- **FR-010**: System MUST complete full pipeline (data generation through error analysis) within 6 hours on 2 CPU cores (See US-1, US-2, US-3)

### Key Entities

- **ChaoticTrajectory**: Represents a time-series from a chaotic system with attributes: system_type (Lorenz/Rössler), parameters (dict), time_points (array), state_values (3×N array), ground_truth_metrics (dict)
- **NoisyTrajectory**: Represents a noise-injected trajectory with attributes: source_trajectory_id, noise_type, SNR_dB, quantization_bits, noisy_values (3×N array), measured_SNR (float)
- **MetricResult**: Represents a computed reconstruction metric with attributes: trajectory_id, metric_name (correlation_dimension/Lyapunov_exponent/FNN_rate), value (float), error_percent (float)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Lyapunov exponent error at high SNR (≥25dB) is measured against the clean-data ground truth value (See US-3)
- **SC-002**: Correlation dimension error across all SNR levels is measured against the clean-data ground truth value (See US-3)
- **SC-003**: False nearest neighbors saturation point is measured against the SNR level where FNN rate exceeds 50% (See US-3)
- **SC-004**: Critical SNR threshold (where any metric error exceeds 30%) is measured against the lookup table derived from error-vs-SNR analysis (See US-4)
- **SC-005**: Pipeline runtime is measured against the 6-hour CPU budget constraint (See US-1, US-2, US-3)

## Assumptions

- Synthetic Lorenz and Rössler attractors generated via scipy.integrate.solve_ivp with standard parameters (σ=10, ρ=28, β=8/3 for Lorenz) serve as valid ground truth for phase space metrics
- Clean trajectories contain ≥10,000 time points to enable reliable correlation dimension estimation per Grassberger-Procaccia requirements
- Gaussian noise is additive white Gaussian noise (AWGN) with zero mean and variance set by target SNR
- Quantization noise follows uniform distribution over [-Δ/2, +Δ/2] where Δ is the quantization step size
- Rosenstein's algorithm for Lyapunov exponent estimation requires minimum 1,000 data points (validated for Lorenz system)
- All computations run on CPU-only environment without GPU acceleration; no CUDA-dependent libraries (e.g., bitsandbytes, load_in_8bit) are used
- Memory footprint stays within 7GB RAM by processing trajectories in batches of ≤10,000 points
- Total pipeline runtime does not exceed 6 hours on GitHub Actions free-tier runner (2 CPU cores)
- The UCI Machine Learning Repository benchmark time-series data (if used) contains sufficient samples and known ground-truth dynamics for validation
- Ground-truth Lyapunov exponent for standard Lorenz attractor is a known benchmark (accepted literature value)
- Ground-truth correlation dimension for standard Lorenz attractor is consistent with accepted literature values.
- SNR values are computed as 10·log₁₀(P_signal/P_noise) where P denotes signal power (variance)
- Multiple hypothesis testing (7 SNR levels × 3 metrics = 21 tests) requires family-wise error rate correction; Bonferroni correction applied with α=0.05/21≈0.0024
- Power analysis for detecting metric degradation at critical SNR threshold is deferred; sample size of 3 independent trajectory replicates per SNR level is used to estimate variance
- Sensitivity analysis sweeps SNR cutoff over {0.01, 0.05, 0.1} absolute error thresholds and reports how critical threshold identification varies across these values
- Predictor collinearity between correlation dimension and Lyapunov exponent is acknowledged as descriptive (both characterize attractor geometry); no independent causal claims are made about their relative predictive power
