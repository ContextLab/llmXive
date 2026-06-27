# Feature Specification: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

**Feature Branch**: `001-cmb-gap-bias-analysis`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: Research project to quantify systematic biases in cosmological parameter recovery from CMB data gaps

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Simulated CMB Maps with Controlled Gap Patterns (Priority: P1)

Researcher MUST be able to generate simulated CMB temperature/polarization maps with systematically varied gap characteristics (fraction, spatial distribution, morphology) to establish ground-truth baselines for bias quantification.

**Why this priority**: Without controlled gap patterns on simulated data, the project cannot isolate gap-induced bias from other systematic effects. This is the foundation for all downstream analysis.

**Independent Test**: Can be fully tested by generating 50 simulation realizations with known gap parameters and verifying each map contains the specified gap fraction (±0.5%) and morphology type.

**Acceptance Scenarios**:

1. **Given** a CMB simulation with known ground-truth cosmological parameters, **When** the system applies a gap mask with [deferred] fraction and clustered distribution, **Then** the masked map contains [deferred] ±0.5% masked pixels and the unmasked regions match the original ground-truth values
2. **Given** 50 simulation realizations, **When** gap patterns are varied across fractions ([deferred], [deferred], [deferred], [deferred], [deferred]), **Then** each realization maintains its assigned gap fraction within tolerance and ground-truth parameters remain accessible for bias comparison

---

### User Story 2 - Apply Gap-Filling Algorithms and Compute Power Spectra (Priority: P2)

Researcher MUST be able to apply multiple gap-filling algorithms (harmonic interpolation, Wiener filtering, iterative harmonic synthesis) to masked maps and compute angular power spectra (Cℓ) using HEALPix Nside=512.

**Why this priority**: This enables comparison of how different reconstruction methods propagate gap-induced uncertainty into power spectrum estimates, which is the mechanism linking gaps to parameter bias.

**Independent Test**: Can be fully tested by applying each algorithm to a masked map and verifying the recovered Cℓ values differ by <5% from the ground-truth power spectrum for ℓ < 2000.

**Acceptance Scenarios**:

1. **Given** a masked CMB map with [deferred] gap fraction, **When** Wiener filtering is applied, **Then** the recovered power spectrum at ℓ = 100-1000 matches ground-truth within 5% for at least 90% of multipoles
2. **Given** the same masked map, **When** all three gap-filling algorithms are applied, **Then** each produces a complete power spectrum (no NaN values) and execution time per algorithm ≤ 30 minutes on CPU-only hardware

---

### User Story 3 - Estimate Cosmological Parameters and Quantify Bias (Priority: P3)

Researcher MUST be able to estimate cosmological parameters (H₀, Ωₘ, nₛ, τ) from recovered power spectra using CAMB/CosmoMC likelihoods and compute bias magnitude relative to ground-truth values.

**Why this priority**: This delivers the final research output—quantified relationship between gap characteristics and parameter bias—which is the core research question.

**Independent Test**: Can be fully tested by comparing recovered parameters from gap-filled maps against ground-truth parameters from unmasked simulations and verifying bias is calculated as absolute difference with p-value < 0.05 for significance testing.

**Acceptance Scenarios**:

1. **Given** a recovered power spectrum from a gap-filled map, **When** CAMB likelihood estimation is executed, **Then** parameter posteriors for H₀, Ωₘ, nₛ, τ are produced with credible intervals at 68% and 95% confidence levels
2. **Given** parameter estimates from gap-filled and unmasked simulations, **When** bias is computed, **Then** the absolute difference is calculated for each parameter and ANOVA/linear regression tests whether bias scales significantly with gap fraction (α = 0.05)

---

### Edge Cases

- What happens when gap fraction exceeds 20% (beyond planned range)? System must flag this as out-of-scope and prevent parameter estimation that would exceed computational constraints
- How does system handle corrupted HEALPix files or missing simulation data? System must log the error, skip the realization, and continue with remaining simulations (minimum 40 of 50 must complete for statistical validity)
- What happens when gap-filling algorithm fails to converge? System must log the failure, record the gap configuration, and exclude that realization from final analysis

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate simulated CMB maps with controllable gap characteristics (fraction ∈ {[deferred], [deferred], [deferred], [deferred], [deferred]}, spatial distribution ∈ {random, clustered}, morphology ∈ {point-source, Galactic plane}) (See US-1)
- **FR-002**: System MUST apply ≥ 3 gap-filling algorithms (harmonic interpolation, Wiener filtering, iterative harmonic synthesis) to each masked map and record execution time per algorithm (See US-2)
- **FR-003**: System MUST compute angular power spectra (Cℓ) using HEALPix with Nside = 512, ensuring all multipoles ℓ ≤ 2000 are calculated without NaN values (See US-2)
- **FR-004**: System MUST estimate cosmological parameters (H₀, Ωₘ, nₛ, τ) from recovered power spectra using CAMB/CosmoMC likelihoods and store ground-truth parameter values for bias comparison (See US-3)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) when testing >1 hypothesis (e.g., bias scaling with gap fraction AND distribution type) to control family-wise error rate at α = 0.05 (See US-3)
- **FR-006**: System MUST run complete analysis pipeline on CPU-only hardware within ≤ 6 hours total runtime, using ≤ 7 GB RAM and ≤ 14 GB disk space (See US-1, US-2, US-3)
- **FR-007**: System MUST perform sensitivity analysis on decision thresholds (α = 0.05 significance threshold, 5% power spectrum accuracy threshold) by sweeping over values ∈ {0.01, 0.05, 0.1} for α and {3%, 5%, 7%} for accuracy, reporting how parameter bias rates vary across the sweep (See US-3)

### Key Entities *(include if feature involves data)*

- **CMB Simulation Map**: Represents a simulated CMB temperature/polarization map with ground-truth cosmological parameters; key attributes include pixel values, gap mask, Nside resolution, and ground-truth (H₀, Ωₘ, nₛ, τ)
- **Gap Configuration**: Represents a specific gap pattern applied to a map; key attributes include gap fraction, spatial distribution type, morphology type, and realization ID
- **Recovered Power Spectrum**: Represents the angular power spectrum (Cℓ) computed from a gap-filled map; key attributes include multipole values (ℓ), power spectrum values, and algorithm used for gap-filling
- **Parameter Posterior**: Represents estimated cosmological parameters with credible intervals; key attributes include parameter name, median estimate, 68% credible interval, 95% credible interval, and ground-truth comparison value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Parameter bias magnitude (absolute difference between recovered and ground-truth H₀, Ωₘ, nₛ, τ) is measured against the ground-truth values from unmasked simulations (See US-3)
- **SC-002**: Statistical significance of bias scaling with gap characteristics (p-value from ANOVA/linear regression) is measured against the α = 0.05 threshold (See US-3)
- **SC-003**: Computational feasibility (total runtime, peak RAM usage) is measured against the free-tier CI constraints (≤ 6 hours, ≤ 7 GB RAM, ≤ 14 GB disk) (See US-1, US-2, US-3)
- **SC-004**: Power spectrum recovery accuracy (percentage of multipoles ℓ ≤ 2000 within 5% of ground-truth) is measured against the unmasked power spectrum baseline (See US-2)
- **SC-005**: Sensitivity analysis coverage (number of threshold values swept, variance in bias rates across sweep) is measured against the minimum requirement of 3 threshold values with documented rate variation (See US-3)

## Assumptions

- CMB simulation data from Planck Legacy Archive or CAMB contains all required variables (temperature/polarization maps, ground-truth cosmological parameters, power spectrum data) without needing external imputation
- HEALPix Nside = 512 maps (≈ 3 million pixels) fit within 7 GB RAM when loaded and processed sequentially; if memory pressure occurs, maps will be processed in chunks or with reduced Nside
- CAMB/CosmoMC likelihood code can run on CPU-only hardware without CUDA/GPU acceleration; if GPU-specific optimizations are required, the analysis will use the CPU-optimized version
- The 50 simulation realizations specified in the methodology are sufficient for statistical power at α = 0.05; if power analysis indicates more realizations are needed, the number will be increased within the 6-hour runtime constraint
- Gap-filling algorithms (harmonic interpolation, Wiener filtering, iterative harmonic synthesis) are available in standard Python packages (healpy, PyWiener, or equivalent) without requiring proprietary software
- Parameter estimation using CAMB/CosmoMC produces converged posteriors within reasonable iteration limits; if convergence fails, the realization will be excluded from final analysis (minimum 40 of 50 must succeed)
- The observational design (simulated gap patterns on simulated CMB) frames findings as associational relationships between gap characteristics and parameter bias; causal claims about real CMB data are out of scope
- [NEEDS CLARIFICATION: Does the Planck Legacy Archive or CAMB simulation output contain the specific ground-truth cosmological parameters (H₀, Ωₘ, nₛ, τ) needed for bias calculation, or must these be derived from metadata?]
- [NEEDS CLARIFICATION: Are the three gap-filling algorithms (harmonic interpolation, Wiener filtering, iterative harmonic synthesis) available as pre-installed packages on the GitHub Actions free-tier runner, or must they be installed during the workflow?]
- [NEEDS CLARIFICATION: Does the 6-hour runtime constraint allow for 50 realizations × 3 algorithms × 5 gap fractions, or must the sample size be reduced (e.g., 30 realizations) to stay within bounds?]
