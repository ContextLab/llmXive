# Research: Testing Lorentz Violation with Publicly Available CMB Data

## Problem Statement

The research question asks whether Planck 2018 PR3 CMB temperature and polarization maps exhibit directional anomalies (power-spectrum asymmetries, non-Gaussian signatures) consistent with Lorentz invariance violation (LIV). This requires testing the isotropic ΛCDM model against an anisotropic model parameterized by Standard Model Extension (SME) coefficients, specifically \(k_{(V)00}^{(5)}\).

## Dataset Strategy

The analysis relies on the Planck 2018 PR3 release. The "Verified datasets" block provided for this project contains specific HuggingFace references for PR3 data in parquet format, but explicitly notes "NO verified source" for the specific SMICA maps required (FITS format). Additionally, the block contains irrelevant LLM training datasets.

| Dataset | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **Planck SMICA (FITS)** | ` (ESA Legacy Archive) | Primary data source for Temperature and Polarization analysis. | **NO Verified Source** in prompt block. *Action: Use ESA directly; flag as known risk.* |
| **Parquet Backup** | ` | *Discarded.* Format mismatch (Parquet vs HEALPix FITS). | Verified URL, but scientifically invalid for this analysis. |
| **LLM Datasets** | `PMATHWORK/...`, `smearle/...` | *Not applicable.* | Verified URLs, but irrelevant to domain. |

**Critical Gap & Mitigation**:
The prompt's verified dataset block does not contain a verified URL for the specific SMICA FITS files required.
* **Action**: The implementation will fetch data directly from the **ESA Legacy Archive** (standard scientific source). The pipeline will fail gracefully with `ERROR_DATA_UNAVAILABLE` if the specific files cannot be retrieved.
* **Justification**: Parquet files are unsuitable for high-resolution HEALPix spherical harmonic analysis. The ESA archive is the canonical source, despite not being in the "Verified" block. The project acknowledges this data resource gap and requires manual verification of the ESA URL structure.

**Note on Irrelevant Datasets**: The MCMC and SME parquet/JSON links in the verified block refer to NLP and LLM training data, not CMB physics. These will **not** be used.

## Methodology & Statistical Rigor

### 1. Data Pre-processing (FR-001, FR-002)
* **Input**: SMICA, EE, TE maps (Nside=2048) from ESA.
* **Masking**: Apply the `COM_Mask_2048.fits` confidence mask.
* **Beam Deconvolution**: Divide observed power spectrum by beam transfer function \(B_\ell^2\) and pixel window function \(W_\ell^2\).
* **Validation**: Verify no NaN values in the masked region.

### 2. Anisotropy Diagnostics (FR-003, FR-004)
* **Power Spectra**: Compute \(C_\ell^{TT}, C_\ell^{EE}, C_\ell^{TE}\) for \(\ell < 200\) using `healpy.anafast`.
* **Dipole Modulation**: Estimate modulation amplitude \(A\) and phase \(\phi\) using the Hanson & Lewis estimator (preliminary screen only).
* **BipoSH**: Calculate Bipolar Spherical Harmonic coefficients \(A_{\ell \ell'}^{LM}\) specifically for **L=2 (Quadrupole)** and **L=3 (Octupole)**.
 * *Rationale*: Theoretical predictions for the photon-sector SME coefficient \(k_{(V)00}^{(5)}\) indicate it primarily induces correlations in these low-L modes. Restricting analysis to \(\ell < 200\) maximizes signal-to-noise and fits memory limits.
* **Null Distribution**: Generate **200** isotropic Gaussian simulations using `healpy.synfast` with the Planck 2018 best-fit ΛCDM spectrum.
 * *Critical Detail*: Simulations must be convolved with the **actual Planck beam transfer function** and **pixel window function**, and have the **actual Planck noise power spectrum** added. This ensures the null distribution includes instrumental systematics.

### 3. Model Comparison & Inference (FR-005, FR-006, FR-007)
* **Forward Model (FR-008)**:
 * The physical mapping is defined as: \( A_{\ell \ell'}^{LM} \approx \alpha_{\ell \ell'}^{LM} \cdot k_{(V)00}^{(5)} \).
 * The factor \(\alpha_{\ell \ell'}^{LM}\) is a geometric coefficient derived from the SME theory and Clebsch-Gordan coefficients.
 * Injection Algorithm: Modify spherical harmonic coefficients \(a_{\ell m}\) of an isotropic map by adding \(k \cdot \alpha \cdot Y_{LM}\) before transforming back to map space.
* **Likelihood Function**:
 * Construct likelihood \(\mathcal{L}(k) \propto \exp(-\frac{1}{2} (A_{obs} - \alpha \cdot k)^T \Sigma^{-1} (A_{obs} - \alpha \cdot k))\).
 * This avoids tautology by using the theoretical \(\alpha\) to link the parameter \(k\) to the observable \(A\).
* **MCMC Sampling**: Use `emcee` to sample the posterior of \(k_{(V)00}^{(5)}\).
 * *Constraint*: Chain length ≤ 10,000 samples.
 * *Convergence*: Monitor Effective Sample Size (ESS). If ESS < 200, issue a warning (SC-002).
* **Multiple Comparisons**: Apply **Benjamini-Hochberg False Discovery Rate (FDR)** correction to the p-values derived from the BipoSH analysis (L=2,3 modes).
* **Causal Framing**: Explicitly state that results are associational (FR-006). No causal claims of LIV will be made without independent verification.

### 4. Non-Gaussianity Check (Edge Cases)
* Implement Minkowski functionals (V0, V1, V2) on the masked maps to detect non-Gaussian artifacts that might mimic anisotropy.

### 5. Computational Feasibility
* **Hardware**: 2 CPU cores, 7 GB RAM.
* **Optimization**:
 * Restrict BipoSH analysis to \(\ell < 200\) (low-ℓ dominance of LIV signal).
 * Limit simulation count to a statistically valid number for low-ℓ p-value estimation.
 * Use `healpy` (C++ backend) for efficient map operations.

## Decision Rationale

* **Why `emcee`?** It is a pure Python/Cython library that runs efficiently on CPU without requiring complex GPU setups. It is well-suited for the low-dimensional parameter space (single SME coefficient) of this problem.
* **Why BipoSH for L=2,3?** BipoSH is the standard formalism for detecting statistical anisotropy. Theoretical predictions for \(k_{(V)00}^{(5)}\) specifically target quadrupole and octupole modes.
* **Why not deep learning?** The spec requires statistical hypothesis testing and precise parameter estimation, which are better served by explicit likelihood models and MCMC.
* **Why ESA Legacy Archive?** It is the canonical source for Planck data in the required FITS/HEALPix format. The parquet file is discarded due to format mismatch.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **ESA Unavailable** | Fatal: Analysis cannot start. | Explicit error handling; project flagged as blocked until data source is verified. |
| **RAM Exceedance** | Job failure on CI. | Restrict analysis to \(\ell < 200\); limit simulations to 200. |
| **MCMC Non-convergence** | Invalid results. | ESS monitoring; fallback to best-effort posterior with warning flag. |
| **False Positives** | Incorrect LIV claim. | Null simulations include realistic noise/beam; FDR correction; Minkowski functional check. |

## References
* Planck Collaboration (2020). "Planck 2018 results. VII. Isotropy and Statistics of the CMB". *Astronomy & Astrophysics*.
* Hanson, D., & Lewis, A. (2010). "Estimators for CMB Anisotropies". *Phys. Rev. D*.
* *Verified Datasets*: See "Dataset Strategy" table above. Note: The project relies on the ESA Legacy Archive despite its absence from the "Verified" block.