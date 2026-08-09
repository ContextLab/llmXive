# Specification: Assessing the Validity of the Cosmological Principle with Public CMB Data

## Overview
This project validates the Cosmological Principle (isotropy and homogeneity) using Planck 2018 CMB data. We test for hemispherical power asymmetry using the Maximum Statistic approach to avoid multiple comparison pitfalls.

## User Stories

### US1: Data Acquisition and Preprocessing
**As a** researcher
**I want** to download, validate, mask, and downsample the Planck SMICA CMB map
**So that** I can perform harmonic analysis within CI resource constraints.

**Acceptance Criteria:**
1. Planck 2018 SMICA Nside=2048 map downloaded from ESA archive.
2. SHA-256 checksum validation passes.
3. Commander mask applied, retaining ≥95% of unmasked sky.
4. Map downgraded to Nside=128 for analysis.
5. No NaN or Inf values in processed map.

### US2: Harmonic Analysis
**As a** researcher
**I want** to compute spherical harmonic coefficients and angular power spectra
**So that** I can quantify power distribution across the sky and hemispheres.

**Acceptance Criteria:**
1. `a_lm` coefficients computed for a range of low to high angular momenta.
2. Full-sky C_l spectrum derived.
3. Hemispherical splits (N/S, E/W) generated with masks.
4. Pseudo-C_l spectra computed using MASTER algorithm for corrections.

### US3: Statistical Testing
**As a** researcher
**I want** to generate Monte Carlo null distributions and compute p-values
**So that** I can determine if observed asymmetries are statistically significant.

**Acceptance Criteria:**
1. Isotropic Gaussian simulations generated using Planck best-fit C_l.
2. Hemispherical variance computed for observed and simulated maps.
3. Maximum Statistic approach applied: p-value = max(N/S asymmetry, E/W asymmetry).
4. **Acceptance Scenario 3**: If the Maximum Statistic p-value < 0.05, we reject the null hypothesis of isotropy. The Benjamini-Hochberg correction is NOT used; instead, the Maximum Statistic approach controls the family-wise error rate by construction.

### US4: Reproducibility and Sensitivity
**As a** researcher
**I want** to document the pipeline and perform sensitivity analysis
**So that** results are reproducible and robust to threshold choices.

**Acceptance Criteria:**
1. Code versions and dependencies pinned in `requirements.txt`.
2. Sensitivity sweep over thresholds documented.
3. README includes installation, usage, and data provenance.

## Data Model
- **CMB Map**: HEALPix formatted array (Nside=128).
- **Power Spectrum**: Array of C_l values for l=2..128.
- **Simulations**: List of CMB maps generated from best-fit C_l.
- **Statistics**: Dictionary containing variance, p-values, and test statistics.

## Statistical Method
**Primary Test**: Maximum Statistic
- Compute asymmetry A_NS for North/South split.
- Compute asymmetry A_EW for East/West split.
- Test Statistic T = max(A_NS, A_EW).
- Null distribution generated from isotropic simulations.
- P-value = (number of simulations with T_sim ≥ T_obs) / N_sims.

**Note**: The Benjamini-Hochberg procedure is explicitly excluded to maintain strict control over the family-wise error rate in this specific hypothesis testing framework.

## Dependencies
- Python >= 3.9
- healpy
- numpy
- scipy
- astropy
- requests
- pyyaml