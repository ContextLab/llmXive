# Feature Specification: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Feature Branch**: `001-assessing-orbital-period-dependence`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Assessing Orbital Period Dependence of the Exoplanet Radius Gap"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1)

**User Journey**: A researcher needs a clean, filtered dataset of confirmed Kepler exoplanets containing precise radius and orbital period measurements, along with stellar parameters, to begin the analysis.

**Why this priority**: Without a validated, filtered dataset, no statistical analysis can proceed. This is the foundational step that enables all subsequent modeling and hypothesis testing.

**Independent Test**: The pipeline can be fully tested by executing the data download and filtering scripts on a subset of the Kepler DR25 catalog and verifying that the output CSV contains only planets meeting the strict uncertainty criteria (radius <20%, period <1%) with no missing critical columns.

**Acceptance Scenarios**:

1. **Given** the Kepler DR25 and Input Catalogs are accessible via HTTPS, **When** the ingestion script runs, **Then** the output dataset contains only confirmed planets with radius uncertainty <20% and period uncertainty <1%, and excludes all others.
2. **Given** a planet entry in the raw catalog has missing stellar effective temperature, **When** the script processes this entry, **Then** the entry is excluded from the final dataset rather than imputed, ensuring data integrity.
3. **Given** the raw data contains duplicate planet entries, **When** the script processes the data, **Then** duplicates are resolved by keeping the entry with the lowest radius uncertainty, and a log of removed duplicates is generated.

---

### User Story 2 - Gap Location Estimation via Gaussian Mixture Modeling (Priority: P2)

**User Journey**: A researcher needs to identify the precise location of the radius gap within specific orbital period bins using a robust statistical method (two-component Gaussian Mixture Model) that accounts for the bimodal distribution, and quantify the uncertainty of these estimates.

**Why this priority**: This is the core analytical engine. It transforms raw planet counts into the specific "gap location" metric required to test the competing physical theories, while avoiding the artifacts of simple Gaussian assumptions on skewed data.

**Independent Test**: The GMM fitting logic can be independently tested by running it against a synthetic dataset with a known bimodal distribution and a known gap location, verifying that the algorithm correctly identifies the valley between peaks within a defined tolerance.

**Acceptance Scenarios**:

1. **Given** a period bin containing ≥30 planets with a bimodal radius distribution, **When** the GMM is fitted, **Then** the algorithm identifies the radius value with the minimum probability density between the two peaks as the gap location.
2. **Given** the gap location is estimated for a specific period bin, **When** 1000 bootstrap resamples are performed, **Then** a 95% confidence interval for the gap location is calculated and stored.
3. **Given** a period bin contains <30 planets, **When** the script attempts to fit the GMM, **Then** the bin is merged with the adjacent bin with the closest period, and a warning is logged indicating the merge.

---

### User Story 3 - Slope Calculation and Theory Comparison (Priority: P3)

**User Journey**: A researcher needs to determine the scaling relationship (slope) between the gap location and orbital period and compare this measured slope against the theoretical predictions of photoevaporation and core-powered mass loss using a robust statistical test that accounts for theoretical uncertainty.

**Why this priority**: This is the final synthesis step that answers the primary research question. It requires aggregating the results from the previous steps and performing the final statistical inference.

**Independent Test**: The regression and comparison logic can be independently tested by feeding it a mock dataset of gap locations with known slopes and verifying that the Monte Carlo simulation correctly identifies consistency or inconsistency with the theoretical distributions.

**Acceptance Scenarios**:

1. **Given** a set of gap locations with associated confidence intervals across multiple period bins, **When** the weighted linear regression is performed (using weighted mean periods), **Then** the slope and its 95% confidence interval are calculated.
2. **Given** the measured slope and its uncertainty, **When** a Monte Carlo simulation is performed using theoretical parameter distributions, **Then** the system outputs a p-value indicating statistical consistency or inconsistency.
3. **Given** the analysis is complete, **When** the final report is generated, **Then** it explicitly states which theoretical mechanism (if any) is favored based on the measured slope and includes the kernel density estimation (KDE) validation results, where the KDE gap location must fall within the GMM 95% confidence interval to pass (See FR-008).

### Edge Cases

- **What happens when** a period bin has a unimodal distribution instead of bimodal? The GMM fitting should fail gracefully, flagging the bin as "unresolved" rather than forcing a fit. A bin is considered unimodal if the Bayesian Information Criterion (BIC) difference between the 2-component model and the 1-component model is < 10 (approx. p-value > 0.05 for bimodality). The bin should be excluded from the final regression.
- **How does the system handle** extreme outliers in radius or period that fall far outside the main population? Outliers beyond a statistically significant threshold from the bin median radius should be flagged and optionally excluded before GMM fitting to prevent skewing the gap location.
- **What happens when** the Kepler Input Catalog is temporarily unavailable? The pipeline should retry the download up to 3 times with exponential backoff before failing with a clear error message, preventing partial data corruption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Kepler DR25 catalog and Kepler Input Catalog via HTTPS and parse them into a unified DataFrame (See US-1).
- **FR-002**: System MUST filter the dataset to retain only confirmed planets with radius uncertainty <20% and period uncertainty <1% (See US-1).
- **FR-003**: System MUST bin the filtered planets by orbital period using a set of log-spaced bins covering 0.7 to 2.0 log(days), which corresponds to the 5–100 day range. If a bin contains <30 planets, it MUST be merged with the adjacent bin with the closest period. The regression MUST use the weighted mean period of the planets in each bin (weighted by inverse variance of the gap location estimate) to mitigate binning bias (See US-2).
- **FR-004**: System MUST fit a two-component Gaussian Mixture Model (GMM) to the radius distribution within each valid period bin to identify the gap location. Initialization MUST use K-Means++ with multiple random seeds, selecting the model with the lowest Bayesian Information Criterion (BIC) to ensure reproducibility. The BIC difference between the 2-component model and the 1-component model MUST be calculated; a difference < 10 indicates unimodality and triggers bin merging. A minimum peak separation of ≥ 0.1 R_earth (in units of Earth radii) MUST be enforced to prevent overfitting (See US-2).
- **FR-005**: System MUST perform 1000 bootstrap resamples for each bin to estimate the uncertainty of the gap location (See US-2).
- **FR-006**: System MUST perform a weighted linear regression of gap radius versus log(period) (using weighted mean periods) to calculate the slope and its 95% confidence interval (See US-3).
- **FR-007**: System MUST execute a Monte Carlo simulation to compare the measured slope against the theoretical slope distributions predicted by the Owen & Wu (2017) and Ginzburg et al. (2018) models. The theoretical slopes MUST be treated as Gaussian distributions with means and standard deviations derived from the cited literature (e.g., Owen & Wu slope mean = -0.11, std = 0.02; Ginzburg slope mean = -0.15, std = 0.03), not as fixed constants. The simulation MUST propagate these theoretical uncertainties along with the measured slope uncertainty [deferred] iterations to generate a joint distribution. Consistency is determined by calculating the overlap area between the measured and theoretical distributions; a p-value < 0.05 (Bonferroni corrected to 0.025 for two tests) indicates inconsistency (See US-3).
- **FR-008**: System MUST validate the primary GMM results by performing kernel density estimation (KDE) with adaptive bandwidth on the cumulative distribution of radii to identify the gap location without assuming a specific parametric shape. The validation PASSES only if the KDE gap location falls within the confidence interval of the GMM estimate (See US-3).
- **FR-009**: System MUST validate the pipeline accuracy by processing a synthetic dataset with known ground-truth gap locations and slopes, recovering them within an acceptable error margin (See US-2).

### Key Entities

- **PlanetRecord**: Represents a single exoplanet observation; attributes include `planet_id`, `radius`, `radius_uncertainty`, `period`, `period_uncertainty`, `stellar_radius`, `stellar_mass`, `stellar_temp`.
- **PeriodBin**: Represents a specific orbital period interval; attributes include `bin_center_log_period`, `weighted_mean_log_period`, `planet_count`, `gap_location`, `gap_uncertainty`.
- **GapAnalysisResult**: Represents the final output; attributes include `measured_slope`, `slope_uncertainty`, `p_value_photoevaporation`, `p_value_core_powered`, `validation_status`, `sensitivity_status`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The measured slope of the radius gap versus log(period) is measured against the theoretical slope distributions (Gaussian) predicted by the Owen & Wu and Ginzburg et al. models to determine statistical consistency. Consistency is defined as the 95% confidence interval of the measured slope overlapping with the 95% credible interval of the theoretical distribution (See US-3).
- **SC-002**: The uncertainty of the gap location in each period bin is measured against the bootstrap resampling distribution to ensure robust error estimation. (See US-2).
- **SC-003**: The consistency of the primary GMM results is measured against the kernel density estimation (KDE) results to validate the gap-finding methodology (See US-3).
- **SC-004**: The statistical power of each period bin is measured against a minimum threshold of sufficient planets (or merged bin equivalent) to ensure reliable bimodal detection. (See US-2).
- **SC-005**: The computational runtime of the full analysis pipeline is measured against a concrete duration of ≤ 6 hours on a GitHub Actions default ubuntu-latest runner (2-core, 7GB RAM) to ensure feasibility (See Assumptions).
- **SC-006**: The stability of the gap location is measured against the Gaussian Mixture Model results compared to the kernel density estimation (KDE) results to verify robustness to distribution shape assumptions (See US-2).

## Assumptions

- **Assumption about data availability**: The Kepler DR catalog and Kepler Input Catalog are publicly accessible via the MAST archive without requiring special authentication or rate-limiting that would block automated retrieval.
- **Assumption about dataset-variable fit**: The Kepler DR25 catalog contains all necessary variables (radius, period, uncertainties) and the Input Catalog contains the required stellar parameters (radius, mass, temperature) to compute incident flux and refine radius estimates; if specific stellar parameters are missing for a subset of stars, those planets will be excluded rather than imputed.
- **Assumption about inference framing**: Since this analysis uses observational data from the Kepler mission without random assignment, all findings regarding the relationship between period and gap location will be framed as associational, not causal, unless a specific identification strategy is introduced in the code.
- **Assumption about multiplicity & power**: The analysis involves multiple hypothesis tests (slope comparison against two theories). To control the family-wise error rate, a Bonferroni correction is applied, adjusting the significance threshold to α = 0.025 (0.05 / 2). The binning strategy (minimum 30 planets) is assumed to provide sufficient power for the GMM fitting.
- **Assumption about threshold justification**: The decision cutoff for bin inclusion (≥30 planets) and uncertainty thresholds (<20% radius, <1% period) are based on community standards for statistical robustness in exoplanet demographics.
- **Assumption about compute feasibility**: The entire analysis, including bootstrap iterations and GMM fitting, can be completed on a CPU-only environment with a minimal number of cores and modest RAM by using optimized vectorized operations and processing the Kepler dataset in manageable chunks if necessary, without requiring GPU acceleration or large model training.
- **Assumption about measurement validity**: The radius and period values in the Kepler catalog are treated as validated measurements derived from the transit light curves, and the Gaussian Mixture Model is assumed to be an appropriate method for identifying the gap in the presence of measurement noise and population skewness.
- **Assumption about predictor collinearity**: While period and radius are measured as independent observables, the regression explicitly models the functional dependence of gap location on period. The analysis MUST apply a completeness correction using the Kepler completeness map as a covariate in the regression model to account for Malmquist bias and detection limits. Period and radius are not treated as independent in the presence of selection effects.

## Constitution

- **Principle I**: Data integrity is paramount; no imputation of missing critical stellar parameters.
- **Principle II**: No factual claims without primary source citation.
- **Principle III**: All statistical thresholds must be concrete numbers.
- **Principle IV**: Traceability from User Stories to Requirements and Success Criteria.
- **Principle V**: Reproducibility via fixed random seeds and documented initialization.
- **Principle VI**: Uncertainty quantification via bootstrap (minimum 1000 iterations) and Monte Carlo propagation.
- **Principle VII**: Slope comparison to theoretical predictions MUST use a Monte Carlo simulation propagating full theoretical uncertainty distributions (Gaussian parameters from cited literature), not a z-test against fixed bounds.
- **Principle VIII**: Validation via independent methods (KDE vs GMM) is mandatory.