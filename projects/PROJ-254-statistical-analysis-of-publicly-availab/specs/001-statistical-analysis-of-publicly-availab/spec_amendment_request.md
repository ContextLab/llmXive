# Spec Amendment Request: Data Source Deviation (Last.fm Omission)

**Date**: 2024-05-21
**Author**: Automated Science Pipeline
**Project**: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution
**Reference Tasks**: T016 (Scope Deviation Log), T017 (This Amendment)

## 1. Summary of Request

This document formally requests a **Spec Amendment** to modify the data ingestion requirements defined in **FR-001** (Ingest Last.fm data) and **FR-009** (Join Last.fm with MusicBrainz) of the original specification.

The amendment proposes to **permanently omit** the ingestion of Last.fm data from the current pipeline execution and proceed exclusively with the **Spotify Million Playlist Dataset (MPD)** as the primary and sole data source.

## 2. Background and Context

### 2.1 Original Specification Requirements
The original feature specification (Spec) mandated the following:
- **FR-001**: Ingest Last.fm user listening history and track metadata.
- **FR-009**: Perform a join operation between Last.fm data and MusicBrainz metadata to enrich the dataset.

### 2.2 Identified Scope Deviation (T016)
As documented in `specs/001-genre-evolution/scope_deviation_log.md` (Task T016), the project Plan explicitly deviated from the Spec by prioritizing the MPD dataset due to its structured, streaming-friendly nature and the lack of a programmatic, real-time API for Last.fm that satisfies the project's volume and reproducibility constraints.

The Plan noted that Last.fm ingestion is **BLOCKED** due to:
1. Missing data sources: No official, free, high-volume API endpoint exists for the specific historical listening logs required.
2. Access restrictions: The Last.fm API requires authentication and has strict rate limits incompatible with large-scale batch processing without a dedicated proxy or paid tier.
3. Data consistency: The MPD dataset provides a self-contained, consistent schema that aligns with the project's memory constraints (FR-011) and streaming architecture (T040).

## 3. Justification for Amendment

The omission of Last.fm data is not a temporary delay but a structural constraint of the current execution environment. Attempting to force Last.fm ingestion would result in:
- **Silent Fabrication**: The pipeline might resort to synthetic data generation to satisfy the join requirement, violating the "Real Data Only" constitution.
- **Pipeline Failure**: Hard failures in the ingestion stage (T050) due to API unavailability, halting the entire research process.
- **Resource Misalignment**: Diverting compute resources to error handling for an unavailable service rather than analyzing the available MPD data.

Therefore, proceeding with **MPD-only** is the only viable path to produce a valid, reproducible scientific result under the current constraints.

## 4. Proposed Changes to Specification

The following changes are requested:

1. **FR-001 Modification**:
 - *Original*: "Ingest Last.fm data."
 - *Amended*: "Ingest the Spotify Million Playlist Dataset (MPD) as the primary data source. Last.fm ingestion is **excluded** for this project iteration due to data source unavailability."

2. **FR-009 Modification**:
 - *Original*: "Join Last.fm data with MusicBrainz."
 - *Amended*: "Join MPD track metadata with MusicBrainz. The Last.fm join step is **skipped** as Last.fm data is not ingested."

3. **New Constraint**:
 - Add a governance flag `lastfm_ingestion_enabled = False` to the pipeline configuration, ensuring all downstream logic (T050, T051) correctly bypasses Last.fm processing without raising errors.

## 5. Impact Analysis

- **Data Coverage**: The analysis will be limited to the MPD dataset (approx. 1 million playlists). While this reduces the total volume compared to a hypothetical Last.fm + MPD union, it ensures 100% data integrity and reproducibility.
- **Methodology**: The Word2Vec embedding training (T042) and similarity analysis (T025) will proceed unchanged, as they rely on track sequences which are fully available in the MPD.
- **Governance**: This amendment ratifies the decision made in T016 and prevents future confusion regarding the missing Last.fm component.

## 6. Approval Status

- **Status**: Pending Formal Approval
- **Dependency**: This amendment is a prerequisite for the successful completion of User Story 1 (Ingestion/Embedding) and User Story 2 (Similarity).
- **Action Required**: Approve this amendment to proceed with the MPD-only pipeline execution.

---
*This document serves as the formal record of the deviation from the original specification requirements.*