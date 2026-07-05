# Feature Specification: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

**Feature Branch**: `001-quantify-resolution-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence"

## User Scenarios & Testing

### User Story 1 - Ground Truth Acquisition and Synthetic Downsampling (Priority: P1)

As a turbulence researcher, I need to download high-resolution isotropic turbulence snapshots from the Johns Hopkins Turbulence Database (JHTDB) and programmatically generate lower-resolution synthetic datasets via Fourier-mode truncation and spatial downsampling, so that I have a controlled ground truth and a set of known perturbations to analyze.

**Why this priority**: This is the foundational step; without a valid ground truth and a reproducible method to create lower-resolution variants, no statistical comparison or bias quantification can occur. It establishes the experimental variable (resolution ratio).

**Independent Test**: Can be fully tested by executing the download and downsampling pipeline on a single snapshot and verifying that the downsampled grid dimensions match the requested factors (, 4, 8, 16) and that the total energy decreases monotonically as resolution drops, consistent with spectral truncation theory.

**Acceptance Scenarios**:

1. **Given** a valid JHTDB FTP credential and a selected snapshot ID, **When** the system downloads the velocity field data, **Then** the data is stored locally in a memory-efficient format (e.g., HDF5 or sliced numpy arrays) without exceeding available system RAM.
2. **Given** a full-resolution 1024³ dataset, **When** the system applies a downsampling factor of 4 via Fourier truncation, **Then** the resulting dataset has dimensions $N^3$ and the high-wavenumber modes (k > N_down/2) satisfy a maximum absolute value < 1e-12 and the energy in the truncated band is < 1e-15 of the total energy.
3. **Given** a downsampling factor of 8, **When** the system processes the data, **Then** the resulting grid is of a fine resolution and the spatial sampling interval is a multiple of the original grid spacing.

---

### User Story 2 - Statistical Computation and Bias Quantification (Priority: P2)

As a researcher, I need the system to compute 3D energy spectra E(k) and longitudinal velocity structure functions S_p(r) for p=2,3 on both the ground truth and all downsampled datasets, and then calculate the relative bias between them, so that I can quantify the magnitude of resolution-induced errors.

**Why this priority**: This delivers the core scientific output. It transforms raw velocity fields into the specific statistics mentioned in the research question and calculates the "gap" between observed and true values.

**Independent Test**: Can be fully tested by running the computation on a small synthetic dataset with known analytical properties (e.g., a Kolmogorov spectrum) and verifying that the computed spectrum matches the analytical form at low wavenumbers and that the bias calculation returns NaN when comparing a dataset to itself at zero energy.

**Acceptance Scenarios**:

1. **Given** a velocity field and a set of downsampled variants, **When** the system computes the energy spectrum E(k), **Then** the output is a 1D array of energy values binned by wavenumber magnitude, covering the range from the integral scale to the Nyquist limit of the specific resolution.
2. **Given** the computed statistics for the ground truth and a downsampled case, **When** the system calculates the relative bias, **Then** the output is a signed relative bias curve (y-axis) plotted against the wavenumber or separation scale (x-axis). For wavenumbers exceeding the Nyquist limit where downsampled energy is zero and ground truth > 0, the system MUST output NaN and a warning flag indicating "bias undefined due to truncation artifact".
3. **Given** multiple resolution levels (factors 2, 4, 8, 16), **When** the system aggregates the bias results, **Then** it produces a single summary plot where the x-axis represents the resolution ratio (grid spacing / Kolmogorov scale) and the y-axis represents the error magnitude.

---

### User Story 3 - Scaling Exponent Deviation and Confidence Interval Estimation (Priority: P3)

As a researcher, I need the system to fit power-law scaling exponents to the structure functions (specifically looking for deviations from Kolmogorov -5/3 and 2/3) and perform bootstrap resampling across the set of multiple independent snapshots to estimate confidence intervals on the bias measurements, so that I can determine the statistical significance of the resolution artifacts.

**Why this priority**: This adds statistical rigor and addresses the "systematic" nature of the bias. It moves from point estimates to probabilistic bounds, which is essential for the "publishable" claim in the expected results.

**Independent Test**: Can be fully tested by injecting synthetic noise into a known power-law dataset and verifying that the bootstrap procedure recovers the known noise level within the calculated confidence interval.

**Acceptance Scenarios**:

1. **Given** the computed second-order structure function S_2(r) and energy spectrum E(k), **When** the system fits power laws in the inertial subrange, **Then** it outputs the scaling exponents and R² values, flagging if the theoretical values (/3 for E(k), 2/3 for S_2(r)) fall outside the 95% confidence interval derived from the spatial block bootstrap. The reference for "deviation" is the empirically fitted value from the 1024³ dataset, not the theoretical value.
2. **Given** a bias measurement at a specific wavenumber, **When** the system performs uncertainty estimation across the 3-5 independent snapshots, **Then** it outputs a confidence interval [lower, upper] calculated using the Standard Error of the Mean (SEM) and a t-distribution with degrees of freedom corresponding to the sample size minus one.
3. **Given** the full set of results, **When** the system generates the final report, **Then** it includes a table listing the fitted exponents for all resolution levels and the corresponding confidence intervals, highlighting the resolution threshold where the exponent deviates significantly from the theoretical prediction.

### Edge Cases

- What happens when the selected JHTDB snapshot has a Reynolds number so low that the inertial subrange is non-existent (no clear -5/3 region)? The system must detect this and flag the result as "Inertial Subrange Not Resolved" rather than fitting a spurious power law.
- How does the system handle memory overflow if the user attempts to download a 2048³ dataset without enabling slice-by-slice processing? The system must abort the download with a clear error message suggesting a smaller grid or enabling chunked processing.
- What if the Fourier truncation introduces aliasing artifacts that are not accounted for? The system must use a standard anti-aliasing filter (e.g., a fractional rule) during the truncation process and document this in the output metadata.
- What if the input data is detected as placeholder, simulated, or hardcoded (e.g., all zeros or constant values)? The system MUST abort execution and report an error: "Invalid Input: Data appears to be synthetic or placeholder. Real JHTDB data required."

## Requirements

### Functional Requirements

- **FR-001**: System MUST download isotropic turbulence snapshots from JHTDB (e.g., 1024³ or 2048³) and store them in a format accessible for in-memory processing, ensuring total memory usage does not exceed a moderate threshold by processing data in spatial slices if necessary. Memory usage MUST be measured via the /proc/self/status RSS field (or equivalent OS memory accounting) to ensure verification. (See US-1)
- **FR-002**: System MUST implement Fourier-mode truncation to generate synthetic lower-resolution datasets at specific factors (2, 4, 8, 16) relative to the ground truth, ensuring high-wavenumber modes are strictly zeroed out within floating-point tolerance (max abs < 1e-12). (See US-1)
- **FR-003**: System MUST compute the 3D energy spectrum E(k) and longitudinal velocity structure functions S_p(r) for p=2 and p=3 for every resolution level using FFT-based methods compatible with CPU-only execution. (See US-2)
- **FR-004**: System MUST calculate the signed relative bias (percent error) between the ground truth statistics and the downsampled statistics across the full range of wavenumbers and separation scales. (See US-2)
- **FR-005**: System MUST perform power-law fitting on the structure functions and energy spectra to extract scaling exponents and compare them against Kolmogorov theoretical values (-5/3 for E(k), 2/3 for S_2(r)). The comparison MUST distinguish between bias relative to the ground truth dataset (for resolution error) and bias relative to the theoretical value (for physical consistency). (See US-3)
- **FR-006**: System MUST execute uncertainty estimation across the set of multiple independent snapshots to generate confidence intervals for all reported error metrics. This MUST use the Standard Error of the Mean (SEM) with a t-distribution (df=N-1) for cross-snapshot variance. Spatial block bootstrap MAY be used within a single snapshot to estimate variance if N is large, but the final cross-snapshot CI MUST use the t-distribution method. (See US-3)
- **FR-007**: System MUST enforce a total runtime constraint of ≤ 6 hours for the analysis of a specific load profile: A small number of cases of 1024³ grids with Multiple resolution levels each, utilizing parallel processing where feasible on the -core runner. (See US-2, US-3)
- **FR-008**: System MUST ensure all reported bias values, scaling exponents, and confidence intervals are derived from real computation on actual JHTDB data or synthetic data generated via the defined Fourier truncation process. The system MUST NOT output hardcoded, placeholder, or simulated metrics. (See US-2, US-3)

### Key Entities

- **TurbulenceSnapshot**: Represents a single flow field from JHTDB, characterized by Reynolds number, grid dimensions (N³), and total energy.
- **ResolutionVariant**: Represents a downsampled version of a snapshot, characterized by the downsampling factor, effective grid spacing, and the set of computed statistics.
- **BiasMetric**: Represents the calculated error between ground truth and a variant, containing the wavenumber/scale, relative error percentage, and confidence interval bounds.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of bias in the energy spectrum at the highest resolvable wavenumber of the downsampled grid is measured against the ground truth value from the full-resolution dataset. The value MUST be the result of the pipeline execution, not a placeholder. (See US-2)
- **SC-002**: The deviation of the fitted structure function scaling exponent from the ground truth exponent derived from the full-resolution dataset (highest available resolution reference) is measured against the ground truth exponent. The value MUST be the result of the pipeline execution, not a placeholder. (See US-3)
- **SC-003**: The width of the 95% confidence interval for the bias estimate at the inertial subrange is measured against the bootstrap distribution generated from the 3-5 independent snapshots. The value MUST be the result of the pipeline execution, not a placeholder. (See US-3)
- **SC-004**: The total computational runtime for the full analysis pipeline (download, downsample, compute, bootstrap) is measured against the prescribed time limit of the GitHub Actions free-tier runner. (See US-2, US-3)
- **SC-005**: The memory peak usage during the processing of the largest selected snapshot is measured against a constrained RAM limit of the runner environment. (See US-1)

## Assumptions

- The Johns Hopkins Turbulence Database (JHTDB) provides public FTP access to isotropic turbulence datasets with known Reynolds numbers and grid sizes (e.g., 1024³) that are sufficient for the requested analysis.
- The JHTDB datasets contain velocity fields in a format (e.g., binary or HDF5) that can be read and processed by standard Python libraries (numpy, scipy) without requiring proprietary software or GPU acceleration.
- The "ground truth" for the analysis is defined as the highest-resolution dataset available in the selected JHTDB case; any bias in the ground truth itself (e.g., numerical dissipation in the original simulation) is considered negligible or outside the scope of this study.
- The project scope involves selecting a small number of cases from the available JHTDB datasets, but the runtime benchmark is defined on a representative set of cases of high-resolution grids.
- The theoretical Kolmogorov scaling exponents (-5/3 for energy spectrum, 2/3 for second-order structure function) are valid references for the inertial subrange of the selected high-Reynolds-number datasets, though the ground truth dataset itself may exhibit finite-Reynolds-number deviations.
- The bootstrap resampling of a sufficient number of iterations across the 3-5 independent snapshots will complete within the 6-hour time budget when applied to the computed statistics across all resolution levels.
- All metrics reported in the final analysis are derived from actual computation on real data; no simulated, placeholder, or hardcoded values are used to represent scientific findings.