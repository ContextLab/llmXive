# Frame of Reference: Gravity Anomaly Definition

## Overview

This document defines the frame of reference for gravity anomaly measurements in the context of Atmospheric River (AR) monitoring using GRACE-FO (Gravity Recovery and Climate Experiment Follow-On) satellite data. It explicitly distinguishes between physical gravitational curvature and coordinate-choice artifacts, addressing concerns raised regarding the covariant description of gravitational fields in general relativity.

## Physical Definition

### Gravity Anomaly

In this study, the **gravity anomaly** is defined as the perturbation in the Earth's gravitational potential field caused by the redistribution of mass—specifically, the water vapor and liquid water associated with Atmospheric Rivers.

Mathematically, the gravitational potential $V$ at a point $\mathbf{r}$ is given by:

$$ V(\mathbf{r}) = G \int \frac{\rho(\mathbf{r}')}{|\mathbf{r} - \mathbf{r}'|} d^3\mathbf{r}' $$

where:
- $G$ is the gravitational constant
- $\rho(\mathbf{r}')$ is the mass density distribution
- $\mathbf{r}$ is the observation point (satellite altitude)
- $\mathbf{r}'$ is the source point (mass distribution)

The **anomaly** $\delta V$ is the deviation from a reference potential field $V_{ref}$ (typically a geopotential model like EGM2008):

$$ \delta V(\mathbf{r}) = V(\mathbf{r}) - V_{ref}(\mathbf{r}) $$

### Geoid Height at Satellite Altitude

GRACE-FO measures changes in the inter-satellite distance, which are directly related to variations in the gravitational potential along the satellite orbit. The data products (Level-2 mascon solutions) provide estimates of the **equivalent water height (EWH)**, which represents the height of a water layer that would produce the observed gravitational signal.

The term "geoid height at satellite altitude" refers to the equipotential surface of the Earth's gravity field that coincides with the mean sea level, projected to the satellite's orbital altitude. In practice, GRACE-FO measures the **spherical harmonic coefficients** of the geopotential, which are then converted to spatially resolved mass anomalies.

## Distinguishing Physical Curvature from Coordinate Artifacts

### The Covariant Requirement

As noted in the Einstein-simulated review, the 1915 field equations demand a covariant description. A static "anomaly" can indeed be a coordinate artifact if not properly defined. We address this by:

1. **Physical Basis**: The mass redistribution associated with Atmospheric Rivers is a real, physical phenomenon. The water vapor and precipitation represent a measurable change in the stress-energy tensor $T_{\mu\nu}$, which sources the curvature of spacetime via the Einstein field equations:

 $$ G_{\mu\nu} = \frac{8\pi G}{c^4} T_{\mu\nu} $$

 where $G_{\mu\nu}$ is the Einstein tensor describing spacetime curvature.

2. **Reference Frame**: We adopt the **Earth-Centered, Earth-Fixed (ECEF)** coordinate system, which is standard for geodetic applications. This is a non-inertial frame, but the gravitational potential is well-defined within this frame for the purposes of satellite gravimetry.

3. **Coordinate Independence**: The gravity anomaly is defined as a scalar field (potential difference), which is invariant under coordinate transformations. While the numerical values of the spherical harmonic coefficients depend on the chosen reference frame, the physical quantity (mass anomaly) is frame-independent when properly transformed.

### Coordinate Artifacts

Potential coordinate artifacts that must be accounted for include:

- **Degree-1 Coefficients**: The center of mass of the Earth-satellite system can shift due to mass redistribution, leading to apparent changes in the gravitational field. These are corrected using degree-1 coefficients from external models.
- **C20 Coefficient**: The zonal harmonic $C_{20}$ (related to the Earth's oblateness) is subject to temporal variations that are better measured by satellite laser ranging (SLR) than GRACE. We replace the GRACE-derived $C_{20}$ with SLR values.
- **Temporal Aliasing**: The orbital sampling of GRACE-FO can introduce aliasing of high-frequency signals (e.g., tides) into the monthly solutions. This is mitigated by the preprocessing pipeline (see `02_preprocessing.py`).

## Operational Definition for This Study

For the purposes of this research, the **gravity anomaly** is operationally defined as:

> The equivalent water height (EWH) derived from GRACE-FO Level-2 mascon solutions, after applying degree-1 coefficient corrections, $C_{20}$ replacement, and Gaussian smoothing, aggregated to a monthly resolution for the West Coast North America region (35°N-50°N, 120°W-125°W).

This definition ensures:
- **Physical Relevance**: The signal corresponds to actual mass changes (water storage).
- **Observability**: The quantity is directly measurable by GRACE-FO.
- **Reproducibility**: The processing steps are documented and repeatable.

## Conclusion

The gravity anomaly used in this study is a physically meaningful quantity that reflects the redistribution of mass due to Atmospheric Rivers. While the choice of coordinate system (ECEF) and the method of representation (spherical harmonics, mascons) involve conventions, the underlying physical phenomenon—the curvature of spacetime induced by mass redistribution—is covariant and frame-independent. The preprocessing steps applied to the GRACE-FO data ensure that coordinate artifacts are minimized, leaving a signal that can be meaningfully correlated with Atmospheric River intensity.

## References

- Tapley, B. D., et al. (2004). "GRACE Measurements of Mass Variability in the Earth System." *Science*.
- Swenson, S., & Wahr, J. (2006). "Post-processing removal of correlated errors in GRACE data." *Geophysical Research Letters*.
- Landerer, F. W., & Swenson, S. C. (2012). "Accuracy of Scaled GRACE Terrestrial Water Storage Estimates." *Water Resources Research*.