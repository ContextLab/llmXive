# Feature Specification: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

**Feature Branch**: `001-quantization-impact-gw`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Quantize Simulated Gravitational Waveforms (Priority: P1)

As a researcher, I need to generate binary black hole merger waveforms and inject them into realistic LIGO O3 noise, then apply controlled quantization at specific bit depths (1, 8, 10, 12, 14, 16 bits), so that I can create a dataset representing the physical conditions where quantization noise competes with instrumental noise.

**Why this priority**: This is the foundational data generation step. Without simulated waveforms with known ground-truth parameters and controlled quantization artifacts, no parameter estimation or error analysis can occur. It directly enables the core measurement of reconstruction error.

**Independent Test**: Can be fully tested by generating a small batch (e.g., 50) of waveforms, applying 8-bit quantization, and verifying that the quantized signal's discrete levels match the theoretical $2^8$ bins and that the signal-to-noise ratio (SNR) falls within the expected range (8-50) for the injected distance.

**Acceptance Scenarios**:

1. **Given** a set of binary black hole parameters (masses 10-50 $M_\odot$, distances 100-1000 Mpc), **When** the system generates waveforms and injects them into LIGO O3 noise, **Then** [deferred] of the resulting strain data must have an SNR within the range [8, 50] with a tolerance of ±0.5.
2. **Given** a generated strain time series, **When** the system applies 12-bit quantization, **Then** the output signal must contain no more than $2^{12}$ (4096) unique discrete amplitude values, and the step size must match the theoretical quantization interval for the signal's dynamic range.
3. **Given** a batch of 10,000 simulated signals, **When** the generation pipeline completes, **Then** the output dataset must be saved in a format compatible with PyCBC/Bilby (e.g., HDF5 or GWOSC format) and fit within the 7 GB RAM limit of the CI runner.

---

### User Story 2 - Perform Parameter Estimation on Quantized Signals (Priority: P2)

As a researcher, I need to run Bayesian parameter estimation (using PyCBC-Inference or Bilby) on the quantized waveforms to recover chirp mass, spin, and luminosity distance, so that I can compare the recovered posteriors against the injected ground truth.

**Why this priority**: This step executes the scientific inference. It transforms the raw quantized data into scientific parameters, allowing the calculation of estimation errors. It is the mechanism by which the "impact" of quantization is measured.

**Independent Test**: Can be fully tested by running the parameter estimation pipeline on a single, low-SNR (SNR=10) 8-bit quantized signal and verifying that the pipeline converges (posterior samples are generated) and that the recovered parameter ranges are physically plausible (e.g., positive mass, spin < 1).

**Acceptance Scenarios**:

1. **Given** a quantized waveform with a known injected chirp mass and SNR > 10, **When** the parameter estimation pipeline runs, **Then** the absolute bias in the recovered chirp mass mean must be less than 10% of the injected value (|mean - truth| < 0.1 × truth).
2. **Given** a set of 50 quantized signals with SNR > 10, **When** the inference is executed, **Then** the truth value must be contained within the 90% credible interval for at least 90% of the signals (calibration check).
3. **Given** a set of 50 quantized signals, **When** the inference is executed, **Then** the total runtime must not exceed 6 hours on a 2-core CPU runner, ensuring the full study is feasible within the CI time limit.
4. **Given** the inference results, **When** the system computes the Mean Squared Error (MSE) between injected and recovered parameters, **Then** the MSE must be calculated for chirp mass, dimensionless spin, and luminosity distance separately.

---

### User Story 3 - Identify Quantization-Dominance Thresholds (Priority: P3)

As a researcher, I need to analyze the error vs. SNR curves across different bit depths to identify the specific SNR threshold where quantization noise becomes a significant systematic bias, so that I can recommend ADC specifications for future detectors.

**Why this priority**: This is the final analysis and output generation. It synthesizes the results to answer the primary research question. Without this, the project produces raw data but no scientific conclusion.

**Independent Test**: Can be fully tested by plotting the error curves for a subset of data (e.g., 100 signals) and visually verifying that the error for lower bit depths (8-bit) diverges from higher bit depths (16-bit) at a specific SNR value, matching the hypothesis that quantization noise dominates at low SNR.

**Acceptance Scenarios**:

1. **Given** the computed error for each bit depth across the SNR range, **When** the system fits error vs. SNR curves, **Then** it must identify a crossover point (SNR threshold) where the quantization-induced error (defined as Total Error minus Instrumental Error from float64 baseline) exceeds 10% of the Instrumental Error for at least one bit depth.
2. **Given** the identified thresholds, **When** the system generates diagnostic plots, **Then** the plots must show that the slope of the error curve changes by >20% at the threshold, clearly distinguishing the transition region.
3. **Given** the full analysis results, **When** the final report is generated, **Then** it must state a concrete SNR range (e.g., 12-18) where 8-bit quantization is deemed insufficient for unbiased parameter estimation.

### Edge Cases

- What happens when the injected SNR is extremely low (SNR < 8)? The system must handle cases where the signal is buried in noise and parameter estimation fails to converge, recording these as "non-detections" rather than infinite error.
- How does the system handle the boundary condition where bit depth is 1? The system must ensure the quantization logic does not crash when $2^1 = 2$ levels are applied, though this may result in total signal loss. (This is now covered by FR-002).
- What happens if the LIGO O3 noise file is missing or corrupted? The system must fail gracefully with a clear error message indicating the missing data source, rather than generating silent garbage data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate binary black hole merger waveforms with masses in the range [10, 50] solar masses and distances in the range [100, 1000] Mpc using PyCBC (See US-1).
- **FR-002**: System MUST inject generated waveforms into LIGO O3 noise PSD data and apply quantization at bit depths of exactly 1, 8, 10, 12, 14, and 16 bits (See US-1).
- **FR-003**: System MUST execute Bayesian parameter estimation using PyCBC-Inference or Bilby to recover chirp mass, spin, and luminosity distance from quantized signals (See US-2).
- **FR-004**: System MUST compute the Mean Squared Error (MSE) between injected ground-truth parameters and recovered posterior means for each signal (See US-2).
- **FR-005**: System MUST fit error-vs-SNR curves and identify the SNR threshold where quantization-induced error (Total Error minus Instrumental Error) exceeds 10% of the Instrumental Error (See US-3).
- **FR-006**: System MUST operate entirely on CPU without GPU acceleration, ensuring compatibility with GitHub Actions free-tier runners (See US-2).
- **FR-007**: System MUST generate a parallel set of float64 (infinite precision) baseline waveforms for every quantized signal to serve as the ground-truth instrumental-only error reference (See US-3).

### Key Entities

- **SimulatedWaveform**: Represents a generated gravitational wave signal with known ground-truth parameters (masses, spins, distance) and an associated SNR.
- **QuantizedSignal**: A waveform version that has been discretized to $2^N$ levels, where $N$ is the bit depth, containing the specific quantization noise artifact.
- **BaselineSignal**: A float64 version of the waveform with no quantization, used to calculate the instrumental-only error.
- **ParameterEstimationResult**: The output of the inference pipeline containing posterior distributions for chirp mass, spin, and distance, along with the computed MSE against the ground truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The SNR threshold where quantization noise becomes a significant bias is measured against the instrumental-only error derived from the float64 baseline (See US-3).
- **SC-002**: The parameter estimation error (MSE) for chirp mass is measured against the injected ground-truth values for each bit depth (See US-2).
- **SC-003**: The computational feasibility is measured against the 6-hour runtime limit and 7 GB RAM limit of the GitHub Actions free-tier runner (See US-2).
- **SC-004**: The bias introduced by quantization is measured against the 10% instrumental-error threshold to determine the "significant bias" point (See US-3).
- **SC-005**: The reproducibility of the threshold is measured by the consistency of the crossover point: the standard deviation of the identified crossover SNR across 10 independent runs of [deferred] signals each must be < 0.5 SNR units (See US-3).

## Assumptions

- **Assumption about data**: The LIGO Open Science Center (LOSC) provides the O3 noise power spectral density data in a format directly usable by PyCBC without requiring additional preprocessing or conversion steps.
- **Assumption about scope**: The study focuses exclusively on binary black hole mergers; binary neutron star mergers or neutron star-black hole systems are out of scope for this specific iteration.
- **Assumption about method**: The PyCBC-Inference or Bilby Bayesian pipelines can converge on parameter estimates for SNR > 10 even with 8-bit quantization, though the estimates may be biased; the system assumes convergence is possible for the defined SNR range.
- **Assumption about compute**: The 10,000 signal simulations and parameter estimations can be parallelized or batched to complete within the 6-hour CI job limit on a 2-core CPU runner.
- **Assumption about noise model**: The LIGO O3 noise PSD is representative enough of the "instrumental noise floor" to serve as the baseline for comparing quantization noise effects, provided that the signal-dependent nature of quantization noise is accounted for by comparing against a signal-specific float64 baseline.
- **Assumption about threshold**: The 10% error threshold (relative to instrumental error) is a defensible community-standard proxy for when systematic errors become significant enough to bias population studies.