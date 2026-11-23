# Specification: Assessing the Validity of the Cosmological Principle with Public CMB Data

## 1. Introduction

This project aims to test the Cosmological Principle (CP) – the assumption that the universe is homogeneous and isotropic on large scales – using public Cosmic Microwave Background (CMB) data from the Planck satellite. We specifically investigate hemispherical power asymmetries using a rigorous statistical framework.

## 2. Objectives

- Download and preprocess Planck 2018 SMICA CMB maps.
- Compute angular power spectra (C_l) for the full sky and hemispherical splits.
- Generate Monte Carlo simulations based on the isotropic ΛCDM model.
- Perform statistical hypothesis testing using the Maximum Statistic approach.

## 3. Data Sources

- **Planck 2018 SMICA Map**: Nside=2048, from the ESA Planck Legacy Archive.
- **Galactic Mask**: Commander mask (R2.0) to exclude foregrounds.
- **Reference Power Spectrum**: Planck 2018 best-fit ΛCDM spectrum for simulations.

## 4. Methodology

### 4.1 Data Preprocessing
1. Download SMICA map (Nside=2048).
2. Validate checksum (SHA-256).
3. Apply Galactic mask (retaining ≥95% of the sky).
4. Downgrade to Nside=128 for computational efficiency.

### 4.2 Harmonic Analysis
1. Compute spherical harmonic coefficients (a_lm) using `healpy.map2alm`.
2. Derive full-sky angular power spectrum (C_l).
3. Split sky into North/South and East/West hemispheres.
4. Compute pseudo-C_l for each hemisphere using the MASTER algorithm.

### 4.3 Statistical Testing
1. Generate 1000 isotropic Gaussian simulations using the best-fit C_l.
2. Compute hemispherical variance asymmetry for each simulation.
3. Calculate observed asymmetry from real data.
4. **Apply Maximum Statistic approach**: Use the maximum of N/S and E/W asymmetries as the test statistic to control family-wise error rate.
5. Derive p-values by comparing observed max statistic against the null distribution.

## 5. Success Criteria

- **SC-001**: Successfully download and validate Planck SMICA map with correct checksum.
- **SC-002**: **Maximum Statistic approach applied** to hemispherical asymmetry analysis to ensure robust multiple comparison correction.
- **SC-003**: Generate 1000+ Monte Carlo simulations within 2 hours on CPU-only infrastructure.
- **SC-004**: Compute p-values for observed asymmetry with proper error control.
- **SC-005**: Document all steps for reproducibility, including code versions and data provenance.

## 6. Deliverables

- **code/data_loader.py**: Data ingestion and preprocessing pipeline.
- **code/harmonics.py**: Spherical harmonic decomposition and power spectrum calculation.
- **code/simulations.py**: Monte Carlo simulation generation.
- **code/statistics.py**: Statistical analysis and p-value computation.
- **data/processed/mask_stats.json**: Mask application statistics.
- **data/reports/power_validation.json**: Power validation report.
- **data/reports/results.json**: Final statistical results including p-values.

## 7. Assumptions & Constraints

- **Computational**: Must run on CPU-only CI (limited RAM, no GPU).
- **Data**: Only real Planck data; no synthetic input data.
- **Statistical**: Maximum Statistic approach used instead of Benjamini-Hochberg for better control of false positives in directional tests.

## 8. Version History

- **v1.0**: Initial specification draft.
- **v1.1**: Updated SC-002 to reflect Maximum Statistic approach (replacing Benjamini-Hochberg).
- **v1.2**: Aligned FR-009 with Maximum Statistic approach.