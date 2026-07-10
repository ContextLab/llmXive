# Project Plan: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Summary

This project implements a rigorous statistical test for the isotropy of cosmic expansion using the Pantheon+ Type Ia Supernova dataset. [UNRESOLVED-CLAIM: c_2015e899 — status=not_enough_info] The core methodology involves calculating the residuals between observed distance moduli and theoretical predictions derived from a **flat ΛCDM model** via numerical integration. These residuals are then projected onto a HEALPix grid (Nside=32) to extract dipole and quadrupole amplitudes using the pseudo-C_l method with MASTER correction. Finally, a null distribution is generated via 10,000 isotropic rotation simulations to assess the statistical significance of any observed anisotropy.

## Objectives

1. Ingest and process the Pantheon+ v1.0 dataset, applying strict quality cuts.
2. Calculate theoretical distance moduli using a flat ΛCDM model (numerical integration of the Hubble parameter).
3. Map residuals to the celestial sphere and decompose them into spherical harmonics (dipole and quadrupole).
4. Generate a null distribution of anisotropy amplitudes via random coordinate rotations.
5. Determine the statistical significance of the observed anisotropy compared to the null hypothesis.

## Technical Context

### Data Source
- **Dataset**: Pantheon+ Type Ia Supernova Compilation (v1.0).
- **Access**: Downloaded programmatically from the official Pantheon+ repository (GitHub/DOI) with checksum verification.
- **Format**: CSV containing ID, RA, Dec, redshift (z), observed distance modulus (μ_obs), and uncertainties.
- **Metadata**: Cosmological parameters (H0, Ω_m) are extracted from the dataset's accompanying JSON metadata or the release paper if not present.

### Methodology
1. **Residual Calculation**:
 - Theoretical distance modulus (μ_th) is computed by numerically integrating the inverse Hubble parameter $1/E(z)$ for a flat ΛCDM model.
 - **Model**: Flat ΛCDM (Ω_k = 0).
 - **Integration**: `scipy.integrate.quad` with `rtol=1e-8`.
 - **Residual**: $\delta\mu = \mu_{obs} - \mu_{th}$.
2. **Sky Projection**:
 - Residuals are mapped to HEALPix pixels (Nside=32).
 - Pixels are binned to calculate mean residuals per pixel.
3. **Anisotropy Extraction**:
 - **Method**: Pseudo-C_l approach with MASTER correction to account for the survey mask.
 - **Target**: Dipole ($\ell=1$) and Quadrupole ($\ell=2$) amplitudes.
4. **Significance Testing**:
 - **Null Hypothesis**: Isotropic expansion (residuals are random noise).
 - **Simulation**: 10,000 iterations of random 3D rotations applied to the supernova coordinates.
 - **Metric**: Comparison of observed dipole/quadrupole amplitudes against the null distribution to derive p-values.

### Software Stack
- **Language**: Python 3.11+
- **Key Libraries**:
 - `astropy`: Coordinate transformations and cosmology utilities.
 - `healpy`: HEALPix pixelization and spherical harmonic transforms.
 - `scipy`: Numerical integration (`quad`) and statistical functions.
 - `pandas`: Data manipulation and I/O.
 - `numpy`: Numerical operations.
- **Testing**: `pytest` with contract, integration, and unit tests.

### File Structure
- `data/raw/`: Original Pantheon+ downloads.
- `data/processed/`: Cleaned residuals, HEALPix maps, simulation results.
- `code/`: Core logic (ingest, spherical_harmonics, simulations, utils).
- `reports/`: Final analysis report and sky maps.

## Constraints & Assumptions

- **Redshift Range**: No arbitrary redshift cuts are applied beyond those required for numerical stability or missing data; filtering is limited to entries with missing RA, Dec, or redshift.
- **Systematics**: Systematic errors (extinction, selection bias) are quantified and logged for transparency but are **NOT** applied to the null distribution generation to preserve the strict isotropic definition of the mock catalogs.
- **Reproducibility**: All random seeds are controlled via environment variables; checksums are verified for all external data.

## Risk Mitigation

- **Data Availability**: If the official Pantheon+ repository is inaccessible, the pipeline will fail loudly with a clear error message rather than using synthetic data.
- **Numerical Stability**: Integration tolerances are set strictly (`rtol=1e-8`) to ensure accurate theoretical predictions.
- **Statistical Power**: The simulation count (N=10,000) is chosen to ensure p-value precision to at least 1e-4.