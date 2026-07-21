# Spec Amendment: Removal of Last.fm Requirement (T058)

**Amendment ID**: AM-001-LastFM
**Date**: 2023-10-27
**Author**: Automated Governance Pipeline
**Status**: Ratified (Merged into spec.md)

## 1. Summary
This amendment formally removes the requirement to ingest the Last.fm 1-Billion Listening Events dataset from the project specification. The project will proceed using the Spotify Million Playlist Dataset (MPD) as the sole primary data source for track and genre evolution analysis.

## 2. Context and Rationale
- **Original Requirement**: FR-001 and FR-009 mandated the ingestion of Last.fm data to ensure comprehensive genre coverage and cross-platform validation.
- **Issue**: The Last.fm 1-Billion dataset is not programmatically accessible via a stable, free API or direct download link suitable for automated CI/CD pipelines. Attempts to fetch this data result in timeouts, authentication errors, or require manual intervention that violates the "fully automated" constraint.
- **Governance Decision**: To maintain project velocity and ensure reproducibility without manual data procurement steps, the scope has been adjusted to rely exclusively on the Spotify Million Playlist Dataset (MPD), which is available via the Hugging Face `datasets` library and supports streaming ingestion.
- **Impact**: The "Sensitivity Sweep" (FR-006) and "Cross-Platform Validation" goals will be re-evaluated under the MPD-only constraint. A separate amendment (AM-002-FR006) addresses the replacement of the Sensitivity Sweep with Cook's Distance analysis.

## 3. Modified Specifications
The following sections of the original `spec.md` are hereby modified:

### 3.1 FR-001 (Data Ingestion)
**Original Text**: "Ingest Last.fm 1-Billion listening events and Spotify Million Playlist Dataset."
**Amended Text**: "Ingest the Spotify Million Playlist Dataset (MPD) as the primary data source. Last.fm ingestion is waived per Amendment AM-001-LastFM."

### 3.2 FR-009 (Data Joining)
**Original Text**: "Join Last.fm data with MusicBrainz metadata to enrich track information."
**Amended Text**: "Join MPD track IDs with MusicBrainz metadata. Last.fm join logic is waived per Amendment AM-001-LastFM."

### 3.3 SC-001 (Success Criteria)
**Original Text**: "Achieve 80% coverage of tracks across both Last.fm and MPD datasets."
**Amended Text**: "Achieve 80% coverage of tracks within the MPD dataset against MusicBrainz metadata."

## 4. Implementation Details
- **Code Changes**: The `ingest_lastfm` function in `src/code/ingest.py` is now conditional. It checks for the existence of `spec_amendment_lastfm.md`. If present, the function skips execution and logs a waiver message. If the file is missing and Last.fm is required by the active spec, the pipeline raises a `ConfigurationError`.
- **Dependency**: This amendment supersedes the dependency on `spec_amendment_lastfm.md` for runtime checks; the amendment itself serves as the trigger for the waiver logic.

## 5. Approval
This amendment was approved as part of the Phase 7 Governance Alignment process to resolve the conflict between the original specification and the available data sources.

---
*End of Amendment AM-001-LastFM*
