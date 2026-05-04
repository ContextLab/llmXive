---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Statistical Properties of Simulated Black Hole Mergers

**Field**: physics

## Research question

Do the statistical distributions of inferred black hole spins and mass ratios in the GWTC-1 and GWTC-2 catalogs align with population predictions derived from cosmological simulations like IllustrisTNG and EAGLE?

## Motivation

Discrepancies between observed merger populations and formation simulations highlight gaps in our understanding of binary evolution and gravitational waveform modeling. Quantifying these differences constrains astrophysical models and improves the accuracy of parameter estimation for future gravitational wave detections.

## Related work

- [GWTC-1: A Gravitational-Wave Transient Catalog of Compact Binary Mergers Observed by LIGO and Virgo during the First and Second Observing Runs (2019)](https://doi.org/10.1103/physrevx.9.031040) — Provides the baseline observed merger catalog and posterior samples for statistical comparison.
- [The IllustrisTNG simulations: public data release (2019)](https://doi.org/10.1186/s40668-019-0028-x) — Offers cosmological simulation data to model merger formation rates and environmental context.
- [GWTC-2: Compact Binary Coalescences Observed by LIGO and Virgo during the First Half of the Third Observing Run (2021)](https://doi.org/10.1103/physrevx.11.021053) — Expands the observational dataset to improve statistical significance of population inference.
- [The EAGLE project: simulating the evolution and assembly of galaxies and their environments (2014)](https://doi.org/10.1093/mnras/stu2058) — Provides an alternative hydrodynamical simulation framework for cross-validating merger rate predictions.

## Expected results

We expect to identify specific regions in the mass-ratio and spin parameter space where simulation-based population models diverge from the GWTC observational posteriors. This will be confirmed by a Kolmogorov-Smirnov test yielding a p-value below 0.05 for at least one parameter dimension, indicating a statistically significant mismatch.

## Methodology sketch

- Download GWTC-1 and GWTC-2 posterior samples from the Zenodo repositories associated with the provided DOIs (e.g., 10.5281/zenodo.3966973).
- Download merger rate data and subgrid physics parameters from the IllustrisTNG public release (Zenodo 10.5281/zenodo.3566863).
- Preprocess data using Python (Pandas/NumPy) to extract component masses, mass ratios, and effective spins.
- Compute 1D and 2D kernel density estimates (KDE) for the observational and simulation datasets.
- Apply the Kolmogorov-Smirnov test to compare the empirical cumulative distribution functions of key parameters.
- Visualize distributions using Matplotlib to highlight regions of convergence or divergence.
- Run the full pipeline on a single CPU core to ensure compatibility with GitHub Actions free-tier limits.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: N/A.
- Verdict: NOT a duplicate
