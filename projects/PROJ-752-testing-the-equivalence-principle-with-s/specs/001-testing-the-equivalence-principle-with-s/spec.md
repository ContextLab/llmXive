# Feature Specification: Testing the Equivalence Principle with Satellite Laser Ranging

**Feature Branch**: `001-testing-equivalence-principle`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Do geodetic satellites of differing composition (e.g., LAGEOS 1 / 2, Etalon‑1 / 2, Starlette) exhibit measurable differential accelerations that would violate the weak equivalence principle (WEP)?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Orbit Pre-processing (Priority: P1)

The researcher must be able to download multi-year Satellite Laser Ranging (SLR) normal-point series for specific geodetic satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette) from the ILRS public archive and process them into a clean, time-aligned dataset compatible with the orbit determination engine.

**Why this priority**: Without high-fidelity, clean observational data spanning multiple years, no dynamical modeling or parameter estimation can occur. This is the foundational input for the entire study.

**Independent Test**: Can be fully tested by executing the data ingestion pipeline and verifying that the output CSV contains ≥ 95% of the total normal points available in the ILRS archive for the requested date range, with no NaN values in the range or timestamp columns.

**Acceptance Scenarios**:

1. **Given** the ILRS archive is accessible, **When** the script requests normal points for LAGEOS-1, **Then** the system downloads the data and outputs a CSV with at least 10,000 valid range measurements.
2. **Given** a satellite with sparse coverage (e.g., Starlette in early years), **When** the script filters for data quality, **Then** the system excludes points with residuals > 2 cm and logs the exclusion count.
3. **Given** the download fails for one satellite (e.g., Etalon-2), **When** the pipeline runs, **Then** the system logs a warning, proceeds with available data, and reports the specific satellite ID missing in the final summary.

---

### User Story 2 - Differential Acceleration Parameter Estimation (Priority: P2)

The researcher must be able to run two separate weighted least-squares orbit determination fits (one for each satellite in a pair) using a high-fidelity dynamical model (geopotential, drag, SRP, relativity), and then calculate the differential acceleration term ($a_c$) and the Eötvös parameter ($\eta$) from the difference in the estimated non-gravitational accelerations.

**Why this priority**: This is the core scientific computation. It transforms raw data into the specific parameter ($a_c$) required to test the Weak Equivalence Principle.

**Independent Test**: Can be fully tested by running the estimation script on a subset of LAGEOS data and verifying that:
1. The solver converges (residuals < 1e-5 meters) for both satellites.
2. The system outputs a non-null estimate for $a_c$ with a valid covariance matrix.
3. The system explicitly calculates and outputs the Eötvös parameter $\eta$ and its 95% confidence interval, verifying that the calculation logic correctly derives $\eta$ from the difference in accelerations and that the confidence interval is derived from the propagated covariance matrix.

**Acceptance Scenarios**:

1. **Given** a converged orbit solution for both satellites, **When** the composition-dependent term is calculated from the difference in non-gravitational accelerations, **Then** the system outputs the post-fit residual RMS for both the null model ($a_c=0$) and the alternative model, allowing the researcher to calculate the improvement.
2. **Given** two satellites of different composition, **When** the differential acceleration is calculated, **Then** the system outputs the Eötvös parameter $\eta$ with a 95% confidence interval derived from the covariance matrix.
3. **Given** a model that fails to converge after 100 iterations, **When** the solver retries with a relaxed tolerance, **Then** the system logs the failure and outputs the best-fit parameters found so far rather than crashing.

---

### User Story 3 - Statistical Validation and Robustness Analysis (Priority: P3)

The researcher must be able to compare the null model against the alternative model using an F-test or BIC, and perform a sensitivity analysis by varying the geopotential model to ensure the result is robust against model misspecification.

**Why this priority**: This step provides the scientific rigor required to claim a discovery or an upper bound. It ensures that the result is not an artifact of arbitrary cutoffs or unmodeled geopotential errors.

**Independent Test**: Can be fully tested by executing the validation script and verifying that it produces a sensitivity plot showing the variation in the Z-score ($\eta / SE_\eta$) across different geopotential models and outputs the final p-value.

**Acceptance Scenarios**:

1. **Given** the null and alternative model fits, **When** the F-test is performed, **Then** the system outputs a p-value and flags the result as "Significant" if $p < 0.05$.
2. **Given** a geopotential model sweep configuration, **When** the script runs, **Then** it evaluates $\eta$ using at least three distinct geopotential models (e.g., GGM05C, EGM2008, GOCO06s) and reports the variation in the Z-score.
3. **Given** multiple satellite pairs are tested simultaneously, **When** the family-wise error is calculated, **Then** the system applies a configurable multiple-comparison correction (default: Bonferroni) and reports the adjusted p-value.

---

### User Story 4 - Compute Feasibility & Resource Validation (Priority: P4)

The researcher must be able to validate that the entire analysis pipeline (data ingestion, orbit determination, and statistical validation) can complete within the constraints of the target compute environment (GitHub Actions free-tier).

**Why this priority**: Ensures the proposed methodology is feasible within the available resources before committing to a full-scale run.

**Independent Test**: Can be fully tested by running the full pipeline on a representative subset of data and verifying that the total compute time remains within a practical operational window.

**Acceptance Scenarios**:

1. **Given** a representative dataset (e.g., 1 year of LAGEOS data), **When** the full pipeline is executed, **Then** the system completes all steps within 6 hours.
2. **Given** a run that exceeds 6 hours, **When** the process is monitored, **Then** the system logs a warning and reports the specific stage causing the delay.

---

### Edge Cases

- What happens when the ILRS archive is temporarily offline or returns a 403 error? (System must implement exponential backoff retry up to 3 attempts, then fail gracefully with a clear error message).
- How does the system handle a satellite with insufficient data points (< 500) to constrain the orbit? (System must skip that satellite in the differential analysis and log a specific "Insufficient Data" warning).
- How does the system handle potential bias from unmodeled geopotential errors? (System must perform a sensitivity analysis by varying the geopotential model (e.g., GGM05C vs EGM2008); if the Z-score varies by > 20% across models, it must flag the result as "Unreliable due to geopotential uncertainty").

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse SLR normal-point series for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette from the ILRS archive, filtering for quality < 2 cm. (See US-1)
- **FR-002**: System MUST generate a high-fidelity dynamical model including geopotential (GGM05C), atmospheric drag, solar radiation pressure, and relativistic corrections for each satellite. (See US-2)
- **FR-003**: System MUST perform two separate weighted least-squares fits (one per satellite) to estimate orbital elements and non-gravitational accelerations, then calculate the differential acceleration term $a_c$ from the difference. (See US-2)
- **FR-004**: System MUST calculate the Eötvös parameter $\eta = |a_c| / g$ and its 95% confidence interval for each satellite pair, where $a_c$ is the differential acceleration ($|a_1 - a_2|$) and $g$ is the local gravitational acceleration at the satellite's orbital altitude. (See US-2)
- **FR-005**: System MUST perform a sensitivity analysis by running the estimation with at least three distinct geopotential models (e.g., GGM05C, EGM2008, GOCO06s) and report the resulting Z-scores ($\eta / SE_\eta$) for each model. (See US-3)
- **FR-006**: System MUST apply a configurable multiple-comparison correction (default: Bonferroni; options: Bonferroni, Holm-Bonferroni, Benjamini-Hochberg) when testing more than one satellite pair to control family-wise error. (See US-3)
- **FR-007**: System MUST output a diagnostic report including the $\chi^2$ improvement, the final $\eta$ limit, and a CSV of post-fit residuals. (See US-2)

### Key Entities

- **NormalPoint**: Represents a single SLR observation with attributes: timestamp, range, satellite_id, station_id, quality_flag.
- **OrbitSolution**: Represents a fitted dynamical model with attributes: orbital_elements, non_gravitational_acceleration, covariance_matrix, $\chi^2$, residuals.
- **EotvosResult**: Represents the final test outcome with attributes: $\eta$ value, confidence_interval, p_value, sensitivity_sweep_data (Z-scores per geopotential model).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The post-fit residual RMS of the orbit determination is measured against the pre-fit residual RMS to verify model improvement. (See US-2)
- **SC-002**: The width of the 95% confidence interval of the Eötvös parameter $\eta$ is measured and reported to assess if it meets the target research precision at the level of high-precision numerical stability (citing current state-of-the-art benchmarks). (See US-3)
- **SC-003**: The F-test p-value is measured against the significance threshold of a conventional level (adjusted for multiple comparisons) to determine statistical validity. (See US-3)
- **SC-004**: The variation in the Z-score ($\eta / SE_\eta$) is measured across the geopotential model sweep to verify robustness against model misspecification. (See US-3)
- **SC-005**: The total compute time is measured against the free-tier runner limit to verify feasibility. (See US-4)

## Assumptions

- **Assumption about data availability**: The ILRS public archive contains sufficient multi-year normal-point data for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, and Starlette to perform a statistically significant test (minimum 500 points per satellite).
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (CPU, sufficient RAM) using CPU-tractable methods (scikit-learn, classical statistics) without GPU acceleration or large-model inference, with a a hard limit on the runtime per run.
- **Assumption about dynamical models**: The GGM05C Earth gravity field model and standard atmospheric drag models (e.g., Jacchia) are sufficient to model non-compositional forces to the required precision.
- **Assumption about statistical framing**: Since the study is observational (no random assignment of satellite composition), all findings regarding $\eta$ will be framed as associational limits or upper bounds, not causal proofs of WEP violation, unless a specific identification strategy is introduced later.
- **Assumption about target precision**: The target research precision for the Eötvös parameter is high sensitivity levels, based on current state-of-the-art benchmarks (e.g., Müller et al.).
- **Assumption about dataset-variable fit**: The SLR normal points and satellite metadata (mass, composition) provided by ILRS contain all necessary variables to compute the differential acceleration; if a specific composition variable is missing for a satellite, that satellite will be excluded from the differential analysis.