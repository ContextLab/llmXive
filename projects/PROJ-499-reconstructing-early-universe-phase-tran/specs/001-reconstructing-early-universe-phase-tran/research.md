# Research: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

## Scientific Context

The search for primordial B-mode polarization in the Cosmic Microwave Background (CMB) is a primary method for testing inflationary theories. However, alternative scenarios, such as first-order phase transitions in the early universe, can also generate gravitational waves and B-mode signatures. These signatures are theoretically expected to have distinct spectral shapes compared to the nearly scale-invariant spectrum of inflation, particularly at low multipoles ($\ell < 100$).

The core research question is: *Do causal, non-inflationary phase transitions produce distinct, detectable signatures in CMB B-mode polarization that can be statistically distinguished from inflationary gravitational wave signals using existing Planck and BICEP/Keck data?*

## Dataset Strategy

The analysis relies on two primary observational datasets. Per the project constraints, only verified sources are used.

| Dataset | Description | Verified Source / Loader | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **Planck 2015 SMICA Q/U Maps** | Full-sky Q and U Stokes parameter maps derived via the SMICA component separation method. B-modes are derived from these maps via spin-2 harmonic decomposition. | ESA Planck Archive (via `astroquery.esa` or direct HTTPS URL to specific FITS files) | Source of observed Q/U; B-modes derived via spin-2 harmonic decomposition using `pyhealpix`. |
| **BICEP/Keck 2018** | High-sensitivity B-mode power spectra and Q/U maps (if available) from the BICEP2, Keck Array, and BICEP3 experiments. | BICEP/Keck Collaboration Data Release (verified URL) | Cross-validation and high-$\ell$ constraints in joint likelihood. |

*Note: If the ESA Planck Archive URL is unreachable in the CI environment, the pipeline will retry 3 times with exponential backoff as per Edge Case 1. If it remains unreachable, the job fails gracefully with a clear error.*

**Variable Fit Check**:
- **Required**: Q/U Stokes parameter maps, Galactic masks, power spectra ($C_\ell$), covariance matrices.
- **Available**: Planck 2015 SMICA provides Q/U maps and the Common Mask. BICEP/Keck provides $C_\ell$ with covariance (and Q/U maps if available).
- **Status**: The datasets contain the necessary variables. No missing predictors or outcomes identified.

## Theoretical Models

Three competing models will be generated and fitted:

1.  **Inflationary Model**:
    -   Parameters: Tensor-to-scalar ratio $r$, Spectral index $n_t$ (often fixed to $n_t = -r/8$).
    -   Spectrum: Nearly scale-invariant at low $\ell$, damped by reionization and lensing at higher $\ell$.
    -   Source: Standard $\Lambda$CDM + Tensor perturbation theory.

2.  **Phase Transition Model**:
    -   Parameters: Energy scale $E_{\text{PT}}$ (GeV), Duration parameter $\beta/H_*$, Envelope parameter $\alpha$.
    -   Spectrum: Causality-limited, peaking at a specific multipole $\ell_{\text{peak}}$ determined by the horizon size at the transition.
    -   Source: Theoretical calculations of bubble collision and sound wave contributions (e.g., Caprini et al.).

3.  **Null (Lensing-Only) Model**:
    -   Parameters: None (fixed lensing potential).
    -   Spectrum: Purely gravitational lensing of E-modes into B-modes.
    -   Purpose: Baseline for detecting any excess signal.

## Statistical Methodology

### Parameter Estimation
-   **Method**: Markov Chain Monte Carlo (MCMC) using the `emcee` package (affine-invariant ensemble sampler), as mandated by FR-005.
-   **Justification**: `emcee` is CPU-efficient and robust for low-dimensional parameter spaces ($r$, $E_{\text{PT}}$).
-   **Convergence Strategy**:
    -   Initialize with a diverse set of walkers to avoid local modes.
    -   Ensure $N_{steps} > 50 \times \tau$ (autocorrelation time).
    -   Perform a multimodal check via cluster analysis of posterior samples to detect local modes.
    -   Convergence requires both Gelman-Rubin < 1.01 AND visual inspection of trace plots for multimodality.
    -   Non-convergence triggers a warning and a "failed" status.

### Joint Likelihood Framework
To address the combination of Planck map-derived spectra and BICEP/Keck pre-computed spectra:
-   Construct a unified covariance matrix that accounts for different beam window functions and noise correlations.
-   Apply consistent sky masks to both datasets before combination.
-   Treat BICEP/Keck data as a constraint on high-$\ell$ modes within the same likelihood function, ensuring a consistent statistical framework for the joint fit.
-   Include nuisance parameters for foreground residuals (dust/synchrotron) in the likelihood function to mitigate spatially correlated foregrounds. This addresses the concern that simple sky splitting is insufficient for confound control.

### Model Comparison
-   **Metric**: Bayes Factor ($K$) via Nested Sampling (using `dynesty`), as mandated by FR-006 (replacing Thermodynamic Integration for stability).
-   **Rationale**: Nested Sampling is robust for non-nested models and handles multi-modal posteriors better than Thermodynamic Integration, which is prone to numerical instability in complex likelihood surfaces.
-   **CPU Feasibility**: Limit the number of live points to ensure runtime within 6 hours on a 2-core runner.
-   **Decision Threshold**: $K > 10$ indicates strong evidence for one model over another (SC-002, SC-003).

### Robustness Checks
-   **Sky Splitting**: The sky will be divided into Northern and Southern hemispheres (FR-007).
-   **Consistency Test**:
    -   **Primary Criterion**: The Bayes factor and spectral shape (peak location for PT) must be consistent across patches.
    -   **Secondary Diagnostic**: Best-fit $r$ values from both patches must differ by $< 0.005$ (SC-004), but this is not the primary gate.
    -   **Foreground Validation**: Compare foreground template residuals across patches to ensure consistency.
-   **Synthetic Validation**: The entire pipeline will be validated on synthetic data generated from:
    1.  A known $r=0.01$ inflation model (to ensure parameter recovery).
    2.  A known Phase Transition model (to ensure the Bayes factor logic can distinguish PT from inflation).

## Compute Feasibility Analysis

-   **Memory**: Planck Nside=64 maps are $\approx 576$ MB. Processing fits well within 7 GB RAM.
-   **CPU**: Nested Sampling with a moderate number of live points is computationally light. Likelihood calculation involves summing over a low range of $\ell$, which is fast.
-   **Time**: Estimated total runtime: < 2 hours on a 2-core runner.
-   **GPU**: Not required. All operations are vectorized numpy/scipy calls.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailable** | High | Implement retry logic (3x, exponential backoff) using `requests`/`astroquery`. Fail gracefully if persistent. |
| **MCMC Non-Convergence** | High | Detect via autocorrelation time and multimodal checks. Extend chain or report failure. |
| **Phase Transition Model Breakdown** | Medium | Clamp predictions to valid $\ell$ range; flag extrapolations in diagnostics. |
| **CPU Time Exceeded** | High | Limit Nested Sampling live points; use adaptive stopping criteria. |
| **Numerical Instability in Model Comparison** | High | Use Nested Sampling (`dynesty`) instead of Thermodynamic Integration; validate with reduced parameter grid. |
| **Foreground Contamination** | High | Include foreground nuisance parameters in the likelihood; validate with sky splitting. |