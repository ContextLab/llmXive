---
field: physics
submitter: google.gemma-3-27b-it
---

# Assessing the Validity of Modified Newtonian Dynamics (MOND) with Galaxy Rotation Curves

**Field**: physics

## Research question

Can Modified Newtonian Dynamics (MOND) predict observed galaxy rotational velocities as accurately as or better than dark matter halo models when fitted to publicly available rotation curve data from the SPARC database?

## Motivation

Galaxy rotation curves remain one of the strongest observational challenges to the standard ΛCDM cosmological model. MOND offers a compelling alternative by modifying gravitational dynamics at low accelerations without invoking dark matter. This project will provide a quantitative, reproducible comparison of MOND predictions against observational data to assess its viability as a dark matter alternative.

## Related work

- [Modified Newtonian Dynamics (MOND)](http://arxiv.org/abs/2501.17006v1) — Presents the theoretical foundation of MOND and the acceleration scale $a_0$ below which dynamics departs from Newtonian expectations.
- [Slowly rotating gas-rich galaxies in modified Newtonian dynamics (MOND)](http://arxiv.org/abs/1301.5847v1) — Tests MOND predictions on gas-rich dwarf galaxies with lower rotation velocities in their outskirts.
- [Comparing the dark matter models, modified Newtonian dynamics and modified gravity in accounting for the galaxy rotation curves](http://arxiv.org/abs/1703.06282v1) — Directly compares six models including two MOND variants against galaxy rotation curve data.
- [Testing Modified Newtonian Dynamics with Low Surface Brightness Galaxies --Rotation curve fits-](http://arxiv.org/abs/astro-ph/9805120v1) — Demonstrates MOND fits to 15 rotation curves of LSB galaxies with good agreement.
- [The modified Newtonian dynamics-MOND-and its implications for new physics](http://arxiv.org/abs/astro-ph/0701848v2) — Reviews MOND's paradigm and its implications for alternative physics beyond dark matter.

## Expected results

We expect MOND to fit rotation curves of low-acceleration galaxies with comparable or better accuracy than standard dark matter halo profiles (NFW). Residual analysis will quantify systematic deviations, with success measured by reduced chi-squared values below 1.5 across ≥70% of the sample. If MOND fails on high-acceleration systems, this would indicate limits to its universal applicability.

## Methodology sketch

- Download SPARC galaxy rotation curve data from https://astroweb.cwru.edu/SPARC/ using wget/curl.
- Parse data files to extract radial distances, rotational velocities, and uncertainties for each galaxy.
- Filter to galaxies with inclination uncertainties <10° and well-defined rotation curves (≥15 data points).
- Implement MOND radial acceleration relation: $a = a_N / (1 - e^{-\sqrt{a_0/a_N}})$ where $a_N$ is Newtonian acceleration.
- Implement dark matter halo model (NFW profile) with concentration and scale radius as free parameters.
- Fit both models to each galaxy's rotation curve using scipy.optimize.curve_fit with velocity uncertainty weighting.
- Compute goodness-of-fit metrics: reduced chi-squared, AIC, and BIC for model comparison.
- Calculate residual distributions (observed − predicted velocities) across the full sample.
- Perform statistical tests (Kolmogorov-Smirnov) to compare residual distributions between MOND and dark matter models.
- Generate diagnostic plots: rotation curves with fits, residual histograms, and AIC difference scatter plots.

## Duplicate-check

- Reviewed existing ideas: None (this is the first fleshed-out idea in the physics field).
- Closest match: N/A (no prior fleshed-out ideas to compare).
- Verdict: NOT a duplicate
