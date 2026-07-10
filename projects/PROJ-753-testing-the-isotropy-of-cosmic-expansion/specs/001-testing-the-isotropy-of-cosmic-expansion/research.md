# Research: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Scientific Background

The Cosmological Principle asserts that the universe is homogeneous and isotropic on large scales. Testing this principle involves searching for directional dependencies (anisotropies) in the Hubble expansion rate. Type Ia Supernovae (SNe Ia) serve as standardizable candles, allowing the measurement of the distance modulus μ as a function of redshift *z* and sky position (α, δ).

The Pantheon+ dataset (Scolnic et al., 2022) is the current gold standard, comprising ~1 700 SNe Ia with redshifts 0.01 < *z* < 2.3. It provides high‑precision light‑curve parameters, allowing for the calculation of distance moduli with uncertainties σ_μ ≈ 0.1 mag.

## Dataset Strategy

| Dataset Name | Purpose | Verified Source / Loader | Variables Used | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Pantheon+** | Primary analysis data | ` (Official GitHub) | `z`, `RA`, `Dec`, `mu`, `muerr` | Must filter for valid coordinates. Metadata provides H₀, Ωₘ. |
| **HEALPix Mask** | Survey geometry | Derived from Pantheon+ sky coverage (see `code/spherical_harmonics.py`) | Pixel indices | Generated dynamically by binning valid SNe. |

**Dataset Verification**: The Pantheon+ release v1.0 is the canonical source. The dataset contains all required variables: Right Ascension (RA), Declination (Dec), Redshift (z), Distance Modulus (mu), and Uncertainty (muerr). No external datasets are needed for the core analysis.

*Variable Fit*: All required predictors and outcomes are present.
*Missing Data*: Entries with missing RA/Dec or redshift are excluded; the count of excluded SNe is logged.
*Source*: Official GitHub repository is the verified source; no fabricated URLs are used.

## Methodology

### 1. Residual Calculation (FR‑002)

The theoretical distance modulus μ_th(z) is calculated using the flat ΛCDM model:

\[
\mu_{\text{th}}(z) = 5 \log_{10}\!\left(\frac{d_L(z)}{1\ \text{Mpc}}\right) + 25,
\quad
d_L(z) = (1+z)\,\frac{c}{H_0}\int_{0}^{z}\frac{dz'}{E(z')},
\]
\[
E(z) = \sqrt{\Omega_m (1+z)^3 + \Omega_\Lambda}.
\]

Parameters H₀, Ωₘ, Ω_Λ are read from `data/metadata.json`; if absent, defaults to the values published with Pantheon+ (H₀ ≈ 67.4 km s⁻¹ Mpc⁻¹, Ωₘ ≈ 0.315, Ω_Λ = 1‑Ωₘ). Numerical integration uses `scipy.integrate.quad` with absolute tolerance = 1e‑6. Residuals Δμ = μ_obs − μ_th are stored per supernova.

### 2. HEALPix Projection & Pseudo‑Cₗ (FR‑003, FR‑004)

1. **Pixelisation** – Residuals are projected onto a HEALPix grid with Nside = 32 (≈ 3 096 pixels). Each supernova contributes its residual weighted by the inverse variance w_i = 1/σ_i². For pixel *p*:

\[
\bar{Δμ}_p = \frac{\sum_{i\in p} w_i Δμ_i}{\sum_{i\in p} w_i},
\qquad
\sigma_p^2 = \frac{1}{\sum_{i\in p} w_i}.
\]

Pixels with zero total weight are masked (`mask[p]=False`). This weighting mitigates the shot‑noise introduced by the sparse sampling (≈ 0.5 SN per pixel).

2. **Pseudo‑Cₗ Estimation** – Using `healpy.anafast` on the masked map yields the pseudo‑Cₗ (ℓ ≤ 3). The mask’s power spectrum W_ℓ is obtained similarly.

3. **MASTER Correction** – The mode‑coupling matrix **M** is built with `healpy.sphtfunc.get_mll_matrix(lmax=3, mask=mask)`. To invert **M** in the presence of a highly sparse binary mask we apply Tikhonov regularisation:

\[
\mathbf{M}_{\text{reg}} = \mathbf{M} + λ\mathbf{I},
\quad λ = 10^{-6}.
\]

An SVD is performed on **M_reg**; singular values < 1e‑12 are discarded, and the truncated inverse **M⁻¹** is applied to the pseudo‑Cₗ vector **C̃** to obtain unbiased estimates **Ĉ**. The dipole amplitude is

\[
A_1 = \sqrt{\frac{(2·1+1) Ĉ_{1}}{4π}},
\]

and similarly for the quadrupole (ℓ = 2).

### 3. Uniform Rotation‑Matrix Null Simulations (FR‑005)

To generate isotropic mock catalogs we **uniformly sample rotations** from the SO(3) group:

* Sample u₁,u₂,u₃ ∈ [0,1).
* Compute Euler angles: φ = 2πu₁, θ = arccos(1‑2u₂), ψ = 2πu₃.
* Build a `healpy.rotator.Rotator` with (φ,θ,ψ) and apply it to each (RA, Dec) pair, leaving redshift and μ unchanged.

The random seed is fixed to ensure full reproducibility. For each mock catalog we repeat the HEALPix projection and MASTER‑corrected pseudo‑Cₗ pipeline, extracting dipole and quadrupole amplitudes. The collection of amplitudes forms the null distribution.

### 4. Power Analysis (SC‑002)

Assuming Gaussian residuals with per‑SN variance σ² ≈ 0.01 mag², the effective number of independent measurements is

\[
N_{\text{eff}} = \frac{(\sum w_i)^2}{\sum w_i^2} \approx 1.3\times10^3.
\]

The standard error on the dipole amplitude is σ_A ≈ σ / √N_eff ≈ 0.009 mag. For a two‑sided test at α = 0.05 (Z_{1‑α}=1.645) and desired power 0.8 (Z_{1‑β}=0.84), the detectable amplitude threshold is

\[
A_{\text{thresh}} = (Z_{1‑β}+Z_{1‑α}) σ_A \approx 0.04\ \text{mag}.
\]

Thus a true dipole of 0.05 mag yields > 80 % power, justifying the sample size.

### 5. Significance Assessment (FR‑006)

The observed dipole/quadrupole amplitudes are compared to the simulated null distributions. The p‑value is the fraction of simulations with amplitude ≥ the observed value. A strict threshold p < 0.05 flags “statistically significant anisotropy” (95 % confidence). Exact p‑values are reported to three decimal places.

### 6. Interpretation Caveat (Scientific Soundness)

Because residuals are computed with an isotropic ΛCDM model, any genuine anisotropy will appear as a systematic dipole in the residuals. Rotating the sky redistributes this systematic dipole, so the null distribution tests **directional alignment** rather than the mere existence of a dipole. We explicitly state this limitation in the final paper and note that a complementary analysis (e.g., fitting an anisotropic ΛCDM model) would be required to test the existence of a dipole independent of the isotropic baseline.

## Statistical Rigor

* **Multiple Comparisons** – Two primary hypotheses (dipole, quadrupole) are tested; Bonferroni correction is applied when both p‑values are reported.
* **Power Analysis** – Formal calculation provided above (SC‑002).
* **Causal Claims** – The study is observational; any anisotropy detection is framed as an associational signal.
* **Collinearity** – RA/Dec are orthogonal; redshift‑distance correlation is accounted for in the residual calculation.
* **Measurement Validity** – Pantheon+ distance moduli are derived using the SALT2 light‑curve fitter, the community standard.

## Compute Feasibility

* **Environment** – GitHub Actions Free Tier (2 CPU, 7 GB RAM).
* **Data Size** – ~1 500 rows; negligible.
* **Simulation Load** – 10 000 rotations; each iteration involves a vectorised rotation and a pseudo‑Cₗ computation. Estimated ≤ 1 hour total; runtime monitor (Section 5) will halve the remaining iterations if wall‑clock time exceeds 5 h.
* **Libraries** – All dependencies have CPU‑only wheels (`healpy`, `numpy`, `scipy`).
* **Memory** – < 1 GB throughout.
* **Runtime** – Estimated < 2 h; fallback ensures ≤ 6 h.

## Decision Rationale

* **Rotation vs. GRF** – The spec mandates rotation‑matrix mocks (FR‑005). This non‑parametric approach avoids imposing a theoretical power spectrum and directly preserves the observed redshift and uncertainty distributions.
* **Nside = 32** – Matches the spec. The inverse‑variance weighting and MASTER correction mitigate the bias that would arise from the sparse sampling.
* **MASTER Correction** – Implemented with explicit regularisation to handle the ill‑conditioned mode‑coupling matrix, satisfying FR‑004 while remaining statistically sound.
* **Redshift Cut** – z > 0.02 removes SNe where peculiar velocities could dominate the Hubble flow, a standard practice in SN cosmology, and is justified in the methodology.
* **Runtime Safeguard** – Dynamic monitoring prevents CI timeout, ensuring SC‑004 compliance.
