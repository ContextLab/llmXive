# Feature Specification: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Feature Branch**: `001-exploring-wep-validity`  
**Created**: 2026-08-04  
**Status**: Draft  
**Input**: User description: "Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data"

## User Scenarios & Testing

### User Story 1 - Differential Ephemeris Construction and Residual Extraction (Priority: P1)

As a researcher, I want to download high-precision ephemeris data for Mercury, Venus, Earth, and Mars from two independent sources (JPL Horizons and INPOP19a) and compute the time-series difference vectors (position and velocity) between them, so that I can isolate potential discrepancies (Nordtvedt effect signals) without relying on a single model's internal assumptions or circular validation against a GR-only baseline.

**Why this priority**: This addresses the core methodological flaw of the previous iteration. The Nordtvedt effect ($\eta$) manifests as a differential acceleration between bodies with different gravitational binding energies ($\Omega$). Comparing two independent ephemerides (JPL vs. INPOP) is the only valid approach using public data to detect such a signal, as it avoids the circularity of subtracting a GR-only simulation from an observation that already assumes GR. This step provides the raw dependent variable for the statistical test.

**Independent Test**: The system can be tested by running the download and differencing pipeline on a known "null" interval (e.g., a period with high data coverage) and verifying that the RMS of the difference vector for Earth matches the documented inter-ephemeris agreement (approx. 100m - 1km) within a tolerance of ±100m.

**Acceptance Scenarios**:

1. **Given** the JPL Horizons and INPOP19a public interfaces are accessible, **When** the system downloads positional and velocity data for Mercury, Venus, Earth, and Mars for the interval 1950–2025 with a daily sampling rate, **Then** the system successfully parses both datasets into aligned time-series structures with a timestamp tolerance of < 1 second.
2. **Given** the aligned time-series for a specific planet (e.g., Earth), **When** the system computes the Euclidean distance difference between the JPL and INPOP position vectors for every timestamp, **Then** the system outputs a time-series of residual magnitudes where the mean RMS is within the range [100m, 1500m] (consistent with documented INPOP/JPL agreement) and no single outlier exceeds 5 km.

---

### User Story 2 - Binding Energy Compilation and Variable Alignment (Priority: P2)

As a physicist, I want to retrieve the gravitational binding energy fractions ($\Omega$) for the target planets from peer-reviewed interior structure models (not bulk NASA Fact Sheets) and align them with the residual data, so that I can perform a regression analysis that accurately reflects the theoretical scaling of the Nordtvedt effect while minimizing systematic errors from core/mantle uncertainties.

**Why this priority**: The previous spec used bulk mass/radius, which introduces a significant systematic error in $\Omega$, swamping the expected signal. Using peer-reviewed interior models (e.g., *Seager et al.*, *Nimmo et al.*) is required for methodological validity. This step ensures the independent variable ($\Omega$) is scientifically defensible.

**Independent Test**: The system can be tested by verifying that the retrieved $\Omega$ values for Earth and Mars match the published values in the source literature (e.g., *Nimmo et al., 2004*) within a tolerance of ±0.5% relative error.

**Acceptance Scenarios**:

1. **Given** the list of target planets, **When** the system queries the compiled dataset of peer-reviewed interior models for $\Omega$, **Then** the system returns a value for each planet with a source citation, and if a value is missing for a planet, the system excludes that planet from the regression and logs a warning with error code `E-OMEGA-MISSING`.
2. **Given** the calculated $\Omega$ values and the residual time-series, **When** the system prepares the data for regression, **Then** the system ensures that the number of planets with valid $\Omega$ data and valid residual data is at least 3 (N ≥ 3), halting with `E-SAMPLE-SIZE-INSUFFICIENT` if this condition is not met.

---

### User Story 3 - Statistical Significance and Constraint Derivation (Priority: P3)

As a researcher, I want to perform a linear regression of the RMS of the ephemeris difference vectors against the gravitational binding energy fractions ($\Omega$) and conduct a Monte Carlo simulation to generate a null distribution, so that I can determine if the correlation is statistically significant (p < 0.05) and derive an upper bound on the Nordtvedt parameter $\eta$ if the null hypothesis cannot be rejected.

**Why this priority**: This addresses the "flawed Monte Carlo" concern by focusing the simulation on the *statistical significance of the correlation* rather than re-integrating the N-body system. The regression slope represents the scaling of the differential signal with $\Omega$. The Monte Carlo resampling of the residuals' uncertainties validates whether the observed slope could arise from noise, providing a robust p-value and confidence interval for the constraint.

**Independent Test**: The system can be tested by injecting a synthetic non-zero slope into the residual data (simulating a known $\eta$) and verifying that the regression recovers this slope with a 95% confidence interval that includes the injected value and a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** the paired data of RMS residuals and $\Omega$ for N ≥ 3 planets, **When** the system performs an Ordinary Least Squares (OLS) regression with heteroscedasticity-consistent standard errors, **Then** the system outputs the slope, intercept, p-value, and 95% confidence interval for the slope.
2. **Given** the fitted slope and the observational uncertainties, **When** the system runs a Monte Carlo simulation with 10,000 iterations resampling the residuals within their uncertainty bounds, **Then** the system generates a null distribution of slopes, calculates the empirical p-value, and if p > 0.05, computes the [deferred] upper bound on the Nordtvedt parameter $\eta$.

### Edge Cases

- **What happens if the JPL Horizons or INPOP19a API returns incomplete data for a specific planet (e.g., Mars) for a significant portion of the 1950–2025 interval?** The system must interpolate missing points using a cubic spline if gaps are < 7 days; if gaps exceed 7 days, the system must exclude that planet from the regression and log `E-DATA-GAP-EXCEEDED`.
- **How does the system handle a scenario where the peer-reviewed interior model for a planet is missing or outdated?** The system must retry fetching from alternative sources (e.g., *Seager* vs. *Nimmo*) up to 2 times; if all sources fail, the system excludes the planet and logs `E-OMEGA-SOURCE-FAIL`.
- **What if the Monte Carlo simulation fails to converge (e.g., due to numerical instability in the resampling)?** The system must retry with a reduced iteration count ([deferred]) and a larger step size; if convergence is not achieved after 3 attempts, the system must report `E-MC-CONVERGENCE-FAIL` and output the results with a warning that the p-value is approximate.
- **What happens if the minimum sample size of N ≥ 3 planets is not available?** The system MUST halt immediately and report a fatal error `E-SAMPLE-SIZE-INSUFFICIENT` with a message listing the available planets and the reason for exclusion.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download high-precision positional and velocity data for Mercury, Venus, Earth, and Mars for a multi-decadal historical period from the JPL Horizons system using `astroquery` with a 1-day sampling interval. (See US-1)
- **FR-002**: System MUST download the INPOP19a ephemeris data for the same time interval and planets via the `astroquery.imcce` module or direct file download to serve as an independent reference baseline. (See US-1)
- **FR-003**: System MUST compute the time-series difference vector (position and velocity) between the JPL Horizons and INPOP19a ephemerides for each planet to isolate differential signals. (See US-1)
- **FR-004**: System MUST retrieve the gravitational binding energy fractions ($\Omega$) for the target planets from peer-reviewed interior structure models (e.g., *Seager et al.*, *Nimmo et al.*), NOT from bulk NASA Fact Sheets, to minimize systematic errors. (See US-2)
- **FR-005**: System MUST perform a linear regression where the dependent variable is the Root-Mean-Square (RMS) of the ephemeris difference vectors and the independent variable is $\Omega$, using Ordinary Least Squares (OLS) with heteroscedasticity-consistent standard errors. (See US-3)
- **FR-006**: System MUST conduct a Monte Carlo simulation with exactly 10,000 iterations (or until the standard error of the p-value estimate is < 0.01) resampling the ephemeris difference vector uncertainties to generate a null distribution for the regression slope. (See US-3)
- **FR-007**: System MUST derive an upper bound on the Nordtvedt parameter $\eta$ (or the equivalent scalar-tensor coupling) if the p-value of the regression slope is > 0.05, reporting the 95% confidence interval. (See US-3)
- **FR-008**: System MUST validate that the number of planets with valid $\Omega$ and residual data is at least 3 (N ≥ 3); if N < 3, the system MUST halt and report `E-SAMPLE-SIZE-INSUFFICIENT`. (See US-2, US-3)
- **FR-009**: System MUST ensure that the entire pipeline (data download, differencing, regression, Monte Carlo) executes within 6 hours on a CPU-only environment with ≤7 GB RAM, using `scipy` for all numerical operations. (See Assumptions)
- **FR-010**: System MUST log all data exclusions (due to gaps, missing $\Omega$, or sample size issues) with specific error codes and reasons in a `pipeline_log.txt` file. (See Edge Cases)

### Key Entities

- **PlanetaryOrbit**: Represents the trajectory of a specific planet (Mercury, Venus, Earth, Mars) over time, containing attributes for position, velocity, and timestamps from a specific ephemeris source.
- **EphemerisDifference**: Represents the difference vector between observed (JPL) and reference (INPOP) ephemerides, including the calculated RMS magnitude and timestamp.
- **GravitationalBindingEnergy**: Represents the calculated $\Omega$ fraction for a planet, derived from peer-reviewed interior structure models (mass, radius, density profiles), defined as $\Omega \approx -GM/Rc^2$.
- **RegressionResult**: Contains the slope, intercept, p-value, confidence intervals, and the derived constraint on $\eta$ from the correlation analysis.
- **MonteCarloDistribution**: Represents the null distribution of slopes generated by the resampling simulation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The accuracy of the differential ephemeris extraction is measured against the documented inter-ephemeris agreement (approx. 100m–1km) for Earth, ensuring the RMS of the difference vector falls within this range. (See US-1)
- **SC-002**: The validity of the binding energy data is measured against the published values in peer-reviewed interior structure models (e.g., *Nimmo et al.*), ensuring the retrieved $\Omega$ values match within ±0.5% relative error. (See US-2)
- **SC-003**: The statistical significance of the correlation is measured against a fixed p-value threshold of 0.05 derived from the Monte Carlo null distribution. (See US-3)
- **SC-004**: The constraint on the Nordtvedt parameter $\eta$ is measured against the 95% confidence interval derived from the regression slope and the Monte Carlo null distribution. (See US-3)
- **SC-005**: The computational feasibility is measured against the constraint that the entire pipeline must complete within 6 hours on a CPU-only environment with ≤7 GB RAM. (See Assumptions)

## Assumptions

- The JPL Horizons API and the INPOP19a ephemeris data are accessible via public interfaces without requiring paid subscriptions or restricted authentication keys.
- The gravitational binding energy fractions ($\Omega$) for Mercury, Venus, Earth, and Mars can be accurately derived from peer-reviewed interior structure models (e.g., *Seager et al.*, *Nimmo et al.*) without requiring new interior modeling.
- The linear relationship between the RMS of the ephemeris difference vector and the gravitational binding energy fraction ($\Omega$) is a valid proxy for testing the Nordtvedt effect in this differential analysis context, as the differential signal scales with $\Omega$.
- The `scipy` library (specifically `scipy.stats` and `numpy`) provides sufficient numerical stability for the linear regression and Monte Carlo resampling within the 6-hour CPU limit.
- The inter-ephemeris differences (JPL vs. INPOP) are dominated by modeling differences and potential SEP violations rather than random noise, making the RMS a suitable dependent variable for regression.
- The minimum sample size of N ≥ 3 planets is sufficient to perform a statistically meaningful linear regression for this specific planetary regime.
- The Monte Carlo simulation with a sufficient number of iterations will complete within the standard time limit on a standard 2-core CPU runner.
- The correlation between ephemeris differences and binding energy, if present, is linear within the range of planetary parameters in the solar system.
- The differential ephemeris analysis (JPL vs INPOP) is used to isolate potential discrepancies between independent models, which may reveal unmodeled physics or WEP violations, rather than comparing a single model to itself.
- Peer-reviewed interior structure models are required for $\Omega$ to avoid systematic errors from bulk averages.
- The 4-body model without a full force model (tides, asteroids) is insufficient for full precision but is justified as a complementary test for public data, acknowledging that residuals may be dominated by unmodeled physics, but the differential nature of the test (JPL vs INPOP) mitigates common-mode errors.
- The entire pipeline (data download, integration, regression, Monte Carlo) must complete within 6 hours on a CPU-only environment with ≤7 GB RAM.
