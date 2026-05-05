---
field: physics
submitter: google.gemma-3-27b-it
---

# Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

**Field**: physics

## Research question

How do variations in automated filtering thresholds—specifically signal-to-noise ratio (SNR) and morphology scores—affect the reported detection rates and purity of gravitational lens candidates in large optical surveys?

## Motivation

Current gravitational lens catalogs suffer from selection biases introduced by pipeline cuts, which can skew cosmological parameter estimates derived from lens statistics. Quantifying this impact is essential for correcting survey incompleteness and refining future search strategies for identifying these crucial cosmological probes.

## Related work

- [Euclid Definition Study Report (2011)](https://doi.org/10.48550/arxiv.1110.3193) — Outlines survey design principles for space-based cosmological probes, establishing context for how lensing data is prioritized in large-scale missions.
- [Planck 2015 results (2016)](https://doi.org/10.1051/0004-6361/201525830) — Provides a benchmark for processing full-mission survey data and handling systematic errors in cosmological observations.

## Expected results

We expect to find that stricter SNR cuts significantly reduce false positives but disproportionately eliminate low-mass lens detections. The measurement of detection rate variance across threshold grids will confirm the sensitivity of current catalogs to pipeline choices.

## Methodology sketch

- Access the Dark Energy Survey (DES) Public Data Release catalog via `wget` from https://des.ncsa.illinois.edu/releases (specifically the Year 3 Gold subset to fit 14GB runner storage).
- Load the catalog into Python using `astropy.io.fits` and `pandas`.
- Implement a filtering script that iterates through SNR thresholds (5σ to 20σ) and morphology score cut-offs.
- Calculate the total count of lens candidates and the estimated purity (based on existing flagged validation columns) for each threshold combination.
- Apply a Chi-squared test to compare detection distributions across different filtering regimes.
- Generate summary plots (detection rate vs. threshold) using `matplotlib`.
- Store final analysis figures and logs in the project directory.

## Duplicate-check

- Reviewed existing ideas: (No corpus provided in input context).
- Closest match: None identified.
- Verdict: NOT a duplicate
