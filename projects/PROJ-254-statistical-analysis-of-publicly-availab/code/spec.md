# Specification: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

**Version**: 2.0 (Ratified)
**Date**: 2024-05-20
**Status**: Active

## 1. Introduction

This project aims to analyze the evolution of music genres over time using publicly available streaming data. The primary goal is to generate yearly genre embeddings, compute temporal similarities, and statistically test for trends in genre convergence or divergence.

## 2. Data Sources

### 2.1 Spotify Million Playlist Dataset (MPD)
The primary data source is the Spotify Million Playlist Dataset (MPD), which contains metadata for one million playlists and the tracks within them.
- **Access**: Programmatically via the `datasets` library (Hugging Face).
- **Format**: Parquet files, streamed in chunks to manage memory.
- **Scope**: All tracks present in the MPD.

### 2.2 Last.fm 1-Billion Listening Events
**Status**: WAIVED.
The original specification (FR-001) required the ingestion of the Last.fm 1-Billion dataset. However, due to unavailability in a programmatically accessible format without proprietary keys or violating terms of service, this requirement has been formally waived via `spec_amendment_lastfm.md` (T061).
- **Action**: The pipeline is now MPD-only.
- **Impact**: All downstream metrics are adjusted to reflect MPD-only data.

## 3. Functional Requirements

### FR-001: Data Ingestion
The pipeline must ingest the MPD dataset using a streaming architecture to ensure memory safety.
- **Constraint**: Must not load the full dataset into RAM at once.
- **Implementation**: `src/code/ingest.py` uses `datasets.load_dataset(..., streaming=True)`.

### FR-004: Similarity Calculation
Compute pairwise cosine similarities between yearly genre vectors.
- **Output**: `data/derived/yearly_similarity.csv`.

### FR-005: Regression Analysis
Fit a linear regression model to test the significance of the similarity trend over time.
- **Method**: Ordinary Least Squares (OLS) with Newey-West HAC standard errors.
- **Robustness**: Cook's Distance analysis is used to identify and handle outliers (replacing FR-006).

### FR-006: Robustness Check (WAIVED)
The original "Sensitivity Sweep" requirement is waived. It is replaced by Cook's Distance outlier analysis as per `spec_amendment_fr006.md` (T062).

### FR-009: Metadata Enrichment
Join MPD tracks with MusicBrainz metadata to obtain genre tags and release years.
- **Fallback**: If MusicBrainz ID is missing, use fuzzy matching on (artist, track, album) via `thefuzz`.

## 4. Success Criteria

### SC-001: Coverage
**Original**: Coverage must be >= 80% of the combined Last.fm and MPD datasets.
**Amended**: Coverage must be >= 80% of the total available tracks in the **Spotify Million Playlist Dataset (MPD)**.
- **Denominator**: Total unique track IDs in the MPD source files.
- **Numerator**: Tracks successfully matched to MusicBrainz and assigned a valid release year.
- **Logic**: Implemented in `src/code/ingest.py` -> `calculate_coverage()` (T053).

### SC-002: Trend Significance
The linear regression slope must be statistically significant (p-value < 0.05) to claim a trend in genre evolution.

### SC-003: Robustness
The results must be robust to the removal of outliers identified by Cook's Distance. If the trend remains significant after outlier removal, the result is considered robust.

## 5. Architecture

The pipeline is modular and follows a streaming architecture:
1. **Ingestion**: `src/code/ingest.py` - Streams MPD data, joins with MusicBrainz.
2. **Embeddings**: `src/code/embeddings.py` - Trains Word2Vec on track sequences, aggregates yearly genre vectors.
3. **Similarity**: `src/code/similarity.py` - Computes pairwise similarities.
4. **Regression**: `src/code/regression.py` - Fits regression, performs Cook's Distance analysis.
5. **Visualization**: `src/code/viz.py` - Generates plots and heatmaps.

## 6. Governance

This specification has been updated to reflect the following amendments:
- **T061**: Removal of Last.fm requirement (`spec_amendment_lastfm.md`).
- **T062**: Replacement of Sensitivity Sweep with Cook's Distance (`spec_amendment_fr006.md`).
- **T063**: Adjustment of SC-001 to MPD-only denominator (`spec_amendment_sc001.md`).

All amendments are ratified and effective immediately.

## 7. Execution

The pipeline can be executed via the CLI:
```bash
python -m src.code.run_pipeline
```

Or stage-by-stage:
```bash
python -m src.code.run_pipeline --stage ingest
python -m src.code.run_pipeline --stage embeddings
python -m src.code.run_pipeline --stage similarity
python -m src.code.run_pipeline --stage regression
```