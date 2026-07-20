# Spec Amendment Request: Last.fm Data Source Omission

**Date**: 2024-05-21
**Project**: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution (PROJ-254)
**Status**: Pending Approval
**Author**: Automated Research Pipeline (llmXive)

---

## 1. Executive Summary

This document formally requests a Specification Amendment to modify the data ingestion requirements defined in **FR-001** and **FR-009**. The amendment proposes the permanent omission of the **Last.fm** dataset from the pipeline's ingestion phase due to the unavailability of a reliable, programmatic, and free data source that meets the project's reproducibility and scale requirements.

Consequently, the pipeline will proceed with a **Spotify Million Playlist Dataset (MPD)**-only architecture. All downstream analysis, including genre evolution tracking and similarity calculations, will be derived exclusively from the MPD data stream.

---

## 2. Background & Context

### 2.1 Original Specification Requirements
- **FR-001**: "The system must ingest and process data from the Last.fm API and the Spotify Million Playlist Dataset (MPD)."
- **FR-009**: "The system must correlate track metadata from Last.fm with MusicBrainz identifiers to enrich genre tagging."

### 2.2 The Scope Deviation (T016)
A prior scope deviation was documented in `specs/001-genre-evolution/scope_deviation_log.md` (Task T016). This log identified that while the MPD source is stable and accessible via the Hugging Face `datasets` library, the Last.fm API:
1. Requires an API key with rate limits that prevent bulk ingestion of the required scale.
2. Lacks a public, downloadable "full dump" that matches the specific track IDs in the MPD without prohibitive query costs.
3. Presents a high risk of pipeline failure during the execution phase due to transient network or quota issues.

### 2.3 Dependency on T016
This amendment request is the formal governance step following the documentation in T016. It seeks to ratify the decision to treat Last.fm as a "Blocked" source rather than a "Failed Retry" source, allowing the pipeline to run deterministically on the available MPD data.

---

## 3. Technical Justification

### 3.1 Data Source Availability
- **MPD (Spotify)**: Available as `spotify_million_playlist` on Hugging Face. Supports streaming (`streaming=True`), ensuring memory safety (FR-011) and full dataset contribution without fabrication.
- **Last.fm**: No verified, open-access bulk dataset exists that aligns with the MPD track IDs. The REST API is unsuitable for processing millions of tracks within the project's time and compute constraints.

### 3.2 Impact on Analysis
The primary research question—*"How do genre embeddings evolve over time?"*—can be robustly answered using the MPD dataset alone. The MPD contains:
- Track titles and artist names.
- Playlist context (implicitly defining co-occurrence for Word2Vec).
- Release year metadata (via MusicBrainz join).

The omission of Last.fm user-tagging data reduces the *breadth* of genre metadata but does not invalidate the *methodology* of temporal embedding analysis. The pipeline will proceed with a "MPD-only" baseline, which is scientifically valid and reproducible.

### 3.3 Risk Mitigation
Continuing to attempt Last.fm ingestion introduces a high probability of:
- **Execution Failure**: The pipeline will halt if the API times out or returns 429 errors.
- **Fabrication**: To bypass failures, there is a risk of inadvertently generating synthetic data (violating the "Real Data Only" constraint).
- **Inconsistency**: Different runs may yield different data volumes based on transient API availability.

Removing Last.fm eliminates these risks, ensuring a stable, reproducible pipeline.

---

## 4. Proposed Amendment Text

**Replace** the following text in the Specification:

> *Current*: "The system must ingest and process data from the Last.fm API and the Spotify Million Playlist Dataset (MPD)."

**With**:

> *Amended*: "The system must ingest and process data from the Spotify Million Playlist Dataset (MPD). The Last.fm data source is **excluded** from this phase due to unavailability of a programmatic bulk source. All analysis will be conducted on MPD-derived metadata."

**Update** FR-009 to:

> *Amended*: "The system must correlate MPD track metadata with MusicBrainz identifiers. If external genre tags (e.g., from Last.fm) are unavailable, the system must rely on MusicBrainz genre metadata and track co-occurrence patterns for embedding generation."

---

## 5. Implementation Plan

Upon approval of this amendment:

1. **Ingestion Logic (T050/T051)**: The `ingest_lastfm` function in `src/code/ingest.py` will be modified to immediately log a `WARNING` and return an empty dataframe, rather than attempting API calls. The `join_lastfm_mb` step will be skipped if no Last.fm data is present.
2. **Pipeline Flow**: The pipeline will proceed directly from `ingest_mpd` to `fetch_musicbrainz` and `join_mpd_mb`.
3. **Documentation**: The `README.md` and `quickstart.md` will be updated to explicitly state "Data Source: MPD Only (Last.fm Blocked)".

---

## 6. Approval Sign-off

| Role | Name | Date | Decision |
|:--- |:--- |:--- |:--- |
| Project Lead | [Pending] | | [ ] Approved / [ ] Rejected |
| Research Lead | [Pending] | | [ ] Approved / [ ] Rejected |

**Note**: If rejected, the project must identify an alternative, verified bulk source for Last.fm data before proceeding, or the project scope must be reduced to exclude genre evolution analysis entirely.

---

## 7. References

- Task T016: `specs/001-genre-evolution/scope_deviation_log.md`
- Task T040: Streaming architecture implementation for MPD.
- Task T050: Conditional Last.fm ingestion logic.
- Constitution Check: Ensures no fabricated data is used in place of the missing source.