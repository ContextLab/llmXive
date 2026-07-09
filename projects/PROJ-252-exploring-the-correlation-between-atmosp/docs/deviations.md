# Deviations and Scope Reductions

This document formally records all deviations from the original project design (specs/001-exploring-the-correlation-between-atmosp) as required by Constitution Principle II.

## Table of Contents

- [FR-001: Global Data Download Blocked](#fr-001-global-data-download-blocked)
- [FR-011: Climate Index Deferment](#fr-011-climate-index-deferment)

---

## FR-001: Global Data Download Blocked

**Original Requirement**: Download and process global atmospheric pressure data from NOAA NCEP/NCAR reanalysis datasets.

**Deviation**: Verified global NOAA NCEP/NCAR sources are not programmatically accessible without authentication or are blocked by current infrastructure constraints.

**Impact**: The analysis is restricted to a verified test dataset (2018 Alaska subset, N=12 earthquakes) for methodology validation. [UNRESOLVED-CLAIM: c_33f2153f — status=not_enough_info]

**Fallback Strategy**:
- Use USGS earthquake catalog for the 2018 Alaska region (M≥4.0, depth≤70km).
- Use a verified, static test dataset for pressure anomalies corresponding to these events.
- The pipeline explicitly checks for the absence of global sources and logs this deviation.

**Verification Logic**:
1. Attempt to access global NOAA NCEP/NCAR endpoints.
2. If access fails or returns invalid data, log "Global source unavailable" and switch to test data mode.
3. Verify the test dataset contains exactly 12 events.
4. If the event count deviates, raise an error.

**Status**: Active (Pilot Phase)

---

## FR-011: Climate Index Deferment

**Original Requirement**: Stratify control windows by ENSO (El Niño-Southern Oscillation) and PDO (Pacific Decadal Oscillation) indices to control for climate variability.

**Deviation**: Verified programmatic sources for real-time ENSO/PDO indices are unavailable or require external APIs not covered in this pilot.

**Impact**: Control windows are matched only by month/day across non-event years, without climate stratification.

**Fallback Strategy**:
- Label the fallback as "unverified" in output artifacts.
- Document the lack of climate stratification in the final report.

**Verification Logic**:
1. Check for availability of ENSO/PDO data sources in `code/config.py` or external APIs.
2. If unavailable, set `climate_stratification_enabled = False`.
3. Output a warning in `data/processed/statistical_results.json` and `docs/pilot_report.md`.

**Status**: Active (Pilot Phase)

---

## Other Deviations

- **FR-005 (Associational Framing)**: Implemented. All results are explicitly labeled as "associational" rather than causal.
- **FR-006 (FDR Correction)**: Implemented. Benjamini-Hochberg correction is applied to multiple tests.
- **FR-008 (Validation Report)**: Implemented. A JSON validation report is generated for missing variables.

## References

- `docs/pilot_report.md`: Final report referencing these deviations.
- `code/download.py`: Implementation of FR-001 check.
- `code/analysis.py`: Implementation of FR-011 fallback.
- `docs/README.md`: High-level summary of limitations.