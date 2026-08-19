# Research: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Scientific Background

The inverse-square law of gravity ($F \propto 1/r^2$) is a cornerstone of classical physics. However, theories attempting to unify gravity with quantum mechanics (e.g., string theory, large extra dimensions) predict deviations at sub-millimeter scales. These deviations are often modeled as a Yukawa-type potential:
$$ V(r) = -\frac{G m_1 m_2}{r} \left( 1 + \alpha e^{-r/\lambda} \right) $$
where $\alpha$ represents the strength of the deviation relative to gravity, and $\lambda$ is the interaction range.

Recent experiments, notably the University of Washington Eöt-Wash group (arXiv:2106.08611) and subsequent reviews (arXiv:2305.06325), have placed stringent constraints on $\alpha$ in the $\lambda \in [10^{-5}, 10^{-4}]$ m range. This project aims to re-analyze the data from these sources using a unified Bayesian framework to verify current constraints and assess the robustness of the null result.

## Dataset Strategy

The analysis relies on two primary sources. The pipeline will attempt to download raw force-vs-separation data from the arXiv supplementary materials. If raw files are missing (as suspected for 2305.06325), the pipeline will parse summary tables and error budgets from the main text of the papers to reconstruct the dataset.

| Dataset | Source | Access Method | Status |
|:--- |:--- |:--- |:--- |
| **Eöt-Wash 2021 Data** | arXiv:2106.08611 (Supplementary Material) | Direct download from arXiv source tarball (`src.tar.gz`) or supplementary link. | **Open**: arXiv supplementary materials are publicly accessible without credentials. |
| **2023 Review Calibration** | arXiv:2305.06325 (Supplementary Material) | Direct download from arXiv source tarball. | **Open**: arXiv supplementary materials are publicly accessible. |

**Note**: The plan does **not** use access-gated datasets (e.g., ADNI, HCP). If the arXiv supplementary links are missing, the pipeline will fail gracefully or fall back to summary tables rather than fabricate data.

**Verified URLs**:
- **arXiv:2106.08611**: `
- **arXiv:2305.06325**: `

**Data Processing Strategy**:
1. **Download**: Fetch `src.tar.gz` or specific data files from the arXiv URLs.
2. **Parse**: Extract force ($F$) and separation ($r$) values. If raw files are missing, parse summary tables.
3. **Unit Conversion**: Convert all units to SI (Newtons, meters) using `astropy.units`. Store original units in metadata.
4. **Model Evaluation**: Evaluate the model at the **exact separation distances** of each raw data point. **No interpolation** of data points onto a common grid is performed to avoid artificial correlations. A common grid is used only for visualization and reporting.
5. **Covariance Construction**: Combine statistical errors (from data points) and systematic errors (from calibration curves) into a **diagonal covariance matrix** $\Sigma$. Off-diagonal elements are set to 0 due to lack of data.

## Methodological Rigor

### Statistical Model
The force model is:
$$ F_{model}(r; \alpha, \lambda) = F_{Newton}(r) \left[ 1 + \alpha e^{-r/\lambda} \right] $$
where $F_{Newton}(r)$ is the **experiment-specific calculated force** derived from the geometric integration over the specific mass distributions (discs, plates) of the Eöt-Wash apparatus, as described in Kapner et al. (2007) and 2106.08611. **Crucially, the Yukawa term is applied consistently to this specific geometry.** A simplified point-mass formula is **not** used. The geometric integration accounts for the actual shape of the attractor and pendulum, ensuring the Yukawa scaling is physically valid at sub-millimeter scales.

### Bayesian Inference
- **Sampler**: `emcee` (Affine-invariant MCMC).
 - **Walkers**: 100.
 - **Steps**: **Up to** 5000, stopping early if Gelman-Rubin < 1.01.
 - **Priors**:
 - $\alpha \sim \text{Uniform}(-0.1, 0.1)$ (with sensitivity analysis).
 - $\lambda \sim \text{Uniform}(10^{-5}, 10^{-4})$ (with sensitivity analysis).
- **Evidence**: `dynesty` (Nested Sampling).
 - Used to compute $\ln \mathcal{Z}_{Newton}$ and $\ln \mathcal{Z}_{Yukawa}$.
 - Bayes Factor $K = \exp(\ln \mathcal{Z}_{Yukawa} - \ln \mathcal{Z}_{Newton})$.

### Robustness & Validation
1. **Leave-One-Out**: If ≥3 runs, iteratively exclude one dataset.
 - **Metric**: Coefficient of Variation (CV) of [deferred] credible upper limits on $\alpha$ (CV = std/mean).
 - **Enforcement**: If CV > 0.15, flag result as "unstable".
2. **Bootstrap Resampling**: If <3 runs, perform N=1000 bootstrap resamples.
3. **Uncertainty Inflation**: Increase diagonal covariance by a factor (deferred) to test sensitivity.
4. **Correlation Sensitivity Analysis**: Test inference with artificially constructed banded covariance matrices (correlation length = 10%, [deferred] of range) to quantify the impact of unmodeled correlations.
5. **Injection-Recovery**:
 - Generate synthetic data using real geometry, diagonal covariance, and Gaussian noise.
 - Inject known $\alpha_{true} \neq 0$.
 - **Validation**: Check if $\alpha_{true}$ falls within 95% credible interval.
 - **Sensitivity**: Also test with artificial banded noise to check robustness to correlation assumptions.
6. **Null Simulation**:
 - N=1000 simulations with $\alpha_{true} = 0$.
 - **Metric**: False-positive rate (fraction where Bayes factor > 3).
 - **Baseline**: Distribution of Bayes factors from these simulations.

### Prior Sensitivity Analysis
- Re-run inference with alternative prior widths for $\alpha$ (e.g., Uniform(-0.2, 0.2)) and $\lambda$ to ensure the Bayes factor conclusion is robust.

## Compute Feasibility (CPU-First)

- **Hardware**: GitHub Actions (standard compute resources).
- **Strategy**:
 - `emcee` and `dynesty` are CPU-tractable for this problem size.
 - No GPU required.
 - Memory usage is low (< 1 GB) as data is small.
 - Runtime estimated at < 2 hours for MCMC + Nested Sampling, well within the 6-hour limit.
- **Fallback Logic**:
 - Trigger: Memory > 6 GB or Runtime > 5 hours.
 - Action: Reduce walkers (e.g., 50) or steps (e.g., 2000) and re-run.
- **Decision**: No GPU escape hatch needed.

## Risk Management

- **Data Availability**: If arXiv supplementary files are missing, the pipeline halts with a clear error or falls back to summary tables. No fallback to synthetic data is permitted (Constitution Principle I).
- **Convergence**: If MCMC chains do not converge ($GR > 1.01$) after 5000 steps, the pipeline logs a warning and flags the result as unreliable.
- **Unit Mismatch**: Rigorous unit testing in `harmonize.py` ensures no silent unit errors.

## References

1. Kapner, D. J., et al. "Tests of the gravitational inverse-square law below the dark-energy length scale." *arXiv preprint arXiv:2106.08611* (2021).
2. Adelberger, E. G., et al. "Torsion balance tests of the weak equivalence principle." *arXiv preprint arXiv:2305.06325* (2023).
3. Goodman, J., & Weare, J. (2010). "Ensemble samplers with affine invariance." *Communications in Applied Mathematics and Computational Science*.
4. Speagle, J. S. (2020). "DYNESTY: a dynamic nested sampling package for estimating Bayesian posteriors and evidences." *Monthly Notices of the Royal Astronomical Society*.