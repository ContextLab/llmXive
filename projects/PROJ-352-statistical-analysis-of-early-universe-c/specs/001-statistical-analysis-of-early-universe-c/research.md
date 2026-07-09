# Research: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Executive Summary

This research project investigates the presence of non-Gaussian signatures in the Cosmic Microwave Background (CMB) temperature anisotropies that could indicate the existence of topological defects (e.g., cosmic strings) from the early universe. The methodology relies on **Minkowski Functionals (MFs)**—geometric descriptors (Area, Perimeter, Genus)—which are sensitive to the topology of the temperature field. We compare observed MFs from the Planck SMICA map against two null hypotheses: (1) a Gaussian random field ($H_0$) and (2) a Gaussian field with injected cosmic string templates ($H_1$). The analysis uses rigorous mask corrections and shrinkage covariance estimation to ensure statistical validity.

## Dataset Strategy

The analysis relies on the **Planck Legacy Archive**, specifically the SMICA component-separated CMB maps and associated beam/noise products.

| Dataset Name | Description | Source / URL | Access Method |
| :--- | :--- | :--- | :--- |
| **Planck 2018 SMICA CMB Map** | Full-sky CMB temperature map, Nside=128, component separated via SMICA. | https://pla.esac.esa.int/pla/ | HTTP Download (Direct link to `COM_CMB_ILM-NR1-000_R2.01.fits`) |
| **Planck 2018 U73 Mask** | Galactic mask providing ≥95% sky coverage for CMB analysis. | https://pla.esac.esa.int/pla/ | HTTP Download (Direct link to `U73.fits`) |
| **Planck 2018 Beam Transfer Function** | Frequency-dependent beam transfer function for SMICA. | https://pla.esac.esa.int/pla/ | HTTP Download (Direct link to beam files) |
| **Planck 2018 Noise Covariance** | Noise covariance map for SMICA component separation. | https://pla.esac.esa.int/pla/ | HTTP Download (Direct link to noise files) |
| **Planck 2018 Power Spectrum** | Theoretical LCDM power spectrum (TT, TE, EE) for simulation generation. | https://pla.esac.esa.int/pla/ | HTTP Download (Direct link to `plck_plik_lite_TTTEEE_lowl_lowE_v4.clik`) |

*Note: All URLs point to the Planck Legacy Archive (PLA), which is the canonical source for Planck data. The `healpy` library will be used to read these FITS files.*

## Methodology

### 1. Minkowski Functionals (MFs)
Minkowski Functionals provide a complete description of the morphology of a 2D excursion set. For a CMB temperature map $T(\hat{n})$, we define the excursion set $A_\nu = \{ \hat{n} | T(\hat{n}) > \nu \}$, where $\nu$ is a threshold in units of standard deviation ($\sigma$).
The three functionals in 2D are:
1.  **Area ($V_0$)**: Fraction of sky above threshold $\nu$.
2.  **Perimeter ($V_1$)**: Length of the boundary of the excursion set.
3.  **Genus ($V_2$)**: Euler characteristic (number of holes minus number of isolated regions), a measure of topology.

For a Gaussian random field, these functionals have known analytical forms depending only on the power spectrum and the threshold $\nu$. Deviations from these analytical curves indicate non-Gaussianity.

**Mask Correction**: To address edge effects near the Galactic mask, we apply the analytical correction method described by **Schmalzing & Gorski (1998)**. This method uses the Minkowski Functionals of the mask itself to correct the observed MFs, avoiding ad-hoc buffer heuristics that may introduce bias. A 2-pixel buffer zone is retained only for edge-case verification and documentation purposes.

### 2. Simulation Strategy (Null & Alternative Hypotheses)
To establish the statistical significance of observed deviations, we generate two sets of simulations:

**Null Hypothesis ($H_0$): Gaussian Random Fields**
- **Power Spectrum**: Matches the Planck 2018 LCDM best-fit.
- **Beam**: Convolved with the **frequency-dependent Planck beam transfer function** (not a simplified isotropic Gaussian) to match the SMICA map's effective resolution.
- **Noise**: Added using the **SMICA noise covariance map** to match the actual noise properties of the component-separated map.
- **Mask**: The same U73 mask is applied to all simulations.

**Alternative Hypothesis ($H_1$): Gaussian + Cosmic Strings**
- **Template Injection**: We generate additional maps where cosmic string templates are injected at varying tensions ($G\mu \in [10^{-9}, 10^{-7}]$).
- **Beam/Noise**: Same as $H_0$ (Planck beam and noise covariance).
- **Purpose**: This library allows us to compute the likelihood $L_1$ for the Likelihood Ratio Test, enabling the derivation of specific $G\mu$ upper bounds rather than just a generic non-Gaussianity detection.

### 3. Statistical Inference
We compute the vector of MFs $\mathbf{V} = [V_0, V_1, V_2]$ for the observed map and each simulation at thresholds $\nu \in \{-1, -0.5, 0, 0.5, 1\}$.
- **Dimensionality Reduction**: To address the underpowered covariance matrix for 15 data points (5 thresholds x 3 functionals) with N=1,000, we apply **Principal Component Analysis (PCA)** to the MF curves, retaining the top 3-5 principal components.
- **Covariance Estimation**: We compute the sample covariance matrix of the reduced vector using a **shrinkage estimator (Ledoit-Wolf)** to ensure the matrix is well-conditioned.
- **Likelihood Ratio Test (LRT)**: Compare the likelihood of the observed data under $H_0$ versus $H_1$.
  - Metric: $\Lambda = -2 \ln (L_0 / L_1)$.
  - If $H_1$ is not fully populated (e.g., early runs), a Hotelling's $T^2$ test against the $H_0$ mean is used as a fallback for generic non-Gaussianity detection.
- **Constraint**: If $H_0$ is rejected, we derive an upper bound on the cosmic string tension $G\mu$ at 95% confidence by finding the $G\mu$ value in the $H_1$ library that maximizes the likelihood.

## Computational Feasibility & Constraints

### Hardware Constraints (GitHub Actions Free Tier)
- **CPU**: 2 Cores
- **RAM**: ~7 GB
- **Disk**: ~14 GB
- **Time**: ≤ 6 hours

### Mitigation Strategies
1.  **Resolution**: Nside=128 results in $12 \times 128^2 \approx 2$ million pixels. This is manageable in RAM for a single map but requires care for 2,000 simulations.
2.  **Memory Management**: Simulations will be generated, MFs computed, and the map discarded immediately. We will not store all maps in memory. Only the MF vectors (small arrays) and the covariance matrix will be retained.
3.  **No GPU**: All operations use `healpy` (CPU-based) and `numpy`/`scipy`. No CUDA dependencies.
4. **Runtime**: Generating Nside=128 Gaussian maps and computing MFs is computationally intensive on 2 cores. We will optimize by:
    - Using `healpy`'s built-in random map generation (efficient).
    - Processing simulations in batches (e.g., 100 at a time) to manage memory and allow intermediate checkpoints.
    - If runtime exceeds 4 hours, we may reduce to N=500 per hypothesis (still statistically valid for rough bounds) or optimize the MF computation code.

## Validation of Assumptions

- **Assumption**: Nside=128 is sufficient to resolve topological defects.
  - **Validation**: Planck 2015 constraints on cosmic strings ($G\mu \le 10^{-7}$) imply signatures at scales > 2 arcmin. Nside=128 has pixel size ~2.9 arcmin. This is borderline but acceptable for a first-pass constraint, as the beam smoothing (dominated by the Planck beam) resolves the relevant scales.
- **Assumption**: Minkowski Functionals are sensitive to cosmic strings.
  - **Validation**: Literature (e.g., *Hikage et al., 2003*; *Planck 2015 XXIV*) confirms MFs are powerful discriminators for non-Gaussian topological defects.
- **Assumption**: 1,000 simulations provide adequate power.
  - **Validation**: Standard practice in cosmology (N=500-2,000) yields stable covariance estimates for multivariate tests, especially when combined with shrinkage estimators and PCA.

## Risks & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Planck Archive Unavailable** | Pipeline fails. | Retry logic (multiple attempts, exponential backoff). Fallback to local cache if available. |
| **Memory Overflow (>7GB)** | Crash during simulation. | Stream processing: Generate -> Compute MF -> Discard Map. Monitor RAM; abort if >6.5GB. |
| **Runtime > 6h** | CI failure. | Reduce simulation count to N=500 per hypothesis if necessary. Optimize MF computation (avoid loops in Python, use vectorized numpy). |
| **Dataset Mismatch** | Analysis invalid. | Verify checksums and pixel counts immediately after download. |

## References

1.  Planck Collaboration, "Planck 2018 results. I. Overview and the Planck mission", *Astronomy & Astrophysics*, 2020.
2.  Planck Collaboration, "Planck 2015 results. XXIV. Constraints on primordial non-Gaussianity", *Astronomy & Astrophysics*, 2016.
3.  Hikage, C., et al., "Minkowski Functionals of CMB Temperature Fluctuations", *PASJ*, 2003.
4.  Schmalzing, J., & Gorski, K. M., "Minkowski functionals used in the morphological analysis of cosmic microwave background sky maps", *MNRAS*, 1998.
5.  Planck Legacy Archive: https://pla.esac.esa.int/pla/