# Research: Quantifying the Impact of Data Gaps on Reconstructed CMB Maps

## Summary

This research validates the feasibility of simulating CMB data gaps, applying gap-filling algorithms, and quantifying parameter bias within strict computational constraints. The study relies entirely on **simulated data** generated via `camb` and `healpy`, avoiding the need for external, unverifiable datasets. The primary challenge is balancing statistical power (number of realizations) against the fixed runtime limit on CPU-only hardware.

## Dataset Strategy

The study does **not** rely on external observational datasets (e.g., Planck raw data) for the core analysis, as the research question concerns the *systematic impact of gaps* which is best isolated using controlled simulations.

| Dataset Name | Source/URL | Access Method | Variables Needed | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Simulated CMB Maps** | Generated via `camb` (local) | `camb.get_cl()` + `healpy.synfast` | Temperature (T), E-mode, B-mode, Ground-truth (H₀, Ωₘ, nₛ, τ) | **Verified**: `camb` is open-source and deterministic. |
| **Gap Masks** | Generated locally | Custom Python scripts | Binary mask (0=observed, 1=gap), Fraction, Morphology | **Verified**: Synthetic generation. |
| **Pre-computed Likelihood Grid** | Generated locally (pilot) | `camb` + `numpy` | Cℓ vs. Parameters | **Verified**: Derived from `camb` theory spectra. |
| **Null Model Baseline** | Generated locally | Custom Python scripts | Random gaps uncorrelated with signal | **Verified**: Synthetic generation. |

**Note**: No external URLs are cited for datasets because the "Verified datasets" block for this project (as per the spec's assumptions) confirms that the Planck Legacy Archive provides parameters but the study generates its own maps to control gap variables precisely. External observational data would introduce uncontrolled systematic noise, confounding the gap-bias measurement.

## Algorithm & Methodology Review

### Gap-Filling Algorithms (FR-002)

1.  **Harmonic Interpolation**:
    *   *Method*: Solve Laplace equation in harmonic space. Fast, deterministic.
    *   *CPU Feasibility*: High. Uses sparse linear algebra (`scipy.sparse`).
    *   *Reference*: Standard technique in CMB analysis (e.g., Eriksen et al.).
2.  **Wiener Filtering**:
    *   *Method*: Optimal linear estimator minimizing MSE given signal and noise power spectra.
    *   *CPU Feasibility*: Moderate. Requires iterative inversion of covariance matrices. Implemented via `PyWiener` or custom `scipy` solver.
    *   *Reference*: Tegmark et al. (1997).
3.  **Iterative Harmonic Synthesis**:
    *   *Method*: Iteratively fill gaps using harmonic constraints and update noise estimates.
    *   *CPU Feasibility*: Moderate/High. May require more iterations.
    *   *Reference*: Starck et al. (2007) or similar inpainting methods.

**Rationale**: These three methods represent a spectrum from fast/heuristic (Harmonic) to optimal/statistical (Wiener) to iterative/refined (Synthesis). All are available in Python and run on CPU.

### Parameter Estimation & Bias Quantification (FR-004, FR-009)

*   **Method**: **Corrected** Fisher Matrix Analysis.
*   **Justification**: Full MCMC (CosmoMC) is too slow for a large number of realizations on CPU. Fisher matrix provides a Gaussian approximation of the posterior.
*   **Critical Correction (FR-009)**: Gap-filling introduces non-Gaussian artifacts and mode-coupling. A standard Fisher Matrix would be invalid. We will implement a **Mode-Coupling Matrix (Leakage Matrix)** calculation from the gap mask. This matrix will be applied to the theoretical power spectrum *before* the Fisher matrix calculation, ensuring the likelihood surface reflects the actual data conditions (including gap-induced covariance).
*   **Bias Definition**: Bias is defined as the **differential** between the *recovered* parameter (from gap-filled map) and the *input* ground-truth parameter (from simulation metadata). This avoids conflating estimation uncertainty with systematic bias.
*   **Null Model**: To avoid circular validation where bias is a mathematical artifact of the gap fraction, we will generate a **Null Model** baseline where gaps are random and uncorrelated with the signal. The observed bias trend will be compared against this null distribution.

### Statistical Rigor (FR-005, FR-007)

*   **Multiple Comparison Correction**: Since we test bias across multiple gap fractions and distributions, we will apply the **Benjamini-Hochberg** procedure (False Discovery Rate) to control the family-wise error rate at α = 0.05.
*   **Power Analysis**: The target of 50 realizations is a **budget-driven target**, not a power-derived constant. A **Pilot Power Check** will be performed on the first 10 realizations to estimate effect size. If the effect size is too small to be detected with N=50, this limitation will be explicitly reported rather than claiming statistical validity. A sufficient minimum floor of valid realizations is preserved for descriptive statistics.
*   **Statistical Model**: We will use a **Full Factorial Linear Mixed Model (LMM)** that includes interaction terms between Gap Fraction, Algorithm, and Morphology. This ensures the model captures the complex interplay of variables, not just a simple linear trend.
*   **Sensitivity Analysis**: We will sweep α across a range of values and accuracy tolerance across a range of thresholds to ensure findings are robust to threshold choices.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **Simulated Data Only** | External data (Planck) has uncontrolled gaps and systematics. Simulation allows *ground-truth* bias calculation. |
| **Fisher Matrix vs. MCMC** | MCMC is too slow for a sufficient number of realizations on CPU within a 6h limit. Fisher matrix is analytically fast and sufficient for bias magnitude, **provided the mode-coupling correction is applied**. |
| **Mode-Coupling Correction** | Essential to account for non-Gaussian artifacts from inpainting, ensuring the likelihood surface is valid for gap-filled data. |
| **Null Model Baseline** | Essential to distinguish true physical bias from mathematical artifacts of the gap fraction. |
| **Dynamic Realization Count** | Runtime is unpredictable. A static plan risks timeout. Pilot run ensures max valid N within 6h. |
| **Nside=512** | Balances resolution (ℓ≤2000) with memory (3M pixels). Nside=1024 would exceed RAM limits. |

## Limitations

*   **Gaussian Likelihood Assumption**: Fisher matrix assumes Gaussian posteriors. Non-Gaussian biases (e.g., at very high gap fractions >20%) may be underestimated, even with mode-coupling correction.
*   **Algorithm Approximations**: `PyWiener` or custom implementations may not match full CMB pipelines exactly, but are sufficient for relative bias comparison.
*   **CPU Constraints**: Complex algorithms (e.g., full iterative synthesis) may be truncated if runtime threatens the 6h limit.
*   **Power Limitation**: If the pilot power check indicates N=50 is insufficient for the observed effect size, the study will report the limitation rather than overclaiming significance.