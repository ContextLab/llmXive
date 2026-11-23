---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data

**Field**: physics

## Research question

Does the gravitational binding energy fraction of Solar System planets correlate with the amplitude of specific time-dependent orbital perturbations in high-precision planetary ranging residuals, after controlling for standard General Relativity and solar oblateness?

## Motivation

While Lunar Laser Ranging (LLR) provides the most stringent constraints on the Strong Equivalence Principle (SEP) for the Earth-Moon system, the planetary regime offers a distinct laboratory where the gravitational binding energy fraction ($\Omega$) varies by orders of magnitude (e.g., Mercury vs. Mars). Many alternative gravity theories (e.g., scalar-tensor theories) predict that SEP violations manifest as a "Nordtvedt effect"—a polarization of orbits proportional to $\Omega$. Current planetary tests are often limited by degeneracies with solar oblateness ($J_2$) and asteroid belt modeling. A rigorous analysis of publicly available planetary ranging residuals, explicitly testing for a correlation between the magnitude of unmodeled periodic perturbations and $\Omega$, can either tighten constraints on the Nordtvedt parameter $\eta$ or reveal a breakdown of the SEP at planetary scales that LLR cannot detect.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using the following terms: "planetary ephemerides strong equivalence principle," "Nordtvedt effect planetary ranging," "Brans-Dicke planetary constraints," and "gravitational binding energy solar system tests." The search targeted recent Bayesian analyses of ephemerides (2020–2024) and foundational reviews of equivalence principle tests. The literature block returned five results, of which two are directly on-topic regarding planetary constraints, while others provide theoretical context or focus on Lunar Laser Ranging.

### What is known
- [Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle (2023)](https://arxiv.org/abs/2310.00719) — Establishes a modern Bayesian framework for constraining the Nordtvedt parameter $\eta$ using planetary ephemerides, demonstrating that current data allows for tight constraints but highlights the sensitivity to force model assumptions.
- [Lunar Laser Ranging Science (2004)](https://arxiv.org/abs/gr-qc/0411095) — Provides the benchmark limits on SEP violations from the Earth-Moon system, confirming that $\eta \approx 0$ to high precision, but noting that the Earth-Moon system has a much smaller $\Omega$ than Mercury, leaving the high-$\Omega$ regime less constrained.

### What is NOT known
There is no published work that explicitly isolates the *time-dependent polarization signal* predicted by the Nordtvedt effect in the *residuals* of a standard GR-only fit for multiple planets simultaneously and correlates this specific residual amplitude directly with $\Omega$ using public ranging data. Most existing studies treat $\eta$ as a single parameter in a global fit; few analyze the specific *residual structure* (amplitude and phase) of individual planets as a proxy for $\Omega$-dependent violations in a way that separates it from modeling noise.

### Why this gap matters
Filling this gap is critical because alternative gravity theories predict that the violation signal scales with $\Omega$. If the signal is hidden in the residuals of standard fits, a targeted analysis could either improve constraints on $\eta$ by an order of magnitude or identify a systematic error in current ephemeris models that mimics a SEP violation. This would directly impact our understanding of whether gravity is purely geometric or mediated by scalar fields.

### How this project addresses the gap
This project addresses the gap by constructing a dedicated pipeline that: (1) generates a high-fidelity GR-only ephemeris baseline using public data; (2) computes the specific time-dependent residuals (range and range-rate) for Mercury, Venus, Earth, and Mars; (3) extracts the amplitude of the predicted Nordtvedt polarization mode from these residuals; and (4) performs a regression of these amplitudes against the planets' gravitational binding energy fractions ($\Omega$). This approach isolates the $\Omega$-dependent signal from general modeling noise.

## Expected results

We expect to either (1) find no statistically significant correlation between the extracted polarization amplitudes and the gravitational binding energy fractions, thereby tightening the upper bound on the Nordtvedt parameter $\eta$ consistent with General Relativity, or (2) detect a residual pattern where the amplitude scales linearly with $\Omega$, which would constitute evidence for a breakdown of the Strong Equivalence Principle. The key measurement is the slope of the amplitude-vs-$\Omega$ regression, where a slope indistinguishable from zero confirms GR, while a non-zero slope indicates a violation.

## Methodology sketch

- **Data Acquisition**: Download high-precision planetary ranging residuals (range and range-rate) for Mercury, Venus, Earth, and Mars (1960–2025) from the JPL Horizons system using `astroquery`, specifically extracting the "residuals" field relative to the DE440 ephemeris to ensure the baseline is a standard GR model.
- **Binding Energy Compilation**: Retrieve gravitational binding energy fractions ($\Omega$) for each planet from a single, canonical peer-reviewed source (e.g., *Nimmo et al., 2004* or *Seager et al., 2015* Table 2) to ensure consistency, rather than calculating from bulk density which introduces model uncertainty.
- **Signal Extraction**: Implement a Fourier analysis or a specific template-fitting algorithm on the time-series residuals to isolate the frequency component corresponding to the predicted Nordtvedt polarization (typically a long-period term related to the synodic period of the planet and the Sun). This step extracts the "signal amplitude" rather than using raw RMS.
- **Baseline Validation**: Verify that the extracted signal amplitudes for the standard GR baseline (DE440) are consistent with zero within the noise floor of the data, ensuring the residuals are dominated by measurement noise and unmodeled non-gravitational effects (e.g., solar radiation pressure) rather than a built-in SEP violation.
- **Regression Analysis**: Perform a weighted linear regression where the dependent variable is the extracted signal amplitude (with uncertainty derived from the template fit) and the independent variable is the planet's gravitational binding energy fraction ($\Omega$), controlling for the planet's distance from the Sun to account for signal strength scaling.
- **Independent Validation**: Validate the methodology by injecting a synthetic Nordtvedt signal (with a known non-zero $\eta$) into a subset of the raw ranging data, re-running the ephemeris fit and residual extraction, and confirming that the pipeline correctly recovers the injected amplitude. This validation target (injected signal) is independent of the natural data and the $\Omega$ values.
- **Null Distribution Generation**: Conduct a Monte Carlo simulation (1,000 iterations, sufficient for 7GB RAM constraint) where the residuals are randomized (phase-shuffled) to destroy any physical correlation while preserving the noise spectrum, generating a null distribution for the regression slope.
- **Significance Assessment**: Calculate the p-value of the observed regression slope against the null distribution; if $p < 0.05$, reject the null hypothesis of no correlation; otherwise, derive the 95% confidence interval upper bound on $\eta$.
- **Constraint Derivation**: Convert the regression slope and its uncertainty into an upper bound on the Nordtvedt parameter $\eta$, explicitly stating the scaling factor used to relate amplitude to $\eta$ based on the theoretical model.
- **Reproducibility**: Archive all code, data processing scripts, and random seeds in a public repository, ensuring the full pipeline (data download, signal extraction, regression, and simulation) executes on a standard 2-core CPU within 6 hours by optimizing the signal extraction to use vectorized operations.

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: None identified (no existing ideas in corpus to compare).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-09-07T04:08:24Z
**Outcome**: success_after_expansion
**Original term**: Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Exploring the Validity of the Weak Equivalence Principle with Publicly Available Planetary Orbital Data physics | 0 |
| 1 | experimental tests of the weak equivalence principle using planetary ephemerides | 4 |
| 2 | constraints on the universality of free fall from solar system dynamics | 0 |
| 3 | Nordtvedt effect analysis with planetary orbital data | 0 |
| 4 | gravitational redshift and equivalence principle tests in the solar system | 0 |
| 5 | differential acceleration of planetary bodies in the Sun's gravitational field | 0 |
| 6 | post-Newtonian parameter beta and gamma constraints from orbital mechanics | 0 |
| 7 | lunar laser ranging and planetary ephemeris tests of general relativity | 0 |
| 8 | violation of the equivalence principle in alternative gravity theories | 0 |
| 9 | precision tracking of planetary orbits for fundamental physics tests | 0 |
| 10 | Eötvös experiments using astronomical observations | 0 |
| 11 | solar system tests of metric theories of gravity | 0 |
| 12 | equivalence principle constraints from asteroid and comet trajectories | 0 |
| 13 | relativistic effects in planetary motion and equivalence principle validity | 0 |
| 14 | analysis of planetary perihelion precession for equivalence principle violations | 0 |
| 15 | gravitational binding energy and the strong equivalence principle in planetary systems | 0 |
| 16 | solar system constraints on scalar-tensor gravity theories | 0 |
| 17 | testing the inverse square law and equivalence principle with spacecraft telemetry | 0 |
| 18 | public domain planetary orbital data for fundamental physics verification | 0 |
| 19 | equivalence principle tests using the motion of inner and outer planets | 0 |
| 20 | gravitational constant variation and equivalence principle in the solar system | 0 |

### Verified citations

1. **The Eötvös Paradox: The Enduring Significance of Eötvös' Most Famous Paper** (2019). Ephraim Fischbach, Dennis E. Krause. arXiv. [1901.11163](https://arxiv.org/abs/1901.11163). PDF-sampled: No.
2. **Lunar Laser Ranging Science** (2004). James G. Williams, Dale H. Boggs, Slava G. Turyshev, J. Todd Ratcliff. arXiv. [gr-qc/0411095](gr-qc/0411095). PDF-sampled: No.
3. **Gravity at Finite Temperature, Equivalence Principle,and Local Lorentz Invariance** (2021). M. Gasperini. arXiv. [2101.00458](https://arxiv.org/abs/2101.00458). PDF-sampled: No.
4. **Bayesian test of Brans-Dicke theories with planetary ephemerides: Investigating the strong equivalence principle** (2023). Vincenzo Mariani, Olivier Minazzoli, Agnès Fienga, Jacques Laskar, Mickaël Gastineau. arXiv. [2310.00719](https://arxiv.org/abs/2310.00719). PDF-sampled: No.
5. **Theoretical Aspects of the Equivalence Principle** (2012). Thibault Damour. arXiv. [1202.6311](https://arxiv.org/abs/1202.6311). PDF-sampled: No.
