# Research: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Scientific Background
The Cosmological Principle asserts statistical homogeneity and isotropy on large scales. Type Ia supernovae (SNe Ia) serve as standardizable candles, providing distance‑modulus measurements across the sky. By examining the spatial pattern of residuals (observed − model distance modulus) we can test for directional dependence in the Hubble flow.

## Dataset Strategy
| Dataset | Description | Verified URL | Access Method |
|---------|-------------|--------------|---------------|
| Pantheon+ | a large sample of SNe Ia with RA, Dec, redshift, distance modulus, and uncertainties. | *No verified URL provided in the specification.* | Programmatic download from the official GitHub repository: ` (released under a permissive open license). A Zenodo mirror (DOI ≈ ) will be used when a verified DOI becomes available, satisfying Principle II. |

**Variable Fit Verification**  
The Pantheon+ release contains the required columns (`RA`, `DEC`, `z`, `mu`, `mu_err`). Rows lacking any of these fields will be excluded and logged (edge‑case handling).

## Methodology

### 0. Power‑Analysis Feasibility Study (FR‑001‑FR‑006 support)
1. **Analytic estimate** – Assuming Gaussian residuals with **heteroscedastic** uncertainties \(\sigma_i = \sqrt{\mu_{\text{err},i}^2 + \sigma_{\text{sys}}^2}\) where \(\sigma_{\text{sys}}=0.02\) mag, and a common systematic term, we compute the smallest dipole amplitude detectable at \(p<0.05\) with ≥ 80 % power.  
2. **Pilot Monte‑Carlo** – Generate 10 000 isotropic mock catalogs by random rotations; each mock **samples each supernova’s individual σ_i** and preserves the observed redshift distribution. The 95 th percentile of the resulting dipole amplitudes defines the detection threshold.  
3. **Output** – `data/processed/power_analysis_results.csv` (schema: `power_analysis_results.schema.yaml`). This satisfies SC‑004 (runtime budgeting) and provides a transparent power justification.

### 1. Ingestion & Residual Calculation (FR‑001, FR‑002)
- Download Pantheon+, verify SHA‑256 checksum, parse with `pandas`.  
- Extract cosmological parameters (H₀, Ωₘ, Ω_Λ) from the dataset metadata; fallback to Planck 2018 values if absent.  
- Apply systematic corrections: Milky Way extinction (Schlegel 1998) and 2M++ peculiar‑velocity flow (Carrick et al. 2015).  
- Compute theoretical distance modulus via numerical integration of \(1/E(z)\) (`scipy.integrate.quad`, tol = 1e‑6).  
- Residuals Δμ = μ_obs − μ_th.  
- Write `data/processed/residuals.csv` (validated by `residuals.schema.yaml`).

### 2. HEALPix Projection (FR‑003)
- Map each SN to a HEALPix pixel (Nside = 32) using `healpy.ang2pix`.  
- For each pixel compute the **inverse‑variance‑weighted** mean residual and a mask (1 = used, 0 = masked).  
- Store as `healpix_map.fits` (validated by `healpix_map.schema.yaml`).  
- SC‑001 will be the ratio of mapped SNe to total valid SNe.

### 3. Spherical Harmonic Decomposition & Direct Fit (FR‑004)
- **Primary estimator**: Perform a **mask‑aware weighted‑least‑squares** fit. Construct a design matrix **X** that maps each SN to the three dipole basis vectors and five quadrupole basis vectors; build a full covariance matrix **C = diag(σ_i²) + σ_sys²·1·1ᵀ** (σ_sys = 0.02 mag) to capture correlated systematic error; apply the HEALPix mask **M** (pixels with no data receive zero weight). Solve \((X^\top C^{-1} M X) \beta = X^\top C^{-1} M y\) where \(y\) are the residuals. This explicitly accounts for uneven sky coverage, heteroscedastic uncertainties, and a common systematic term.  
- **Secondary estimator**: Pseudo‑\(C_\ell\) up to ℓ = 3 with MASTER mask correction (Hivon et al. 2002).  
- Validate the pseudo‑\(C_\ell\) pipeline on synthetic full‑sky maps with known injected dipole/quadrupole signals (methodology‑7cc2ffb5).  
- Extract scalar amplitudes \(A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_m |a_{\ell m}|^2}\).  
- SC‑002 is verified by reproducing coefficients on a synthetic subset and comparing to a reference `healpy` implementation.

### 4. Null Distribution via Mask‑Aware Random Rotations (FR‑005)
- Generate isotropic mock catalogs by applying a random 3‑D rotation matrix (seed = 42) **to both** the RA/Dec positions **and** the **survey‑depth (magnitude‑limit) mask** derived from the observed sky‑density map. After rotation, re‑apply the same magnitude cut to enforce the original sky‑dependent selection function while preserving redshift and uncertainty distributions.  
- For each mock repeat Steps 2 & 3, recording dipole and quadrupole amplitudes.  
- **Simulation count**: Enforce a **minimum of 5 000 simulations**. After this floor, continue until **both** (a) the running mean of dipole amplitude changes by < 0.001 mag over the last 1 000 sims **and** (b) the 95 % binomial confidence interval for the estimated p‑value has width ≤ 0.01. If either condition is not met, run up to a hard cap of **20 000 simulations**.  
- Results saved to `simulation_results.csv` (schema: `simulation_results.schema.yaml`), satisfying SC‑003 and guaranteeing adequate tail sampling for a 0.05 significance test.

### 5. Significance Assessment (FR‑006)
- Compute p‑values as the fraction of simulations with amplitude ≥ observed, and report the 95 % binomial confidence interval.  
- Flag “statistically significant anisotropy” if \(p_{\rm dipole}<0.05\) (primary test).  
- Produce `final_report.txt` (validated against `final_report.schema.yaml`) and `analysis_result.json` (validated against `analysis_result.schema.yaml`).  
- Record total runtime; ensure SC‑004 (runtime ≤ 6 h) is satisfied.

## Decision Rationale
- **Flat ΛCDM residuals** are mandated by FR‑002; no alternative model is introduced.  
- **Weighted‑least‑squares** directly accounts for irregular sky coverage, per‑object uncertainties, and a modest common systematic term, fulfilling scientific‑soundness‑f59a770e.  
- **Pseudo‑\(C_\ell\) + MASTER** provides a complementary, CPU‑friendly estimator and mitigates mask‑induced bias.  
- **Mask‑aware rotations** preserve the exact selection function by rotating both positions and the magnitude‑limit mask, satisfying FR‑005 without ignoring sky‑dependent depth variations.  
- **Power analysis** (Phase 0) supplies a quantitative justification for the detection limits, addressing a reviewer‑raised gap and ensuring the study’s interpretability.  
- All steps are **CPU‑first** and respect the 6 h wall‑clock budget; no GPU is required.

## References
1. Pantheon+ Collaboration, *The Pantheon+ Analysis: Cosmological Constraints* (2021). Repository: https://github.com/PantheonPlusSH0ES/DataRelease  
2. Healpy Documentation – Spherical Harmonic Analysis. https://healpy.readthedocs.io/  
3. Hivon et al. (2002), “MASTER of the CMB Anisotropy Power Spectrum”, *ApJ*, 567, 2.  
4. Schlegel, D. J., Finkbeiner, D. P., Davis, M. (1998), “Maps of Dust Infrared Emission…”, *ApJ*, 500, 525.  
5. Carrick, J., et al. (2015), “2M++ Flow Model”.  
6. Planck Collaboration (2018), *Planck 2018 results. VI. Cosmological parameters*.  

---  
*End of Research Document*===