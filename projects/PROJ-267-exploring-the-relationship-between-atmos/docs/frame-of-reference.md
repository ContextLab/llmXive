# Frame of Reference: Gravity Anomaly Definition

## 1. Overview

This document defines the frame of reference and physical interpretation of the "gravity anomaly" used in this study. It explicitly distinguishes between the physical curvature of the gravitational field caused by mass redistribution (atmospheric rivers) and coordinate-choice artifacts that may arise in satellite gravimetry.

## 2. Definition of Gravity Anomaly

In the context of the GRACE-FO (Gravity Recovery and Climate Experiment Follow-On) mission, the gravity anomaly is defined as the **perturbation in the Earth's gravitational potential** at the altitude of the satellite, relative to a reference ellipsoid (typically GGM05C or a similar high-degree static model).

Mathematically, if $V$ is the total gravitational potential and $V_{ref}$ is the potential of the reference field:
$$ \Delta V(r, \theta, \lambda) = V(r, \theta, \lambda) - V_{ref}(r, \theta, \lambda) $$

The quantity measured and reported as "mascon solutions" or "spherical harmonic coefficients" corresponds to the time-variable part of this potential difference, $\delta V(t)$.

### 2.1 Geoid Height vs. Potential at Satellite Altitude

A critical distinction must be made between:
1. **Geoid Height Anomalies ($\delta N$):** The displacement of the equipotential surface (the geoid) at mean sea level. This is often derived from $\Delta V$ via Bruns' formula: $\delta N = \Delta V / \gamma$, where $\gamma$ is normal gravity.
2. **Potential at Satellite Altitude ($\Delta V_{sat}$):** The direct measurement of the potential perturbation at the altitude of the GRACE-FO satellites (~500 km (Wikipedia: Low Earth orbit, https://en.wikipedia.org/wiki/Low_Earth_orbit)).

**This study utilizes the potential perturbation at satellite altitude ($\Delta V_{sat}$) as the primary observable.** While results are often visualized as equivalent water height (EWH) or geoidheight for interpretability, the physical signal is the perturbation in the gravitational field geometry at the sensor altitude.

## 3. Physical Curvature vs. Coordinate Artifacts

### 3.1 Physical Curvature (General Relativity Context)
Per the Einstein field equations ($G_{\mu\nu} = 8\pi G T_{\mu\nu}$), the redistribution of mass associated with an Atmospheric River (AR) alters the stress-energy tensor $T_{\mu\nu}$. This necessitates a change in the metric tensor $g_{\mu\nu}$, physically bending the geometry of spacetime. The GRACE-FO inter-satellite ranging measurements detect this physical curvature as a change in the gravitational force vector acting on the satellites.

The "anomaly" in this context is a **real, physical change** in the gravitational field strength and direction, not an illusion. It represents the actual redistribution of water mass in the atmosphere and hydrosphere.

### 3.2 Coordinate Artifacts
In satellite gravimetry, "coordinate artifacts" can arise from:
* **Reference Frame Selection:** The choice of the reference ellipsoid (e.g., WGS84 vs. GRS80) or the static gravity model (e.g., EGM2008) defines the "zero" level. A shift in this reference can create an apparent anomaly where none exists physically, or mask a real one if the reference model is inaccurate.
* **Degree-1 and C20 Corrections:** GRACE-FO does not directly measure the degree-1 coefficients (center of mass motion) or the time-variable $C_{20}$ (degree-2, order-0, related to the Earth's dynamic oblateness). These are estimated and added back using external models (e.g., satellite laser ranging). If these corrections are applied in a coordinate system inconsistent with the mascon solution, artifacts may appear.
* **Leakage and Smoothing:** The application of Gaussian smoothing (as performed in `02_preprocessing.py`) is a mathematical operation in the spectral domain. While it reduces noise, it can spread signal from adjacent regions, creating "artificial" anomalies in areas with no mass change. This is a processing artifact, not a physical one, and must be accounted for in the uncertainty budget.

## 4. Operational Definition for this Study

For the purpose of correlation analysis with Atmospheric River data:

1. **Observable:** The time-variable Stokes coefficients ($\Delta C_{nm}, \Delta S_{nm}$) or Mascon solutions derived from GRACE-FO Level 2 data.
2. **Frame:** Earth-Centered, Earth-Fixed (ECEF) rotating frame, corrected for polar motion and UT1-UTC as per IERS conventions.
3. **Anomaly Metric:** The Root Mean Square (RMS) of the equivalent water height (EWH) over the target region (35°N-50°N, 120°W-125°W), derived from the potential perturbation at satellite altitude.
4. **Correction:** All degree-1 coefficients and $C_{20}$ terms are replaced with external estimates to ensure the center of mass and dynamic oblateness are physically consistent with the mascon solution.

## 5. Conclusion

The gravity anomaly analyzed in this project is a **physical manifestation** of mass redistribution, measured as a perturbation in the gravitational potential at satellite altitude. While coordinate choices and processing steps (smoothing, leakage correction) introduce artifacts, the primary signal—the bending of the gravitational field due to atmospheric river mass—is a covariant, physical reality consistent with general relativity. This study explicitly separates the physical signal from these artifacts through rigorous preprocessing and control region validation.