# Research: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Scientific Background
The Cosmological Principle posits that the Universe is statistically homogeneous and isotropic on large scales. Type Ia supernovae (SNe Ia) are standardizable candles that trace the expansion history via their distance moduli. By examining the spatial pattern of residuals—differences between observed and model‑predicted distance moduli—we can test for directional dependence (anisotropy) in the Hubble flow.

## Dataset Strategy
| Dataset | Description | Verified URL | Access Method |
|---------|-------------|--------------|---------------|
| Pantheon+ | Comprehensive SNe Ia compilation with RA, Dec, redshift, distance modulus, and uncertainties. | *No verified URL provided in the specification.* | Manual download from the official Pantheon+ repository (e.g., GitHub `PantheonPlusSH0ES/DataRelease`). |

**Variable Fit Verification**  
Required columns (RA, Dec, redshift *z*, distance modulus μ, uncertainty σ_μ) are present in the official Pantheon+ release. Any rows missing these fields will be excluded and logged (Edge‑Case handling).

## Methodology

### 1. Ingestion & Residual Calculation (FR‑001, FR‑002)
- Download the Pantheon+ file, verify its SHA‑256 checksum, and parse it with `pandas`.  
- Extract cosmological parameters (H₀, Ωₘ, Ω_Λ) from the dataset’s metadata; fall back to the values reported in the Pantheon+ paper if absent.  
- Compute the theoretical distance modulus  
  \[
  \mu_{\rm th}(z)=5\log_{10}\!\bigl[d_L(z)\bigr]+25,\qquad
  d_L(z)=(1+z)\frac{c}{H_0}\int_0^z\frac{dz'}{E(z')}
  \]
  where \(E(z)=\sqrt{\Omega_m(1+z)^3+\Omega_\Lambda}\).  
  Numerical integration uses `scipy.integrate.quad` with tolerance `1e‑6`.  
- Residuals: \(\Delta\mu = \mu_{\rm obs} - \mu_{\rm th}\).  
- Output: `data/processed/residuals.csv` (schema: `residuals.schema.yaml`).

### 2. HEALPix Projection (FR‑003)
- Map each supernova’s sky coordinates (RA, Dec) to a HEALPix pixel using `healpy.ang2pix` with **Nside = 32** (as required).  
- For each pixel compute the mean residual and the number of contributing SNe.  
- Build a mask that marks pixels with at least one observation as valid (value = 1) and others as masked (value = 0).  
- Store the map in a FITS file `healpix_map.fits` (schema: `healpix_map.schema.yaml`).  
- SC‑001 will be measured as the ratio of mapped SNe to the total valid SNe.

### 3. Spherical Harmonic Decomposition (FR‑004)
- Apply the pseudo‑\(C_\ell\) estimator with MASTER mask correction (Hivon et al. 2002) to obtain coefficients \(a_{\ell m}\) for \(\ell\le3\).  
- Compute scalar amplitudes  
  \[
  A_\ell = \sqrt{\frac{1}{2\ell+1}\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2}.
  \]  
- Extract dipole (\(\ell=1\)) and quadrupole (\(\ell=2\)) amplitudes (units: magnitudes).  
- SC‑002 will be verified by reproducing the coefficients on a synthetic subset and comparing to a reference `healpy` implementation.

### 4. Null Distribution via Random Rotations (FR‑005)
- Generate isotropic mock catalogs by applying a random 3‑D rotation matrix to the RA/Dec of every supernova while preserving redshift and uncertainties.  
- Use a fixed random seed (`seed=42`) for reproducibility.  
- For each rotated catalog repeat steps 2‑3 to obtain dipole and quadrupole amplitudes.  
- Continue simulations until either (a) 10 000 realizations are completed, **or** (b) the running mean of the dipole amplitude changes by < 0.001 mag over the last 1 000 simulations (SC‑003).  
- Record results in `simulation_results.csv` (schema: `simulation_results.schema.yaml`).

### 5. Significance Assessment (FR‑006)
- Compute p‑values:
  \[
  p_{\rm dipole} = \frac{N(A_1^{\rm sim} \ge A_1^{\rm obs})}{N_{\rm sims}},\qquad
  p_{\rm quad}   = \frac{N(A_2^{\rm sim} \ge A_2^{\rm obs})}{N_{\rm sims}}.
  \]  
- Flag “statistically significant anisotropy” if \(p_{\rm dipole}<0.05\) (primary test) per SC‑004.  
- Produce `final_report.txt` and a JSON file `analysis_result.json` validated against `analysis_result.schema.yaml`.

## Decision Rationale
- **Flat ΛCDM residuals**: The specification (FR‑002) explicitly requires a flat ΛCDM model; a model‑independent spline would deviate from the mandated approach and is therefore not used.  
- **Pseudo‑\(C_\ell\) with MASTER**: Direct maximum‑likelihood estimators are unnecessary and not requested; the pseudo‑\(C_\ell\) method satisfies FR‑004 while remaining CPU‑friendly.  
- **Random rotations**: Aligns exactly with FR‑005; GRF simulations would not preserve the survey mask and are outside the spec.  
- **Nside = 32**: Required by US‑2; despite sparse sampling, the MASTER correction mitigates bias, and the resolution is kept to honor the spec.  
- **CPU‑only feasibility**: All chosen libraries (`healpy`, `scipy`) run efficiently on the GitHub Actions runner; the simulation loop includes an early‑stop convergence criterion to respect the 6 h runtime budget (SC‑004).

## References
1. Pantheon+ Collaboration, *The Pantheon+ Analysis: Cosmological Constraints* (2021). Official repository: https://github.com/PantheonPlusSH0ES/DataRelease  
2. Healpy Documentation – Spherical Harmonic Analysis. https://healpy.readthedocs.io/  
3. Hivon et al. (2002), “MASTER of the CMB Anisotropy Power Spectrum”, *ApJ*, 567, 2.  

---
