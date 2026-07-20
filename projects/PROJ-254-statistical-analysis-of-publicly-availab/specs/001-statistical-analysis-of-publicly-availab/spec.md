# Project Specification: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

**Version**: 2.0 (Amended)
**Last Updated**: 2024-05-21

## 1. Overview

This project analyzes the evolution of music genres over time using large-scale streaming data. The primary goal is to derive yearly genre embeddings and analyze the temporal similarity trends to determine if music genres are becoming more homogenized or diversified over the decades.

## 2. Data Sources

* **Primary Dataset**: Spotify Million Playlist Dataset (MPD).
* **Metadata Source**: MusicBrainz API for track/artist/album metadata and genre tagging.
* **Waiver**: The original requirement to ingest Last.fm 1-Billion Listening Events (FR-001, FR-009) has been waived via `spec_amendment_lastfm.md`. The pipeline now operates on MPD-only data.

## 3. Functional Requirements

* **FR-001**: Ingest and process the Spotify Million Playlist Dataset (MPD).
* **FR-004**: Compute pairwise cosine similarity between yearly genre embeddings.
* **FR-005**: Fit a linear regression model to the similarity trend with Newey-West HAC standard errors.
* **FR-006 (AMENDED)**: **Cook's Distance Outlier Analysis**. Instead of the original "Sensitivity Sweep", the system MUST perform a Cook's Distance analysis to identify influential outliers in the regression model.
 * *Implementation*: Calculate Cook's Distance for each year.
 * *Output*: `data/derived/cooks_distance_report.csv`.
 * *Threshold*: Flag years where $D_i > 4/n$.
* **FR-007**: Generate visualizations for similarity trends and genre heatmaps.
* **FR-008**: Ensure deterministic reproducibility via seed pinning.
* **FR-009**: Join MPD data with MusicBrainz metadata (conditional on waiver).
* **FR-010**: Implement fuzzy matching fallback for MusicBrainz lookups.
* **FR-011**: Enforce memory limits (<6GB) via streaming and garbage collection.

## 4. Success Criteria

* **SC-001**: At least 80% of MPD tracks must be successfully matched with metadata and assigned a year.
* **SC-003 (AMENDED)**: The pipeline must successfully execute the Cook's Distance analysis and report any influential outliers. The trend significance (p-value) must be reported alongside the outlier analysis.

## 5. Architecture

The system is built as a Python-based pipeline with the following modules:
* `code/ingest.py`: Data loading, streaming, and metadata joining.
* `code/embeddings.py`: Word2Vec training and yearly embedding aggregation.
* `code/similarity.py`: Cosine similarity computation.
* `code/regression.py`: Linear regression and Cook's Distance analysis.
* `code/viz.py`: Visualization generation.

## 6. Governance

This specification has been amended to reflect the following changes:
* **Last.fm Waiver**: `spec_amendment_lastfm.md` removes the Last.fm requirement.
* **Robustness Check Amendment**: `spec_amendment_fr006.md` replaces the Sensitivity Sweep with Cook's Distance.
* **Success Criterion Adjustment**: `spec_amendment_sc001.md` adjusts the denominator to MPD tracks only.

## 7. Execution

The pipeline is executed via `python -m src.code.run_pipeline`.
All outputs are written to `data/derived/` and `yearly_embeddings/`.
Logs are written to `pipeline_log.txt`.