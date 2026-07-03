# Research: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Research Question
*Can Minkowski Functionals computed on the Planck SMICA temperature map reveal statistically significant deviations from the Gaussian random‑field null hypothesis expected under standard inflation, thereby constraining the energy scale (tension Gμ) of cosmic strings or other topological defects?*

## Methodology Overview
1. **Data Acquisition** – Retrieve the Planck 2015/2018 SMICA temperature map (Nside = 128) from the **Planck Legacy Archive**. Validate integrity via SHA‑256 checksum recorded in `data/manifest.yaml`.  
2. **Masking** – Apply the official Planck Galactic mask (available from the same archive). Enforce ≥95 % sky coverage; discard boundary pixels using a 2‑pixel buffer as per the edge‑case specification.  
3. **Minkowski Functional Computation** – Compute area, perimeter, and genus across five standardized temperature thresholds (±0.5σ, ±1σ, 0σ). Use healpy’s pixel‑based estimators; round results to six decimal places.  
4. **Gaussian Simulations** – Generate a sufficient number of Gaussian random‑field realizations matching the observed TT power spectrum (`Cl_TT` from Planck 2015). Each map is beam‑smoothed (Gaussian FWHM ≈ 5′) and injected with white noise (σ² = 1.1 µK² arcmin). Simulations are produced with `healpy.synfast` and a fixed random seed for reproducibility.  
5. **Covariance Estimation** – For each threshold, compute the empirical covariance matrix of the three functionals across the simulation ensemble.  
6. **Statistical Comparison** – Conduct a multivariate Hotelling’s T² test (α = 0.05) comparing the observed functional vector to the simulation mean, accounting for the full covariance. P‑values are reported with ≥6 decimal precision.  
7. **Interpretation** – If the null hypothesis is rejected, translate the significance into an upper bound on Gμ using the analytic relationship described in *Planck 2015 results XXIV* (Eq. 5.12). Otherwise, report the 95 % confidence upper limit.

## Dataset Strategy
| Role | Dataset | Source (Verified) | Access Method | Notes |
|------|---------|-------------------|---------------|-------|
| Primary CMB map | Planck 2015/2018 SMICA temperature map (Nside = 128) | Planck Legacy Archive (no URL provided in verified block) | HTTP GET via `urllib.request` → saved to `data/raw/` | SHA‑256 checksum recorded; retry logic with exponential backoff (1 s, 2 s, 4 s). |
| Galactic mask | Planck official Galactic mask (Nside = 128) | Planck Legacy Archive | Same download routine | Integrity checked; mask applied with 2‑pixel buffer. |
| Power spectrum | Planck 2015 TT angular power spectrum (`Cl_TT`) | Planck Legacy Archive – `planck_likelihood/` files | Load via `astropy.io.fits` | Used as input to `healpy.synfast`. |
| Gaussian simulations | Synthetic maps generated on‑the‑fly | No external source – produced by pipeline | `healpy.synfast` with beam & noise | 1 000 realizations; adaptive down‑sampling to 500 if RAM >6.5 GB. |

*No alternative datasets are used; any missing source would be flagged as a fatal mismatch.*

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not required; Hotelling’s T² inherently accounts for the three correlated functionals (Principle VI). |
| Power / sample‑size justification | A large number of simulations – consistent with standard cosmological practice (N ≈ 500–2 000) – will be run. and provide stable covariance estimates; if RAM constraints force 500 simulations, a power limitation will be noted in the final report. |
| Causal‑inference framing | The analysis is observational; results are presented as **associational constraints** on defect tension, respecting Principle VI. |
| Measurement validity | Planck SMICA map and mask are the gold‑standard CMB products; beam and noise parameters are taken directly from Planck 2015 instrument papers (cited in `research.md`). |
| Predictor collinearity | The three Minkowski Functionals are known to be correlated; the covariance matrix is explicitly used in the Hotelling test, satisfying the collinearity requirement. |

## Decision / Rationale for Compute‑Friendly Choices
- **Resolution (Nside = 128)** – Chosen per the specification; balances angular fidelity with memory constraints.  
- **Simulation Count** – 1 000 provides a well‑conditioned covariance; the pipeline monitors RAM and will fall back to 500 simulations if needed, preserving feasibility on the free‑tier runner.  
- **Hotelling’s T²** – Implemented via `scipy.stats` (no heavy external libraries).  
- **Parallelism** – Simulations are generated in batches using Python's `concurrent.futures.ThreadPoolExecutor` (IO‑bound) and `ProcessPoolExecutor` (CPU‑bound) limited to a small number of workers to respect the 2‑CPU limit.

## Expected Deliverables
- `data/processed/minkowski_observed.csv` – observed functional values.  
- `data/processed/minkowski_sims.csv` – simulated functional values (A substantial number of × 3 × thresholds. 

The research question is: Can a thresholding approach improve the performance of [redacted for brevity]?
The method is: We will implement a thresholding approach on [redacted for brevity] and compare its performance to [redacted for brevity].
References: [redacted for brevity] (DOI/arXiv/author-year).).  
- `data/processed/minkowski_covariance.npy` – covariance matrix per threshold.  
- `data/processed/hotelling_result.json` – T² statistic, p‑value, degrees of freedom.  
- `report.md` – concise narrative with all numeric results, confidence intervals for Gμ, and a PNG plot (`figures/mf_comparison.png`).  

---
