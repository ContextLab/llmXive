# Feature Specification: Mapping Cosmic Microwave Background Cold Spots to Large-Scale Structure

**Feature Branch**: `001-mapping-cosmic-microwave-background-cold`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Mapping CMB Cold Spots to Large-Scale Structure to test the supervoid hypothesis via Integrated Sachs-Wolfe effect."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1) (See US-1)

The researcher MUST be able to download, parse, and preprocess the Planck 2018 CMB temperature maps and the SDSS/DES galaxy density catalogs into a unified, memory‑efficient format suitable for CPU‑only analysis.

**Why this priority**: Without clean, aligned data, no statistical analysis can occur. This is the foundational step for the entire project.

**Independent Test**: The system can be tested by running the data pipeline on a small subset (e.g., [deferred] of the sky) and verifying that the output HEALPix maps (nside=64) contain valid temperature and density values without NaNs or memory errors on a 7 GB RAM limit.

**Acceptance Scenarios**:

1. **Given** the Planck Legacy Archive (https://pla.esac.esa.int) and SDSS DR16 (https://data.sdss.org) / DES (https://des.ncsa.illinois.edu) URLs, **When** the ingestion script executes, **Then** the system downloads the commander/smica CMB maps and the galaxy catalog subset, converts them to HEALPix nside=64, and saves them as compressed FITS files within 30 minutes.
2. **Given** the raw galaxy catalog, **When** the redshift binning process runs for z=0.2–1.0, **Then** the system produces three distinct density maps (z‑bins) with no more than 5 % pixel loss due to missing redshift data, and the total memory usage remains below **7 GB**. If a redshift gap is detected, the affected pixels are masked and a warning is logged (FR‑007).

---

### User Story 2 - Cold Spot Identification and Cross‑Correlation (Priority: P2) (See US-2)

The researcher MUST be able to identify cold spot candidates using a top‑hat filter and compute the cross‑correlation function $\xi(\theta)$ between these spots and the underdense regions in the galaxy maps.

**Why this priority**: This implements the core physics hypothesis (alignment of CMB anomalies with supervoids). It is the primary analytical engine of the feature.

**Independent Test**:  
*Null‑control*: Apply the pipeline to a synthetic Gaussian random field where the true correlation is zero; verify that the computed $\xi(\theta)$ is statistically indistinguishable from zero.  
*Positive‑control*: Apply the pipeline to a synthetic field with an injected ISW‑like correlation (e.g., add a known dipole pattern); verify that the pipeline recovers a statistically significant positive $\xi(\theta)$.

**Acceptance Scenarios**:

1. **Given** the preprocessed CMB map, **When** the top‑hat filter (with an appropriate radius) is applied, **Then** the system identifies all pixels with temperature $< -2\sigma$ from the mean and outputs a **non‑empty list of candidate cold spot coordinates (count deferred)**. If no pixels satisfy the threshold, the system returns an empty list and logs a p‑value of 1.0 (FR‑008).
2. **Given** the cold spot coordinates and the galaxy density maps, **When** the cross‑correlation function is computed, **Then** the system outputs a correlation curve $\xi(\theta)$ for angular separations $\theta \in [0°, 10°]$ with a resolution of sub‑degree precision, completing the calculation in [deferred].

---

### User Story 3 - Statistical Significance (Priority: P3) (See US-3)

The researcher MUST be able to generate a sufficiently large set of ΛCDM Gaussian random realizations to establish a null distribution and perform a Monte‑Carlo rank test.

**Why this priority**: This provides the statistical rigor required to claim a discovery or a null result, addressing the "multiplicity" and "threshold justification" methodological requirements.

**Independent Test**: The system can be tested by running the simulation suite on a CPU‑only runner; the Monte‑Carlo p‑value must be returned.

**Acceptance Scenarios**:

1. **Given** the observed correlation amplitude, **When** the simulation module generates a set of ΛCDM realizations using CAMB/CLASS, **Then** the system applies the identical detection‑and‑cross‑correlation pipeline to each realization **(including a freshly generated synthetic log‑normal galaxy density map matching the observed mask statistics for each CMB realization)** and computes a Monte‑Carlo rank‑test p‑value within 60 seconds of simulation completion (FR‑004, US‑3). The ensemble size is **1 000** realizations (Constitution VI) to enable p‑values down to a very low significance level.
2. **Given** the baseline threshold of $-2\sigma$, **When** the null‑distribution analysis runs, **Then** the system reports the Monte‑Carlo p‑value and logs the number of realizations used.

### Edge Cases

- **Redshift‑gap handling**: If the galaxy catalog has a gap in redshift coverage (e.g., $z \approx 0.5$), the system must mask the affected pixels, log a warning, and continue without crashing (FR‑007).
- **Empty‑candidate handling**: If no cold spots meet the $-2\sigma$ threshold, the system must gracefully return an empty candidate list and report a p‑value of 1.0 (FR‑008).
- **Memory‑pressure handling**: If memory usage exceeds the 7 GB limit during HEALPix map generation, the system must abort the operation, log a clear error suggesting processing a smaller sky fraction, and **must not** downsample to nside=32 (FR‑009).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Planck 2018 CMB maps (commander/smica) from the Planck Legacy Archive (https://pla.esac.esa.int) and SDSS/DES galaxy catalogs from their public repositories (https://data.sdss.org, https://des.ncsa.illinois.edu), converting them to HEALPix nside=64 format, serving US-1 (See US-1).  
  *Justification*: Using authentic data preserves construct validity for the ISW supervoid hypothesis.
- **FR-002**: System MUST identify cold spot candidates by applying a top‑hat filter **with a baseline radius = 5°** and thresholding at $-2\sigma$ from the mean temperature, serving US-2 (See US-2).  
  *Justification*: Baseline radius and threshold are standard in ISW analyses (e.g., Granett et al. 2008).
- **FR-003**: System MUST compute the cross‑correlation function $\xi(\theta)$ between identified cold spots and underdense regions in redshift bins $z \in [0.2, 1.0]$, serving US-2 (See US-2).  
  *Justification*: Cross‑correlation across these bins captures the expected ISW signal.
- **FR-004**: System MUST generate a set of **1 000** ΛCDM Gaussian random realizations, **and for each realization also generate a fresh synthetic galaxy density map (log‑normal, matching the observed mask statistics)**, run the identical detection‑and‑cross‑correlation pipeline on each, and compute a Monte‑Carlo rank‑test p‑value for the **average $\xi(\theta)$ over $\theta\in[0°,10°]$** (See US-3).  
  *Justification*: Constitution VI requires exactly 1 000 realizations; this number provides sufficient power (≥80 % for ISW amplitude ≥0.5 µK, α=0.05) per literature.
- **FR-006**: System MUST ensure total pipeline runtime ≤ 6 hours and peak memory usage ≤ 7 GB on a 2‑core CPU‑only environment (project‑wide constraint) (See US-1, US-2, US-3).
- **FR-007**: System MUST detect redshift gaps, mask the affected pixels, and log a warning without aborting (See US-1).  
  *Justification*: Guarantees graceful handling of incomplete data.  
  *Test fixture*: FR-024 provides a synthetic galaxy catalog containing a known redshift gap for automated testing.
- **FR-008**: System MUST handle the case of zero cold‑spot detections by returning an empty list and a p‑value of 1.0, with an appropriate log entry (See US-2). The output CSV `cold_spots.csv` must contain columns `ra_deg, dec_deg, temperature_delta, filter_radius_deg`.  
  *Justification*: Guarantees well‑defined output in edge cases.  
  *Test fixture*: FR-025 supplies a synthetic CMB map with no pixels below –2σ to trigger this path deterministically.
- **FR-009**: System MUST abort map generation if memory usage would exceed 7 GB, logging a suggestion to limit the processed sky fraction; no downsampling to nside=32 is performed (See US-1).  
  *Justification*: Prevents silent degradation of data quality.
- **FR-010**: System MUST compute and report per‑redshift‑bin correlation amplitudes **and descriptive per‑bin p‑values** (reported for information only), and produce a plot of significance versus redshift bin (See US-3).
- **FR-011**: System MUST produce the final deliverables: (a) correlation plots (PNG), (b) a p‑value table (CSV), (c) a reproducible Jupyter notebook (.ipynb) containing the full analysis pipeline (See US-3).
- **FR-013**: // FR-013–FR-015 reserved for future requirements; numbering gap intentional
- **FR-019**: // (Removed per scope review)
- **FR-020**: // (Removed per scope review)
- **FR-021**: // (Removed per scope review)
- **FR-022**: System MUST include an automated test for FR‑009 that verifies the memory‑exceed abort behavior using a synthetic oversized HEALPix map (See US‑1).
- **FR-023**: System MUST perform a power analysis using the 1 000 Monte‑Carlo realizations to confirm that the pipeline can detect an ISW amplitude ≥ 0.5 µK with ≥ 80 % power at α=0.05 (see SC‑009).  
  *Justification*: Demonstrates that the chosen simulation budget is sufficient for the scientific goal.
- **FR-024**: System MUST provide a synthetic galaxy catalog containing a deliberately introduced redshift gap (e.g., missing galaxies in 0.48 < z < 0.52) for deterministic testing of FR‑007.  
  *Justification*: Enables reproducible verification of gap‑handling logic.
- **FR-025**: System MUST provide a synthetic CMB temperature map in which no pixel falls below the –2σ threshold, to deterministically trigger the empty‑candidate path required by FR‑008.  
  *Justification*: Guarantees reproducible testing of the no‑cold‑spot edge case.
- **FR-026**: System MUST validate the theoretical ISW curve (FR‑012) by comparing selected $\xi_{\text{theory}}$ values at $\theta = 2°, 5°, 8°$ against published reference numbers (e.g., Granett 2008) and require agreement within a 5 % relative tolerance.  
  *Justification*: Ensures the theoretical benchmark is correctly implemented.

### Key Entities

- **CMB Map**: A HEALPix pixelized representation of the CMB temperature anisotropy (nside=64), derived from Planck 2018 data.
- **Galaxy Density Map**: A HEALPix pixelized representation of galaxy number density in specific redshift shells, derived from SDSS/DES catalogs.
- **Cold Spot Candidate**: A coordinate (RA, Dec) and temperature deviation value identified as an underdense region in the CMB map.
- **Correlation Amplitude**: The scalar value representing the strength of the alignment between cold spots and underdensities at a specific angular scale (defined as the mean of $\xi(\theta)$ over $\theta\in[0°,10°]$).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed cross‑correlation amplitude is evaluated against the null distribution from **1 000** ΛCDM realizations using a Monte‑Carlo rank‑test p‑value (average $\xi(\theta)$ over 0°–10°) (See US-3). **Report the expected signal‑to‑noise ratio (≈1–3) from ΛCDM forecasts and the minimum detectable effect size given N=1 000.**
- **SC-002**: The sensitivity of the detection (p‑value stability) is measured across the threshold and filter‑radius sweeps defined in FR‑005 (See US-3). *(Note: FR‑005 has been removed; this criterion now reflects the original scope and is retained for completeness of earlier analysis.)*
- **SC-003**: The computational feasibility is measured against the 6‑hour runtime limit and 7 GB RAM constraint on the GitHub Actions free‑tier runner (See US-1, US-2, US-3).
- **SC-004**: The alignment strength is measured by computing a χ² statistic between the observed $\xi(\theta)$ and the theoretical ISW curve (FR‑012) over $\theta\in[0°,10°]$ with 0.5° bins; per‑bin uncertainties $\sigma_i$ are obtained from the variance across the 1 000 Monte‑Carlo realizations, and a diagonal covariance approximation is used. The result is considered acceptable if χ²/ndf ≤ 1.5 (p≥0.05) (See US-2).
- **SC-005**: Per‑redshift‑bin significance (descriptive p‑value) is reported and plotted as a function of redshift bin (See US-3).
- **SC-006**: The final artifact package (correlation plots, p‑value table, reproducible notebook) is generated and included in the repository release (See US-3).
- **SC-007**: All output artifacts must pass schema validation against their respective YAML/JSON contracts (See FR‑019). *(FR‑019 removed; this criterion now reflects prior expectations and will be satisfied by existing validation scripts.)*
- **SC-008**: CI pipeline must complete all tests and report a green status on each push (See FR‑020). *(FR‑020 removed; CI integration is no longer a required deliverable.)*
- **SC-009**: Power analysis confirms that with **1 000** realizations the pipeline can detect an ISW amplitude ≥ 0.5 µK at 80 % power (α=0.05) (derived from FR‑023 and FR‑004).  

## Assumptions

- The Planck CMB maps and SDSS/DES galaxy catalogs are publicly available and accessible via the provided URLs without requiring authentication or complex proxy configurations.
- The "cold spot" definition using a $-2\sigma$ threshold and **baseline radius of 5°** is sufficient for initial detection; more complex topological definitions are out of scope for this MVP.
- The galaxy photometric redshifts in the SDSS/DES catalogs are accurate enough to bin galaxies into $z=0.2–1.0$ shells with minimal catastrophic outlier contamination.
- The integrated Sachs‑Wolfe (ISW) effect is the primary physical mechanism linking CMB cold spots to large‑scale structure underdensities in this redshift range.
- The dataset fits within the 7 GB RAM limit after HEALPix downsampling to nside=64; if the full‑resolution data is required, the analysis will be restricted to a [deferred] sky fraction.
- **Statistical methodology**: We adopt a Monte‑Carlo rank test as a non‑parametric alternative to the Kolmogorov‑Smirnov test; both assess tail‑probability of the observed amplitude. The rank test is chosen for robustness to discrete test statistics. (Justification for scope‑level change – see concern scope-734a85d9.)
- **Per‑redshift‑bin p‑values** are reported for information only; statistical significance is assessed using the global Monte‑Carlo rank test (see FR‑004). This avoids multiple‑testing inflation across bins.
- **Multiple‑testing correction**: The Benjamini‑Hochberg false‑discovery rate procedure is applied to the 35 sensitivity‑sweep configurations; the baseline (5°, –2σ) configuration is pre‑registered as the primary analysis. *(Note: sensitivity sweep removed; this note retained for historical context.)*
- The synthetic galaxy density maps used in the Monte‑Carlo simulations are generated as log‑normal fields matching the observed mask and power spectrum, ensuring realistic variance contributions from the galaxy field.
