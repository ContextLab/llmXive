# Spec: Assessing the Validity of the Cosmological Principle with Public CMB Data

## Overview
This project assesses the validity of the Cosmological Principle (CP) by testing for statistical isotropy in Cosmic Microwave Background (CMB) data using the Planck 2018 SMICA map. The analysis focuses on hemispherical power asymmetry and dipole modulation.

## User Stories

### US-1: Acquire and Preprocess Planck CMB Data
**Goal**: Download, validate, mask, and downgrade the Planck SMICA CMB map to Nside=128 for efficient analysis.

**Acceptance Criteria**:
1. The Planck SMICA Nside=2048 map is downloaded from the ESA archive and validated via SHA-256 checksum.
2. A Commander-based galactic mask is applied, retaining ≥95% of the unmasked sky while excluding foregrounds.
3. The map is downgraded to Nside=128 with no NaN/inf values and memory usage <100MB.
4. Preprocessed data is saved to `data/processed/planck_nside128.fits`.

**Acceptance Scenario 1**:
- Given the Planck 2018 SMICA map URL, when `download_planck_map()` is executed, then the file is saved to `data/raw/` and the checksum matches the official release.

**Acceptance Scenario 2**:
- Given the raw map, when `apply_galactic_mask()` is executed, then `data/processed/mask_stats.json` contains `sky_fraction` ≥ 0.95 and the masked map is written to `data/processed/planck_masked.fits`.

**Acceptance Scenario 3**:
- Given the masked map, when `downgrade_resolution()` is executed, then the output map at Nside=128 is saved to `data/processed/planck_nside128.fits` with no NaN values.

---

### US-2: Compute Spherical Harmonic Decomposition and Angular Power Spectrum
**Goal**: Compute a_lm coefficients and C_l spectra for full sky and hemispherical splits using the MASTER algorithm.

**Acceptance Criteria**:
1. `compute_alm()` returns a_lm for l ∈ [2, 128] using `map2alm` with `iter=3`.
2. `compute_full_sky_cl()` derives C_l from a_lm correctly.
3. `split_hemispheres()` generates North/South and East/West pixel masks.
4. `compute_hemisphere_cl()` uses the MASTER pseudo-C_l estimator to correct for mode coupling.
5. Results are saved to `data/processed/cl_spectra.json`.

**Acceptance Scenario 1**:
- Given the Nside=128 map, when `compute_alm()` is run, then a_lm coefficients are computed for l=2 to 128.

**Acceptance Scenario 2**:
- Given a_lm, when `compute_full_sky_cl()` is run, then C_l values are positive and saved to `data/processed/cl_spectra.json`.

**Acceptance Scenario 3**:
- Given the map, when `split_hemispheres()` and `compute_hemisphere_cl()` are run, then hemispherical power spectra for N/S and E/W are generated and stored.

---

### US-3: Generate Monte Carlo Null Distribution and Perform Statistical Test
**Goal**: Generate isotropic Gaussian simulations, compute hemispherical variance, and derive p-values using the Maximum Statistic approach.

**Acceptance Criteria**:
1. `generate_isotropic_sims()` creates N simulations using the Planck 2018 best-fit ΛCDM spectrum.
2. `compute_hemispherical_variance()` calculates variance asymmetry for observed and simulated maps.
3. `build_null_distribution()` aggregates variance stats from simulations.
4. `calculate_max_stat_pvalue()` computes the p-value using the maximum of N/S and E/W asymmetries.
5. Power validation report is generated at `data/reports/power_validation.json` with detection rate ≥80%.

**Acceptance Scenario 1**:
- Given the best-fit C_l, when `generate_isotropic_sims()` is run, then N Gaussian maps are saved to `data/simulations/`.

**Acceptance Scenario 2**:
- Given observed and simulated maps, when `compute_hemispherical_variance()` is run, then variance statistics are computed for each hemisphere.

**Acceptance Scenario 3**:
- Given the null distribution, when `calculate_max_stat_pvalue()` is run, then the p-value is derived using the Maximum Statistic approach (max of N/S and E/W asymmetries) and saved to `data/reports/pvalues.json`.

**Acceptance Scenario 4**:
- When `generate_power_validation_report()` is run, then `data/reports/power_validation.json` is created with `detection_rate` ≥ 0.80 for injected anisotropy.

---

### US-4: Document Reproducibility and Sensitivity Analysis
**Goal**: Document code versions, perform threshold sensitivity sweep, and report adjusted p-values.

**Acceptance Criteria**:
1. `run_sensitivity_sweep()` tests thresholds across {2.5σ, 3.0σ, 3.5σ}.
2. `requirements.txt` includes pinned versions of all dependencies.
3. `README.md` documents installation, usage, and data provenance.
4. Main report includes uncorrected and Maximum Statistic p-values.

**Acceptance Scenario 1**:
- When `run_sensitivity_sweep()` is executed, then `data/reports/sensitivity_sweep.json` contains rejection rates for each threshold.

**Acceptance Scenario 2**:
- When `main.py` is executed, then the final report includes both uncorrected and Maximum Statistic p-values.

**Acceptance Scenario 3**:
- Given the analysis results, when the final report is generated, then it explicitly states the p-value derived from the Maximum Statistic approach (max of N/S and E/W asymmetries) rather than Benjamini-Hochberg correction.

---

## Data Model

### Entities
- **CMBMap**: FITS file containing temperature anisotropies.
- **Mask**: Binary HEALPix map defining sky coverage.
- **PowerSpectrum**: Dictionary of l and C_l values.
- **Simulation**: Generated isotropic Gaussian map.
- **StatResult**: Dictionary containing p-values, test statistics, and method details.

## Contracts

### Input/Output Paths
- Raw Data: `data/raw/planck_smica_nside2048.fits`
- Processed Data: `data/processed/planck_nside128.fits`
- Simulations: `data/simulations/`
- Reports: `data/reports/`

### API Surface
- `code/data_loader.py`: `download_planck_map`, `apply_galactic_mask`, `downgrade_resolution`
- `code/harmonics.py`: `compute_alm`, `compute_full_sky_cl`, `split_hemispheres`, `compute_hemisphere_cl`
- `code/simulations.py`: `generate_isotropic_sims`
- `code/statistics.py`: `compute_hemispherical_variance`, `build_null_distribution`, `calculate_max_stat_pvalue`, `generate_power_validation_report`
- `code/sensitivity.py`: `run_sensitivity_sweep`
- `code/main.py`: Pipeline orchestrator

## Notes
- All statistical tests use the Maximum Statistic approach to control family-wise error rate.
- Benjamini-Hochberg correction is explicitly NOT used, as per Plan alignment.
- CPU-only execution is required for CI compatibility.