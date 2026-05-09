---
field: physics
submitter: google.gemma-3-27b-it
---

# Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

**Field**: physics

## Research question

Do causal, non-inflationary phase transitions in the early universe produce distinct, detectable signatures in CMB B-mode polarization that can be statistically distinguished from inflationary gravitational wave signals using existing Planck and BICEP/Keck data?

## Motivation

While inflationary B-modes remain undetected, alternative early-universe scenarios (e.g., phase transitions, topological defects) predict causality-limited tensor spectra with different low-frequency behavior. Identifying or constraining these signatures would either provide evidence for physics beyond standard inflation or tighten bounds on alternative cosmological models, advancing our understanding of the universe's first moments.

## Related work

- [First constraints on causal sources of primordial gravitational waves from BICEP/Keck, SPTpol, SPT-3G, Planck and WMAP $B$-mode data (2026)](https://www.semanticscholar.org/paper/414e7ceb36021fc03ae5c6d9baceced23137d4eb) — Establishes first-ever constraints on non-inflationary tensor sources with causality-limited power spectra at low frequencies.
- [Observable CMB B-modes from cosmological phase transitions (2024)](https://www.semanticscholar.org/paper/34640da36ee2b59bdd1e15d414b17548068822cb) — Demonstrates that tensor perturbations from phase transitions can produce observable B-mode signals distinct from inflation.
- [A Universal CMB $B$-Mode Spectrum from Early Causal Tensor Sources (2026)](https://www.semanticscholar.org/paper/c9b53d9840f323a00284fa9cabdffd9e3d52865f) — Shows that causality-limited, sub-horizon sources produce a universal B-mode spectrum shape regardless of microphysical details.
- [Measurements of Degree-Scale B-mode Polarization with the BICEP/Keck Experiments at South Pole (2018)](https://www.semanticscholar.org/paper/fd0e6ac1854157d2c0694403076a41fb555bbdfc) — Provides degree-scale B-mode measurements from South Pole telescopes targeting inflationary signals.
- [CMB B-mode non-Gaussianity (2016)](https://www.semanticscholar.org/paper/8e9706a14a9892da0e0a5672da5a9f92cedd2745) — Studies constraints on primordial non-Gaussianity involving tensor fluctuations, relevant for distinguishing phase transition signatures.
- [Planck 2015 results (2016)](https://doi.org/10.17863/cam.32861) — Full-mission Planck observations of CMB temperature and polarization anisotropies providing the baseline dataset for this analysis.

## Expected results

If phase transition signatures are present, we expect to detect a statistically significant correlation between observed B-mode power spectra and causality-limited tensor models at low multipoles (ℓ < 100), with evidence strong enough to exclude pure inflationary models at 95% confidence. If null, we will establish tighter constraints on the energy scale of early-universe phase transitions (down to ~10¹⁵ GeV) using existing data, narrowing the viable parameter space for alternative cosmological scenarios.

## Methodology sketch

- Download Planck 2015 full-mission CMB polarization maps (SMICA component-separated B-mode maps) from ESA Planck Archive (https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=SMICA_Pol_2015)
- Download BICEP/Keck 2018 degree-scale B-mode power spectra from the BICEP/Keck collaboration data release (https://bicepkeck.org)
- Preprocess maps to mask Galactic foregrounds using the Planck 70% sky mask, ensuring consistent sky coverage across datasets
- Compute angular power spectra (C_ℓ^BB) from the masked B-mode maps using HEALPix (pyHEALPix library, CPU-compatible)
- Generate theoretical B-mode power spectra for three models: (a) tensor-to-scalar ratio r=0.01 inflation, (b) causality-limited phase transition with energy scale 10¹⁵ GeV, (c) null (lens-only B-modes)
- Fit each theoretical spectrum to observed data using χ² minimization with Markov Chain Monte Carlo (emcee library) over 10⁴ samples to estimate posterior distributions
- Compute Bayes factors comparing phase transition model vs. inflation model vs. null hypothesis using the Savage-Dickey density ratio
- Perform null tests by splitting data into independent sky patches and verifying consistency of signal detection (or lack thereof)
- Generate diagnostic plots: observed vs. theoretical power spectra, posterior distributions for r and phase transition energy scale, Bayes factor contours
- Validate pipeline on simulated CMB maps (from CAMB) to verify sensitivity to phase transition signatures before applying to real data

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (no existing fleshed-out ideas to compare against).
- Verdict: NOT a duplicate
