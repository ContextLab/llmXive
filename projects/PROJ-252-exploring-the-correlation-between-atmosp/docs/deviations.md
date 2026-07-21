# Project Deviations and Scope Reductions

This document formally records deviations from the original functional requirements (FRs)
as mandated by Constitution Principle II. Each deviation includes the reason, impact,
and verification logic.

## Table of Contents

1. [FR-001: Global Data Download Blocked](#fr-001-global-data-download-blocked)
2. [FR-011: Climate Index Stratification Deferred](#fr-011-climate-index-stratification-deferred)

---

## FR-001: Global Data Download Blocked

**Status**: Active
**Impact**: High
**Verification**: See `verify_deviations()` in `code/download.py`

### Description
The original requirement FR-001 specified downloading global atmospheric pressure data
from NOAA NCEP/NCAR for the period 2013-2023. This download is explicitly blocked due
to the absence of verified, programmatically accessible sources for this specific dataset
within the project's compute and bandwidth constraints.

### Reason
- No verified global NOAA NCEP/NCAR download source is available.
- The global dataset (2013-2023) exceeds the compute budget for the pilot phase.
- The pilot scope (T011a) is limited to a verified test subset (2018 Alaska, N=12).

### Fallback Strategy
The project uses a **Pilot Scope** approach:
- Only the 2018 Alaska subset (N=12 earthquakes) is processed.
- Verified test data is used for validation.
- Global data feasibility remains unverified.

### Verification Logic
The system must explicitly check for the absence of the global source and log this state.
The `verify_deviations()` function in `code/download.py` performs this check.

---

## FR-011: Climate Index Stratification Deferred

**Status**: Active
**Impact**: Medium
**Verification**: See `stratify_control_windows()` in `code/analysis.py`

### Description
The original requirement FR-011 specified stratifying control windows by climate indices
(ENSO, PDO) to account for climate variability. This is deferred due to the absence of
verified ENSO/PDO data sources.

### Reason
- No verified, programmatically accessible ENSO/PDO data sources are available.
- The complexity of integrating climate indices exceeds the pilot scope.

### Fallback Strategy
- Use **date-matching** (month/day across non-event years) as a proxy for climate stratification.
- This is a staged simplification.
- The output artifacts are labeled as "unverified" regarding climate stratification.

### Verification Logic
- The `stratify_control_windows()` function implements date-matching.
- The `docs/pilot_report.md` explicitly states this limitation.
- A comparison of date-matched vs. climate-index-matched distributions is planned for a future pilot subset.

---

## Verification Summary

| Deviation | Status | Verification Step |
|-----------|--------|-------------------|
| FR-001 | Active | `verify_deviations()` checks for global source absence |
| FR-011 | Active | `stratify_control_windows()` uses date-matching; report notes limitation |
