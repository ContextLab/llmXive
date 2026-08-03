# Feature Specification: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Feature Branch**: `001-exploring-wep-validity`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and GR Baseline Construction (Priority: P1)

As a researcher, I want to download high-precision positional and raw tracking data (range/range-rate) for Mercury, Venus, Earth, and Mars from the JPL Horizons system and generate a General Relativity (GR) predicted trajectory using a numerical integrator compliant with the project Constitution (`scipy.integrate.odeint` with LSODA), so that I have a validated baseline to compare against observed ephemerides.

**Why this priority**: This is the foundational step; without accurate data ingestion and a correct GR reference model using a scientifically valid integrator, no residual analysis or hypothesis testing can occur. It establishes the "truth" against which deviations are measured.

**Independent Test**: The system can be tested by running the data acquisition and integration pipeline on a subset of dates (e.g., a historical interval) and verifying that the generated GR trajectory matches the expected precession rates for Mercury within the known numerical tolerance of the `scipy.integrate.odeint` integrator (e.g., relative energy error within a negligible tolerance of 1e-10).

**Acceptance Scenarios**:

1. **Given** the JPL Horizons API is accessible, **When** the system requests positional and tracking data for Mercury, Venus, Earth, and Mars for the interval mid-20th century–2025 with a Short-interval sampling rate, **Then** the system successfully downloads and parses the data into a structured time-series format without data loss.
2. **Given** the parsed observational data and planetary parameters (mass, semi-major axis), **When** the numerical integrator runs using `scipy.integrate.odeint` with the LSODA method and standard GR corrections (Schwarzschild), **Then** the output trajectory reproduces the known secular precession of Mercury's perihelion (approx. tens of arcseconds/century) within a tolerance of ±0.1 arcseconds/century.

---

### User Story 2 - Differential Ephemeris Analysis and SEP Testing (Priority: P2)

As a physicist, I want to perform a differential analysis by comparing the difference vector between the JPL Horizons ephemeris and the INPOP19a ephemeris against the gravitational binding energy fractions ($\Omega$) of the planets, so that I can determine if Strong Equivalence Principle (SEP) violations exist at planetary scales without circularity.

**Why this priority**: This addresses the core research question by using independent ephemerides to isolate the Nordtvedt effect signal, avoiding the circularity of residual-based tests against a single model. It transforms raw ephemeris differences into statistical evidence for SEP violations.

**Independent Test**: The system can be tested by feeding it synthetic data where the "ephemeris difference" is explicitly generated with a known non-zero Nordtvedt parameter. The analysis module must recover this known value in the majority of synthetic runs, with a confidence interval that includes the true value.

**Acceptance Scenarios**:

1. **Given** the JPL Horizons ephemeris and the INPOP19a ephemeris for the same time interval, **When** the system calculates the difference vector in position and velocity for each planet, **Then** the system outputs the time-series difference data and its uncertainty estimates, with a tolerance of within 1 km as per INPOP19a documentation.
2. **Given** the difference vector and planetary gravitational binding energy fractions ($\Omega$), **When** the system performs a time-domain regression analysis to detect the polarization signature of the Nordtvedt effect, **Then** the system outputs the regression slope, p-value, and the upper bound on the Nordtvedt parameter $\eta$.

---

### User Story 3 - Statistical Validation and Constraint Derivation (Priority: P3)

As a researcher, I want to run a Monte Carlo simulation that resamples the ephemeris difference vector uncertainties and re-runs the time-domain regression to generate a null distribution for the fitted parameters, so that I can robustly quantify the significance of the results and tighten constraints on alternative gravity theories.

**Why this priority**: This adds statistical rigor and handles the "null result" case, which is scientifically valuable. It ensures the findings are not artifacts of noise and provides a concrete bound on theoretical parameters.

**Independent Test**: The system can be tested by running the Monte Carlo simulation on a dataset known to have zero violation. The resulting p-value distribution must pass a Kolmogorov-Smirnov test against a uniform distribution (p > 0.05) over 1000 runs, and the derived upper bound must be consistent with the input noise levels.

**Acceptance Scenarios**:

1. **Given** the fitted parameters and observational uncertainties, **When** the system runs a Monte Carlo simulation with a sufficient number of iterations (until the standard error of the p-value estimate is < 0.01 or a maximum of 10,000 iterations) resampling the uncertainties, **Then** it generates a null distribution of parameters and calculates a p-value for the observed violation.
2. **Given** a non-significant p-value (p > 0.05), **When** the system calculates the upper bound on the scalar-tensor coupling parameter $\omega_{BD}$, **Then** it outputs a numerical lower bound for $\omega_{BD}$ (e.g., $\omega_{BD} > X$) with a specified confidence level.

### Edge Cases

- What happens if the JPL Horizons API returns incomplete data for a specific date range (e.g., gaps in Mars tracking)? The system must interpolate missing points or exclude the planet from the regression for that specific epoch, logging the exclusion.
- How does the system handle a scenario where the gravitational binding energy fraction ($\Omega$) for a planet is not available in the compiled peer-reviewed interior models? The system must retry the data fetch up to 3 times; if still missing, it must exclude the planet from the regression and log a warning with error code E-DATA-MISSING-BE.
- What if the Monte Carlo simulation fails to converge due to numerical instability in the resampling? The system must retry with a reduced iteration count and report the reduced confidence level, or fail gracefully if convergence is impossible after attempts.
- What happens if the minimum sample size of N >= 3 planets is not available for the regression? The system MUST halt and report a failure code E-SAMPLE-SIZE-INSUFFICIENT.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download high-precision positional, velocity, and raw tracking data (range/range-rate) for Mercury, Venus, Earth, and Mars for the period starting in the midth century through 2025 from the JPL Horizons system using `astroquery` with a 1-day sampling interval. (See US-1)
- **FR-002**: System MUST implement a numerical N-body integrator using the `scipy.integrate.odeint` library with the LSODA method that incorporates standard General Relativity corrections (Schwarzschild term only) and Newtonian N-body perturbations to generate a GR-predicted trajectory. Lense-Thirring effects are excluded as they are below the noise floor of current ephemerides. This choice is mandated by Constitution Principle VII. (See US-1)
- **FR-003**: System MUST download the INPOP19a ephemeris data for the same time interval and planets via the `astroquery.imcce` module or direct file download to serve as an independent reference baseline. (See US-2)
- **FR-004**: System MUST perform a time-domain regression analysis where the dependent variable is the difference vector between the JPL Horizons and INPOP19a ephemerides and the independent variable is the planetary gravitational binding energy fraction ($\Omega \approx -GM/Rc^2$), derived from peer-reviewed interior structure models (e.g., *Seager et al.*), controlling for mass and semi-major axis using the functional form: `difference_vector ~ $\Omega$ + $\log(Mass)$ + $\log(a)$` via Ordinary Least Squares (OLS) with heteroscedasticity-consistent standard errors. (See US-2)
- **FR-005**: System MUST conduct a Monte Carlo simulation with a sufficient number of iterations (until the standard error of the p-value estimate is < 0.01 or a maximum of 10,000 iterations) resampling the ephemeris difference vector uncertainties to generate a null distribution for the fitted parameters and calculate the p-value. (See US-3)
- **FR-006**: System MUST validate results by comparing the difference vector against the documented inter-ephemeris uncertainty bounds, with a tolerance of within 1 km (approx. sub-arcsecond precision at 1 AU) as per INPOP19a documentation. (See US-2)
- **FR-007**: System MUST derive an upper bound on the scalar-tensor coupling parameter $\omega_{BD}$ if the correlation is not statistically significant (p > 0.05). (See US-3)
- **FR-008**: System MUST exclude any planet from the regression analysis if its gravitational binding energy data is missing after 3 retry attempts, and MUST ensure a minimum sample size of N >= 3 planets is available for the regression to proceed; if N < 3, the system MUST halt and report a failure code E-SAMPLE-SIZE-INSUFFICIENT. (See US-1, US-2)
- **FR-009**: System MUST validate extraction-selector coverage against a labelled sample to ensure the data acquisition logic correctly identifies and parses all required fields. (See US-1)

### Key Entities

- **PlanetaryOrbit**: Represents the trajectory of a specific planet (Mercury, Venus, Earth, Mars) over time, containing attributes for position, velocity, and perihelion precession rate.
- **GravitationalBindingEnergy**: Represents the calculated $\Omega$ fraction for a planet, derived from mass, radius, and peer-reviewed interior structure models. Defined as $\Omega \approx -GM/Rc^2$.
- **EphemerisDifference**: Represents the difference vector between observed (JPL) and reference (INPOP) ephemerides, including uncertainty estimates.
- **RegressionResult**: Contains the slope, intercept, p-value, and confidence intervals derived from the correlation analysis.
- **PPNParameters**: Contains the fitted values and uncertainties for $\gamma, \beta$, and $\eta$.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The accuracy of the GR baseline trajectory is measured against the known secular precession of Mercury's perihelion as established by standard astronomical tables, within a tolerance of ±0.1 arcseconds/century. (See US-1)
- **SC-002**: The statistical significance of the correlation between the ephemeris difference vector and gravitational binding energy fractions is measured against a fixed p-value threshold of 0.05 derived from the Monte Carlo null distribution. (See US-2)
- **SC-003**: The robustness of the results is measured against the INPOP19a ephemeris by comparing the derived difference values to ensure they fall within the documented inter-ephemeris uncertainty bounds as per INPOP19a documentation. (See US-3)
- **SC-004**: The constraint on the scalar-tensor coupling parameter $\omega_{BD}$ is measured against the confidence interval derived from the residual uncertainty limits. (See US-3)
- **SC-005**: The computational feasibility is measured against the constraint that the entire pipeline (data download, integration, regression, Monte Carlo) must complete within 6 hours on a CPU-only environment with ≤7 GB RAM. (See Assumptions)

## Assumptions

- The JPL Horizons API and the INPOP19a ephemeris data are accessible via public interfaces without requiring paid subscriptions or restricted authentication keys.
- The gravitational binding energy fractions ($\Omega$) for Mercury, Venus, Earth, and Mars can be accurately derived from peer-reviewed interior structure models (e.g., *Seager et al.*) without requiring new interior modeling.
- The `scipy.integrate.odeint` library with the LSODA method is sufficiently accurate to resolve the small secular precession effects of General Relativity within the mid-20th century to 2025 timeframe without requiring higher-order symplectic integrators that might exceed CPU time limits. This choice is mandated by Constitution Principle VII, despite `rebound` being scientifically superior for N-body dynamics.
- The Monte Carlo simulation with a sufficient number of iterations will complete within the standard time limit on a standard 2-core CPU runner.
- The planetary data sampling interval is sufficient to capture secular trends without introducing aliasing artifacts that would obscure the precession signal.
- The correlation between ephemeris differences and binding energy, if present, is linear within the range of planetary parameters in the solar system.
- The Nordtvedt effect (SEP violation) is the relevant phenomenon for self-gravitating bodies, and the signal-to-noise ratio is sufficient to establish upper bounds on $\eta$ even if a definitive detection is not possible.
- The entire pipeline (data download, integration, regression, Monte Carlo) must complete within 6 hours on a CPU-only environment with ≤7 GB RAM.
- While Lunar Laser Ranging (LLR) provides the primary constraint on the Nordtvedt parameter $\eta$, this project uses planetary differential ephemeris analysis as a complementary test using publicly available data, justified by the need to constrain $\eta$ across different mass scales and orbital configurations.
- The 4-body model without a full force model (tides, asteroids) is insufficient for full precision but is justified as a complementary test for public data, acknowledging that residuals may be dominated by unmodeled physics.
- The differential ephemeris analysis (JPL vs INPOP) is used to isolate potential discrepancies between independent models, which may reveal unmodeled physics or WEP violations, rather than comparing a single model to itself.
- Peer-reviewed interior structure models are required for $\Omega$ to avoid systematic errors from bulk averages.