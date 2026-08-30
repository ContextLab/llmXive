# Feature Specification: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

**Feature Branch**: `001-quantify-resolution-impact`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence"

## User Scenarios & Testing

### User Story 1 - Ground Truth Acquisition and Synthetic Downsampling (Priority: P1)

User Story ID: US-1

As a turbulence researcher, I need to download high-resolution isotropic turbulence snapshots from the Johns Hopkins Turbulence Database (JHTDB) and programmatically generate lower-resolution synthetic datasets via Fourier-mode truncation and spatial downsampling, so that I have a controlled ground truth and a set of known perturbations to analyze.

**Why this priority**: This is the foundational step; without a valid ground truth and a reproducible method to create lower-resolution variants, no statistical comparison or bias quantification can occur. It establishes the experimental variable (resolution ratio).

**Independent Test**: Can be fully tested by executing the download and downsampling pipeline on a single snapshot and verifying that the downsampled grid dimensions match the requested factors (2, 4, 8, 16) and that the total energy decreases monotonically as resolution drops, consistent with spectral truncation theory.

**Acceptance Scenarios**:

1. **Given** a valid JHTDB FTP credential and a selected snapshot ID, **When** the system downloads the velocity field data, **Then** the data is stored locally in a memory‑efficient format (e.g., HDF5 or sliced numpy arrays) without exceeding available system RAM.
2. **Given** a full‑resolution 512³ dataset, **When** the system applies a downsampling factor of 4 via Fourier truncation, **Then** the resulting dataset has dimensions $N^3$ and the high‑wavenumber modes (k > N_down/2) satisfy a maximum absolute value < 1e-10 * max_energy (relative to the signal energy) and the energy in the truncated band is < 1e-15 of the total energy.
3. **Given** a downsampling factor of 8, **When** the system processes the data, **Then** the resulting grid is of a coarser resolution and the spatial sampling interval is a multiple of the original grid spacing.

### User Story 2 - Statistical Computation and Bias Quantification (Priority: P2)

User Story ID: US-2

As a researcher, I need the system to compute 3D energy spectra E(k) and longitudinal velocity structure functions S_p(r) for p=2,3 on both the ground truth and all downsampled datasets, and then calculate the relative bias between them, so that I can quantify the magnitude of resolution‑induced errors.

**Why this priority**: This delivers the core scientific output. It transforms raw velocity fields into the specific statistics mentioned in the research question and calculates the "gap" between observed and true values.

**Independent Test**: Can be fully tested by running the computation on a small synthetic dataset with known analytical properties (e.g., a Kolmogorov spectrum) and verifying that the computed spectrum matches the analytical form at low wavenumbers. **Additionally**, comparing a dataset to itself must yield a bias of exactly zero (within floating‑point tolerance), while comparing a dataset to a null field must trigger a "Division by Zero" or "Undefined" flag.

**Acceptance Scenarios**:

1. **Given** a velocity field and a set of downsampled variants, **When** the system computes the energy spectrum E(k), **Then** the output is a 1D array of energy values binned by wavenumber magnitude, covering the range from the integral scale to the Nyquist limit of the specific resolution.
2. **Given** the computed statistics for the ground truth and a downsampled case, **When** the system calculates the relative bias, **Then** the output is a signed relative bias curve (y‑axis) plotted against the wavenumber or separation scale (x‑axis). For wavenumbers exceeding the Nyquist limit of the *downsampled* grid where downsampled energy is zero and ground truth > 0, the system MUST output NaN and a warning flag indicating "bias undefined due to truncation artifact". The bias curve is valid and populated for all wavenumbers ≤ Nyquist_limit_downsampled.
3. **Given** multiple resolution levels (factors 2, 4, 8, 16), **When** the system aggregates the bias results, **Then** it produces a single summary plot where the x‑axis represents the resolution ratio (grid spacing / Kolmogorov scale) and the y‑axis represents the error magnitude.

### User Story 3 - Scaling Exponent Deviation and Confidence Interval Estimation (Priority: P3)

User Story ID: US-3

As a researcher, I need the system to fit power‑law scaling exponents to the structure functions (specifically looking for deviations from Kolmogorov -5/3 and 2/3) and perform bootstrap resampling across the set of multiple independent snapshots to estimate confidence intervals on the bias measurements, so that I can determine the statistical significance of the resolution artifacts.

**Why this priority**: This adds statistical rigor and addresses the "systematic" nature of the bias. It moves from point estimates to probabilistic bounds, which is essential for the "publishable" claim in the expected results.

**Independent Test**: Can be fully tested by injecting synthetic noise into a known power‑law dataset and verifying that the bootstrap procedure (resampling across independent snapshots) recovers the known noise level within the calculated confidence interval.

**Acceptance Scenarios**:

1. **Given** the computed second-order structure function S_2(r) and energy spectrum E(k), **When** the system fits power laws in the inertial subrange, **Then** it outputs the scaling exponents and R² values, flagging if the theoretical values (-5/3 for E(k), 2/3 for S_2(r)) fall outside the 95% confidence interval derived from the **cross‑snapshot** bootstrap. The reference for "deviation" is the empirically fitted value from the highest‑resolution dataset in the study, acknowledging that this reference contains finite‑Reynolds‑number deviations.
2. **Given** a bias measurement at a specific wavenumber, **When** the system performs uncertainty estimation across the 3 independent snapshots in the primary benchmark, **Then** it outputs a confidence interval [lower, upper] calculated using the **cross‑snapshot bootstrap** method to account for inter‑snapshot variability.
3. **Given** the full set of results, **When** the system generates the final report, **Then** it includes a table listing the fitted exponents for all resolution levels and the corresponding confidence intervals, highlighting the resolution threshold where the exponent deviates significantly from the theoretical prediction.

### User Story 4 - Temporal Downsampling and Bias Quantification (Priority: P2)

User Story ID: US-4

As a turbulence researcher, I need to coarsen the temporal resolution of the JHTDB snapshots by sub‑sampling the time dimension (e.g., retaining every n‑th time‑step) and evaluate how this temporal coarsening influences the same statistics (energy spectrum, structure functions) and their bias relative to the fully‑resolved temporal series.

**Why this priority**: The original research question calls for assessing *both* spatial and temporal resolution limits. Temporal downsampling completes the scope by exposing how time‑step size affects spectral fidelity and scaling‑law estimation.

**Independent Test**: Can be fully tested by taking a short, high‑frequency time series from JHTDB, applying a temporal factor of 4, and verifying that (a) the number of retained time‑steps matches the factor, and (b) the computed spectra remain consistent with the spatial‑only case within a tolerance of 5 % RMS error for frequencies below the Nyquist frequency of the downsampled series.

**Acceptance Scenarios**:

1. **Given** a full‑resolution temporal series (e.g., 64 time‑steps) for a snapshot, **When** the system applies a temporal downsampling factor of 4, **Then** the resulting series contains 16 time‑steps and the time‑step interval is exactly 4 × the original.
2. **Given** the temporally downsampled series, **When** the system recomputes E(k) and S_p(r) for each retained time‑step and averages over time, **Then** the bias curve versus spatial wavenumber is produced and must satisfy the same validation criteria as spatial downsampling (see FR‑003 verification).
3. **Given** multiple temporal factors (2, 4, 8), **When** the system aggregates the bias results, **Then** it produces a 2‑D summary plot with spatial resolution ratio on one axis and temporal factor on the other, showing combined error magnitude.

### Edge Cases

- What happens when the selected JHTDB snapshot has a Reynolds number so low that the inertial subrange is non‑existent (no clear -5/3 region)? The system must detect this and flag the result as "Inertial Subrange Not Resolved" rather than fitting a spurious power law.
- How does the system handle memory overflow if the user attempts to download a 2048³ dataset without enabling slice‑by‑slice processing? The system must abort the download with a clear error message suggesting a smaller grid or enabling chunked processing.
- What if the Fourier truncation introduces aliasing artifacts that are not accounted for? The system must use a standard anti‑aliasing filter (e.g., a 2/3 rule) during the truncation process and document this in the output metadata.
- What if the input data is detected as placeholder, simulated, or hardcoded (e.g., all zeros or constant values)? The system MUST abort execution and report an error: "Invalid Input: Data appears to be synthetic or placeholder. Real JHTDB data required."

## Requirements

### Functional Requirements

- **FR-001**: System MUST download isotropic turbulence snapshots from JHTDB (e.g., 512³ or 1024³) and store them in a format accessible for in‑memory processing, ensuring peak memory usage stays below **≤ 5.6 GB** by processing data in spatial slices or chunks. Memory usage MUST be measured via OS‑agnostic memory accounting (e.g., psutil or equivalent) to ensure verification. (Justification: keeps the pipeline runnable on the CI runner’s 7 GB RAM while leaving headroom for OS overhead.) (See US-1)
- **FR-002**: System MUST implement Fourier‑mode truncation to generate synthetic lower‑resolution datasets at specific factors (2, 4, 8, 16) relative to the ground truth, ensuring high‑wavenumber modes are strictly zeroed out within floating‑point tolerance (max abs < 1e‑10 × max_energy). (Justification: guarantees that the downsampled data faithfully represent a lower‑resolution physical field without spurious high‑frequency content.) (See US-1)
- **FR-003**: System MUST compute the 3D energy spectrum E(k) and longitudinal velocity structure functions S_p(r) for p=2 and p=3 for every resolution level using FFT‑based methods compatible with CPU‑only execution (no GPU/CUDA). **Verification:** (a) output dimensions must be exactly **N/2 + 1** wavenumber bins for a grid of size N³; (b) for a synthetic Kolmogorov test case, RMS error of the computed spectrum against the analytical k⁻⁵ᐟ³ law for k < 0.2 k_Nyquist must be **≤ 5 %**; (c) repeated execution on the same input must produce identical spectra within a relative tolerance of **1e‑12**. (Justification: these tolerances ensure numerical accuracy sufficient for scientific conclusions.) (See US-2)
- **FR-004**: System MUST calculate the signed relative bias (percent error) between the ground truth statistics and the downsampled statistics across the full range of wavenumbers and separation scales. The bias MUST be derived from actual numerical computation on the downloaded JHTDB data. (Justification: provides the primary quantitative measure of resolution‑induced error.) (See US-2)
- **FR-005**: System MUST perform power‑law fitting on the structure functions and energy spectra to extract scaling exponents. **Testable thresholds:** (i) fitted power‑law must have coefficient of determination **R² ≥ 0.95** within the inertial subrange; (ii) 95 % confidence‑interval half‑width for the exponent must be **≤ 0.1**; (iii) **Resolution‑Bias target:** report exponent deviation from the highest‑resolution ground‑truth exponent and flag if |Δexponent| > 0.05; **Physical‑Consistency target:** compare fitted exponent to theoretical Kolmogorov values (‑5/3 for E(k), 2/3 for S₂(r)) and flag if the theoretical value lies outside the 95 % CI. (Justification: these statistical criteria ensure that fitted exponents are both accurate and precise enough to detect resolution effects.) (See US-3)
- **FR-006**: System MUST execute uncertainty estimation across the set of multiple independent snapshots (N=3) to generate confidence intervals for all reported error metrics. This MUST use a **cross‑snapshot bootstrap** method (resampling the set of independent snapshots) rather than spatial block resampling within a single snapshot, to ensure valid degrees of freedom for global scaling exponents. The final confidence interval MUST be calculated using the 2.5th and 97.5th percentiles of the bootstrap distribution. (Justification: cross‑snapshot resampling captures true variability between independent realizations.) (See US-3)
- **FR-007**: System MUST enforce a total runtime constraint of **≤ 12 hours** for the analysis of the **primary benchmark load profile**: **3 independent snapshots** of 512³ grid (JHTDB isotropic turbulence Re=1000, specific dataset ID: `iso_ts1000_512`) with resolution factors 2, 4, 8, 16, utilizing **4 parallel threads** on a GitHub Actions `ubuntu-latest` runner (minimum 2 vCPUs, 7 GB RAM). To meet this bound the implementation shall employ out‑of‑core FFT via memory‑mapped arrays (e.g., pyFFTW with `wisdom` and chunked transforms) and may allocate up to **≤ 5.6 GB** peak memory. This constraint applies to the **full analysis** (download, downsample, compute, bootstrap) and **prohibits shortcuts, pre‑computed results, or reduced dataset subsets** to meet the time limit. (Justification: runtime and memory limits guarantee that the full scientific workflow can be executed reproducibly within CI resources.) (See US-2, US-3)
- **FR-008**: System MUST ensure all reported bias values, scaling exponents, and confidence intervals are derived from **actual numerical computation** on real JHTDB data or valid synthetic variants generated via the defined Fourier truncation process. The system MUST NOT output **hardcoded, placeholder, fabricated, or pre‑computed metrics**. **Ground Truth** is strictly defined as the highest‑resolution JHTDB snapshot (real data); bias is measured against **that specific real dataset**, not a theoretical or synthetic ideal. Synthetic downsampled data is the experimental variable and is permitted; however, metrics derived from it must be computed at runtime. If the pipeline fails to compute a metric from real data, the result MUST be flagged as "UNCOMPUTED" and the process halted. (Justification: ensures scientific integrity by avoiding fabricated results.) (See US-2, US-3)
- **FR-009**: System MUST implement temporal downsampling by retaining every *n*‑th time‑step of a JHTDB snapshot (temporal factors 2, 4, 8). An appropriate anti‑aliasing filter (e.g., a 2/3 rule) shall be applied before sub‑sampling. Verification requires that the number of retained steps equals ⌈original_steps / n⌉ and that the temporal spectra of the downsampled series match the full‑resolution spectra within **≤ 5 % RMS error** for frequencies below the downsampled Nyquist frequency. (Justification: anti‑aliasing is essential to prevent spurious high‑frequency energy from contaminating the downsampled temporal signal.) (See US-4)

### Key Entities

- **TurbulenceSnapshot**: Represents a single flow field from JHTDB, characterized by Reynolds number, grid dimensions (N³), and total energy.
- **ResolutionVariant**: Represents a downsampled version of a snapshot, characterized by the downsampling factor, effective grid spacing, and the set of computed statistics.
- **TemporalVariant**: Represents a temporally coarsened version of a snapshot, characterized by the temporal factor, retained time‑step indices, and associated statistics.
- **BiasMetric**: Represents the calculated error between ground truth and a variant, containing the wavenumber/scale, relative error percentage, and confidence interval bounds.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of bias in the energy spectrum at the highest resolvable wavenumber of the downsampled grid is measured against the ground truth value from the full‑resolution JHTDB dataset. The value MUST be the result of the pipeline execution on real JHTDB data. (See US-2)
- **SC-002**: The deviation of the fitted structure function scaling exponent from the ground truth exponent derived from the highest‑resolution JHTDB dataset in the study is measured against that ground truth exponent. The value MUST be the result of the pipeline execution on real JHTDB data. (See US-3)
- **SC-003**: The width of the confidence interval for the bias estimate at the inertial subrange is measured against the bootstrap distribution generated from the 3 independent snapshots. The value MUST be the result of the pipeline execution on real JHTDB data. (See US-3)
- **SC-004**: The total computational runtime for the full analysis pipeline (download, downsample, compute, bootstrap) is measured against the 12‑hour limit on a GitHub Actions `ubuntu-latest` runner (minimum 2 vCPUs, 7 GB RAM), processing 3 snapshots of 512³ grid with factors 2, 4, 8, 16. (See US-2, US-3)
- **SC-005**: The peak memory usage during the processing of the largest selected snapshot is measured against an absolute limit of **≤ 5.6 GB**. (See US-1)
- **SC-006**: For temporal downsampling factors 2, 4, 8, the RMS difference between the temporal spectra of the downsampled series and the full‑resolution series for frequencies below the downsampled Nyquist must be **≤ 5 %**. (See US-4)

## Assumptions

- The Johns Hopkins Turbulence Database (JHTDB) provides public FTP access to isotropic turbulence datasets with known Reynolds numbers and grid sizes (e.g., 512³, 1024³) that are sufficient for the requested analysis.
- The JHTDB datasets contain velocity fields in a format (e.g., binary or HDF5) that can be read and processed by standard Python libraries (numpy, scipy) without requiring proprietary software or GPU acceleration.
- The "ground truth" for the analysis is defined as the highest‑resolution dataset available in the selected JHTDB case; any bias in the ground truth itself (e.g., numerical dissipation in the original simulation) is considered part of the reference signal, and the study measures resolution‑induced error relative to this reference.
- The project scope involves selecting a small number of cases from the available JHTDB datasets, with the primary benchmark defined on a representative set of 512³ grids to ensure feasibility within CI constraints.
- The theoretical Kolmogorov scaling exponents (‑5/3 for energy spectrum, 2/3 for second‑order structure function) are valid references for the inertial subrange of the selected high‑Reynolds‑number datasets, though the ground truth dataset itself may exhibit finite‑Reynolds‑number deviations.
- The cross‑snapshot bootstrap resampling of a sufficient number of iterations across the independent snapshots will complete within the 12‑hour time budget when applied to the computed statistics across all resolution levels.
- All metrics reported in the final analysis are derived from actual computation on real data; no simulated, placeholder, or hardcoded values are used to represent scientific findings.