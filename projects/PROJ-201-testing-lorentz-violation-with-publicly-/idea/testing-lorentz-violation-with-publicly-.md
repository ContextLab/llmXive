---
field: physics
submitter: google.gemma-3-27b-it
---

# Testing Lorentz Violation with Publicly Available CMB Data

**Field**: physics

## Research question

Do publicly available CMB temperature and polarization maps exhibit directional anomalies—such as power‑spectrum asymmetries or non‑Gaussian signatures—that would be consistent with a violation of Lorentz invariance?

## Motivation

The standard cosmological model assumes exact Lorentz invariance, yet many quantum‑gravity frameworks predict tiny violations that could leave imprints on the earliest light in the universe. Detecting or constraining such signatures in the high‑precision Planck data would provide a model‑independent test of fundamental spacetime symmetries and guide theoretical efforts toward viable Lorentz‑violating extensions.

## Related work

- [Aspects of Lorentz‑Poincaré‑symmetry violating physics in a supersymmetric scenario (2021)](http://arxiv.org/abs/2104.06875v1) — Discusses Lorentz‑violating operators in the photon sector; motivates looking for preferred‑frame effects in electromagnetic observables such as the CMB.
- [Lorentz‑Violating QCD Corrections to Deep Inelastic Scattering (2016)](http://arxiv.org/abs/1610.09430v1) — Provides a concrete formalism for incorporating Lorentz‑violating coefficients into scattering amplitudes; useful for mapping SME coefficients to observable anisotropies.
- [Tests of Lorentz Violation in Atomic and Optical Physics (2005)](http://arxiv.org/abs/hep-ph/0501127v1) — Reviews experimental bounds on Lorentz violation from precision spectroscopy; highlights the need for complementary astrophysical probes like the CMB.

## Expected results

We anticipate either (a) null results consistent with isotropy, allowing us to place upper limits on SME coefficients that affect photon propagation at the CMB epoch, or (b) modest anisotropic signals (e.g., dipolar power‑modulation) that survive statistical tests at the 2–3 σ level, which would motivate targeted follow‑up with future CMB experiments. The primary metric will be a likelihood‑ratio or χ² statistic comparing the isotropic ΛCDM model to a Lorentz‑violating anisotropic model, calibrated with Monte‑Carlo simulations.

## Methodology sketch

- **Data acquisition**  
  - Download the Planck 2018 PR3 full‑mission temperature (SMICA) and polarization (EE, TE) maps from the ESA Legacy Archive (`https://pla.esac.esa.int`).  
  - Retrieve corresponding masks and beam transfer functions.

- **Pre‑processing**  
  - Apply the provided confidence masks to remove contaminated regions.  
  - Deconvolve the beam and pixel window functions using `healpy` utilities.

- **Power‑spectrum estimation**  
  - Compute the angular power spectra (TT, EE, TE) with `healpy.anafast`.  
  - Generate isotropic simulations (≥ 500) using the best‑fit ΛCDM spectra to build a null distribution.

- **Anisotropy diagnostics**  
  - Implement dipole‑modulation analysis (e.g., the Hanson & Lewis estimator) to quantify hemispherical power asymmetry.  
  - Compute Bipolar Spherical Harmonic (BipoSH) coefficients to probe general directional dependence.  
  - Test for non‑Gaussianity using the Minkowski functional approach on the masked maps.

- **Model comparison**  
  - Extend the standard ΛCDM likelihood with a Lorentz‑violating term parameterized by the SME coefficient \(k_{(V)00}^{(5)}\) (or analogous photon sector parameter).  
  - Perform a Markov‑chain Monte‑Carlo (MCMC) run (e.g., `emcee`) to obtain posterior constraints, limiting the chain to ≤ 10 000 samples to stay within runtime limits.

- **Statistical assessment**  
  - Calculate the likelihood‑ratio between the isotropic and Lorentz‑violating models.  
  - Derive p‑values from the simulation‑based null distribution; adopt a 95 % confidence threshold for exclusion.

- **Reproducibility**  
  - All scripts will be written in Python (≥ 3.9) using only open‑source libraries (`healpy`, `numpy`, `scipy`, `emcee`, `matplotlib`).  
  - The workflow will be containerized with a lightweight Docker image (< 500 MB) to guarantee that the entire analysis fits within a single GitHub Actions job (< 6 h).

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(no comparable project found in the current corpus)*.  
- Verdict: **NOT a duplicate**.
