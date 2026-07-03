# Feature Specification: Testing the Equivalence Principle with Satellite Laser Ranging

**Feature Branch**: `001-testing-equivalence-principle`
**Created**: 2026-06-21
**Status**: Draft
**Input**: User description: "Testing the Equivalence Principle with Satellite Laser Ranging physics"

## User Scenarios & Testing

### User Story 1 - Ingest and Preprocess SLR Normal Points (Priority: P1)

The system must successfully download, parse, and format multi-year Satellite Laser Ranging (SLR) normal-point data for a selected set of geodetic satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette) from the ILRS public archive.

**Why this priority**: Without clean, time-aligned observational data, no orbit determination or physics analysis can occur. This is the foundational data layer.

**Independent Test**: Can be fully tested by verifying the script downloads the specified epoch ranges, parses the ASCII/CSV normal-point files, and outputs a unified CSV with columns: `timestamp`, `satellite_id`, `range_m`, `sigma_m`, `elevation_deg`.

**Acceptance Scenarios**:

1. **Given** the ILRS archive contains valid normal-point files for LAGEOS-1 from 2020-01-01 to 2023-12-31, **When** the ingestion script runs, **Then** a unified CSV is generated containing exactly the expected number of rows with no parsing errors.
2. **Given** a corrupted or incomplete file in the archive, **When** the ingestion script runs, **Then** the script logs the error, skips the specific file, and continues processing remaining valid data without crashing.

---

### User Story 2 - Execute CPU-Tractable Orbit Determination (Priority: P2)

The system must perform a weighted least-squares orbit determination for each satellite using a CPU-only dynamical model (geopotential, drag, SRP, relativity) to estimate standard orbital elements and, in the alternative hypothesis model, estimate a composition-dependent acceleration parameter ($\eta$).

**Why this priority**: This establishes the baseline "null model" (no WEP violation) and the alternative model against which the hypothesis will be tested. It must run within the 6-hour free-tier limit.

**Independent Test**: Can be fully tested by running the orbit fit on a 1-year subset of data. **Target Metric**: Verify that the RMS of post-fit residuals is < 2.0 cm (matching expected SLR precision) and that the process completes within 45 minutes on a 2-core CPU. **Hard Constraint**: The full pipeline must complete within 6 hours on a 2-core runner.

**Acceptance Scenarios**:

1. **Given** preprocessed normal points and a standard Earth gravity model (e.g., GGM05C), **When** the orbit determination module runs, **Then** it outputs a file of post-fit residuals and a state vector for each epoch with a runtime < 6 hours on a 2-core CPU.
2. **Given** a convergence failure in the least-squares solver (e.g., due to bad initial guesses), **When** the module runs, **Then** it automatically retries with a perturbed initial state up to 3 times before flagging the specific time segment as "unconverged" in the log.

---

### User Story 3 - Compute Eötvös Parameter and Statistical Bounds (Priority: P3)

The system must calculate the differential acceleration between satellite pairs by estimating the Eötvös parameter ($\eta$) as a dynamic parameter in the least-squares solution, and perform an F-test (or BIC comparison) to establish a 95% confidence upper bound on WEP violation.

**Why this priority**: This delivers the scientific result (the constraint on $\eta$) and determines whether the null hypothesis can be rejected, fulfilling the research goal.

**Independent Test**: Can be fully tested by injecting a synthetic "fake" WEP violation signal into the differential acceleration term with magnitude $\eta_{synth} = 10^{-10}$ and period $T=1$ year. Verify the analysis correctly detects it with a p-value < 0.05, and conversely, that it reports a null result when no signal is present.

**Acceptance Scenarios**:

1. **Given** the differential residual time series between LAGEOS-1 and Starlette, **When** the statistical analysis runs, **Then** it outputs a 95% confidence interval for $\eta$ and a p-value for the F-test comparing the null vs. alternative model.
2. **Given** a scenario where the F-test indicates no significant improvement from the alternative model, **When** the analysis completes, **Then** the system outputs a conservative upper bound on $\eta$ (e.g., $\eta < 10^{-9}$) rather than a false positive detection.

### Edge Cases

- What happens when the ILRS archive is temporarily unavailable or rate-limited? (System retries with exponential backoff up to 5 times, then fails gracefully).
- How does the system handle satellites with sparse data coverage (e.g., < 100 points in a year)? (The system flags these as "insufficient data" and excludes them from the differential analysis to prevent statistical noise).
- How does the system handle collinearity between Solar Radiation Pressure (SRP) and the WEP signal if both are modeled simultaneously? (The system performs a Variance Inflation Factor (VIF) check; if VIF > 10, it reports the correlation and refrains from claiming independent significance for the SRP term. Note: Atmospheric drag is negligible for geodetic satellites like LAGEOS and is not the primary confounder).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download SLR normal-point data for at least 5 distinct geodetic satellites from the ILRS public archive (See US-1).
- **FR-002**: System MUST execute a weighted least-squares orbit determination using only CPU-tractable methods (no GPU/CUDA) and complete within 6 hours on a 2-core runner (See US-2).
- **FR-003**: System MUST compute the Eötvös parameter $\eta$ by estimating the composition-dependent acceleration term as a dynamic parameter in the least-squares solution for pairs of satellites with distinct bulk compositions (See US-3).
- **FR-004**: System MUST perform a statistical F-test (or BIC comparison) to evaluate the significance of the composition-dependent acceleration term against the null model (See US-3).
- **FR-005**: System MUST output a 95% confidence upper bound on $\eta$ and a CSV of post-fit residuals for independent validation (See US-3).
- **FR-006**: System MUST retrieve satellite mass, cross-sectional area, and specific nuclear composition metrics (Z/A ratios, neutron excess) from external catalogs. The system MUST check CelesTrak first, then the NASA NSSDC Master Catalog. If data is missing from both sources for a specific satellite ID, the system MUST log `MISSING_METADATA`, exclude that satellite from the differential analysis, and continue processing remaining satellites. (See US-1 for data ingestion scope).

### Key Entities

- **NormalPoint**: An observation record containing timestamp, range, sigma, and satellite ID.
- **OrbitSolution**: A time-series of estimated state vectors (position, velocity) and dynamic parameters (including $\eta$ if estimated) for a specific satellite.
- **ResidualSeries**: The difference between observed ranges and modeled ranges, used to derive acceleration anomalies.
- **WEPResult**: A structured output containing the estimated $\eta$, its confidence interval, and the F-test statistic.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The RMS of post-fit range residuals is measured against the expected SLR precision baseline (typically < 2.0 cm) as a Target Metric to validate orbit determination quality (See US-2).
- **SC-002**: The 95% confidence upper bound on the Eötvös parameter $\eta$ is measured against the current state-of-the-art limits from Lunar Laser Ranging (LLR) as defined by Adelberger et al. and Williams et al. to assess competitive validity (See US-3).
- **SC-003**: The total execution time of the full analysis pipeline is measured against the GitHub Actions free-tier limit to ensure feasibility (See US-2).
- **SC-004**: The p-value from the F-test is measured against the significance threshold $\alpha = 0.05$ to determine if the null hypothesis is rejected (See US-3).
- **SC-005**: The Variance Inflation Factor (VIF) for correlated predictors (SRP vs. WEP term) is measured against the threshold VIF < 10 to ensure measurement validity and avoid collinearity artifacts (See US-3).

## Assumptions

- The ILRS public archive provides sufficient historical normal-point data (at least 3 years of overlap) for the selected satellites (LAGEOS-1/2, Etalon-1/2, Starlette) to perform a statistically robust differential analysis.
- The material composition (density and bulk properties) of the selected satellites is available in public satellite catalogs (e.g., CelesTrak or NASA NSSDC) and can be reliably mapped to the ILRS data without ambiguity.
- The "free CPU" constraint (A minimal computational configuration, comprising a few cores and several gigabytes of RAM, will be employed to evaluate the research question regarding resource efficiency. The method involves a controlled simulation study [] to determine feasibility under constrained hardware conditions.) is sufficient for the orbit determination of these specific satellites if the time span is limited to a 1-year window per satellite or if data is subsampled to a 1-day cadence for the differential analysis.
- The dynamical models (geopotential, drag, SRP) available in the open-source `pyoorb` or `pyorbital` libraries are accurate enough that residual errors do not mimic a composition-dependent signal at a negligible level.
- The analysis frames findings as associational constraints on $\eta$ (observational test) rather than claiming causal proof of new physics, consistent with the non-randomized nature of satellite orbits.