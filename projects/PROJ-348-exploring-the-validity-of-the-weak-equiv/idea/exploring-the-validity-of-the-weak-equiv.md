---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Field**: physics

## Research question

Do planets with different bulk compositions (iron core fraction, silicate mantle ratio) exhibit systematically different orbital deviations from General Relativity predictions over multi-decadal timescales, which would indicate a composition-dependent violation of the Weak Equivalence Principle?

## Motivation

The Weak Equivalence Principle (WEP) — that all objects fall with the same acceleration regardless of composition — is a foundational postulate of General Relativity and all metric theories of gravity. While laboratory torsion balance tests and lunar laser ranging have constrained WEP violations to parts in 10^13, planetary orbital data offers a complementary test at solar-system scales with decades-long baselines. If WEP violations exist that couple to baryon number or nuclear binding energy, they should manifest as composition-dependent orbital perturbations in the inner solar system. This project addresses whether such signals are detectable in existing public ephemerides.

## Literature gap analysis

### What we searched

We queried arXiv and Living Reviews in Relativity using search terms: "Weak Equivalence Principle planetary orbit", "WEP violation solar system ephemeris", "equivalence principle composition dependence orbit", and "JPL Horizons equivalence principle test". We reviewed 4 papers returned from the literature block and conducted additional searches via Semantic Scholar queries on "gravitational composition dependence" and "solar system tests of general relativity".

### What is known

- [Gravity at Finite Temperature, Equivalence Principle, and Local Lorentz Invariance (2021)](http://arxiv.org/abs/2101.00458v2) — Theoretical work establishing formal connections between WEP violation and finite-temperature gravitational effects, but does not address planetary-scale orbital tests.
- [Cosmology and Fundamental Physics with the Euclid Satellite (2013)](https://doi.org/10.12942/lrr-2013-6) — Reviews fundamental physics tests including WEP with space-based missions, but focuses on cosmological scales rather than inner solar system planetary orbits.
- [Ultracold neutrons, quantum effects of gravity and the Weak Equivalence Principle (2002)](http://arxiv.org/abs/hep-ph/0204284v3) — Proposes laboratory-scale WEP tests using quantum matter waves, establishing that WEP violations remain an active experimental frontier but not at planetary orbital scales.

### What is NOT known

No published work has systematically analyzed JPL Horizons planetary ephemerides (1950–present) to search for composition-dependent orbital residuals after accounting for standard General Relativity and N-body perturbations. Existing solar-system tests of gravity (e.g., Cassini Shapiro delay, lunar laser ranging) constrain different parameters (PPN γ, β) but do not directly test composition-dependent acceleration at the planetary scale. The sensitivity of inner planet orbital fits to WEP-violating differential accelerations remains unquantified.

### Why this gap matters

Solar-system WEP tests provide complementary constraints to laboratory torsion balance experiments (e.g., Eöt-Wash) and lunar laser ranging. A null result at planetary scales would tighten bounds on certain WEP-violating theories (e.g., dilaton couplings, chameleon fields) that predict composition-dependent effects scaling with gravitational potential depth. A positive signal would indicate new physics at astronomical scales, with implications for dark sector models and modified gravity theories.

### How this project addresses the gap

We will download publicly available JPL Horizons planetary ephemerides for Mercury, Venus, Earth, and Mars (1950–2025), fit standard GR+PPN orbital models, and examine composition-correlated residuals. The methodology explicitly tests whether differential accelerations scale with planetary iron core fraction and nuclear binding energy per nucleon — parameters not addressed in existing solar-system gravity tests.

## Expected results

We expect to either (1) recover null composition-dependent residuals within current ephemeris uncertainty (≈10 meters for inner planets), tightening WEP violation bounds by a factor of 2–5 for certain coupling models, or (2) identify statistically significant (p < 0.01) composition-correlated orbital drifts that warrant follow-up with independent ephemeris sources. Evidence will be measured via χ² comparison of composition-dependent vs. composition-independent orbital models, with significance assessed through Monte Carlo resampling of observational errors.

## Methodology sketch

- Download planetary ephemerides from JPL Horizons public API for Mercury, Venus, Earth, Mars (1950–2025), including position/velocity vectors at 1-day intervals (~25,000 data points per planet).
- Obtain planetary bulk composition parameters from NASA Planetary Fact Sheet and peer-reviewed interior models (iron core mass fraction, mean nuclear binding energy per nucleon).
- Implement N-body orbital integrator in Python using `astropy` and `scipy.integrate.odeint`, incorporating standard GR corrections (Schwarzschild precession, Lense-Thirring frame-dragging).
- Fit orbital elements via least-squares minimization to JPL ephemerides, then compute residuals (observed minus model).
- Test for composition-dependent residuals by regressing residual magnitudes against iron core fraction and binding energy per nucleon using linear mixed-effects models.
- Perform Monte Carlo error propagation: resample observational uncertainties (±10 m) 10,000 times to establish null distribution of composition-residual correlations.
- Compute χ² difference between composition-independent and composition-dependent models; assess significance via F-test (α = 0.01).
- Validate against independent ephemeris source (INPOP19a from IMCCE) to rule out systematic artifacts from JPL-specific modeling assumptions.
- Document all code, data versions, and random seeds in a public GitHub repository for reproducibility.

## Duplicate-check

- Reviewed existing ideas: [None provided in input corpus]
- Closest match: None identified (no existing ideas in corpus to compare)
- Verdict: NOT a duplicate
