# Research: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Dataset Strategy

The analysis relies on two primary sources. Per the project constraints, we must verify the availability of these datasets.

| Dataset Name | Description | Verified Source / Loader | Status |
|:--- |:--- |:--- |:--- |
| **Kepler DR25 Planet Table** | The primary source for planet parameters (radius, period, uncertainties). Contains a substantial number of confirmed planets. | **MAST: Kepler DR25** (). Loader: `astroquery.mast.Mast.query_object` with table name "Kepler DR25 Planet Table". | **Verified** (MAST) |
| **Kepler Input Catalog (KIC)** | Source for stellar parameters (radius, mass, temperature) required to refine planet radii. | **MAST: KeplerInputCatalog** (). Loader: `astroquery.mast.Mast.query_object` with table name "KeplerInputCatalog". | **Verified** (MAST) |
| **GMM/Parquet Test Sets** | Synthetic or pre-processed test data for unit testing GMM logic. | ` (and variants) | **Verified** (Used for synthetic testing only) |

**Critical Note on Dataset Fit**: The spec assumes the Kepler DR25 catalog contains the necessary variables (`radius`, `radius_uncertainty`, `period`, `period_uncertainty`) and that KIC contains stellar parameters. If the raw download lacks specific stellar columns (e.g., `stellar_temp`), the pipeline **must** exclude those entries rather than impute, adhering to Principle I and FR-002.

**Data Loading Strategy**:
1. **Ingestion**: Use `astroquery.mast` to fetch `KeplerTable` (DR25) and `KeplerInputCatalog`.
2. **Parsing**: Use `pandas` to load into DataFrames.
3. **Cross-Match**: Join on `kepler_id` (KIC ID). If a match is missing, the planet is excluded (no imputation). The pipeline halts with a `DataIntegrityError` if the join fails for critical columns.
4. **Validation**: Immediately check for missing columns. If critical columns are missing, raise a `DataIntegrityError` and halt.
5. **Filtering**: Apply strict thresholds (radius uncertainty < 20%, period uncertainty < 1%) as per FR-002.

## Statistical Methodology

### 1. Binning Strategy (FR-003)
- **Range**: Log-period from 0.7 to 2.0 (5 to 100 days).
- **Bins**: Log-spaced.
- **Minimum Count**: 30 planets per bin.
- **Merge Logic**: If a bin has < 30 planets, merge with the adjacent bin (closest period) until the threshold is met.
- **Weighting**: Regression will use the weighted mean period of the bin, weighted by the inverse variance of the gap location estimate.
- **Survivorship Bias Mitigation**: Merging bins introduces bias. The final regression is restricted to bins with sufficient power (≥30 planets). A "Gap Visibility" analysis will report on the excluded regions to ensure transparency.

### 2. Gap Location Estimation (FR-004, FR-005)
- **Method**: Two-component Gaussian Mixture Model (GMM).
- **Initialization**: K-Means++ with multiple random seeds; select model with lowest BIC.
- **Completeness Correction**: The GMM likelihoods are **weighted** by the detection completeness value from the Kepler completeness map for each planet's (period, radius) coordinate. This accounts for Malmquist bias without introducing circularity. Bins with average completeness < 5% are excluded entirely.
- **Validation**:
 - BIC difference (2-comp vs 1-comp) must be ≥ 10 to confirm bimodality.
 - Minimum peak separation ≥ 0.1 R_earth (justified as the physical resolution limit for typical Kepler uncertainties).
 - **Unimodal Handling**: If BIC < 10, the bin is flagged as unimodal. The plan **triggers a merge with the adjacent bin**. If the merged bin is still unimodal, it is excluded from the final regression but reported in the "Gap Visibility" analysis.
- **Uncertainty**: Sufficient bootstrap resamples per bin to generate a confidence interval for the gap location.
- **Threshold Justification**: The 0.1 R_earth threshold is a physical resolution limit. A sensitivity analysis (FR-009) will test if the slope changes if this is relaxed to 0.05 R_earth.

### 3. Slope Calculation & Theory Comparison (FR-006, FR-007)
- **Regression**: Weighted Linear Regression of `gap_radius` vs `log(period)` using only bins where the gap was successfully resolved.
- **Theoretical Distributions**:
 - **Photoevaporation (Owen & Wu, 2017)**: Mean slope = -0.11, Std = 0.02.
 - **Core-Powered Mass Loss (Ginzburg et al., 2018)**: Mean slope = -0.15, Std = 0.03.
- **Simulation**: Monte Carlo simulation propagating both measured slope uncertainty and theoretical parameter uncertainty.
- **Hypothesis Test**:
 - **Method**: Calculate the probability (p-value) that the measured slope (drawn from its posterior) is consistent with the theoretical distribution. This correctly treats the theoretical parameters as distributions, avoiding the category error of a Z-score against a fixed value.
 - **Significance**: Bonferroni corrected α = 0.025 (for 2 tests).
 - **Inconsistency**: p-value < 0.025 indicates inconsistency with the theory.
- **Inference Framing**: Findings are framed as "consistency with theoretical predictions" for an associational trend. Causal claims are not made due to uncontrolled confounders (stellar age, metallicity).

### 4. Validation (FR-008, FR-009)
- **KDE Validation**: Adaptive bandwidth KDE on cumulative distribution. Pass if KDE gap falls within GMM 95% CI.
- **Synthetic Test**:
 - **Generation**: Generate synthetic planet populations with known bimodal radii and a predefined slope. Inject noise matching Kepler uncertainties.
 - **Recovery**: Run full pipeline. Verify recovered slope is within 5% of ground truth.
 - **Sensitivity**: Test recovery with the 0.1 R_earth threshold relaxed to 0.05 R_earth.

## Compute Feasibility & Rationale

The analysis is designed for a CPU-only environment (2 cores, 7GB RAM):
- **Data Volume**: Kepler DR is small (~few MBs). No GPU memory required.
- **GMM**: `scikit-learn` GMM is CPU-optimized. Fitting on a sufficient number of points per bin is trivial.
- **Bootstrap**: 1000 iterations per bin (max ~15 bins) = 15,000 GMM fits. This is computationally light on CPU.
- **Monte Carlo**: 10,000 iterations of simple Gaussian sampling. Negligible cost.
- **Total Runtime**: Estimated < 1 hour on standard CI. Well within the -hour limit.
- **Runtime Measurement**: The pipeline will log `run_duration_seconds` and compare against the 6-hour threshold (SC-005) in the final report.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use MAST for Kepler Data** | Verified source. `astroquery.mast` provides programmatic access to DR25 and KIC. |
| **Exclude, Don't Impute** | Adheres to Principle I (Data Integrity) and FR-002. Missing stellar data invalidates the radius calculation. |
| **Bonferroni Correction** | Required by FR-007 and Assumption (Multiplicity) to control family-wise error rate across two theory comparisons. |
| **KDE Validation** | Required by FR-008 to ensure GMM results are not artifacts of parametric assumptions. |
| **Completeness-Weighted GMM** | Replaces the flawed "completeness covariate" in regression. Corrects for Malmquist bias in the gap estimation phase. |
| **Monte Carlo P-value** | Replaces "overlap area" to provide a standard statistical test for consistency with theoretical distributions. |
| **Unresolved Bin Handling** | Bins failing BIC test are excluded from regression to prevent bias, but reported for transparency. |
| **Constitution Conflict** | Spec FR-007 (Monte Carlo) supersedes Constitution Principle VII (z-test). Flagged for amendment. |
| **Survivorship Bias Mitigation** | Merging bins introduces bias; final regression restricted to bins with sufficient power. "Gap Visibility" analysis reports on excluded regions. |
| **Threshold Justification** | 0.1 R_earth threshold is a physical resolution limit; sensitivity analysis tests robustness. |