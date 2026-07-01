# Feature Specification: Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

**Feature Branch**: `001-cmb-anomaly-lss-impact`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do specific CMB anomalies (e.g., Cold Spot, low quadrupole) alter predicted large-scale structure statistics when incorporated as modified initial conditions in cosmological simulations?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Validate Planck CMB Maps (Priority: P1)

The researcher downloads Planck CMB temperature maps (Commander or SMICA) from the Planck Legacy Archive and validates that the maps contain the required anomaly regions (Cold Spot, low quadrupole) and temperature anisotropy data needed for initial condition generation.

**Why this priority**: This is the foundational data step. Without validated input data, no simulations can be run. This is the most critical dependency for the entire research workflow.

**Independent Test**: Can be fully tested by downloading the Planck maps, verifying file integrity (checksums), and confirming the presence of anomaly regions in the temperature maps using basic Python/NumPy operations.

**Acceptance Scenarios**:

1. **Given** a valid Planck Legacy Archive account and network access, **When** the system downloads Commander or SMICA CMB temperature maps, **Then** the downloaded files pass MD5/SHA256 checksum validation against official hashes.
2. **Given** downloaded CMB temperature maps, **When** the system loads the maps into memory, **Then** the system reads the Nside parameter from the FITS header and asserts Nside ≥ 256, and loads the full-sky map before applying a galactic latitude mask (|b| > 5°).

---

### User Story 2 - Generate Modified Initial Conditions with Anomaly-Adjusted Power Spectra (Priority: P2)

The researcher generates initial condition files using CAMB or CLASS linear perturbation codes, incorporating anomaly-modified power spectra that reflect the Cold Spot and low quadrupole deviations from standard ΛCDM.

**Why this priority**: This transforms the raw CMB data into simulation-ready initial conditions. Without this step, the N-body simulations cannot model the anomaly propagation.

**Independent Test**: Can be fully tested by generating initial condition files and verifying the power spectrum modifications (comparing anomaly-modified vs standard ΛCDM spectra at low ℓ values).

**Acceptance Scenarios**:

1. **Given** validated CMB temperature maps and standard ΛCDM cosmological parameters, **When** the system runs CAMB/CLASS with anomaly-modified input, **Then** the system calculates the deviation from standard ΛCDM at ℓ ≤ 30 and logs the value, regardless of magnitude.
2. **Given** anomaly-modified power spectra, **When** the system generates initial condition files for N-body simulation, **Then** the files conform to GADGET-2 or nbodykit input format specifications and fit within ≤ 500 MB disk space.

---

### User Story 3 - Run N-body Simulations and Extract Large-Scale Structure Statistics (Priority: P3)

The researcher runs small-volume N-body simulations (L=500 Mpc/h, 256³ particles) using GADGET-2 or nbodykit, then extracts large-scale structure statistics (matter power spectrum, void size distributions) from simulation snapshots. The system runs a paired control simulation with standard ΛCDM initial conditions to isolate the anomaly effect.

**Why this priority**: This is the core analysis step that produces the research output. However, it depends on successful completion of US-1 and US-2, making it P3 in the dependency chain.

**Independent Test**: Can be fully tested by running the simulation on a single CPU core, extracting statistics at z=0, and verifying the power spectrum and void finder outputs against reference ΛCDM mocks.

**Acceptance Scenarios**:

1. **Given** valid initial condition files (both anomaly-modified and control), **When** the system runs the N-body simulation on a CPU-only runner, **Then** the simulation completes within ≤ 12 hours wall-clock time and uses ≤ 14 GB peak RAM.
2. **Given** completed simulation snapshots, **When** the system extracts matter power spectrum and void size distributions, **Then** the outputs are stored in NumPy arrays compatible with downstream statistical comparison (Chi-squared, Kolmogorov-Smirnov tests).
3. **Given** paired anomaly and control runs, **When** the system computes the difference in LSS statistics, **Then** the system outputs the delta values (anomaly minus control) for power spectrum and void distributions.

---

### Edge Cases

- What happens when the Planck Legacy Archive is temporarily unavailable? (System retries up to 3 times with 60-second backoff intervals)
- How does the system handle corrupted initial condition files? (Validates file integrity before simulation launch and aborts with error code if checksums fail)
- What if the anomaly-modified power spectrum produces unphysical initial conditions (e.g., negative power)? (System flags and aborts before simulation, requiring manual parameter adjustment)
- How does the system handle insufficient disk space on the CI runner? (Monitors disk usage at each stage and fails gracefully with ≤ 28 GB threshold check)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Planck CMB temperature maps from the Planck Legacy Archive and validate file integrity using official checksums (See US-1)
- **FR-002**: System MUST generate anomaly-modified power spectra that compute and log the deviation from standard ΛCDM at ℓ ≤ 30 (See US-2)
- **FR-003**: System MUST generate initial condition files compatible with GADGET-2 or nbodykit input specifications using a mode-coupling approximation for low-ℓ anomalies (See US-2)
- **FR-004**: System MUST execute paired N-body simulations (anomaly-modified and control) on CPU-only hardware within ≤ 12 hours wall-clock time total (See US-3)
- **FR-005**: System MUST extract matter power spectrum and void size distributions from simulation snapshots at z=0 (See US-3)
- **FR-006**: System MUST perform multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for the defined hypothesis tests on power spectrum and void statistics (See US-3)
- **FR-007**: System MUST tag all statistical output metadata with classification: associational (See US-3)

### Key Entities

- **CMB Temperature Map**: Represents Planck CMB temperature anisotropy data with key attributes including resolution (Nside), galactic mask, and anomaly region coordinates
- **Initial Condition File**: Represents N-body simulation input with key attributes including particle count (256³), box size (500 Mpc/h), and power spectrum parameters
- **Simulation Snapshot**: Represents matter distribution output at specific redshift (z=0) with key attributes including particle positions, velocities, and density field
- **Power Spectrum**: Represents matter power spectrum P(k) with key attributes including wavenumber bins, amplitude values, and error bars
- **Void Catalog**: Represents detected cosmic voids with key attributes including radius, center coordinates, and underdensity contrast

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System MUST output the p-value from the Kolmogorov-Smirnov test comparing the *delta* (anomaly minus control) power spectrum against the standard ΛCDM reference mock (See US-3)
- **SC-002**: System MUST output the p-value from the Chi-squared test comparing the *delta* (anomaly minus control) void size distribution against the standard ΛCDM reference mock, with multiple-comparison correction applied (See US-3)
- **SC-003**: Simulation runtime is measured against the 12-hour wall-clock time limit on GitHub Actions free-tier runner (See US-3)
- **SC-004**: Peak RAM usage is measured against the memory constraint on GitHub Actions free-tier runner (See US-3)
- **SC-005**: Initial condition file size is measured against the specified disk space allocation per simulation (See US-2)

## Assumptions

- Planck Legacy Archive provides stable HTTP access to Commander and SMICA CMB temperature maps without requiring authentication beyond public API
- The Planck CMB data contains all required variables (temperature anisotropies at low-ℓ, Cold Spot coordinates, quadrupole measurements) needed for anomaly-modified initial conditions; The Planck Legacy Archive (PR4/Commander/SMICA) provides full-sky maps at Nside=2048, yielding a cosmic-variance-limited power spectrum up to ℓ ≈ 2500. For the low-ℓ region (ℓ ≤ 30), the measurement uncertainty is dominated by cosmic variance, not instrumental noise, providing sufficient precision to detect a deviation if the anomaly amplitude matches the observed Cold Spot or low-quadrupole deficit (ΔCℓ/Cℓ ≈ 0.1–0.3). This precision is standard in the field for low-ℓ anomaly studies, see Planck 2018 Results Paper VII.
- A simulation volume of appropriate scale with a sufficient number of particles provides a grid resolution adequate to resolve voids of cosmological interest. While this is below the resolution required for high-k non-linear clustering, it is the community standard for small-volume exploratory studies of large-scale initial condition perturbations (e.g., low-ℓ mode coupling) where the primary signal is on scales >10 Mpc/h. For a power-law effect size of |ΔP/P| ≥ 0.1 on large scales, this resolution yields a statistical power ≥ 0.80 at α=0.05, assuming 5 independent simulation realizations. This resolution is consistent with prior studies of CMB-LSS coupling, see [2021 JCAP 03 025].
- The low-ℓ CMB anomalies (quadrupole, octopole) span physical scales > 3000 Mpc/h, which exceed the 500 Mpc/h simulation box. Therefore, the system uses a mode-coupling approximation: the anomaly power is imposed as a global modulation factor on the high-ℓ spectrum to simulate the effect on large-scale structure statistics without simulating the full mode topology.
- N-body simulations with 256³ particles in a 500 Mpc/h box will complete within 12 hours on 4-core CPU-only GitHub Actions runner
- GADGET-2 or nbodykit are available and functional on the CI environment (or can be installed within the job timeout)
- Statistical tests (Kolmogorov-Smirnov, Chi-squared) are computationally trivial on CPU and fit within the 12-hour runtime budget
- All findings are framed as associational (observational design) since there is no random assignment of CMB anomalies
- For any threshold introduced (e.g., p < 0.05 for hypothesis rejection), a sensitivity analysis sweeps the cutoff over {0.01, 0.05, 0.1} and reports how rejection rates vary across it
- CAMB or CLASS linear perturbation codes are available and functional on the CI environment for generating initial conditions
- The anomaly-modified power spectrum does not produce unphysical initial conditions (e.g., negative power at any ℓ)