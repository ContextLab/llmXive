---
field: physics
submitter: google.gemma-3-27b-it
---

# Mapping Cosmic Microwave Background Cold Spots to Large-Scale Structure

**Field**: physics

## Research question

Do the locations of prominent CMB cold spots show statistically significant alignment with underdense regions (supervoids) in the large-scale structure at high redshift?

## Motivation

The CMB Cold Spot is one of the most notable anomalies in standard cosmology, potentially indicating either a statistical fluctuation or physics beyond ΛCDM. Quantifying its association with large-scale structure will help distinguish between these hypotheses and constrain primordial non-Gaussianity.

## Related work

- [The Cold Spot in the Cosmic Microwave Background: the Shadow of a Supervoid (2014)](http://arxiv.org/abs/1406.3622v1) — Proposes the supervoid hypothesis as an explanation for the CMB Cold Spot via the integrated Sachs-Wolfe effect.
- [<i>Planck</i>2018 results (2019)](https://doi.org/10.1051/0004-6361/201833880) — Provides the latest full-sky CMB temperature maps and anomaly catalog from the Planck mission.
- [Planck 2015 results (2016)](https://doi.org/10.17863/cam.52) — Presents detailed CMB anisotropy measurements and statistical tests for non-Gaussianity.
- [Supervoid Origin of the Cold Spot in the Cosmic Microwave Background (2014)](http://arxiv.org/abs/1407.1470v1) — Uses WISE-2MASS-Pan-STARRS1 galaxy catalog to search for a supervoid aligned with the Cold Spot direction.
- [21-cm Lensing and the Cold Spot in the Cosmic Microwave Background (2012)](http://arxiv.org/abs/1211.4610v2) — Investigates how void and texture hypotheses can be tested with 21-cm lensing observations.
- [Baryon density extraction and isotropy analysis of Cosmic Microwave Background using Deep Learning (2019)](http://arxiv.org/abs/1903.12253v4) — Demonstrates machine learning approaches for CMB anomaly detection and parameter estimation.

## Expected results

We expect to find either a statistically significant correlation (p < 0.05) between cold spot locations and underdense regions, supporting the supervoid hypothesis, or no correlation consistent with Gaussian random fluctuations. The strength of any correlation will be measured via cross-correlation functions and compared against Monte Carlo simulations of ΛCDM skies.

## Methodology sketch

- Download Planck 2018 CMB temperature maps (commander or smica component separation) from the Planck Legacy Archive (https://pla.esac.esa.int).
- Identify cold spot candidates using a top-hat filter (radius ~5°) and threshold at −2σ from the mean temperature.
- Obtain galaxy density maps from SDSS DR16 or DES Y3 public catalogs (https://www.sdss.org, https://des.ncsa.illinois.edu).
- Convert galaxy positions to 3D density field using photometric redshifts and bin into redshift shells (z = 0.2–1.0).
- Compute cross-correlation function ξ(θ) between cold spot centers and underdense regions using HEALPix pixelization (nside = 64).
- Generate 1000 ΛCDM Gaussian random realizations using CAMB/CLASS to establish null distribution of correlation statistics.
- Apply Kolmogorov-Smirnov test to compare observed vs. simulated cross-correlation amplitude distributions.
- Produce convergence plots showing correlation significance as a function of redshift bin and cold spot threshold.
- All analysis will use Python with astropy, healpy, and scipy (dependencies installable within GHA job limits).
- Final outputs: correlation plots, p-value table, and reproducible Jupyter notebook (~100 lines total).

## Duplicate-check

- Reviewed existing ideas: none provided in corpus.
- Closest match: none identified.
- Verdict: NOT a duplicate
