# Research: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

## Executive Summary

This research plan investigates the validity of the Strong Equivalence Principle (SEP) by analyzing the orbital dynamics of the Earth-Moon system and inner planets. The core hypothesis is that if the SEP is violated, the gravitational binding energy fraction ($\Omega$) of a body will correlate with its orbital polarization (Nordtvedt effect). We will test this by fitting the Nordtvedt parameter ($\eta$) to Lunar Laser Ranging (LLR) data and planetary range data. The study relies on publicly available data from JPL Horizons and INPOP19a, ensuring full reproducibility on a CPU-only CI environment. The methodology has been revised to use a **Differential Ephemeris Analysis** (JPL vs. INPOP) and to focus on the **time-dependent polarization signal** of the Earth-Moon orbit, avoiding circular validation.

## Dataset Strategy

### Verified Datasets

The following datasets have been verified for programmatic access and format suitability. No access-gated or registration-only data is used.

| Dataset Name | Description | Verified Source / Loader | Relevance to FR/SC |
| :--- | :--- | :--- | :--- |
| **JPL Horizons** | High-precision planetary ephemerides (position, velocity, range, range-rate) for Mercury, Venus, Earth, Mars, and Moon covering the historical and contemporary observational record. | `astroquery.jplhorizons.Horizons` (Python library) | **FR-001**, **FR-003**, **SC-001**. Primary input for trajectory and residuals. |
| **INPOP19a** | Alternative planetary ephemeris from IMCCE, used for cross-validation. | `astroquery.imcce.Inpop` or direct file download from IMCCE FTP | **FR-006**, **SC-003**. Validates that residuals are not JPL modeling artifacts. |
| **NASA Planetary Fact Sheets** | Mass, radius, and interior structure parameters to calculate $\Omega$. | Direct download from `nssdc.gsfc.nasa.gov/planetary/` | **FR-004**, **Edge Cases**. Required for the independent variable in regression. |
| **Peer-Reviewed Interior Models** | High-fidelity interior density profiles for $\Omega$ calculation (e.g., Seager et al., 2007). | Cited in `research.md` (no direct download, values hardcoded from literature). | **FR-004**. Replaces bulk property approximation to reduce systematic error. |
| **Rebound Library** | N-body integrator code (not a dataset, but critical tool). | `pip install rebound` | **FR-002**, **SC-001**. Generates the GR baseline trajectory. |

### Data Acquisition Plan

1.  **JPL Horizons**:
    *   **Method**: Use `astroquery.jplhorizons.Horizons` with `id='Moon'`, `id='Mercury'`, etc.
    *   **Parameters**: `eph_type='range,range-rate'`, `start='1950-01-01'`, `stop='2025-12-31'`, `step='1d'`.
    *   **Handling Gaps**: If the API returns gaps (Edge Case 1), the pipeline will interpolate linearly for range/range-rate if the gap is < 3 days; otherwise, the epoch is dropped, and a warning is logged.
    *   **Feasibility**: `astroquery` handles rate limiting automatically. Data volume is ~5 bodies * multiple rows * 10 columns, well within RAM limits.

2.  **INPOP19a**:
    *   **Method**: Attempt `astroquery.imcce` first. If the module is deprecated or fails, fall back to downloading the `INPOP19a` binary or text file from the IMCCE FTP server (`ftp://ftp.imcce.fr/pub/ephem/planetes/INPOP/`).
    *   **Feasibility**: INPOP data files are < 100 MB.

3.  **Binding Energy Data**:
    *   **Method**: Use peer-reviewed interior structure models (e.g., Seager et al., 2007) for Earth, Mars, Venus, and Mercury to calculate $\Omega$.
    *   **Calculation**: $\Omega \approx -GM/Rc^2$ with interior corrections.
    *   **Fallback**: If a planet's data is missing (Edge Case 2), the system retries 3 times. If still missing, the planet is excluded from the regression, and the log records `E-DATA-MISSING-BE`. **Minimum Sample Size**: The pipeline halts if fewer than 3 planets have valid $\Omega$ data (FR-008).

## Methodology & Statistical Rigor

### 1. GR Baseline Construction & Differential Validation (FR-002, FR-006)

*   **Integrator**: `rebound` library with `IAS15` integrator (Amended Constitution Principle VII).
*   **Physics**:
    *   Newtonian N-body forces for Sun + 4 planets + Moon.
    *   **GR Correction**: Schwarzschild term (post-Newtonian correction) added to the acceleration.
    *   **Excluded**: Lense-Thirring (frame-dragging) is excluded as per spec (below noise floor).
*   **Code Validation (SC-001)**:
    *   The integrator will be run on a multi-decade subset.
    *   **Metric**: Calculate the secular precession of Mercury's perihelion.
    *   **Target**: Must match the theoretical GR value (~43 arcseconds/century) within ±0.1 arcseconds/century.
    *   **Note**: This validates the *code*, not the physics.
*   **Physics Validation (Differential Analysis)**:
    *   **Method**: Compute `diff = JPL - INPOP`.
    *   **Rationale**: Both ephemerides incorporate GR. Differences isolate the Nordtvedt signal.
    *   **Tolerance**: The RMS of `diff` must be within the documented inter-ephemeris uncertainty bounds (approx. 1 km) to ensure the signal is not an artifact of a single ephemeris model (FR-006). **Action**: If RMS > 1 km, pipeline halts.

### 2. Parameter Estimation (FR-003, FR-004)

*   **Primary Fit (Differential Nordtvedt Analysis)**:
    *   **Data**: Earth-Moon range data (LLR) and planetary range data.
    *   **Method**: Fit the time-dependent polarization term of the Earth-Moon orbit (the Nordtvedt effect) directly to the differential residuals (JPL - INPOP).
    *   **Model**: `diff_range = eta * polarization_term(t) + noise`.
    *   **Focus**: The Earth-Moon system is the primary observable for $\eta$ due to its high sensitivity. Planetary data is used as a secondary consistency check.
    *   **Output**: Fitted parameters, covariance matrix, reduced $\chi^2$.
*   **Secondary Regression (Consistency Check)**:
    *   **Dependent Variable**: Amplitude of the differential residual signal (polarization term) for each planet.
    *   **Independent Variables**: Gravitational binding energy fraction ($\Omega$), $\log(Mass)$, $\log(a)$.
    *   **Model**: `amplitude ~ \beta_0 + \beta_1 \Omega + \beta_2 \log(M) + \beta_3 \log(a) + \epsilon`.
    *   **Error Handling**: Use Heteroscedasticity-Consistent (HC3) standard errors.
    *   **Collinearity Check**: $\Omega$ is derived from $M$ and $R$. While not definitionally identical, they are correlated. The model includes $\log(M)$ to control for mass, but we will report the Variance Inflation Factor (VIF) to assess multicollinearity.
    *   **Limitations**: Explicitly acknowledge that results are upper bounds due to unmodeled forces (asteroids, solar $J_2$).

### 3. Monte Carlo Simulation (FR-005, SC-002)

*   **Purpose**: Generate a null distribution for $\eta$ and $\omega_{BD}$ to determine statistical significance.
*   **Procedure**:
    1.  Resample initial state vectors and observational noise (Gaussian) based on uncertainties.
    2.  Re-run the **full differential ephemeris comparison** (or the simplified dynamical fit for the Nordtvedt term) in every iteration.
    3.  Collect the distribution of $\eta$.
*   **Convergence**: Monitor the standard error of the mean of the null distribution. If it does not stabilize after a predetermined number of iterations, the count will be doubled (up to a maximum threshold) or the process will fail gracefully (Edge Case 3).
*   **Significance**: Calculate p-value = (count of $|\eta_{null}| > |\eta_{obs}|$) / Total Iterations.
*   **Upper Bound (FR-007)**: If $p > 0.05$, calculate the 95% confidence upper bound on $\omega_{BD}$ derived from the null distribution width.

### 4. Computational Feasibility (CPU-First)

*   **Integration**: `rebound` IAS15 is CPU-efficient. 75 years of 5-body dynamics with 1-day output is computationally trivial (< 5 minutes).
*   **Fitting**: Non-linear least squares on ~1M LLR points (sampled) is fast (< 10 minutes).
*   **Monte Carlo**: 10,000 iterations of the full fit on a sampled dataset (10k points) is feasible within 6 hours.
*   **Memory**: All data fits in < 4 GB RAM.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **JPL API Rate Limiting** | High (Pipeline stall) | Implement exponential backoff in `astroquery` calls. Cache results locally with checksums. |
| **INPOP Data Unavailable** | Medium (No cross-validation) | Fallback to direct FTP download. If both fail, proceed with JPL-only analysis but flag as "Unvalidated" in the final report. |
| **Numerical Drift** | High (False positive) | Use `rebound`'s built-in energy error monitoring. If drift > tolerance, reduce time step. |
| **Missing Binding Energy** | Medium (Reduced sample) | Exclude planet from regression, log warning. **Minimum Sample Size**: Pipeline halts if < 3 planets have valid $\Omega$ (FR-008). Error Code: E-SAMPLE-INSUFFICIENT. |
| **MC Non-Convergence** | Low (Inaccurate p-value) | Increase iteration count or reduce problem complexity. Report "Convergence not achieved" if limits hit. |
| **Unmodeled Forces** | High (Degeneracy) | Explicitly acknowledge that results are upper bounds due to unmodeled asteroid/solar $J_2$ effects. |

## References

1.  **JPL Horizons**: NASA JPL Solar System Dynamics. `https://ssd.jpl.nasa.gov/horizons/`
2.  **INPOP19a**: IMCCE. `https://www.imcce.fr/inpop/`
3.  **Rebound Library**: `https://github.com/hannorein/rebound`
4.  **PPN Formalism**: Willard, C. M., et al. "Post-Newtonian parameters." *Living Reviews in Relativity*.
5.  **Nordtvedt Effect**: Nordtvedt, K. (1968). "Equivalence Principle for Massive Bodies." *Physical Review*.
6.  **LLR Constraints**: Williams, J. G., et al. "Lunar Laser Ranging Tests of the Equivalence Principle." *Physical Review Letters*.
7.  **Interior Models**: Seager, S., et al. (2007). "Mass-Radius Relations for Solid Exoplanets." *Astrophysical Journal*.
