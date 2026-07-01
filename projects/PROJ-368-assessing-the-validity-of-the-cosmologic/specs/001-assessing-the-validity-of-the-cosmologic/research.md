# Research: Assessing the Validity of the Cosmological Principle with Public CMB Data

## Scientific Background

The Cosmological Principle asserts that the universe is homogeneous and isotropic on large scales. Violations of isotropy (anisotropy) would challenge standard ΛCDM cosmology. The Planck 2018 mission provides high-precision CMB temperature maps. Previous studies (e.g., Planck Collaboration 2014 XLVI, Planck 2018 Results. XVI) have investigated "hemispherical power asymmetry," where one hemisphere of the sky appears to have more power than the other. This project implements a rigorous statistical test to quantify this asymmetry using Monte Carlo simulations and a Maximum Statistic approach.

## Dataset Strategy

The primary dataset is the **Planck 2018 SMICA** CMB temperature map.

| Dataset | Description | Source/URL | Verification Status |
|:--- |:--- |:--- |:--- |
| **Planck 2018 SMICA** | CMB temperature map (Nside=2048), µK units. | ** | Verified: ESA Planck Legacy Archive. URL is reachable and accessible. |
| **Commander Mask** | Galactic mask (U73) to exclude foregrounds. | Derived from Planck 2018 release (same archive). | Verified: Standard Planck mask files. |
| **Theoretical ΛCDM** | Power spectrum for generating null simulations. | Planck 2018 best-fit parameters (TT+TE+EE+lensing). | Verified: Planck 2018 Collaboration Paper. |

**Dataset-Variable Fit**: The Planck SMICA map contains the temperature fluctuations required to compute hemispherical variance. No missing variables are anticipated for the primary analysis.

## Methodology

### 1. Data Preprocessing
1. **Download**: Fetch Planck 2018 SMICA map (Nside=2048) from the verified ESA URL. Validate checksum.
2. **Masking**: Apply Commander Galactic mask (U73) to exclude foregrounds. Ensure ≥ 95% sky remains unmasked.
3. **Downgrade**: Reduce resolution to Nside=128 using `healpy.ud_grade`. This reduces pixel count from millions to tens of thousands, fitting within 7 GB RAM and allowing fast CPU computation.

### 2. Spherical Harmonic Analysis
1. **Transform**: Compute spherical harmonic coefficients ($a_{lm}$) from the masked, downgraded map using `healpy.map2alm`.
 * **Critical Step**: Execute `map2alm` with `iter=3` and `lmax=128` to iteratively correct for mask-induced mode coupling, ensuring accurate reconstruction of low-$l$ modes (l=2, 3, 4).
2. **Power Spectrum**: Calculate the angular power spectrum ($C_l$) for $l \in [2, 128]$ using `healpy.alm2cl`.
3. **Hemispherical Split**: Define North/South and East/West hemispheres.
 * **Critical Step**: For each hemisphere (N, S, E, W), compute a **unique effective mask** by intersecting the Galactic mask with the specific hemispherical cut.
 * Compute $C_l$ for each hemisphere independently using a **per-hemisphere pseudo-C_l estimator (MASTER)**. The mode-coupling matrix $M_{ll'}$ is derived separately for each unique effective mask to account for differing sky fractions and geometric biases.
 * *Note on Low-l Modes*: The iterative `map2alm` and distinct MASTER matrices ensure that the mode-coupling effects and geometric biases of the mask at low multipoles (l=2, 3, 4) are correctly modeled, preventing artificial asymmetry.
 * *Simulation Consistency*: For the null distribution, the **exact same unique effective masks** and hemispherical cuts are applied to each simulated isotropic map before computing the statistic. This ensures the shared variance structure and mask geometry are perfectly matched between observed and null.

### 3. Monte Carlo Null Distribution
1. **Generation**: Generate $N$ (e.g., 1000) isotropic Gaussian random field simulations using the theoretical ΛCDM $C_l$ as input to `healpy.synalm` and `healpy.alm2map`.
 * **Circular Validation Avoidance & Systematic Uncertainty**: The theoretical ΛCDM parameters (A_s, n_s, etc.) used here are fixed external constants from the Planck 2018 'TT+TE+EE+lensing' best-fit paper. While derived from the same mission, they are treated as fixed theoretical priors for the null hypothesis. **Limitation Acknowledgement**: Since these parameters are derived from the global fit of the observed map, any hemispherical asymmetry present in the global fit is implicitly "baked in" to the null distribution. The analysis is therefore framed as testing for *excess* asymmetry beyond what is expected from the global best-fit model. This limitation is documented as a systematic uncertainty.
2. **Statistics**: For each simulation, compute the hemispherical power asymmetry statistic.
 * **Test Statistic Definition**: The asymmetry amplitude is defined as $A = \frac{P_N - P_S}{P_N + P_S}$, where $P_N$ and $P_S$ are the integrated power in the North and South hemispheres respectively. This statistic is standard in CMB literature (e.g., Planck 2014 XLVI).
 * **Maximum Statistic**: The primary test statistic for the global test is $T = \max(|A_{NS}|, |A_{EW}|)$. This aggregates evidence from both axes into a single value.
 * **Null Distribution Construction**: Crucially, for each simulation, the **exact same unique effective masks** and hemispherical cuts used for the observed data are applied before computing the statistic. This ensures the shared variance structure and mask geometry are perfectly matched between observed and null. The statistic is computed on the split realization of the *same* simulation, not by comparing independent simulations.
3. **Null Distribution**: Aggregate the $T$ values from all simulations to form the empirical null distribution.

### 4. Hypothesis Testing
1. **Observed Statistic**: Compute $T_{obs} = \max(|A_{NS}^{obs}|, |A_{EW}^{obs}|)$ for the observed data.
2. **P-value**: Calculate the two-tailed p-value: the fraction of simulations where $T_{sim} \ge T_{obs}$.
3. **Multiple Comparisons**: The **Maximum Statistic** approach inherently accounts for the dependence between N/S and E/W tests by controlling the Family-Wise Error Rate (FWER). No Benjamini-Hochberg correction is applied, as it is statistically inappropriate for only two dependent tests.
 * **Trade-off Acknowledgment**: While the Maximum Statistic method is valid for FWER control, it is conservative, potentially increasing the risk of Type II errors (missing a real effect) compared to FDR methods. This trade-off is accepted to ensure valid p-value interpretation.
4. **Sensitivity**: Sweep significance thresholds (2.5σ, 3.0σ, 3.5σ) and document rejection rates.

## Statistical Rigor & Assumptions

* **Multiple Comparisons**: Addressed via the 'Maximum Statistic' approach ($T = \max(|A_{NS}|, |A_{EW}|)$). This controls the family-wise error rate for the global test of isotropy without the misuse of Benjamini-Hochberg.
* **Power Justification**: With N=1000 simulations, the standard error on the p-value is $\sqrt{p(1-p)/N} \approx 0.015$ at $p=0.05$. This is sufficient for a binary rejection decision but limited for precise p-value estimation near 0.001.
* **Causal/Associational**: The analysis is observational. Any detected asymmetry is an *associational* anomaly, not a causal claim.
* **Measurement Validity**: Planck SMICA is the standard component-separated map; validated by Planck Collaboration.
* **Collinearity**: Hemispherical splits share data; independent $C_l$ estimates are not statistically independent. The test compares the *maximum* of the paired differences (or ratios) against the null distribution of maximums, which correctly accounts for the shared variance structure and mask geometry.
* **Low-l Mode Coupling**: Addressed by iterative `map2alm` (iter=3) and distinct MASTER mode-coupling matrices per hemisphere.
* **Systematic Uncertainty**: The use of Planck-derived parameters for the null distribution may bias the null if the global fit was affected by the asymmetry. The test is interpreted as detecting *excess* asymmetry beyond the global model.

## Compute Feasibility

* **Memory**: Nside=128 map is ~52k pixels. Float array is approximately hundreds of kilobytes in size. Even with 1000 simulations, processing one-by-one or in small batches keeps RAM < 1 GB.
* **Runtime**: `map2alm` and `alm2cl` for Nside=128 are sub-second on CPU. Generating a large number of simulations may take a moderate amount of time on A limited number of CPU cores. Total pipeline < 60 minutes.
* **No GPU**: All operations use `healpy` in default CPU mode. No CUDA dependencies.

## Decision Rationale

* **Nside=128**: Chosen to balance angular resolution (high arcmin) with CI constraints. Higher Nside (e.g., 512) would increase memory and runtime significantly without adding value for low-$l$ ($l \le 128$) isotropy tests.
* **MASTER Algorithm**: Essential for masked maps to correct for mode coupling. Naive estimation would bias results.
* **Monte Carlo vs. Analytic**: Analytic variance formulas for masked hemispheres are complex and sensitive to mask geometry. Monte Carlo is the robust, standard approach in CMB literature.
* **Maximum Statistic vs. BH**: Benjamini-Hochberg is designed for controlling the False Discovery Rate in large-scale multiple testing (e.g., thousands of pixels or multipoles). For two dependent tests (N/S and E/W), BH is statistically inappropriate and may lead to incorrect p-value interpretations. The 'Maximum Statistic' approach is the standard robust method for this specific problem in CMB literature, providing valid FWER control despite being conservative.
* **Per-Hemisphere Masks**: Essential to avoid artificial asymmetry caused by the non-symmetric Galactic mask when splitting the sky. Distinct MASTER matrices are required for valid comparison.

