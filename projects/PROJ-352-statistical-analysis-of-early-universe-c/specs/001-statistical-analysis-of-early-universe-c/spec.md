# Feature Specification: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Feature Branch**: `001-cmb-defect-analysis`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to download and preprocess the Planck 2015/2018 SMICA CMB temperature maps with appropriate masking so that I have clean input data for statistical analysis.

**Why this priority**: This is the foundational data pipeline without which no analysis can proceed. It delivers immediate value by establishing reproducible data access.

**Independent Test**: Can be fully tested by downloading a single Planck map, applying the Galactic mask, and verifying pixel counts and coverage.

**Acceptance Scenarios**:

1. **Given** access to the Planck Legacy Archive, **When** the pipeline requests the SMICA temperature map at Nside=128, **Then** the file downloads successfully and validates against expected checksums
2. **Given** a downloaded CMB map, **When** the Galactic mask is applied, **Then** ≥95% sky coverage is preserved and the masked map contains ≥2.5 million valid pixels
3. **Given** the masked map, **When** basic statistics are computed, **Then** mean temperature and standard deviation are within physically plausible ranges

---

### User Story 2 - Minkowski Functional Computation (Priority: P2)

As a researcher, I need to compute all three Minkowski Functionals (area, perimeter, genus) on the masked CMB map so that I can quantify non-Gaussian topological signatures.

**Why this priority**: This is the core analytical capability that addresses the research question. Without Minkowski Functional computation, the project cannot measure defect signatures.

**Independent Test**: Can be tested by computing Minkowski Functionals on a single masked map and verifying the three functional values are returned with physically consistent ranges.

**Acceptance Scenarios**:

1. **Given** a masked CMB map with ≥2.5 million valid pixels, **When** Minkowski Functional computation is executed, **Then** all three functionals (area, perimeter, genus) are returned with numerical precision ≥6 decimal places
2. **Given** the computed functionals, **When** the computation is repeated on the same input, **Then** results are reproducible within ±0.001% numerical tolerance
3. **Given** the computation workflow, **When** executed on GitHub Actions free-tier (2 CPU, 7GB RAM), **Then** the Minkowski Functional computation completes within ≤4 hours

---

### User Story 3 - Gaussian Simulation and Statistical Comparison (Priority: P3)

As a researcher, I need to generate [deferred] Gaussian random field realizations and perform Kolmogorov-Smirnov tests comparing observed Minkowski Functionals against the Gaussian null hypothesis so that I can assess statistical significance of any deviations.

**Why this priority**: This provides the statistical validation framework. While essential for interpretation, it depends on User Stories 1 and 2 being functional.

**Independent Test**: Can be tested by generating 100 Gaussian simulations and running the KS test on mock functional data to verify the comparison pipeline works end-to-end.

**Acceptance Scenarios**:

1. **Given** the Planck power spectrum, **When** [deferred] Gaussian random field realizations are generated using `healpy`, **Then** the simulated maps preserve the input power spectrum within ±2% across multipoles ℓ=2 to ℓ=200
2. **Given** observed and simulated Minkowski Functional distributions, **When** Kolmogorov-Smirnov tests are performed, **Then** p-values are computed and stored with ≥6 decimal precision
3. **Given** multiple hypothesis tests across the three Minkowski Functionals, **When** statistical significance is assessed, **Then** family-wise error correction (Bonferroni or Holm-Bonferroni) is applied to maintain α ≤ 0.05 overall

---

### Edge Cases

- **What happens when the Planck Legacy Archive is temporarily unavailable?** The system retries download up to 3 times with exponential backoff (1s, 2s, 4s) before failing gracefully with an error message.
- **How does the system handle corrupted mask files?** If mask file integrity check fails (checksum mismatch), the system aborts with a clear error and does not proceed with analysis.
- **What happens when memory usage approaches the 7GB limit?** The system monitors RAM usage and if it exceeds 6.5GB, it reduces the number of Gaussian simulations from 1,000 to 500 and logs a warning.
- **How does the system handle edge effects near the Galactic mask boundary?** Minkowski Functional computation uses a 2-pixel buffer zone around mask edges and excludes boundary pixels from functional calculations.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Planck 2015/2018 SMICA CMB temperature map at Nside=128 resolution from the Planck Legacy Archive and validate file integrity via checksum comparison (See US-1)
- **FR-002**: System MUST apply a Galactic mask that preserves ≥95% sky coverage and produces a masked map containing ≥2.5 million valid pixels (See US-1)
- **FR-003**: System MUST compute all three Minkowski Functionals (area, perimeter, genus) on the masked CMB map with numerical precision ≥6 decimal places (See US-2)
- **FR-004**: System MUST generate [deferred] Gaussian random field realizations matching the Planck power spectrum using `healpy` for null hypothesis comparison (See US-3)
- **FR-005**: System MUST perform Kolmogorov-Smirnov tests comparing observed Minkowski Functional distributions against the Gaussian null hypothesis with p-values computed to ≥6 decimal precision (See US-3)
- **FR-006**: System MUST apply family-wise error correction (Bonferroni or Holm-Bonferroni) when assessing statistical significance across multiple hypothesis tests (See US-3)
- **FR-007**: System MUST complete the full analysis pipeline within ≤6 hours on GitHub Actions free-tier runners (2 CPU, 7GB RAM, no GPU) (See US-2)

### Key Entities

- **CMB Map**: Represents the Planck SMICA temperature anisotropy map; key attributes include Nside resolution, pixel count, and masked pixel count
- **Minkowski Functionals**: Represents the three topological statistics (area, perimeter, genus) computed on the CMB map; key attributes include functional values and threshold levels
- **Gaussian Realization**: Represents a single simulated CMB map generated from the Planck power spectrum; key attributes include simulation ID and power spectrum fidelity
- **Statistical Test Result**: Represents the output of a Kolmogorov-Smirnov test; key attributes include D-statistic, p-value, and corrected significance level

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data pipeline completion rate is measured against the Planck Legacy Archive availability baseline (See US-1)
- **SC-002**: Minkowski Functional computation accuracy is measured against analytical expectations for Gaussian random fields (See US-2)
- **SC-003**: Statistical comparison validity is measured against the published cosmic string tension constraints (Gμ ≤ 10⁻⁷) from Planck 2015 results (See US-3)
- **SC-004**: Compute resource adherence is measured against the GitHub Actions free-tier specification (2 CPU, 7GB RAM, ≤6h) (See US-2)

---

## Assumptions

- The Planck 2015/2018 SMICA CMB temperature maps at Nside=128 contain sufficient information to detect or constrain non-Gaussian signatures consistent with topological defects
- The Galactic mask provided by the Planck Legacy Archive removes foreground contamination while preserving ≥95% of the cosmological signal
- Minkowski Functionals computed on temperature anisotropies are sensitive to the non-Gaussian signatures predicted by cosmic string and domain wall models
- The analysis is observational (no random assignment); therefore all findings regarding defect constraints must be framed as ASSOCIATIONAL rather than causal
- The [deferred] Gaussian random field realizations provide adequate statistical power for the Kolmogorov-Smirnov test; if power is insufficient, this limitation will be explicitly documented
- Family-wise error correction using Bonferroni or Holm-Bonferroni maintains the overall Type I error rate at α ≤ 0.05 across the three Minkowski Functional tests
- Any decision thresholds introduced (e.g., significance cutoffs) will be justified by community standards in cosmological data analysis and will be accompanied by sensitivity analysis sweeping the threshold over {0.01, 0.05, 0.1} to assess robustness
- The Planck power spectrum data required to generate Gaussian realizations is available and compatible with the `healpy` library version used in the analysis
- All statistical instruments (Kolmogorov-Smirnov test, Minkowski Functional computation) are validated methods with citable validation in the cosmological literature
- [NEEDS CLARIFICATION: Does the Planck SMICA map at Nside=128 resolution contain the specific non-Gaussian signature scales predicted by the topological defect models referenced in the literature?]
- [NEEDS CLARIFICATION: Is the sample size of 1,000 Gaussian simulations sufficient for the Kolmogorov-Smirnov test to achieve adequate statistical power at α=0.05?]
- [NEEDS CLARIFICATION: Are there additional covariates (e.g., beam effects, noise characteristics) that must be explicitly modeled in the Gaussian simulations beyond the power spectrum matching?]
