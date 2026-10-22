---
field: physics
submitter: google.gemma-3-27b-it
---

# Exploring the Statistical Significance of Fine-Structure Constant Variations  

**Field**: physics  

## Research question  

Do publicly available quasar absorption‑line spectra provide statistically robust evidence for spatial or temporal variations in the fine‑structure constant (α) after rigorously accounting for systematic uncertainties and selection biases?  

## Motivation  

Hints of α varying across the sky or with redshift would challenge the Standard Model and suggest new physics. Prior claims rely on heterogeneous data sets and ad‑hoc error handling, leaving open the possibility that unmodelled systematics drive the signal. A reproducible, fully Bayesian re‑analysis of real quasar spectra can either solidify the evidence for new physics or demonstrate that the observed variations are consistent with measurement noise.  

## Related work  

- [Local and Global Variations of The Fine Structure Constant (2003)](https://arxiv.org/abs/astro-ph/0309273) — Introduces the BSBM varying‑α theory and provides a cosmological framework that motivates empirical searches for spatial/temporal α drift.  
- [High‑precision limit on variation in the fine‑structure constant from a single quasar absorption system (2016)](https://arxiv.org/abs/1609.03860) — Shows the achievable precision on Δα/α from a well‑studied absorber (HE 0515‑4414), serving as a benchmark for pipeline accuracy.  
- [Searching for new physics using high precision absorption spectroscopy; continuum placement uncertainties and Δα/α towards the quasar PHL957 (2024)](https://arxiv.org/abs/2410.00684) — Quantifies key systematic effects (continuum placement, wavelength‑calibration drift) that must be explicitly modelled in any robust α‑variation analysis.  
- [Probing the variability of the fine‑structure constant with the VLT/UVES (2003)](https://arxiv.org/abs/astro-ph/0311280) — Provides a large‑sample VLT/UVES data set and an early methodological baseline; the spectra are publicly released for reuse.  

## Expected results  

The analysis will yield posterior distributions for the fractional change Δα/α in multiple redshift bins and for individual sightlines, derived exclusively from observed line wavelengths and laboratory reference values. A 95 % credible interval that excludes zero will constitute statistically significant evidence for variation; otherwise, the study will set tighter upper limits. Bayes factors will quantify support for (a) a constant α (null), (b) a linear redshift trend, and (c) a dipole spatial pattern.  

## Methodology sketch  

- **Data acquisition** – Download the publicly released VLT/UVES quasar spectra cited in the 2003 VLT/UVES study (e.g., `https://archive.eso.org/wdb/wdb/eso/uves/qso/HE0515-4414.fits`) and additional spectra listed in the 2024 continuum‑placement paper.  
- **Line‑list extraction** – Use `astropy.io.fits` and `specutils` to identify metal absorption lines (Fe II, Mg II, Si IV, etc.), recording observed wavelengths and statistical uncertainties.  
- **Laboratory reference compilation** – Query the NIST Atomic Spectra Database (`https://physics.nist.gov/PhysRefData/ASD/`) via its REST API to obtain rest‑frame wavelengths and their uncertainties for each transition.  
- **Systematic‑error modelling** – Encode known systematics (wavelength‑calibration drift, intra‑order distortions, continuum placement) as nuisance parameters with informative priors taken from the 2024 continuum‑placement study.  
- **Hierarchical Bayesian model (PyMC v5)** –  
  1. *Level 1*: For each absorber, relate observed line positions to a per‑absorber Δα/α, incorporating measurement error and the systematic nuisance terms.  
  2. *Level 2*: Model the collection of per‑absorber Δα/α values under three competing global hypotheses: (a) constant α, (b) linear dependence on redshift, (c) dipole variation across the sky (amplitude + direction).  
  3. Hyper‑parameters: trend slope, dipole amplitude/direction, intrinsic scatter.  
- **Inference** – Run the No‑U‑Turn Sampler (NUTS) with 1 000 warm‑up draws and 2 000 posterior draws per chain (2 chains) to keep runtime < 30 min on a free‑tier runner. Diagnose convergence with R̂ ≈ 1 and effective sample size > 500.  
- **Model comparison** – Estimate marginal likelihoods using bridge sampling (`pymc3-bridge`) and compute Bayes factors between the null and each alternative model.  
- **Independent validation** – Correlate the posterior Δα/α estimates with an external large‑scale‑structure density field from SDSS DR12 (`https://data.sdss.org/sas/dr12/`) using a Spearman rank test; this validation target is independent of the spectroscopic measurements.  
- **Robustness checks** – Repeat the full pipeline after: (a) removing the highest‑redshift absorbers, (b) widening systematic priors, (c) bootstrapping absorbers with replacement. Report how results change.  
- **Reporting** – Generate tables of posterior summaries, corner plots with `arviz`, and a LaTeX manuscript compiled on the runner. All code, environment files, and data‑access scripts will be committed to the repository for full reproducibility.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-22T12:32:32Z
**Outcome**: success_after_expansion
**Original term**: Exploring the Statistical Significance of Fine-Structure Constant Variations physics
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Exploring the Statistical Significance of Fine-Structure Constant Variations physics | 5 |

### Verified citations

1. **Local and Global Variations of The Fine Structure Constant** (2003). D. F. Mota, J. D. Barrow. arXiv. [astro-ph/0309273](astro-ph/0309273). PDF-sampled: No.
2. **High-precision limit on variation in the fine-structure constant from a single quasar absorption system** (2016). Srđan M. Kotuš, Michael T. Murphy, Robert F. Carswell. arXiv. [1609.03860](https://arxiv.org/abs/1609.03860). PDF-sampled: No.
3. **Searching for new physics using high precision absorption spectroscopy; continuum placement uncertainties and $Δα/α$ towards the quasar PHL957** (2024). John K. Webb, Chung-Chi Lee, Dinko Milaković, Darren Dougan, Vladimir A. Dzuba, et al.. arXiv. [2410.00684](https://arxiv.org/abs/2410.00684). PDF-sampled: No.
4. **Fine-tunings in radiative $α$-particle capture on $^{12}$C at astrophysical energies** (2026). Ulf-G. Meißner, Bernard Ch. Metsch, Helen Meyer. arXiv. [2601.11180](https://arxiv.org/abs/2601.11180). PDF-sampled: No.
5. **Probing the variability of the fine-structure constant with the VLT/UVES** (2003). Ralf Quast, Dieter Reimers, Sergei A. Levshakov. arXiv. [astro-ph/0311280](astro-ph/0311280). PDF-sampled: No.
