# Deviations Log

This document tracks formal deviations from the project's original scope, feature requirements, and data acquisition plans as mandated by Constitution Principle II.

## Table of Contents

1. [FR-001: Global Data Download Blocked](#fr-001-global-data-download-blocked)
2. [FR-011: Climate Index Deferment](#fr-011-climate-index-deferment)

---

## FR-001: Global Data Download Blocked

**Status**: Active
**Date Recorded**: 2023-10-27
**Reference**: `specs/001-exploring-the-correlation-between-atmosp/plan.md`, `code/download.py`

### Description
The original feature requirement FR-001 intended to download global atmospheric pressure data from the NOAA NCEP/NCAR Reanalysis 1 dataset. This deviation records the explicit blocking of this global download due to the absence of a verified, programmatically accessible, and stable source for the full historical global dataset within the project's compute and bandwidth constraints.

### Justification
- **Source Verification Failure**: Extensive attempts to locate a direct, programmatic download endpoint for the full global NCEP/NCAR dataset (e.g., via `cdsapi` or direct FTP mirrors) have failed or resulted in unstable connections unsuitable for automated CI/CD pipelines.
- **Resource Constraints**: The full global dataset exceeds the memory and disk limits of the standard execution environment (~7GB RAM / ~14GB disk), and streaming the full historical record is not feasible for the current pilot phase.
- **Scope Reduction**: To ensure the project remains executable and reproducible, the scope has been reduced to a verified test subset.

### Fallback Strategy
The project now relies exclusively on **verified test data** for the 2018 Alaska subset.
- **Data Source**: USGS Earthquake Catalog (verified via `https://earthquake.usgs.gov/fdsnws/event/1/query`).
- **Pressure Data**: Synthetic test data generated to match the schema of the expected pressure anomalies, derived from the 2018 Alaska subset coordinates, as a placeholder for the missing global source.
- **Constraint**: All analysis is strictly limited to this subset (N=12 earthquakes) for the purpose of pipeline validation.

### Verification Logic
To confirm this state and prevent accidental execution against non-existent global sources, the following verification logic is implemented in `code/download.py` (function `verify_deviations`):
1. Check for the existence of the global NOAA source URL. If it fails to resolve or returns a non-200 status, raise a `DataUnavailableError`.
2. Explicitly check for the presence of the deviation record in this file (`docs/deviations.md`). If missing, raise a `ConfigurationError`.
3. Enforce that the input dataset is strictly the 2018 Alaska subset (or a synthetic equivalent with matching schema). If the dataset contains global coordinates outside the defined test region, the pipeline must fail.

### Impact on Analysis
- **Generalizability**: Results are not generalizable to global seismicity.
- **Statistical Power**: Limited to the small sample size of the test subset.
- **Conclusion Framing**: All outputs must be explicitly labeled as "Pilot/Methodology Validation" and not as a definitive scientific conclusion on global correlations.

---

## FR-011: Climate Index Deferment

**Status**: Deferred
**Date Recorded**: 2023-10-27
**Reference**: `specs/001-exploring-the-correlation-between-atmosp/plan.md`

### Description
The original requirement FR-011 to stratify control windows by ENSO (El Niño-Southern Oscillation) and PDO (Pacific Decadal Oscillation) indices has been deferred due to the lack of verified, real-time accessible sources for these specific climate indices in the current environment.

### Justification
- **Data Availability**: No verified, programmatic source for historical ENSO/PDO indices was found that integrates seamlessly with the current data pipeline without external API keys or complex authentication.
- **Scope Reduction**: To maintain the pilot focus on the core pressure-seismicity correlation, this stratification layer is removed for the current iteration.

### Fallback Strategy
Control windows are matched by month/day across non-event years (basic date matching) only, as implemented in `code/analysis.py` (function `stratify_control_windows`).

### Verification Logic
The system checks for the absence of ENSO/PDO data sources and labels any resulting analysis as "Unverified Climate Stratification" in the output artifacts, referencing this deviation record.

### Impact on Analysis
- **Confounding Variables**: Potential climate-driven pressure anomalies are not explicitly controlled for, introducing a limitation in the causal interpretation of results.
- **Reporting**: The final report must explicitly state that climate stratification was not performed.