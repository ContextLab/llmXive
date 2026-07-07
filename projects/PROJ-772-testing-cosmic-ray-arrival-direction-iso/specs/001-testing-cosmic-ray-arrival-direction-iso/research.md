# Research: Testing Cosmic Ray Arrival Direction Isotropy

## 1. Scientific Background

Ultra-High-Energy Cosmic Rays (UHECRs) with energies exceeding $50$ EeV are rare particles whose origins remain one of the major mysteries in astroparticle physics. If their sources are distributed isotropically and their deflection by magnetic fields is negligible, their arrival directions on Earth should reflect an isotropic sky distribution. Conversely, significant anisotropies (clustering or large-scale dipoles) could point to specific astrophysical sources or magnetic field structures.

The analysis focuses on the **Angular Power Spectrum (APS)**, $C_\ell$, which decomposes the sky map into spherical harmonics. For an isotropic sky, the expected $C_\ell$ values are determined by the noise properties (Poisson counting statistics) and the exposure map, not zero. The study tests the null hypothesis ($H_0$): *The arrival directions are isotropic*, against the alternative ($H_1$): *There is a large-scale anisotropy up to multipole $\ell=5$*.

## 2. Dataset Strategy

### 2.1 Data Sources

The project relies on public event catalogs from two major observatories:
1. **Pierre Auger Observatory**: Provides the Southern Hemisphere coverage.
2. **Telescope Array (TA)**: Provides the Northern Hemisphere coverage.

**Verified Sources**:
Per the project's verified dataset constraints, the following specific sources are used:

* **Pierre Auger Observatory**:
 * **Source**: Auger Open Data 2020 Release.
 * **DOI**: ``
 * **URL**: `
 * **Content**: Event catalog (E > 50 EeV) and the corresponding time-integrated Exposure Map.
 * **Version**: Pinned to `2020.1` in `code/config.yaml`.

* **Telescope Array**:
 * **Source**: Telescope Array Public Data Release.
 * **URL**: `
 * **Content**: Event catalog (E > 50 EeV) and Exposure Map.
 * **Version**: Pinned to `2023-01` release date in `code/config.yaml`.

**Variable Fit Check**:
* **Required Variables**: Energy (EeV), Right Ascension (RA), Declination (Dec), Detector ID.
* **Availability**: The specified public releases contain these exact fields for events above the threshold.
* **Constraint**: If the specific public event tables are not accessible, the pipeline will **halt with an error**. No synthetic fallback is permitted for the primary scientific result.

**Exposure map Source**:
* **Source**: The exposure maps provided in the Auger Open Data 2020 release and the TA Public Data release.
* **Rationale**: These are the actual time-integrated exposures for the specific datasets being analyzed, not theoretical models. Using the specific release files ensures systematic errors are minimized.

### 2.2 Data Quality & Pre-processing

* **Energy Cut**: Only events with $E > 50$ EeV will be retained.
* **Coordinate Validation**: Events with NaN or invalid RA/Dec will be logged and excluded.
* **Exposure Handling**: The analysis uses the **Detector Exposure Map** from the specific data release to correct for the fact that neither observatory sees the entire sky with equal efficiency.

## 3. Methodology

### 3.1 Coordinate Transformation (FR-002)
* **Input**: RA (degrees), Dec (degrees).
* **Method**: Convert to HEALPix pixel indices using `healpy.ang2pix` with `nside=64`.
* **Rationale**: HEALPix provides an equal-area pixelization of the sphere, essential for accurate spherical harmonic transforms. Nside=64 yields $\sim 1.1^\circ$ resolution, sufficient for $\ell=5$.

### 3.2 Angular Power Spectrum Computation (FR-003)
* **Input**: HEALPix map of observed events ($N_{obs}$), HEALPix map of expected exposure ($N_{exp}$).
* **Method**:
 1. Generate the **Exposure-Corrected Intensity Map**: $I = N_{obs} / N_{exp}$. (Note: If $N_{exp}=0$, the pixel is masked).
 2. Compute spherical harmonic coefficients $a_{\ell m}$ from the intensity map using `healpy.map2alm`.
 3. Calculate the raw power spectrum $C_\ell^{raw} = \frac{1}{2\ell+1} \sum_m |a_{\ell m}|^2$.
 4. **Subtract Shot Noise**: $C_\ell = C_\ell^{raw} - \frac{1}{N_{tot}}$.
* **Rationale**: For low-count data (~100 events), simple subtraction ($N_{obs} - N_{exp}$) creates non-stationary noise. The intensity map ($N_{obs}/N_{exp}$) combined with explicit shot-noise subtraction isolates the true anisotropy signal from Poisson noise, consistent with standard Auger/TA analysis methods. This avoids the bias where the noise floor is mistaken for anisotropy.

### 3.3 Statistical Significance Testing (FR-004, FR-005)
* **Null Hypothesis Generation**: Generate a sufficient number of Monte Carlo realizations of isotropic events to ensure statistical robustness.
 * Each realization has the same number of events as the observed dataset.
 * Events are distributed **according to the exposure map** (i.e., sampled from the probability distribution $P(\theta, \phi) \propto N_{exp}(\theta, \phi)$). This ensures the simulated data has the exact same geometric bias and noise properties as the real data.
 * For each realization, compute the intensity map ($N_{obs}^{MC}/N_{exp}$), apply the same shot-noise subtraction, and calculate $C_\ell$.
* **Test Statistic**: The maximum $C_\ell$ value across $\ell=1..5$ ($C_{\ell, max}$).
* **Global P-value**:
 $$ p_{global} = \frac{\text{count}(C_{\ell, max}^{MC} \ge C_{\ell, max}^{obs}) + 1}{N_{MC} + 1} $$
 where $N_{MC} = 1,000$.
* **Decision Rule**: Reject $H_0$ if $p_{global} \le 0.05$.
* **Multiple Comparison Correction**: The use of the *maximum* statistic across multipoles inherently corrects for the family-wise error rate (FWER) without needing Bonferroni or Benjamini-Hochberg, as the test statistic is a single scalar derived from the set. This is appropriate because adjacent multipoles are correlated.
* **Statistical Power**: With $N_{MC}=1,000$, the standard error for a p-value of 0.05 is $\approx 0.022$. This is sufficient to make a binary decision at the $\alpha=0.05$ level. The reduced count (vs a substantially larger baseline) is a necessary trade-off to ensure the pipeline completes within the 6-hour CI limit on a 2-CPU runner, as `map2alm` for Nside=64 is computationally expensive.
* **Estimator Properties**: The max-$C_\ell$ statistic is chosen for its robustness in detecting large-scale anisotropies. While the distribution of $C_\ell$ for low-count data is non-Gaussian, the exposure-weighted Monte Carlo simulation correctly models this distribution, allowing for a valid empirical p-value calculation.

## 4. Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (multi-core CPU, substantial RAM).
* **Memory**: The dataset is tiny (< 1 MB). The HEALPix map (Nside=64) is small. The primary memory load is the 1,000 Monte Carlo simulations.
 * Strategy: Process simulations sequentially or in small batches to minimize memory overhead.
 * Estimate: A large number of simulations of a computationally manageable scale is feasible. The bottleneck is the `map2alm` call, but [deferred] calls should complete well within 6 hours (estimated ~2-3 hours).
* **Time Limit**: 6 hours.
 * Projection: < 4 hours total runtime.
* **Dependencies**: `healpy` and `numpy` are CPU-optimized. No GPU required.

## 5. Limitations & Risks

* **Data Availability**: If the specific pinned versions of the Auger or TA data are inaccessible, the pipeline will halt. No synthetic data will be used.
* **Low Statistics**: With a limited number of events, the statistical power to detect small anisotropies is limited. The study is powered to detect *large* scale anisotropies (dipole/quadrupole).
* **Observational Nature**: This is an observational study. Any detected correlation is associational, not causal.
* **P-value Precision**: With $N_{MC}=1,000$, the p-value has a standard error of ~0.022. A result near the 0.05 threshold should be interpreted with caution.

## 6. References

* **Anisotropy of the arrival directions of ultra-high-energy cosmic rays**: arXiv:astro-ph/0507510 (Reference for exposure correction method).
* **Pierre Auger Observatory Open Data 2020**: DOI ``.
* **Telescope Array Public Data**: `.