---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Field**: physics

## Research question

Do inner planets with distinct gravitational binding energy fractions exhibit differential orbital precession consistent with scalar-tensor screening mechanisms that suppress WEP violations in the Earth-Moon system but remain active at planetary scales?

## Motivation

The Weak Equivalence Principle (WEP) is a cornerstone of General Relativity, yet many alternative gravity theories (e.g., scalar-tensor models) predict composition-dependent violations that are screened in high-density environments like the Earth-Moon system but may persist for planets with different binding energies. While Lunar Laser Ranging (LLR) has constrained WEP violations to parts in $10^{13}$, these tests are limited to the specific composition of the Earth and Moon. Analyzing the orbital precession of inner planets (Mercury, Venus, Mars) offers a unique probe of these screening mechanisms, as their distinct gravitational binding energy fractions ($\Omega \approx -GM/Rc^2$) create a natural laboratory to test if WEP violations scale with self-gravity in a way that LLR cannot detect.

## Related work

- [Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle (2023)](https://arxiv.org/abs/2310.00719) — Applies Bayesian methods to planetary ephemerides to constrain Brans-Dicke scalar-tensor theories, directly addressing the parameter space where WEP violations might manifest in planetary orbits.
- [Testing Theories of Gravity with Planetary Ephemerides (2023)](https://arxiv.org/abs/2303.01821) — Details the construction of planetary ephemerides in General Relativity and outlines the framework for testing alternative gravity theories, providing the necessary baseline for identifying deviations.
- [Lunar Laser Ranging Science (2004)](https://arxiv.org/abs/gr-qc/0411095) — Establishes the current stringent limits on WEP violations from the Earth-Moon system, serving as the critical comparison point to determine if planetary scales reveal different behavior due to screening effects.
- [Gravity at Finite Temperature, Equivalence Principle, and Local Lorentz Invariance (2021)](https://arxiv.org/abs/2101.00458) — Theoretical exploration of WEP violations in specific contexts, highlighting the gap in empirical tests that connect finite-temperature effects or specific screening mechanisms to planetary orbital dynamics.

## Expected results

We expect to either (1) confirm that planetary orbital precession residuals are consistent with General Relativity within current ephemeris uncertainties (tightening constraints on scalar-tensor coupling parameters), or (2) detect a statistically significant correlation between residual precession rates and planetary gravitational binding energy fractions. The latter would provide evidence for a breakdown of the Strong Equivalence Principle at planetary scales, distinguishing this project from existing LLR constraints.

## Methodology sketch

- **Data Acquisition**: Download high-precision positional and velocity data for Mercury, Venus, Earth, and Mars (1950–2025) from the JPL Horizons system via the `astroquery` Python package, selecting a sampling interval of 1 day to capture long-term secular trends.
- **Parameter Compilation**: Compile planetary gravitational binding energy fractions ($\Omega$) and bulk composition parameters from NASA Planetary Fact Sheets and peer-reviewed interior structure models (e.g., *Seager et al.*).
- **Reference Model Construction**: Implement a numerical N-body integrator using `scipy.integrate.odeint` that incorporates standard General Relativity corrections (Schwarzschild, Lense-Thirring) and Newtonian N-body perturbations to generate a GR-predicted trajectory for each planet.
- **Residual Analysis**: Compute the difference between the observed JPL ephemeris positions and the GR model predictions to isolate orbital residuals, focusing on the secular precession of the perihelion.
- **Statistical Testing**: Perform a linear regression analysis where the dependent variable is the residual precession rate and the independent variable is the planetary gravitational binding energy fraction, controlling for mass and semi-major axis.
- **Independent Validation**: Validate the results by comparing against the INPOP19a ephemeris (IMCCE) to ensure detected signals are not artifacts of the JPL modeling pipeline.
- **Significance Assessment**: Conduct a Monte Carlo simulation (10,000 iterations) resampling observational uncertainties to generate a null distribution for the regression slope, calculating the p-value for the correlation.
- **Constraint Derivation**: If no significant correlation is found, derive upper bounds on the scalar-tensor coupling parameter $\omega_{BD}$ using the residual uncertainty limits; if a correlation exists, estimate the violation magnitude.
- **Reproducibility**: Archive all code, data processing scripts, and random seeds in a public repository, ensuring the full pipeline is reproducible on standard CPU hardware.

## Duplicate-check

- Reviewed existing ideas: [None provided in input corpus]
- Closest match: None identified (no existing ideas in corpus to compare)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-11T12:29:36Z
**Outcome**: exhausted
**Original term**: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics | 0 |
| 1 | test of the weak equivalence principle using planetary ephemerides | 4 |
| 2 | constraints on the universality of free fall from solar system dynamics | 0 |
| 3 | lunar laser ranging and equivalence principle violations | 0 |
| 4 | PPN parameters gamma and beta from planetary orbit analysis | 0 |
| 5 | differential acceleration of planets in the solar gravitational field | 0 |
| 6 | search for fifth forces using planetary orbital residuals | 0 |
| 7 | Nordtvedt effect in planetary motion | 0 |
| 8 | gravitational redshift and equivalence principle tests with spacecraft tracking | 0 |
| 9 | violations of the Einstein equivalence principle in the solar system | 0 |
| 10 | post-Newtonian constraints on alternative gravity theories from ephemeris data | 0 |
| 11 | composition-dependent gravitational acceleration of solar system bodies | 0 |
| 12 | analysis of MESSENGER and Cassini tracking data for equivalence principle tests | 0 |
| 13 | solar system tests of general relativity and modified gravity | 0 |
| 14 | planetary perihelion precession and equivalence principle constraints | 0 |
| 15 | dark matter coupling to baryonic matter via planetary orbit perturbations | 0 |
| 16 | scalar-tensor theory constraints from planetary orbital data | 0 |
| 17 | equivalence principle tests using astrometric data from Gaia and VLBI | 0 |
| 18 | gravitational binding energy contribution to planetary inertial mass | 0 |
| 19 | long-range forces and equivalence principle violation limits | 0 |
| 20 | solar system dynamics as a probe for new gravitational interactions | 0 |

### Verified citations

1. **Lunar Laser Ranging Science** (2004). James G. Williams, Dale H. Boggs, Slava G. Turyshev, J. Todd Ratcliff. arXiv. [gr-qc/0411095](gr-qc/0411095). PDF-sampled: No.
2. **Gravity at Finite Temperature, Equivalence Principle,and Local Lorentz Invariance** (2021). M. Gasperini. arXiv. [2101.00458](https://arxiv.org/abs/2101.00458). PDF-sampled: No.
3. **Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle** (2023). Vincenzo Mariani, Olivier Minazzoli, Agnès Fienga, Jacques Laskar, Mickaël Gastineau. arXiv. [2310.00719](https://arxiv.org/abs/2310.00719). PDF-sampled: No.
4. **Testing Theories of Gravity with Planetary Ephemerides** (2023). Agnès Fienga, Olivier Minazzoli. arXiv. [2303.01821](https://arxiv.org/abs/2303.01821). PDF-sampled: No.
