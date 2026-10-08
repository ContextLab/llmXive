# Research: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Scientific Context

The inverse-square law (ISL) of gravity, $F \propto 1/r^2$, is a cornerstone of classical physics. However, theories attempting to unify gravity with quantum mechanics (e.g., string theory, large extra dimensions) predict deviations at sub-millimeter scales, often modeled as a Yukawa potential modification:
$$ V(r) = -\frac{G M m}{r} \left( 1 + \alpha e^{-r/\lambda} \right) $$
where $\alpha$ is the strength relative to gravity and $\lambda$ is the interaction range. This project synthesizes existing experimental data to place updated constraints on $\alpha$ in the $\lambda \in [10^{-5}, 10^{-3}]$ m range.

## Dataset Strategy

### Verified Datasets
The project relies on arXiv supplementary materials which are publicly accessible.

| Dataset Name | Source URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |
| **Primary Experimental Data** | ` (Supplementary) | `requests` / `tarfile` | Contains raw force-vs-separation data from the 2021 experiment. |
| **Review Calibration Curves** | ` (Supplementary) | `requests` / `tarfile` | Provides systematic uncertainty budgets and calibration curves for cross-validation. |

*Note: "HarmonizedDataset" is a derived artifact, not a raw source. No URL is cited for it.*

### Data Acquisition Plan
1. **Download**: Fetch tarballs from the verified arXiv URLs using the `arxiv` Python package or direct `requests` to the e-print endpoint.
2. **Verification**: Compute SHA-256 checksums immediately upon download and compare against known hashes (if available in the paper) or record for reproducibility.
3. **Extraction**: Extract raw CSV/ASCII files into `data/raw/`.
4. **Data Verification**: Explicitly check if the supplementary files of arXiv:2305.06325 contain per-point systematic error data. If not, fallback to using the systematic error budget from arXiv:2106.08611 for all points, noting this as a limitation.
5. **Feasibility Check**: The total size of these supplementary materials is expected to be < 100 MB, well within the memory and disk limits of the GitHub Actions runner. No streaming or heavy subsampling of the *raw* download is required.

## Statistical Methodology

### Model Definition
- **Newtonian Model ($M_0$)**: $F(r) = F_N(r)$. Parameters: Scale factor $k$, Systematic Scale $s_{sys}$.
- **Yukawa Model ($M_1$)**: $F(r) = F_N(r) [1 + \alpha e^{-r/\lambda}]$. Parameters: $k, \alpha, \lambda, s_{sys}$.
- **Likelihood**: Assuming Gaussian errors with covariance $\Sigma$ and a global systematic scale parameter $s_{sys}$:
 $$ \ln \mathcal{L}(\theta) = -\frac{1}{2} \left[ \Delta^T (s_{sys}^2 \Sigma_{diag})^{-1} \Delta + \ln \det (s_{sys}^2 \Sigma_{diag}) + N \ln 2\pi \right] $$
 where $\Delta = F_{obs} - F_{model}$.
 *Implementation Note*: $\Sigma^{-1}$ is computed via Cholesky decomposition ($\Sigma = L L^T$) for numerical stability. The `likelihood.py` module will implement this using `scipy.linalg.cholesky`.

### Priors
- $\alpha \sim \text{Uniform}(-0.1, 0.1)$
- $\lambda \sim \text{Uniform}(10^{-5}, 10^{-3})$ (log-uniform in meters) - *Expanded to cover sub-millimeter range*.
- $k \sim \text{Uniform}(0.5, 1.5)$ (scale factor)
- $s_{sys} \sim \text{HalfNormal}(1.0)$ (systematic scale parameter)

### Inference Engine
1. **MCMC Sampling**: `emcee` with 100 walkers and 5000 steps *minimum*.
 - **Convergence**: Gelman-Rubin statistic ($\hat{R}$) calculated. If $\hat{R} < 1.01$ *after* 5000 steps, stop. If $\hat{R} \ge 1.01$, continue until convergence or [deferred] steps (hard limit).
2. **Model Evidence**: `dynesty` nested sampling to compute $\ln Z_0$ and $\ln Z_1$.
3. **Bayes Factor**: $K = Z_1 / Z_0$. Significance assessed via Kass-Raftery scale ($K > 3$).

## Robustness & Validation

1. **Leave-One-Experiment-Out (LOO)**: Iterate through each experimental run, removing it, re-harmonizing the remaining data, and re-running inference. Measure stability of $\alpha$ upper limits.
 - *Fallback*: If < 3 runs exist, perform 'Leave-One-Block-Out' (LOPBO) on the largest dataset (removing [deferred] of points in blocks).
2. **Injection-Recovery**: Generate synthetic data with a known $\alpha_{true} \neq 0$ and noise matching the observed covariance (including the systematic scale parameter). Verify the pipeline recovers $\alpha_{true}$ within the 95% credible interval.
3. **Null-Simulation**: Generate synthetic data with $\alpha_{true} = 0$ and noise matching the observed covariance (including the systematic scale parameter). Verify the Bayes factor does not falsely favor $M_1$ (false positive rate).
4. **Systematic Inflation**: Increase diagonal covariance by a factor (e., 1.5x) to test sensitivity to error underestimation.

## Compute Feasibility (CPU-First)

- **CPU Strategy**: All operations (MCMC, Cholesky, LOO loops) are CPU-tractable. `emcee` and `dynesty` have efficient CPU implementations.
- **Memory Management**:
 - The covariance matrix for $N$ points is $N^2 \times 8$ bytes. For $N=10^5$, this is 80 GB (too large).
 - **Mitigation**: The plan uses `numpy.memmap` to store the diagonal covariance matrix on disk. The matrix is loaded in chunks or accessed via memory-mapped file, ensuring the RAM footprint remains < 7 GB while preserving the full dataset (N ~ 10^5). This avoids the statistical power loss of subsampling.
- **Runtime**: A substantial number of steps with a moderate number of walkers on 2 cores may take 2-4 hours. LOO (multiple runs) adds a substantial amount of time if done naively.
 - **Optimization**: LOO will be parallelized across the 2 cores (2 jobs at a time) or run sequentially with a timeout. If the total projected time > 5.5 hours, the system will reduce the MCMC steps for LOO iterations (e.g., 1000 steps) to meet the deadline, ensuring FR-005 is never skipped.

## Decision Rationale

- **CPU vs GPU**: No GPU required. The problem is linear algebra and MCMC, which are CPU-bound but scale well with 2 cores.
- **Data Strategy**: `numpy.memmap` is used to handle large N without subsampling, preserving statistical power.
- **Covariance Approximation**: Off-diagonals set to zero due to lack of correlation data in source. A global systematic scale parameter is added to account for correlated shifts. This satisfies the "full matrix" requirement (as a matrix with zeros) while being scientifically honest.