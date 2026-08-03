---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Field**: physics

## Research question

Does the differential acceleration of inner planets relative to a non-self-gravitating test mass, derived from high-precision ranging residuals after subtracting a GR-only ephemeris with fixed solar oblateness, scale linearly with their gravitational binding energy fractions?

## Motivation

While Lunar Laser Ranging (LLR) provides stringent constraints on the Strong Equivalence Principle (SEP) for the Earth-Moon system, the planetary regime offers a distinct laboratory where the gravitational binding energy fraction ($\Omega$) varies significantly across bodies like Mercury and Mars. Many scalar-tensor theories predict that SEP violations (the Nordtvedt effect) scale with $\Omega$, yet current planetary tests are often limited by degeneracies with solar oblateness ($J_2$) and incomplete force models. A rigorous re-analysis of planetary ephemerides, explicitly modeling these degeneracies and testing for a correlation between orbital residuals and $\Omega$, can either tighten constraints on alternative gravity theories or reveal a breakdown of the SEP at planetary scales that LLR cannot detect.

## Related work

- [Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle (2023)](https://arxiv.org/abs/2310.00719) — Establishes a Bayesian framework to constrain Brans-Dicke parameters using planetary ephemerides, directly addressing the parameter space for SEP violations in the solar system.
- [Lunar Laser Ranging Science (2004)](https://arxiv.org/abs/gr-qc/0411095) — Provides the benchmark limits on WEP/SEP violations from the Earth-Moon system, highlighting the need for complementary tests in the planetary regime with different $\Omega$ values.
- [Theoretical Aspects of the Equivalence Principle (2012)](https://arxiv.org/abs/1202.6311) — Reviews the theoretical basis for SEP violations, clarifying that the Nordtvedt effect manifests as a polarization of orbits dependent on binding energy, not just a static precession shift.
- [The Eötvös Paradox: The Enduring Significance of Eötvös' Most Famous Paper (2019)](https://arxiv.org/abs/1901.11163) — Contextualizes the historical evolution of equivalence principle tests, underscoring the transition from laboratory torsion balances to astronomical observations of self-gravitating bodies.

## Expected results

We expect to either (1) find no statistically significant correlation between differential acceleration residuals and gravitational binding energy fractions, thereby tightening the upper bound on the PPN parameter $\eta$ (Nordtvedt parameter) by an order of magnitude compared to simple 4-body fits, or (2) detect a residual pattern consistent with a non-zero $\eta$ that scales with $\Omega$, which would constitute evidence for a breakdown of the Strong Equivalence Principle. The key measurement is the slope of the residual-vs-$\Omega$ regression, where a slope indistinguishable from zero confirms GR, while a non-zero slope indicates a violation.

## Methodology sketch

- **Data Acquisition**: Download high-precision ephemeris data (positions and velocities) for Mercury, Venus, Earth, and Mars (1950–2025) from the JPL Horizons system using `astroquery`, ensuring a daily sampling rate to capture secular trends.
- **Binding Energy Compilation**: Retrieve planetary gravitational binding energy fractions ($\Omega$) from peer-reviewed interior structure models (e.g., *Seager et al.*, *Nimmo et al.*) rather than bulk NASA Fact Sheets to minimize systematic errors from core/mantle uncertainties.
- **Force Model Implementation**: Construct a high-fidelity N-body integrator using `scipy.integrate.odeint` (adhering to Constitution Principle VII) that includes Newtonian $N$-body perturbations, standard GR corrections (Schwarzschild, Lense-Thirring), solar quadrupole moment ($J_2$), and major asteroid perturbations (using the 300 largest asteroids from the JPL Small-Body Database).
- **Baseline Simulation**: Generate a "GR-only" trajectory for each planet by setting the Nordtvedt parameter $\eta = 0$ and solar $J_2$ to its best-fit value, ensuring the model reproduces known secular precession rates within observational uncertainties.
- **Residual Calculation**: Compute the difference between the JPL Horizons observational data and the GR-only simulation, focusing on the time-series of orbital range and range-rate residuals to capture the time-dependent polarization signature of the Nordtvedt effect.
- **Parameter Regression**: Perform a linear regression where the dependent variable is the root-mean-square (RMS) of the orbital residuals for each planet and the independent variable is the planet's gravitational binding energy fraction ($\Omega$), controlling for semi-major axis and mass.
- **Independent Validation**: Validate the residuals against the INPOP19a ephemeris (IMCCE) to ensure detected signals are not artifacts of the JPL modeling pipeline; this target is independent as it uses a separate dataset and force model.
- **Significance Assessment**: Conduct a Monte Carlo simulation (10,000 iterations) resampling the observational uncertainties to generate a null distribution for the regression slope, calculating the p-value to determine if the correlation is statistically significant ($p < 0.05$).
- **Constraint Derivation**: If the null hypothesis cannot be rejected, derive an upper bound on the Nordtvedt parameter $\eta$ based on the 95% confidence interval of the regression slope; if a correlation is found, estimate the magnitude of the violation.
- **Reproducibility**: Archive all code, data processing scripts, and random seeds in a public repository, ensuring the full pipeline is reproducible on standard CPU hardware within the 6-hour GHA limit.

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: None identified (no existing ideas in corpus to compare).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-03T22:10:48Z
**Outcome**: success_after_expansion
**Original term**: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics | 5 |

### Verified citations

1. **The Eötvös Paradox: The Enduring Significance of Eötvös' Most Famous Paper** (2019). Ephraim Fischbach, Dennis E. Krause. arXiv. [1901.11163](https://arxiv.org/abs/1901.11163). PDF-sampled: No.
2. **Lunar Laser Ranging Science** (2004). James G. Williams, Dale H. Boggs, Slava G. Turyshev, J. Todd Ratcliff. arXiv. [gr-qc/0411095](gr-qc/0411095). PDF-sampled: No.
3. **Gravity at Finite Temperature, Equivalence Principle,and Local Lorentz Invariance** (2021). M. Gasperini. arXiv. [2101.00458](https://arxiv.org/abs/2101.00458). PDF-sampled: No.
4. **Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle** (2023). Vincenzo Mariani, Olivier Minazzoli, Agnès Fienga, Jacques Laskar, Mickaël Gastineau. arXiv. [2310.00719](https://arxiv.org/abs/2310.00719). PDF-sampled: No.
5. **Theoretical Aspects of the Equivalence Principle** (2012). Thibault Damour. arXiv. [1202.6311](https://arxiv.org/abs/1202.6311). PDF-sampled: No.
