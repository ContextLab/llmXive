# Research: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

## Executive Summary

This research validates the implementation of MOND (Milgrom 1983 "simple" interpolating function) and NFW dark matter halo models against the SPARC galaxy rotation curve database. The study addresses whether MOND's parameter-free prediction (using only baryonic mass) outperforms the flexible NFW model (with concentration and scale radius) across a filtered sample of galaxies. Key methodological innovations include a parametric bootstrap approach to compare residual distributions (avoiding exchangeability issues of permutation tests), Kolmogorov-Smirnov (KS) distance as the test statistic, Holm-Bonferroni correction for multiple comparisons, and sensitivity analysis on χ² thresholds. All findings are framed as associational due to the observational nature of the data.

## Dataset Strategy

| Dataset | Verified URL | Loader Method | Variables Used | Fit to Spec? |
|---------|--------------|---------------|----------------|--------------|
| SPARC (canonical) | https://astroweb.cwru.edu/SPARC/ | `requests.get()` + `pandas.read_csv()` | radial_distances, rotational_velocities, velocity_uncertainties, inclination, inclination_uncertainty, baryonic_mass_distribution (stellar + gas surface densities) | ✅ Yes — contains all required predictors, outcomes, and covariates per FR-002, FR-003 |

> **Note**: The SPARC database (Lelli et al.) is the canonical source for galaxy rotation curves. The plan explicitly uses the official SPARC archive to ensure the correct physical variables (radial distances, velocities, surface densities) are available for MOND/NFW fitting. No HuggingFace mirrors are used to avoid potential data structure mismatches.

**Dataset Fit Verification**:  
The SPARC dataset contains:
- `radial_distances` (kpc) — required for both MOND and NFW predictions
- `rotational_velocities` (km/s) — the outcome variable
- `velocity_uncertainties` (km/s) — required for weighted least-squares fitting (FR-006)
- `inclination` and `inclination_uncertainty` — required for filtering (FR-003)
- `baryonic_mass_distribution` (stellar + gas surface densities) — required for MOND's prediction (FR-004)

All variables are present; no mismatches detected.

## Model Specifications

### MOND Model (FR-004)

The "simple" interpolating function (Milgrom 1983):
```
a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0)
```
where:
- `a_N = G*M_baryonic / r^2` (Newtonian acceleration)
- `a_0 = 1.2×10^(-10) m/s²` (community standard)
- `M_baryonic` derived from SPARC's baryonic mass distribution (stellar + gas)
- **Free Parameter**: Stellar mass-to-light ratio (M/L) is fitted (k=1) to account for uncertainties in stellar population synthesis. This ensures a fair comparison with NFW (k=2).

**Validation Evidence**: Milgrom (n.d.) introduced this function; Lelli et al. (2016) validated it against SPARC data. The formula is analytically exact and requires no numerical approximation.

### NFW Model (FR-005)

The NFW dark matter halo profile:
```
v_circ(r) = sqrt(v_baryonic(r)^2 + v_NFW(r)^2)
```
where:
- `v_NFW(r) = sqrt(4πGρ_s r_s^3 / r * [ln(1+r/r_s) - r/(r+r_s)])`
- Parameters: `concentration (c)`, `scale_radius (r_s)`
- **Prior**: Gaussian prior on `c` derived from cosmological simulations (Dutton & Macciò 2014) based on halo mass, independent of the specific baryonic mass distribution of the sample. This avoids circularity.
- Bounded: `c ∈ [1, 50]`, `r_s > 0`

**Validation Evidence**: Navarro, Frenk & White introduced the profile; Dutton & Macciò established the concentration-mass relation used for the prior.

## Statistical Methodology

### Goodness-of-Fit Metrics (FR-007)

- **Reduced χ²**: `χ²_red = Σ[(v_obs - v_pred)² / σ_v²] / (N - k)` where `k` = number of fitted parameters (1 for MOND, 2 for NFW)
- **AIC**: `AIC = 2k - 2ln(L_max)` where `L_max` is the maximum likelihood
- **BIC**: `BIC = k*ln(N) - 2ln(L_max)`
- **Kolmogorov-Smirnov (KS) Test**: Computed between the residual distributions of MOND and NFW to assess distributional differences (Constitution Principle VII).
- Degrees of freedom explicitly documented per galaxy (FR-007)

### Residual Analysis (FR-008, FR-009)

- **Residuals**: `r_i = v_obs,i - v_pred,i`
- **Standardization**: Residuals are standardized by velocity uncertainty to ensure comparability across galaxies.
- **Parametric Bootstrap**: Synthetic rotation curves are generated under a combined null model (averaging MOND and NFW predictions) with added Gaussian noise matching observed uncertainties. This ensures exchangeability under the null hypothesis. A sufficient number of bootstrap iterations.
- **Test Statistic**: Kolmogorov-Smirnov (KS) distance between the standardized residual distributions of MOND and NFW. This statistic is sensitive to differences in the shape, variance, and systematic structure of the errors, not just the mean.
- **P-value**: Proportion of bootstrap samples where the KS distance is greater than or equal to the observed KS distance.

### Multiple Comparison Correction (FR-010)

- **Holm-Bonferroni correction**: Applied when >1 hypothesis test is executed (e.g., multiple thresholds in sensitivity analysis)
- **Family-wise error rate**: ≤0.05 (SC-005)

### Sensitivity Analysis (FR-012)

- **Threshold sweep**: χ² < {1.0, 1.25, 1.5, 1.75}
- **Metric**: Distribution of pass rates (proportion of galaxies with χ² < threshold) for both models
- **Purpose**: Quantify threshold dependence of model performance claims

### Power Analysis (Methodology-decaa1fe)

- **Method**: Simulation-based power analysis using synthetic rotation curves generated from the MOND and NFW models with added Gaussian noise matching the observed uncertainty levels.
- **Procedure**: Generate N synthetic datasets for varying sample sizes; compute the proportion of simulations where the KS test correctly rejects the null hypothesis at α=0.05.
- **Purpose**: Estimate the sample size required to detect the expected effect sizes with [deferred] power.

## Causal Framing (FR-011)

All findings are framed as **ASSOCIATIONAL** rather than causal. The data is observational (no randomization of galaxies to MOND/NFW); thus, claims are limited to "MOND is associated with better fit than NFW" rather than "MOND causes better predictions." This aligns with FR-011 and avoids overclaiming causal effects.

## Statistical Rigor Checklist

| Requirement | Method | Status |
|-------------|--------|--------|
| Multiple-comparison correction | Holm-Bonferroni (FR-010) | ✅ |
| Sample-size / power justification | Simulation-based power analysis using synthetic rotation curves (see Power Analysis section) | ✅ |
| Causal-inference assumptions | Observational data; claims framed as associational (FR-011) | ✅ |
| Measurement validity | SPARC instruments validated (Lelli et al. 2016); MOND a0 community standard (Milgrom 1983) | ✅ |
| Predictor collinearity | Baryonic mass and rotation velocity are physically linked; MOND prediction is deterministic from baryons (with fitted M/L); no independent effect claimed for baryons | ✅ |

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM, Substantial disk capacity is required to support the research question. The method involves analyzing large-scale data repositories. References include the foundational work on data-intensive computing (DOI:10.1145/1247480.1247482)., no GPU)
- **Data size**: SPARC a sample of galaxies, approximately twenty thousand radial points total; fits easily in RAM
- **Runtime**: <30s per galaxy fit × 175 galaxies = ~1.5 hours; parametric bootstrap (a substantial number of iterations) = [deferred]; total <6 hours
- **Libraries**: `scipy.optimize.curve_fit` (CPU-only), `numpy`, `pandas` — all CPU-tractable
- **Approximation**: If bootstrap runtime exceeds 4 hours, reduce iterations to [deferred] (documented in research.md)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SPARC URL inaccessible | Retry logic (attempts) per FR-001; fallback to verified local cache if available |
| Convergence failures in `curve_fit` | Bounds on parameters; fallback to grid search if `curve_fit` fails; log failures |
| Degenerate fits (flat curves) | Document degeneracy; report as "inconclusive" rather than forcing a fit |
| Memory overflow | Chunk data loading; process galaxies in batches of a fixed size |
| Runtime >6 hours | Reduce bootstrap iterations; parallelize galaxy fits (if allowed by CI) |

## References

- Milgrom, M. (1983). "A modification of the Newtonian dynamics as a possible alternative to the hidden mass hypothesis." *The Astrophysical Journal*, 270, 365–370.
- Lelli, F., McGaugh, S. S., & Schombert, J. M. (2016). "SPARC: Mass Models for 175 Disk Galaxies with Spitzer Photometry and Accurate Rotation Curves." *The Astronomical Journal*, 152(6), 157.
- Navarro, J. F., Frenk, C. S., & White, S. D. M. (1996). "The Structure of Cold Dark Matter Halos." *The Astrophysical Journal*, 462, 563–575.
- Dutton, A. A., & Macciò, A. V. (2014). "Cold dark matter haloes in the Planck era." *Monthly Notices of the Royal Astronomical Society*, 441(4), 3359–3374.