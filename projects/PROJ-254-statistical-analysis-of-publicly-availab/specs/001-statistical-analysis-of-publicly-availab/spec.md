# Project Specification: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

**Version**: 2.1 (Amended)
**Date**: 2024-10-27
**Status**: Active

## 1. Introduction

This project analyzes the evolution of music genres over time using publicly available streaming data. The primary goal is to determine whether music genres have become more or less distinct (converging or diverging) over recent decades.

## 2. Data Sources

### 2.1 Primary Source: Spotify Million Playlist Dataset (MPD)
- **Description**: A large-scale dataset containing millions of playlists from Spotify.
- **Access**: Publicly available via Hugging Face Datasets (`spotify_million_playlist`).
- **Scope**: Covers tracks from the mids to 2024.
- **Note**: The original requirement for Last.fm 1-Billion Listening Events (FR-001) has been **WAIVED** per Spec Amendment `spec_amendment_lastfm.md` (T061). The pipeline now operates on MPD data only.

### 2.2 Metadata Enrichment: MusicBrainz
- **Description**: Used to fetch genre tags and release years for tracks not explicitly tagged in MPD.
- **Method**: API lookup with fuzzy matching fallback (Thefuzz).

## 3. Functional Requirements

### FR-001: Data Ingestion
The system must ingest the MPD dataset using a streaming architecture to handle large data volumes without exhausting memory (RAM < 6GB).

### FR-002: Metadata Matching
The system must match MPD tracks to MusicBrainz records to obtain genre tags.

### FR-003: Embedding Generation
The system must train a global Word2Vec model on track sequences to generate genre-level embeddings for each year.

### FR-004: Similarity Calculation
The system must compute pairwise cosine similarities between yearly genre vectors.

### FR-005: Trend Analysis
The system must fit a linear regression model to the similarity trend over time, using Newey-West HAC standard errors to account for autocorrelation.

### FR-006: Robustness Analysis (AMENDED)
**Status**: **MODIFIED** (See Spec Amendment `spec_amendment_fr006.md`)

**Requirement**: The pipeline must perform a **Cook's Distance Outlier Analysis** to identify influential years in the regression model. The analysis must calculate Cook's Distance for each data point, flag points exceeding the threshold $D_i > 4/n$ (where $n$ is the number of observations), and generate a report (`cooks_distance_report.csv`) detailing influential points. The regression results must be re-evaluated excluding these influential points to confirm trend stability.

*Note: The previous requirement for a "Sensitivity Sweep" over arbitrary thresholds has been replaced by this statistically rigorous method.*

## 4. Success Criteria

### SC-001: Data Coverage
The pipeline must successfully process at least 80% of the available MPD tracks.
*Note: The denominator for this calculation is now MPD tracks only, per Spec Amendment `spec_amendment_sc001.md` (T063).*

### SC-002: Statistical Significance
The trend slope must be statistically significant (p-value < 0.05) after accounting for autocorrelation.

### SC-003: Robustness Validation (AMENDED)
**Status**: **MODIFIED** (See Spec Amendment `spec_amendment_fr006.md`)

**Requirement**: The trend result is considered robust if the p-value remains < 0.05 after excluding data points identified as highly influential by Cook's Distance (where $D_i > 4/n$). If influential points are removed, the revised regression slope and p-value must be reported alongside the original.

## 5. Deliverables

1. **Yearly Embeddings**: `yearly_embeddings/{year}.npy`
2. **Similarity Data**: `data/derived/yearly_similarity.csv`
3. **Regression Results**: `data/derived/regression_results.json`
4. **Cook's Distance Report**: `data/derived/cooks_distance_report.csv` (Replaces `sensitivity_report.csv`)
5. **Visualizations**: `similarity_trend.png`, `genre_similarity_heatmap.html`

## 6. Governance & Amendments

This specification is subject to formal amendments to address scope deviations and methodological improvements.

- **Amendment T061**: Removal of Last.fm 1-Billion requirement (MPD-only execution).
- **Amendment T062**: Replacement of Sensitivity Sweep with Cook's Distance Analysis.
- **Amendment T063**: Adjustment of Success Criterion SC-001 to MPD-only denominator.

All amendments are stored in `specs/001-genre-evolution/`.

## 7. Execution Pipeline

The pipeline is executed via `python -m src.code.run_pipeline` or individual modules:
- `ingest.py`: Data ingestion and cleaning.
- `embeddings.py`: Word2Vec training and aggregation.
- `similarity.py`: Cosine similarity computation.
- `regression.py`: Statistical testing and Cook's Distance analysis.
- `viz.py`: Plot generation.
