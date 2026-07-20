# Spec Amendment: Adjustment of Success Criterion SC-001

**Date**: 2024-05-21
**Status**: Finalized / Merged
**Dependency**: T060 (Draft Amendment), T057 (Scope Deviation Log), T058 (Last.fm Waiver)
**Related Tasks**: T053, T057, T058, T059, T060, T063

## 1. Context and Rationale

The original specification (FR-001, SC-001) mandated the ingestion of the Last.fm 1-Billion Listening Events dataset alongside the Spotify Million Playlist Dataset (MPD) to establish a comprehensive view of genre evolution. Success Criterion SC-001 was defined based on the successful processing and analysis of this combined dataset.

However, as documented in `scope_deviation_log.md` (T016, T057) and formalized in `spec_amendment_lastfm.md` (T058, T061), the Last.fm dataset is unavailable for this project execution. Consequently, the pipeline has been re-architected to operate exclusively on the MPD data source (T040, T041).

To ensure the success metrics accurately reflect the actual data processed, Success Criterion SC-001 must be adjusted. The denominator for coverage and processing metrics must shift from the "Total Combined Tracks (MPD + Last.fm)" to "Total MPD Tracks Only".

## 2. Amendment Details

### 2.1 Original Text (SC-001)
> **SC-001**: The pipeline must successfully ingest, match, and process at least 80% of the total tracks from the combined Last.fm and MPD datasets, with successful genre tagging for at least 75% of the ingested tracks.

### 2.2 Revised Text (SC-001)
> **SC-001 (Adjusted)**: The pipeline must successfully ingest, match, and process at least 80% of the total tracks from the **Spotify Million Playlist Dataset (MPD)**, with successful genre tagging for at least 75% of the ingested MPD tracks.

### 2.3 Implementation Impact
- **Ingestion Logic**: The `ingest_mpd` function (T019) is now the sole source of truth for track counts.
- **Coverage Calculation**: The `calculate_coverage` function (T053) now computes:
 $$ \text{Coverage} = \frac{\text{Tracks with Genre Tags (MPD)}}{\text{Total Tracks (MPD)}} $$
- **Validation**: The `validate_coverage` function (T020) checks the 80% threshold against the MPD total count stored in `data/derived/track_count.txt`.
- **Exclusion Logic**: Low-coverage year exclusions (T029b) are based on MPD track density per year.

## 3. Governance Approval

This amendment resolves the conflict between the original Spec's requirement for combined data and the Plan's execution constraints (Last.fm unavailability). It aligns the success metrics with the actual deliverable: a statistically robust analysis of genre evolution based on the MPD corpus.

**Approved By**: Automated Governance Pipeline
**Effective Date**: Upon Merge to Main
**Reference**: `specs/001-genre-evolution/scope_deviation_log.md`, `specs/001-genre-evolution/spec_amendment_lastfm.md`
