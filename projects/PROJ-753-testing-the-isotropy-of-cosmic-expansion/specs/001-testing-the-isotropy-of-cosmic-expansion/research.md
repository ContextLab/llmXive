# Research: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

## Dataset Strategy

The analysis relies on the **Pantheon+ Type Ia Supernova Sample**, the current gold standard for low-to-mid redshift cosmology.

| Dataset Name | Source URL | Load Method | Verified Status |
|:--- |:--- |:--- |:--- |
| Pantheon+ (v1.0) | ` | `requests` (GitHub Raw) | **Verified** |

**Dataset Details**:
- **Content**: [deferred] Type Ia supernovae with light-curve fit parameters, redshifts, and distance moduli.
- **Variables Required**: RA, Dec, Redshift ($z$), Distance Modulus ($\mu$), Uncertainty ($\sigma_\mu$).
- **Coverage**: $z \approx 0.01$ to $2.3$.
- **Handling Missing Data**: Entries with missing RA, Dec, or $z$ are filtered out (logged count).

**Note on Data Access**: The dataset is hosted on GitHub. The implementation will fetch the raw CSV via the GitHub Raw content URL to ensure reproducibility and avoid transient repository redirects.

## Methodology

### 1. Data Ingestion and Residual Calculation (FR-001, FR-002)
- **Ingestion**: Parse the Pantheon+ CSV. Filter for valid RA, Dec, $z$, $\mu$.
- **Cosmological Model**: Flat $\Lambda$CDM.
 - Parameters: $H_0 = 67.4$ km/s/Mpc, $\Omega_m = 0.315$, $\Omega_\Lambda = 1 - \Omega_m$ (Default Pantheon+ values if metadata missing).
 - Calculation: $\mu_{th}(z) = 5 \log_{10}(d_L(z)) + 25$.
 - $d_L(z)$ computed via numerical integration of $c / (H_0 \sqrt{\Omega_m(1+z)^3 + \Omega_\Lambda})$ with tolerance $10^{-6}$.
- **Residuals**: $\Delta \mu = \mu_{obs} - \mu_{th}$.

### 2. Anisotropy Signal Quantification via Maximum Likelihood Estimation (FR-003, FR-004)
**Methodological Shift**: Replaced pixel-based harmonic decomposition (MASTER) with a **Maximum Likelihood Estimator (MLE)** for sparse point sources. This avoids the instability of pixelizing [deferred] points onto a grid with <0.5 SN/pixel.

- **Grid Resolution**: A HEALPix grid of **Nside=16** (768 pixels) is used *only* to define the survey mask and for visualization. The MLE operates directly on the point-source coordinates.
- **Model**: The residuals are modeled as $\Delta \mu_i = \mathbf{d} \cdot \hat{n}_i + \mathbf{q} \cdot \hat{n}_i + \epsilon_i$, where $\mathbf{d}$ is the dipole vector, $\mathbf{q}$ is the quadrupole tensor, and $\epsilon_i$ is the noise (measurement error + intrinsic scatter).
- **Likelihood Function**:
 $$ \mathcal{L} = \prod_{i=1}^{N} \frac{1}{\sqrt{2\pi(\sigma_i^2 + \sigma_{int}^2)}} \exp\left( -\frac{(\Delta \mu_i - \mu_{model}(\hat{n}_i))^2}{2(\sigma_i^2 + \sigma_{int}^2)} \right) $$
 where $\sigma_{int}$ is an intrinsic scatter term to be marginalized or fitted.
- **Optimization**: The dipole ($A_1$) and quadrupole ($A_2$) amplitudes are extracted by maximizing $\mathcal{L}$ using `scipy.optimize`.
- **Mask Handling**: The likelihood calculation includes a mask term $M(\hat{n}_i)$ which is 1 if the supernova is within the survey footprint and 0 otherwise. This is handled by only including observed supernovae in the sum.

### 3. Null Distribution and Significance (FR-005, FR-006)
**Methodological Shift**: Replaced "rotating observed data" with "synthetic isotropic field simulation" to correctly account for selection effects.

- **Simulation Strategy**:
 1. **Generate Isotropic Field**: Create a synthetic Gaussian Random Field (GRF) on the full sky with a power spectrum $C_\ell$ that matches the *observed monopole* (variance) of the Pantheon+ residuals. This simulates an isotropic universe with the same noise/scatter properties.
 2. **Apply Static Mask**: Sample this synthetic field at the *exact* RA/Dec coordinates of the observed Pantheon+ supernovae. This effectively applies the static survey selection function to the isotropic field.
 3. **Calculate Amplitudes**: Run the same MLE procedure on this masked synthetic sample to extract the dipole and quadrupole amplitudes.
- **Null Distribution**: Repeat steps 1-3 for $N=10,000$ iterations.
- **P-value Calculation (Look-Elsewhere Effect)**:
 - The test statistic is defined as the **maximum dipole amplitude** found in the observed data (direction not pre-specified).
 - The p-value is the fraction of simulations where the *maximum* simulated dipole amplitude exceeds the observed maximum.
 - If testing a specific pre-defined direction, the standard amplitude comparison is used.
 - **Bonferroni Correction**: If both dipole and quadrupole are tested simultaneously, the significance threshold is adjusted ($\alpha_{adj} = 0.05 / 2$).
- **Threshold**: $p < 0.05$ indicates statistically significant anisotropy.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Addressed via the max-statistic approach for the dipole direction and Bonferroni correction for dipole vs. quadrupole.
- **Causal Inference**: This is an observational study. Claims will be framed as "associational evidence for anisotropy" rather than causal mechanisms.
- **Collinearity**: RA and Dec are independent coordinates; no collinearity issues in the MLE.
- **Power**: With [deferred] supernovae, the statistical power to detect a dipole of amplitude > 0.01 mag is high. The simulation count ensures p-value precision to a sufficient level.
- **Systematic Errors**:
 - *Extinction*: Handled by the SALT2 fitter in the original Pantheon+ release; residuals are extinction-corrected.
 - *Selection Bias*: Mitigated by the GRF + Static Mask simulation. By sampling the isotropic field at the observed positions, we preserve the exact selection function.

## Compute Feasibility

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 14 GB disk).
- **Strategy**:
 - **Streaming Simulation**: The simulation loop computes the dipole/quadrupole amplitudes for each iteration and writes **only the scalar values** (2 floats) to a CSV. It does not store the full synthetic maps. This reduces the disk footprint of [deferred] runs to <1MB and RAM usage to negligible levels.
 - **Parallelization**: Use `multiprocessing.Pool` with `processes=2` (matching the runner's CPU cores) to parallelize the simulation loop.
 - **Libraries**: `healpy` (CPU optimized), `scipy` (CPU native). No GPU required.
 - **Runtime**: Estimated runtime for a substantial number of simulations (MLE on a large dataset) is expected to be within the 6-hour limit on 2 cores.