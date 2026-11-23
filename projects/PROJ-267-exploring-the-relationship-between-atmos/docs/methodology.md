# Methodology: Atmospheric River Gravity Correlation

## 1. Introduction
This document outlines the methodology for investigating the relationship between Atmospheric River (AR) intensity and gravitational field anomalies in the West Coast of North America. The study utilizes data from the GRACE-FO (Gravity Recovery and Climate Experiment Follow-On) mission and the NOAA CPC Atmospheric River Catalog.

## 2. Data Sources
- **GRACE-FO**: Level-2 Mascon Solutions (RL06) obtained from the PO.DAAC CMR search API.
- **NOAA**: Atmospheric River Catalog obtained from the NOAA ERDDAP tabledap endpoint.

## 3. Data Preprocessing
- **GRACE-FO**: Application of degree-1 coefficient corrections, C20 replacement, and Gaussian smoothing. Monthly aggregation is performed to align with AR event timelines.
- **NOAA**: Monthly aggregation of Integrated Water Vapor Transport (IWVT). Months with zero AR events are excluded from correlation calculations to prevent bias.
- **Merging**: Data is merged on a monthly basis for the region 35°N-50°N, 120°W-125°W.

## 4. Statistical Analysis
- **Correlation**: Pearson correlation coefficient is computed between AR intensity and gravity anomalies.
- **Lag Analysis**: Correlation is analyzed across lag windows of 0, 1, 2, and 3 months.
- **Autocorrelation Correction**: AR(1) pre-whitening and Newey-West standard errors are applied to control for temporal autocorrelation.
- **Bootstrap Resampling**: 1000 iterations with seed=42 are used to generate 95% confidence intervals.
- **Multiple Comparison Correction**: False Discovery Rate (FDR) correction is applied to p-values.
- **Signal-to-Noise**: Calculated as the correlation coefficient divided by the uncertainty of the gravity anomaly.

## 5. Frame of Reference and Coordinate System
The measurement of gravitational anomalies by GRACE-FO relies on tracking inter-satellite distance variations, which are subsequently converted into spherical harmonic coefficients representing the Earth's gravitational potential.

In this analysis, we utilize the **"geoid height at satellite altitude"** as the primary proxy for mass redistribution. It is critical to explicitly distinguish this quantity from the standard definition of the **geoid**, which is the equipotential surface of the Earth's gravity field that best fits mean sea level. The GRACE-FO observations are made at Low Earth Orbit (LEO) altitudes (approximately 500 km). Therefore, the "anomaly" derived from these measurements represents the perturbation in the gravitational potential at that specific orbital altitude, not the geoid height at the Earth's surface.

This distinction is rooted in the principles of General Relativity. As noted in the 1915 field equations, the gravitational potential is a covariant quantity. A "static" anomaly observed over a monthly integration period is, in a dynamic field, a coordinate-dependent artifact resulting from the integration of orbital perturbations. However, for the purposes of this study, we assume a static, non-rotating frame for the duration of the monthly aggregation. This approximation allows us to treat the monthly averaged spherical harmonic coefficients as a scalar potential anomaly within the satellite's reference frame.

By anchoring our analysis to the potential at satellite altitude, we ensure that the "gravity anomaly" metric is physically consistent with the measurement geometry of the GRACE-FO mission, avoiding the coordinate artifacts that would arise from projecting surface geoid definitions directly onto the orbital data without proper potential transformation.

## 6. Limitations and Sensitivity
- **Temporal Resolution**: Monthly resolution is chosen to match the averaging period of GRACE-FO data, though this may obscure sub-monthly dynamics.
- **Spatial Resolution**: Gaussian smoothing is applied, which limits the spatial resolution of the detected anomalies.
- **Causal Inference**: This study establishes associational relationships. Causal language is avoided in reporting; correlation does not imply causation.

## 7. Validation
- **Control Region**: A control region outside the primary study domain is used to validate that observed correlations are not due to global noise or systematic errors.
- **Sensitivity Analysis**: Threshold sweeps are performed to assess the stability of correlation coefficients and confidence intervals.