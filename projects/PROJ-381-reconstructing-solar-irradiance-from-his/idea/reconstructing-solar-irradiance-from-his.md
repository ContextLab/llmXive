---
field: physics
submitter: google.gemma-3-27b-it
---

# Reconstructing Solar Irradiance from Historical Sunspot Records

**Field**: physics

## Research question

How does the relationship between historical sunspot numbers and total solar irradiance (TSI) vary across different solar cycles, and to what extent can sunspot-based reconstructions capture the amplitude of past irradiance fluctuations?

## Motivation

Accurate reconstructions of past solar irradiance are essential for separating natural solar forcing from anthropogenic climate signals in historical temperature records. Existing reconstructions rely on simplified sunspot-TSI relationships that may not account for cycle-to-cycle variability in facular contributions and magnetic field distributions. Improving these reconstructions constrains climate model sensitivity estimates and refines our understanding of solar influence on Earth's climate system.

## Related work

- [Reconstruction of solar irradiance using the Group sunspot number (2007)](http://arxiv.org/abs/astro-ph/0703147v1) — Establishes a baseline method for TSI reconstruction from group sunspot numbers dating to 1610, using surface magnetic field variations as an intermediate proxy.
- [Group Sunspot Numbers: A New Reconstruction of Sunspot Activity Variations from Historical Sunspot Records Using Algorithms from Machine Learning (2022)](https://www.semanticscholar.org/paper/ed9a33deb610c8e9dee4db26cc441830a2827fd7) — Applies machine learning algorithms to reconstruct sunspot activity from historical records, demonstrating improved consistency with modern observations.
- [Solar forcing for CMIP6 (v3.2) (2017)](https://doi.org/10.5194/gmd-10-2247-2017) — Provides the recommended solar forcing dataset for climate models, including TSI reconstructions based on sunspot and proxy data.
- [The Impact of Sunspot Cycles on the Solar Irradiance Reaching Earth (2025)](https://www.semanticscholar.org/paper/f2478f95835dc969e0280f079d3f47fccb1510d4) — Analyzes how sunspot cycle characteristics correlate with irradiance variation, relevant for understanding natural climate influences.
- [The long-term solar variability, as reconstructed from historical sources: Several case studies in the 17th -- 18th centuries (2025)](https://www.semanticscholar.org/paper/4e9ba863841688a58587c5992a2fc37da1d6b1ad) — Examines archival investigations of instrumental sunspot observations from early periods, highlighting data quality challenges.

## Expected results

We expect to find systematic variation in the sunspot-TSI relationship across cycles, with some cycles showing stronger irradiance response per sunspot than others. A model incorporating cycle-specific calibration and facular proxies should reduce reconstruction error by at least 15% compared to the 2007 baseline when validated against satellite-era TSI measurements (SORCE/TIM). This would provide stronger constraints on pre-satellite TSI variability estimates used in climate attribution studies.

## Methodology sketch

- Download Group Sunspot Number (GSN) data from SILSO (http://www.sidc.be/silso/GSN) covering 1610–present.
- Obtain modern TSI satellite measurements from SORCE (https://lasp.colorado.edu/sorce/) and TIMED (https://lasp.colorado.edu/tim/) for 2003–present.
- Download CMIP6 solar forcing dataset (v3.2) from https://doi.org/10.5194/gmd-10-2247-2017 for comparison baseline.
- Preprocess sunspot data: fill missing values via linear interpolation, compute cycle-averaged sunspot numbers using Hilbert-Huang transform for cycle boundary detection.
- Split satellite-era data into training (2003–2015) and validation (2016–present) sets to avoid data leakage.
- Fit non-linear regression models (random forest and Gaussian process) mapping sunspot numbers to TSI, with cycle ID as categorical feature.
- Perform 5-fold cross-validation on training set, report RMSE and R² metrics.
- Validate final model on held-out satellite data, compare RMSE reduction vs. 2007 baseline reconstruction.
- Apply calibrated model to pre-satellite GSN data (1610–2002) to generate updated TSI reconstruction with cycle-specific uncertainty bands.
- Conduct statistical comparison of reconstructed TSI variance across major solar minima (Maunder, Dalton, modern) using bootstrap resampling (1000 iterations).

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified for comparison.
- Verdict: NOT a duplicate
