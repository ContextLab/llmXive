---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Field**: physics

## Research question

Does solar wind elemental composition (specifically O/Fe and He/H ion ratios) independently predict geomagnetic storm intensity (Dst, Kp indices) beyond what is explained by solar wind velocity and interplanetary magnetic field strength?

## Motivation

Space weather forecasting currently relies primarily on solar wind bulk parameters (velocity, density, magnetic field), but the role of compositional signatures in geomagnetic coupling remains unclear. Understanding whether compositional features provide predictive power could improve storm forecasts and protect satellite infrastructure and power grids from geomagnetic disturbances.

## Literature gap analysis

### What we searched

Queried Semantic Scholar / arXiv / OpenAlex using terms: "solar wind composition geomagnetic", "solar wind ion ratios Dst", "ACE WIND solar wind elemental abundance geomagnetic activity". Retrieved 8 results covering solar wind parameters, geomagnetic indices, and related space weather forecasting literature.

### What is known

- [Wavelet Analysis on Solar Wind Parameters and Geomagnetic Indices (2012)](http://arxiv.org/abs/1205.2229v1) — Establishes frequency-domain relationships between solar wind parameters and geomagnetic indices but does not address elemental composition.
- [Statistical Characteristics of the Heliospheric Plasma and Magnetic Field at the Earth's Orbit during Four Solar Cycles 20-23 (2013)](http://arxiv.org/abs/1301.2929v1) — Provides comprehensive solar wind plasma statistics across solar cycles but focuses on bulk parameters (velocity, density, IMF) rather than ion composition ratios.
- [Dependence of geosynchronous relativistic electron enhancements on geomagnetic parameters (2014)](http://arxiv.org/abs/1402.0735v1) — Links geomagnetic indices (PC, Kp, Dst) to particle fluxes but does not examine solar wind compositional drivers.

### What is NOT known

No published work has systematically tested whether solar wind elemental composition ratios (O/Fe, He/H, C/O) provide independent predictive information for geomagnetic indices beyond bulk plasma parameters. Existing statistical studies focus on velocity, density, and magnetic field strength, leaving compositional coupling mechanisms unquantified.

### Why this gap matters

If compositional signatures improve storm prediction, space weather models could incorporate ACE/WIND composition data from public archives, enabling earlier warnings for satellite operators and power grid managers. Conversely, confirming composition is non-predictive would constrain theoretical models of magnetospheric coupling.

### How this project addresses the gap

This project will download paired ACE/WIND composition datasets and NOAA geomagnetic indices, perform multivariate regression controlling for bulk parameters, and test whether composition ratios add statistically significant explanatory power to Dst/Kp predictions.

## Expected results

We expect to find either (1) composition ratios provide modest but significant independent prediction (ΔR² > 0.05 in cross-validated models), or (2) bulk parameters fully explain variance with composition adding no predictive value. Either outcome constrains magnetospheric coupling theory and informs forecasting pipeline design.

## Methodology sketch

- Download ACE Solar Wind Ion Composition Spectrometer (SWICS) data from CDAWeb (https://cdaweb.gsfc.nasa.gov) for 2000-2020
- Download WIND plasma and composition data from NASA CDAWeb for overlapping period
- Download NOAA Dst and Kp geomagnetic indices from World Data Center (https://www.ngdc.noaa.gov/stp/geomag/indices.html)
- Align time series by resampling all data to 1-hour resolution using nearest-neighbor interpolation
- Compute composition ratios: O/Fe, He/H, C/O from ion flux measurements
- Calculate lagged cross-correlations between composition ratios and geomagnetic indices (0-72 hour lags)
- Fit multivariate linear regression: Dst ~ velocity + density + IMF + composition ratios
- Perform k-fold cross-validation (k=5) to assess out-of-sample predictive gain from composition
- Apply permutation tests to validate statistical significance of composition coefficients
- Generate figures: correlation heatmaps, regression coefficient plots, residual analysis

## Duplicate-check

- Reviewed existing ideas: Wavelet Analysis on Solar Wind Parameters, Statistical Characteristics of Heliospheric Plasma, Relativistic Electron Enhancements on Geomagnetic Parameters.
- Closest match: Wavelet Analysis on Solar Wind Parameters and Geomagnetic Indices (similarity sketch: both analyze solar wind-geomagnetic relationships, but this project uniquely focuses on elemental composition ratios rather than bulk parameters or frequency-domain analysis).
- Verdict: NOT a duplicate
