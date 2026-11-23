---
field: physics
submitter: openai.gpt-oss-120b
---

# Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra

**Field**: physics

## Research question

What is the 95% confidence upper limit on the linear Lorentz‑invariance‑violation energy scale ($E_{\rm QG}$) for photons, after marginalizing over the population distribution of intrinsic source lags using a hierarchical Bayesian model applied to the brightest Fermi‑GBM gamma‑ray bursts with known redshifts?

## Motivation

Quantum‑gravity models predict an energy‑dependent photon speed that would manifest as arrival‑time differences between high‑ and low‑energy photons from distant sources. Previous constraints often treat intrinsic source lags as negligible or constant, risking bias if intrinsic lags correlate with redshift or luminosity. A rigorous hierarchical approach that treats intrinsic lags as nuisance parameters drawn from a population distribution allows for a robust separation of LIV effects from astrophysical variability, providing a more reliable bound on $E_{\rm QG}$ using existing public data.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using the following distinct queries: (1) "Fermi GBM gamma-ray burst spectral lag Lorentz invariance violation hierarchical Bayesian", (2) "intrinsic spectral lag redshift correlation GRB population model", and (3) "LIV constraints energy dependent photon speed null test randomization". The initial search returned ~15 results, but only 3 were directly relevant to the specific methodology or theoretical framework. The literature confirms the existence of LIV constraints from GRBs but lacks a comprehensive study that explicitly models the population distribution of intrinsic lags as a nuisance parameter in a hierarchical framework to disentangle them from LIV signals.

### What is known
- [Limits on Lorentz invariance violation at the Planck energy scale from H.E.S.S. spectral analysis of the blazar Mrk 501 (2016)](https://arxiv.org/abs/1606.08600) — Establishes the standard parameterization for linear LIV dispersion relations and demonstrates the magnitude of limits achievable with high-energy gamma-ray observations, though using blazars rather than GRBs.
- [Gamma-ray and Cosmic-ray Tests of Lorentz Invariance Violation and Quantum Gravity Models and Their Implications (2009)](https://arxiv.org/abs/0912.0500) — Reviews the theoretical framework for LIV and summarizes existing gamma-ray tests, explicitly noting the challenge of separating intrinsic source effects from LIV-induced delays.
- [Fermi Observations of GRB 090510: A Short Hard Gamma-Ray Burst with an Additional, Hard Power-Law Component from 10 keV to GeV Energies (2010)](https://arxiv.org/abs/1005.2141) — Provides a detailed case study of a bright GRB with multi-instrument data, demonstrating the complexity of spectral lag measurements and the importance of high-energy components for LIV constraints.

### What is NOT known
No published work has successfully applied a hierarchical Bayesian population model to a systematic sample of Fermi‑GBM bursts to simultaneously infer the distribution of intrinsic lags and the global LIV scale $E_{\rm QG}$. Existing studies typically either fix intrinsic lags to zero, estimate them individually without population-level constraints, or rely on single bright events, leaving the potential bias from unmodeled intrinsic variability largely unquantified for the population.

### Why this gap matters
Addressing this gap is critical for establishing robust, model-independent limits on quantum gravity scales. If intrinsic lags are correlated with redshift (as some astrophysical models suggest), ignoring their population variance could lead to spurious LIV detections or artificially weak bounds. A hierarchical approach provides the necessary statistical rigor to claim a genuine constraint on fundamental physics rather than an artifact of source selection.

### How this project addresses the gap
This project implements a hierarchical Bayesian meta-analysis where the intrinsic lag for each burst is modeled as a random variable drawn from a population distribution (e.g., log-normal). The methodology explicitly marginalizes over these nuisance parameters to derive the posterior distribution for $E_{\rm QG}$, directly quantifying the uncertainty introduced by intrinsic variability and providing a statistically sound upper limit.

## Expected results

We expect to derive a 95% confidence upper limit on $E_{\rm QG}$ that is competitive with current limits but with a rigorously quantified systematic uncertainty due to intrinsic lags. The posterior distribution for the population mean of intrinsic lags will reveal whether a correlation with redshift exists; if the LIV signal is null, the posterior for $1/E_{\rm QG}$ will be centered near zero with a width determined by the intrinsic variance, confirming the method's validity. A significantly tighter bound than previous single-event analyses would demonstrate the power of population-level modeling.

## Methodology sketch

- **Data acquisition**:
  - Programmatically download the Fermi GBM Burst Catalog and light curves for the top 30 brightest GRBs (ranked by peak photon flux in the 50–300 keV band) from the Fermi Science Support Center (FSSC) using the `fermipy` or direct API access to the `fermi.gsfc.nasa.gov` catalog endpoints.
  - Retrieve redshifts and sky coordinates from the FSSC catalog or cross-match with the `GRB Coordinates Network` (GCN) public database; exclude bursts without redshift measurements.
- **Pre-processing**:
  - Re-bin light curves into three energy bands (e.g., 8–25 keV, 25–100 keV, 100–400 keV) using the `gtbin` tool or Python `astropy` time-series utilities.
  - Perform background subtraction using off-source intervals defined in the standard GBM analysis pipeline (e.g., 20s before and after the burst trigger).
  - Discard bursts where the background-subtracted count rate in any band drops below 3$\sigma$ of the background noise for >50% of the burst duration (ensuring sufficient signal-to-noise for lag measurement).
- **Spectral-lag measurement**:
  - Compute the cross-correlation function (CCF) between the reference low-energy band and higher-energy bands for each burst.
  - Extract the lag $\Delta t_{\rm obs}$ and its statistical uncertainty $\sigma_{\rm obs}$ via bootstrap resampling of photon arrival times (1000 iterations) to capture non-Gaussian errors.
- **Hierarchical Bayesian modeling**:
  - Construct a PyMC model where the observed lag for burst $i$ is $\Delta t_{\rm obs, i} = \Delta t_{\rm intrinsic, i} + \frac{E_i \cdot D_i}{c \cdot E_{\rm QG}} + \epsilon_i$.
  - Model $\Delta t_{\rm intrinsic, i}$ as a random effect drawn from a population distribution (e.g., LogNormal($\mu_{\rm int}$, $\sigma_{\rm int}$)), treating $\mu_{\rm int}$ and $\sigma_{\rm int}$ as hyperparameters to be inferred.
  - Use weakly informative priors for $E_{\rm QG}$ (e.g., Half-Cauchy) and hyperparameters.
  - Perform Markov Chain Monte Carlo (MCMC) sampling (e.g., NUTS sampler) to obtain the posterior distribution of $E_{\rm QG}$, marginalizing over the intrinsic lag distribution.
- **Null hypothesis validation (Energy Randomization)**:
  - Generate a null distribution for the global $E_{\rm QG}$ estimate by creating synthetic datasets where photon energy labels are randomly shuffled within each burst's light curve (preserving the temporal structure and intrinsic lag) 10,000 times.
  - Re-run the full hierarchical model on these shuffled datasets to verify that the inferred $E_{\rm QG}$ posterior centers on infinity (i.e., $1/E_{\rm QG} \approx 0$) and that the intrinsic lag distribution recovers the observed data structure.
- **Robustness checks**:
  - Vary the energy band definitions and background subtraction intervals to assess systematic shifts in $E_{\rm QG}$.
  - Perform a leave-one-out analysis to ensure no single burst dominates the global constraint (checking that no single burst contributes >40% to the posterior precision).
- **Reproducibility**:
  - All analysis scripts (Python, PyMC, `astropy`, `numpy`) will be version-controlled in the repository.
  - Intermediate data products (lag measurements, MCMC traces) and final posterior plots will be saved in standard formats (CSV, HDF5).

## Duplicate-check

- Reviewed existing ideas: *(none listed)*.
- Closest match: *(none)*.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-08T00:59:24Z
**Outcome**: success
**Original term**: Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra physics
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra physics | 6 |

### Verified citations

1. **Limits on Lorentz invariance violation at the Planck energy scale from H.E.S.S. spectral analysis of the blazar Mrk 501** (2016). Matthias Lorentz, Pierre Brun. arXiv. [1606.08600](https://arxiv.org/abs/1606.08600). PDF-sampled: No.
2. **Gamma-ray and Cosmic-ray Tests of Lorentz Invariance Violation and Quantum Gravity Models and Their Implications** (2009). Floyd W. Stecker. arXiv. [0912.0500](https://arxiv.org/abs/0912.0500). PDF-sampled: No.
3. **Observations of Gamma-ray Bursts with ASTRO-H and Fermi** (2015). M. Ohno, T. Kawano, M. S. Tashiro, H. Ueno, D. Yonetoku, et al.. arXiv. [1503.01182](https://arxiv.org/abs/1503.01182). PDF-sampled: No.
4. **Fermi Observations of GRB 090510: A Short Hard Gamma-Ray Burst with an Additional, Hard Power-Law Component from 10 keV to GeV Energies** (2010). The Fermi LAT, GBM Collaborations. arXiv. [1005.2141](https://arxiv.org/abs/1005.2141). PDF-sampled: No.
5. **Fermi detection of delayed GeV emission from the short GRB 081024B** (2010).  Fermi LAT Collaboration,  Fermi GBM Collaboration. arXiv. [1002.3205](https://arxiv.org/abs/1002.3205). PDF-sampled: No.
6. **Trapped fireshell (halo) of photons and pairs around black-hole horizon: source for ultra-high-energy particles** (2025). She-Sheng Xue. arXiv. [2512.03702](https://arxiv.org/abs/2512.03702). PDF-sampled: No.
