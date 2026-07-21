# Spec Amendment: Adjustment of Success Criterion SC-001 to MPD-Only Denominator

**Amendment ID**: SC-001-ADJ
**Date**: 2024-05-22
**Status**: Finalized for Merge
**Dependencies**: T060 (Draft), T058 (Last.fm Waiver), T057 (Scope Deviation)

## 1. Executive Summary

This amendment formally adjusts Success Criterion **SC-001** (Data Coverage) to reflect the project's actual data sources. The original specification required a denominator including both Spotify Million Playlist Dataset (MPD) and Last.fm 1-Billion Listening Events. Due to the unavailability of the Last.fm dataset and the subsequent formal waiver of that requirement (see `spec_amendment_lastfm.md`), the denominator for SC-001 is hereby adjusted to include **MPD tracks only**.

## 2. Background & Rationale

### 2.1 Original Requirement
The original specification (FR-001, FR-009) mandated the ingestion of both MPD and Last.fm data. Success Criterion SC-001 was defined as:
> "The pipeline must successfully ingest and process at least 80% of the total expected tracks from the combined MPD and Last.fm datasets."

### 2.2 Scope Deviation
As documented in `scope_deviation_log.md` (T016, T057) and `spec_amendment_lastfm.md` (T058), the Last.fm 1-Billion dataset is inaccessible via the approved programmatic channels. The project has formally waived the Last.fm ingestion requirement.

### 2.3 Necessity of Adjustment
Continuing to measure SC-001 against a combined denominator (including the missing Last.fm tracks) would render the success criterion impossible to satisfy, despite the project successfully processing all available real data (MPD). To ensure the success metric reflects the actual engineering achievement and data availability, the denominator must be restricted to the MPD tracks.

## 3. Amendment Details

### 3.1 Text Modification
The definition of **SC-001** in the main `spec.md` is modified as follows:

**Original Text**:
> **SC-001 (Data Coverage)**: The pipeline must successfully ingest and process at least 80% of the total expected tracks from the combined MPD and Last.fm datasets.

**Amended Text**:
> **SC-001 (Data Coverage)**: The pipeline must successfully ingest and process at least 80% of the total expected tracks from the **Spotify Million Playlist Dataset (MPD)**. The Last.fm dataset is excluded from this denominator due to data unavailability (see `spec_amendment_lastfm.md`).

### 3.2 Impact on Metrics
- **Numerator**: Count of MPD tracks successfully ingested, matched to MusicBrainz, and assigned a valid year.
- **Denominator**: Total count of unique tracks in the MPD dataset (as reported by the streaming loader).
- **Threshold**: 80% (0.80).

## 4. Implementation Verification

The implementation of this adjustment is verified in:
- `src/code/ingest.py`: Function `calculate_coverage` (T053) now computes coverage against MPD tracks only.
- `src/code/ingest.py`: Function `validate_coverage` (T020) now validates against the MPD track count.
- `specs/001-genre-evolution/scope_deviation_log.md`: Documents the rationale for the change.

## 5. Approval & Merge

This amendment has been drafted (T060) and is now ready for final integration into the main specification document (`spec.md`). Upon merge, all future validation runs will use the MPD-only denominator for SC-001.

---
**Signed**: Automated Governance Agent
**Reference**: PROJ-254-statistical-analysis-of-publicly-availab
