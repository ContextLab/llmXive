# Dynamics Specification for Satellite Laser Ranging (SLR) Analysis

**Project**: Testing the Equivalence Principle with Satellite Laser Ranging (PROJ-752)
**Task**: T023a - Define Dynamics Specification
**Target Implementation**: `code/models/dynamics.py` (T023)
**Date**: 2023-10-27

## 1. Overview

This document defines the exact mathematical formulation and constants for the dynamical model used in the joint least-squares orbit determination (T024) and differential acceleration estimation (T025). The model must be implemented in `code/models/dynamics.py` and must support the following force components:

1. **Geopotential (GGM)**: High-order Earth gravity field.
2. **Atmospheric Drag (Jacchia)**: Neutral atmosphere density and drag force.
3. **Solar Radiation Pressure (SRP)**: Direct and Earth-reflected radiation.
4. **Relativistic Corrections**: Post-Newtonian terms for the solar system.

All accelerations are computed in the **ITRS** (International Terrestrial Reference System) or converted to **GCRS** (Geocentric Celestial Reference System) as required by the integrator, consistent with `astropy.coordinates` usage in the existing codebase.

## 2. Constants and Units

All values are consistent with IERS Conventions (2010) and JPL DE440 ephemerides where applicable.

| Constant | Symbol | Value | Unit | Source |
|:--- |:--- |:--- |:--- |:--- |
| Gravitational Constant | $G$ | $6.67430 \times 10^{-11}$ | m³ kg⁻¹ s⁻² | CODATA 2018 |
| Earth Mass | $M_E$ | $5.97219 \times 10^{24}$ | kg | IERS 2010 |
| Earth GM | $\mu$ | $3.986004418 \times 10^{14}$ | m³ s⁻² | IERS 2010 |
| Equatorial Radius | $R_E$ | $6378136.3$ | m | IERS 2010 |
| Speed of Light | $c$ | $299792458$ | m s⁻¹ | SI Definition |
| Solar Constant | $S_0$ | $1361$ | W m⁻² | IERS 2010 |
| AU | $1 \text{ AU}$ | $1.495978707 \times 10^{11}$ | m | IAU 2012 |
| Solar Mass Parameter | $\mu_S$ | $1.32712440018 \times 10^{20}$ | m³ s⁻² | JPL DE440 |

## 3. Force Models

### 3.1. Geopotential (GGM)

The gravitational acceleration due to the non-spherical Earth is modeled using a spherical harmonic expansion. We utilize the **GGM03C** (or similar high-fidelity GGM) model.

**Equation**:
$$ \mathbf{a}_{geo} = \nabla U(r, \phi, \lambda) $$

Where the potential $U$ is:
$$ U = \frac{\mu}{r} \left[ 1 + \sum_{n=2}^{N_{max}} \sum_{m=0}^{n} \left( \frac{R_E}{r} \right)^n P_{nm}(\sin \phi) \left( C_{nm} \cos(m\lambda) + S_{nm} \sin(m\lambda) \right) \right] $$

**Implementation Details**:
- **Order/Degree**: $N_{max} = 70$ (sufficient for LAGEOS/Etalon precision; higher if computationally feasible).
- **Coefficients**: Loaded from `data/coefficients/ggm03c.txt` (or similar) at runtime.
- **Coordinate System**: Computed in ECI (GCRS) to avoid time-dependent rotation of coefficients, then rotated to ITRS if the state vector is in ITRS.
- **Tesseral/Resonant**: Must include tesseral terms ($m > 0$) to capture day-side/night-side asymmetries.

**Reference**: IERS Conventions (2010), Chapter 6.

### 3.2. Atmospheric Drag (Jacchia-Roberts)

Drag is modeled using the Jacchia-Roberts 1971 empirical atmosphere model for neutral density, modified for high-altitude satellites (LAGEOS/Etalon).

**Equation**:
$$ \mathbf{a}_{drag} = -\frac{1}{2} \frac{C_D A}{m} \rho(h) v_{rel} \mathbf{v}_{rel} $$

**Components**:
- **$C_D$**: Drag coefficient (typically $2.2$ for LAGEOS).
- **$A/m$**: Area-to-mass ratio (m²/kg).
- **$\rho(h)$**: Atmospheric density at altitude $h$.
- **$v_{rel}$**: Relative velocity magnitude with respect to the rotating atmosphere.
- **$\mathbf{v}_{rel}$**: Relative velocity vector.

**Atmosphere Model**:
- **Jacchia 71**: Density is a function of altitude, solar flux ($F_{10.7}$), and geomagnetic index ($K_p$).
- **Inputs**: Solar flux and $K_p$ indices must be fetched from `data/raw/solar_indices.csv` or interpolated from standard tables.
- **Exosphere Temperature**: $T_\infty$ is calculated based on $F_{10.7}$.

**Implementation Note**: For LAGEOS (altitude ~5900 km), density is negligible, but for Starlette/Etalon (lower altitudes), this is critical. The model must gracefully handle $h > 1000$ km where density $\approx 0$.

**Reference**: Jacchia, L. G. (1971). "Slowly varying model thermospheric temperatures".

### 3.3. Solar Radiation Pressure (SRP)

SRP is the dominant non-gravitational perturbation for high-area-to-mass ratio satellites.

**Equation**:
$$ \mathbf{a}_{SRP} = -\nu \frac{S_0}{c} \frac{A}{m} C_R \left( \frac{1 \text{ AU}}{r_{Sun}} \right)^2 \hat{\mathbf{r}}_{Sun} $$

**Components**:
- **$\nu$**: Shadow function (1 if in sunlight, 0 if in Earth's shadow, partial if in penumbra).
- **$C_R$**: Radiation pressure coefficient (typically $1.1$ to $1.3$ for spherical satellites with retroreflectors).
- **$\hat{\mathbf{r}}_{Sun}$**: Unit vector from satellite to Sun.
- **$r_{Sun}$**: Distance from Earth to Sun.

**Shadow Function**:
- Implement cylindrical shadow model (umbra/penumbra) based on Earth's radius and Sun's angular size.
- $\nu = 0$ in umbra, $\nu \in (0, 1)$ in penumbra, $\nu = 1$ in sunlight.

**Implementation Note**: Must use `astropy.coordinates` to compute the Sun's position in GCRS/ITRS at the observation epoch.

**Reference**: Montenbruck, O., & Gill, E. (2000). "Satellite Orbits".

### 3.4. Relativistic Corrections

Post-Newtonian corrections are required for millimeter-level precision.

**Equation (Einstein-Infeld-Hoffmann)**:
$$ \mathbf{a}_{rel} = \mathbf{a}_{EIH} + \mathbf{a}_{LenseThirring} + \mathbf{a}_{deSitter} $$

**Simplified Form for Earth Satellites**:
The dominant term is the Schwarzschild correction (Einstein):
$$ \mathbf{a}_{Sch} = \frac{\mu}{c^2 r^3} \left[ \left( 4 \frac{\mu}{r} - v^2 \right) \mathbf{r} + 4 (\mathbf{r} \cdot \mathbf{v}) \mathbf{v} \right] $$

**Lense-Thirring (Frame Dragging)**:
$$ \mathbf{a}_{LT} = \frac{2G}{c^2 r^3} \left[ \frac{3(\mathbf{r} \cdot \mathbf{J})}{r^2} \mathbf{v} - \mathbf{J} \times \mathbf{v} \right] $$
Where $\mathbf{J}$ is Earth's angular momentum vector.

**deSitter (Geodetic Precession)**:
Usually negligible for orbit determination compared to Schwarzschild, but included in full EIH.

**Implementation Note**: Use `astropy` constants for $G$ and $c$. Ensure vectors are in an inertial frame (GCRS).

**Reference**: IERS Conventions (2010), Chapter 10.

## 4. Integration and State Vector

- **State Vector**: $\mathbf{x} = [\mathbf{r}, \mathbf{v}]^T$ (Position and Velocity).
- **Coordinates**: The integrator operates in **GCRS** (Geocentric Celestial Reference System).
- **Transformation**: Input `OrbitSolution.state` (from T007a) must be converted from ITRS to GCRS before dynamics evaluation.
- **Integrator**: The `JointLeastSquaresSolver` (T024) will use a numerical integrator (e.g., `scipy.integrate.solve_ivp` with 'DOP853') to propagate the state.

## 5. Parameterization for T024 (Joint Fit)

The dynamics model in T023 will be wrapped by the estimator in T024. The following parameters are adjustable:

- **$C_R$ (SRP Coefficient)**: Tied to specific satellites.
- **$C_D$ (Drag Coefficient)**: Tied to specific satellites.
- **$a_c$ (Differential Acceleration)**: A constant or piecewise-constant bias term added to the acceleration vector to test the Equivalence Principle.
 - **Form**: $\mathbf{a}_{total} = \mathbf{a}_{gravity} + \mathbf{a}_{drag} + \mathbf{a}_{SRP} + \mathbf{a}_{rel} + \eta \cdot g \cdot \hat{\mathbf{r}}_{Sun}$ (or similar direction depending on the specific EP violation model).
 - **Implementation**: In T023, this term must be optional and injectable via the `model_params` dictionary.

## 6. Verification Criteria

The implementation in `code/models/dynamics.py` must pass the following checks (T020):

1. **Conservation**: For a purely Keplerian orbit (all perturbations off), energy should be conserved to within $10^{-9}$ relative error over 1 orbit.
2. **SRP Shadow**: The acceleration must drop to zero when the satellite enters Earth's shadow.
3. **Relativity**: The magnitude of $\mathbf{a}_{Sch}$ at LAGEOS altitude must be $\approx 10^{-9}$ m/s².
4. **GGM**: The acceleration must match a reference propagator (e.g., Orekit) within $10^{-6}$ m/s² for a test epoch.

## 7. Dependencies

- `astropy` (for coordinate transformations and ephemerides).
- `numpy` (for vector operations).
- `scipy` (for integration).
- `data/coefficients/ggm03c.txt` (for GGM coefficients).
- `data/raw/solar_indices.csv` (for Jacchia drag inputs).

## 8. References

1. IERS Conventions (2010), Petit, G. & Luzum, B. (eds.), 2010.
2. JPL Development Ephemeris DE440.
3. Montenbruck, O., & Gill, E. (2000). *Satellite Orbits: Models, Methods, and Applications*. Springer.
4. Jacchia, L. G. (1971). *Slowly varying model thermospheric temperatures*. Smithsonian Astrophysical Observatory Special Report 332.
5. GGM03C Gravity Model: http://earth-info.nga.mil/GandG/wgs84/gravitymod/

---
**Status**: Approved for Implementation (T023).
**Gate**: This document must be referenced in the code comments of `code/models/dynamics.py`.