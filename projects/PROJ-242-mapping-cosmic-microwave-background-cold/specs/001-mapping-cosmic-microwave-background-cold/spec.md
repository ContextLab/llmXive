# Feature Specification: Mapping Cosmic Microwave Background Cold Spots to Large-Scale Structure

**Feature Branch**: `001-mapping-cosmic-microwave-background-cold`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Mapping CMB Cold Spots to Large-Scale Structure to test the supervoid hypothesis via Integrated Sachs-Wolfe effect."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The researcher MUST be able to download, parse, and preprocess the Planck 2018 CMB temperature maps and the SDSS/DES galaxy density catalogs into a unified, memory‑efficient format suitable for CPU‑only analysis.

**Why this priority**: Without clean, aligned data, no statistical analysis can occur. This is the foundational step for the entire project.

**Independent Test**: The system can be tested by running the data pipeline on a small subset (e.g., [deferred] of the sky) and verifying that the output HEALPix maps (nside=64) contain valid temperature and density values without NaNs or memory errors on a 7 GB RAM limit.

**Acceptance Scenarios**:

1. **Given** the Planck Legacy Archive and SDSS DR16 URLs, **When** the ingestion script executes, **Then** the system downloads the commander/smica CMB maps and the galaxy catalog subset, converts them to HEALPix nside=64, and saves them as compressed FITS files within 30 minutes.
2. **Given** the raw galaxy catalog, **When** the redshift binning process runs for z=0.2–1.0, **Then** the system produces three distinct density maps (z‑bins) with no more than 5 % pixel loss due to missing redshift data, and the total memory usage remains below 4 GB. If a redshift gap is detected, the affected pixels are masked and a warning is logged (FR‑007).

---

### User Story 2 - Cold Spot Identification and Cross‑Correlation (Priority: P2)

The researcher MUST be able to identify cold spot candidates using a top‑hat filter and compute the cross‑correlation function $\xi(\theta)$ between these spots and the underdense regions in the galaxy maps.

**Why this priority**: This implements the core physics hypothesis (alignment of CMB anomalies with supervoids). It is the primary analytical engine of the feature.

**Independent Test**:  
*Null‑control*: Apply the pipeline to a synthetic Gaussian random field where the true correlation is zero; verify that the computed $\xi(\theta)$ is statistically indistinguishable from zero.  
*Positive‑control*: Apply the pipeline to a synthetic field with an injected ISW‑like correlation (e.g., add a known dipole pattern); verify that the pipeline recovers a statistically significant positive $\xi(\theta)$.

**Acceptance Scenarios**:

1. **Given** the preprocessed CMB map, **When** the top‑hat filter (with an appropriate radius) is applied, **Then** the system identifies all pixels with temperature $< -2\sigma$ from the mean and outputs a **non‑empty list of candidate cold spot coordinates (count deferred)**. If no pixels satisfy the threshold, the system returns an empty list and logs a p‑value of 1.0 (FR‑008).
2. **Given** the cold spot coordinates and the galaxy density maps, **When** the cross‑correlation function is computed, **Then** the system outputs a correlation curve $\xi(\theta)$ for angular separations $\theta \in [0°, 10°]$ with a resolution of sub‑degree precision, completing the calculation in [deferred].

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to generate a sufficiently large set of ΛCDM Gaussian random realizations to establish a null distribution, perform a Monte‑Carlo rank test, and run a sensitivity analysis on the cold‑spot detection parameters.

**Why this priority**: This provides the statistical rigor required to claim a discovery or a null result, addressing the "multiplicity" and "threshold justification" methodological requirements.

**Independent Test**: The system can be tested by running the simulation suite on a CPU‑only runner; the Monte‑Carlo p‑value must be returned, and the sensitivity sweep must show how the p‑value changes with threshold and filter‑radius adjustments.

**Acceptance Scenarios**:

1. **Given** the observed correlation amplitude, **When** the simulation module generates 1000 ΛCDM realizations using CAMB/CLASS, **Then** the system applies the identical detection‑and‑cross‑correlation pipeline to each realization (keeping the real galaxy mask fixed) and computes a Monte‑Carlo rank‑test p‑value within 60 seconds of simulation completion (FR‑004, US‑3).
2. **Given** the baseline threshold of $-2\sigma$, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over $\{-1.5\sigma, -1.75\sigma, -2.0\sigma, -2.25\sigma, -2.5\sigma, -2.75\sigma, -3.0\sigma\}$ **and** the filter radius over $\{3°,4°,5°,6°,7°\}$, outputting a table showing the variation in p‑values and the number of detected cold spots for each combination (FR‑005).

### Edge Cases

- **Redshift‑gap handling**: If the galaxy catalog has a gap in redshift coverage (e.g., $z \approx 0.5$), the system must mask the affected pixels, log a warning, and continue without crashing (FR‑007).
- **Empty‑candidate handling**: If no cold spots meet the $-2\sigma$ threshold, the system must gracefully return an empty candidate list and report a p‑value of 1.0 (FR‑008).
- **Memory‑pressure handling**: If memory usage exceeds the 7 GB limit during HEALPix map generation, the system must abort the operation, log a clear error suggesting processing a smaller sky fraction, and **must not** downsample to nside=32 (FR‑009, FR‑016).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Planck 2018 CMB maps (commander/smica) and SDSS/DES galaxy catalogs, converting them to HEALPix nside=64 format, serving US-1 (See US-1).
- **FR-002**: System MUST identify cold spot candidates by applying a top‑hat filter (radius 5°) and thresholding at $-2\sigma$ from the mean temperature, serving US-2 (See US-2).
- **FR-003**: System MUST compute the cross‑correlation function $\xi(\theta)$ between identified cold spots and underdense regions in redshift bins $z \in [0.2, 1.0]$, serving US-2 (See US-2).
- **FR-004**: System MUST generate 1000 ΛCDM Gaussian random realizations, run the identical detection‑and‑cross‑correlation pipeline on each (using the real galaxy mask), and compute a Monte‑Carlo rank‑test p‑value for the observed correlation amplitude (See US-3).
- **FR-005**: System MUST execute a sensitivity analysis sweeping the cold‑spot threshold over $-1.5\sigma$ to $-3\sigma$ in 0.25σ steps **and** the filter radius over 3°–7° in 1° steps, reporting the resulting p‑value variations (See US-3).
- **FR-006**: System MUST ensure total pipeline runtime ≤ 6 hours and peak memory usage ≤ 7 GB on a 2‑core CPU‑only environment (project‑wide constraint) (See US-1, US-2, US-3).
- **FR-007**: System MUST detect redshift gaps, mask the affected pixels, and log a warning without aborting (See US-1).
- **FR-008**: System MUST handle the case of zero cold‑spot detections by returning an empty list and a p‑value of 1.0, with an appropriate log entry (See US-2).
- **FR-009**: System MUST abort map generation if memory usage would exceed 7 GB, logging a suggestion to limit the processed sky fraction; no downsampling to nside=32 is performed (See US-1).
- **FR-010**: System MUST compute and report per‑redshift‑bin correlation amplitudes and their Monte‑Carlo p‑values, and produce a plot of significance versus redshift bin (See US-3).
- **FR-011**: System MUST produce the final deliverables: (a) correlation plots (PNG), (b) a p‑value table (CSV), and (c) a reproducible Jupyter notebook (.ipynb) containing the full analysis pipeline (See US-3).
- **FR-012**: System MUST compute the theoretical ISW cross‑correlation curve for supervoids using the linear‑theory model of Granett et al. 2008 (ApJ 2008) as the reference (See US-2).
- **FR-016**: System MUST include a synthetic oversized HEALPix map fixture (nside=256) to trigger the memory‑pressure path; a test must verify that the system aborts with the correct log message and does not perform any downsampling (See US-1).

### Key Entities

- **CMB Map**: A HEALPix pixelized representation of the CMB temperature anisotropy (nside=64), derived from Planck 2018 data.
- **Galaxy Density Map**: A HEALPix pixelized representation of galaxy number density in specific redshift shells, derived from SDSS/DES catalogs.
- **Cold Spot Candidate**: A coordinate (RA, Dec) and temperature deviation value identified as an underdense region in the CMB map.
- **Correlation Amplitude**: The scalar value representing the strength of the alignment between cold spots and underdensities at a specific angular scale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed cross‑correlation amplitude is evaluated against the null distribution from 1000 ΛCDM realizations using a Monte‑Carlo rank‑test p‑value (See US-3).
- **SC-002**: The sensitivity of the detection (p‑value stability) is measured across the threshold and filter‑radius sweeps defined in FR‑005 (See US-3).
- **SC-003**: The computational feasibility is measured against the 6‑hour runtime limit and 7 GB RAM constraint on the GitHub Actions free‑tier runner (See US-1, US-2, US-3).
- **SC-004**: The alignment strength is measured against the theoretical ISW cross‑correlation curve for supervoids computed by FR‑012 (Granett et al. 2008) (See US-2).
- **SC-005**: Per‑redshift‑bin significance (p‑value) is reported and plotted as a function of redshift bin (See US-3).
- **SC-006**: The final artifact package (correlation plots, p‑value table, reproducible notebook) is generated and included in the repository release (See US-3).

## Assumptions

- The Planck CMB maps and SDSS/DES galaxy catalogs are publicly available and accessible via the provided URLs without requiring authentication or complex proxy configurations.
- The "cold spot" definition using a $-2\sigma$ threshold and 5° radius is sufficient for initial detection; more complex topological definitions are out of scope for this MVP.
- The galaxy photometric redshifts in the SDSS/DES catalogs are accurate enough to bin galaxies into $z=0.2–1.0$ shells with minimal catastrophic outlier contamination.
- The integrated Sachs‑Wolfe (ISW) effect is the primary physical mechanism linking CMB cold spots to large‑scale structure underdensities in this redshift range.
- The dataset fits within the 7 GB RAM limit after HEALPix downsampling to nside=64; if the full‑resolution data is required, the analysis will be restricted to a [deferred] sky fraction.
- The "multiplicity" issue of testing multiple redshift bins is addressed by the global Monte‑Carlo rank test across the combined correlation signal, rather than individual bin tests requiring Bonferroni correction.
