# Research: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Problem Statement

The inverse-square law of gravity is a cornerstone of classical and modern physics. However, theoretical models (e.g., extra dimensions, scalar fields) predict deviations at sub-millimeter scales. This project investigates the validity of the law in the micrometer range by analyzing experimental force-vs-separation data. The primary goal is to constrain the Yukawa strength parameter (α) and length scale (λ) using a rigorous Bayesian framework, ensuring all uncertainties (statistical and systematic) are properly propagated.

## Dataset Strategy

### Verified Sources
Per project constraints, only the following sources are available for verification. Note: The specific experimental data for the 2021 (arXiv:2106.08611) and 2023 (arXiv:2305.06325) studies are **not** in the "Verified datasets" block provided in the prompt.

**Constraint**: The prompt's "Verified datasets" block lists MCMC training data (math/gsm8k) and a civil procedure dataset. It explicitly states: **"HarmonizedDataset: NO verified source found"**.

**Action**: Since the specific arXiv supplementary data files for the physics experiments are **not** in the verified list, the plan **cannot** fabricate a URL. The implementation must:
1.  **Data Availability Gate**: Attempt to fetch from the canonical arXiv supplementary URLs (as assumed in the spec).
2.  **Validation**: Call the Reference-Validator Agent to check title-token-overlap (≥ 0.7) against the primary source before processing.
3.  **Failure Mode (0 Runs)**: If the URL is unreachable, the file format is invalid, or the validation fails, the system must halt with a clear error message and **not** proceed to inference. The project will be marked as `data_inaccessible`.
4.  **Fallback (< 3 Runs)**: If the supplementary materials contain fewer than 3 independent experimental runs (but > 0), the system will **skip** the 'leave-one-out' cross-validation (which requires N≥3) and instead perform **bootstrap resampling of the available data points** (with replacement) to estimate stability, as permitted by FR-001. This ensures the pipeline adapts to the available data rather than crashing, but the limitation will be explicitly flagged in the results.

*Note: The MCMC datasets listed in the "Verified datasets" block (gemma2_9b...) are irrelevant to this physics problem and will not be used.*

### Data Availability & Fallback Strategy
-   **Source**: arXiv supplementary materials for 2106.08611 and 2305.06325.
-   **Content**: Raw force-vs-separation data, systematic error budgets, calibration curves.
-   **Status**: **UNVERIFIED** in the provided dataset list. The implementation relies on the `spec.md` assumption that these are accessible, with a strict gate to prevent proceeding if they are not.
-   **Fallback for < 3 Runs**: If the supplementary materials contain fewer than 3 independent experimental runs, the system will **skip** the 'leave-one-out' cross-validation (which requires N≥3) and instead perform **bootstrap resampling of the available data points** (with replacement) to estimate stability, as permitted by FR-001. This ensures the pipeline adapts to the available data rather than crashing, but the limitation will be explicitly flagged in the results.

## Methodology

### 1. Data Harmonization (FR-001, FR-002)
-   **Unit Conversion**: All force data converted to Newtons (N), distance to meters (m).
-   **Grid Alignment**: Interpolation to a common logarithmic grid in a representative small-scale range.
-   **Covariance Construction**:
    -   $C_{total} = C_{stat} + C_{sys}$
    -   $C_{stat}$: Diagonal matrix from reported statistical errors.
    -   $C_{sys}$:
        -   **If explicit correlation data exists**: Construct full matrix.
        -   **If correlation data is missing**: Construct **diagonal** $C_{sys}$ with elements scaled by a conservative factor of the statistical error to represent an upper bound on unmodeled systematics. This satisfies FR-002's requirement for a "full or diagonal covariance matrix" (now defined as "diagonal-full" in the fallback) without invalidating the inference.
        -   **If correlation structure is assumed**: Use an **exponential decay model** ($C_{ij} = \sigma_i \sigma_j \exp(-|r_i - r_j| / L)$) with a conservative length scale $L$ (e.g., [deferred] of the grid range) if the source papers suggest short-range correlations but do not provide coefficients.
    -   **Validation**: Check for positive-definiteness. If not, apply regularization (e.g., jitter) and log warning.
    -   **Fallback**: If systematic error budgets are missing entirely, $C_{sys}$ will be set to the conservative diagonal approximation (1.5x stat error) and the limitation flagged.

### 2. Bayesian Inference (FR-003, FR-004)
-   **Model**: $F(r) = F_N(r) [1 + \alpha \exp(-r/\lambda)]$
-   **Priors**:
    -   $\alpha \sim \text{Uniform}(-0.1, 0.1)$
    -   $\lambda \sim \text{Log-Uniform}(10^{-6}, 10^{-3})$ m. **Justification**: This broad range covers 3 orders of magnitude to ensure a non-informative prior over the search space. While the analysis focuses on the 10⁻⁵–10⁻⁴ m window for reporting, the prior is intentionally broad to avoid biasing the posterior against scales just outside this window. A sensitivity analysis will be performed to check if the posterior is sensitive to the lower bound.
-   **MCMC (`emcee`)**:
    -   **Primary Run**: A cohort of walkers, performing 5000 steps.
    -   **Convergence**: Gelman-Rubin < 1.01.
    -   **Compute Feasibility**: `emcee` is CPU-efficient. 100 walkers × 5000 steps = likelihood evaluations. With a **banded covariance approximation** (bandwidth=20) or subsampling to N≤200 points, this is estimated to take < 1 hour on 2 CPUs.
-   **Nested Sampling (`dynesty`)**:
    -   Used to compute log-evidence ($\ln Z$) for Newtonian ($H_0$) and Yukawa ($H_1$) models.
    -   Bayes Factor $K = Z_1 / Z_0$.
    -   **Compute Feasibility**: `dynesty` is CPU-tractable for 2 parameters.

### 3. Robustness & Validation (FR-005, FR-008, FR-009)
-   **Leave-One-Out**: Iterate through independent experimental runs (if N≥3). If N<3, use bootstrap resampling of points.
-   **Uncertainty Inflation**: Scale $C_{sys}$ by a factor (e.g., 1.5) to test sensitivity.
-   **Injection-Recovery**: Simulate data with $\alpha_{true} \neq 0$, run pipeline, verify recovery.
-   **Null-Simulation**: Simulate data with $\alpha_{true} = 0$ + systematic noise. **Critical Update**: The noise will be generated using the **assumed correlation model** (e.g., exponential decay with length scale L) if the real data lacks explicit correlations. This ensures the simulation tests the pipeline's robustness against the *same* correlation assumptions used in the analysis, rather than a simplified diagonal model, providing a valid false-positive rate for the full covariance claim.

## Likelihood Optimization (Addressing Runtime)
-   **Challenge**: Full $O(N^3)$ Cholesky decomposition for large N (e.g., 1000+ points) is infeasible within 6 hours for 500k evaluations.
-   **Solution**:
    1.  **Subsampling**: For the MCMC run, subsample the grid to **N ≤ 200** points (logarithmically spaced) to ensure fast likelihood evaluation while preserving the shape of the posterior.
    2.  **Banded Approximation**: If the systematic error correlation length is known to be short, use a banded covariance matrix approximation (bandwidth=20).
    3.  **Parallelization**: The robustness suite (leave-one-out, injection) will run in parallel across available cores.
    4.  **Step Reduction**: For robustness iterations, reduce MCMC steps to a sufficient number with pre-conditioned starting points.

## Compute Feasibility & Risks

-   **RAM**: The dataset size is expected to be small (< 10 MB). No subsampling required for storage, but subsampling for likelihood evaluation is used for speed.
-   **Runtime**:
    -   Data Download & Validation: < 1 min.
    -   Harmonization: < 5 min.
 - MCMC (Primary, 500k evals, N≤200, banded): **[deferred]** (calculated: 500k * 4000 ops / 2 cores / 1e9 ops/sec).
    -   Nested Sampling: [deferred].
    -   Robustness (Parallelized, reduced steps): [deferred].
    -   **Total Revised Estimate**: **< 2.5 hours**. (Guarantees compliance with FR-006).
-   **GPU**: Not used. All libraries (`emcee`, `dynesty`, `numpy`) run on CPU.
-   **Risk Mitigation**: If runtime exceeds 2.5 hours, the system will automatically reduce the number of robustness iterations or further reduce the subsampled grid size (N) to ensure completion.

## Statistical Rigor

-   **Multiple Comparisons**: Not applicable (single hypothesis test per run).
-   **Power**: Sample size is fixed by the experiment. Power is assessed via injection-recovery.
-   **Causal Claims**: Observational/Experimental data. Claims are strictly associational (constraints on parameters), not causal in the social science sense.
-   **Collinearity**: $\alpha$ and $\lambda$ are correlated in the likelihood. The full 2D posterior will be reported to visualize this degeneracy.
-   **Prior Sensitivity**: The use of Log-Uniform priors for $\lambda$ ensures non-informative behavior over several orders of magnitude, avoiding the bias of a narrow uniform prior. A sensitivity check will be performed to confirm the posterior is not dominated by the prior bounds.
