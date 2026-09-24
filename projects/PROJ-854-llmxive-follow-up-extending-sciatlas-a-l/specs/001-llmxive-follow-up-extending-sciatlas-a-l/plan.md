# Implementation Plan: Interdisciplinary Bridging Coefficient Analysis

## Project Structure
- `code/src/`: Source code
- `code/tests/`: Test suites
- `data/`: Raw and processed data
- `artifacts/`: Results and reports

## Phase 1: Setup
- Initialize project structure and dependencies.
- Configure linting and formatting tools.

## Phase 2: Foundational
- Implement strict data fetcher for **OpenAlex** with streaming support.
- Implement Snowball Sampling for subgraph extraction.
- Orchestrate ingestion pipeline.

## Phase 3: User Story 1 (MVP)
- Implement Louvain clustering on the **OpenAlex-derived Subgraph**.
- Calculate bridging coefficients.
- Validate sample representativeness.
- Save processed graph to Parquet.

## Phase 4: User Story 2
- Generate title embeddings.
- Perform K-Means clustering for topic assignment.
- Compute novelty scores based on centroid distance.
- Save final analysis dataset.

## Phase 5: User Story 3
- Perform statistical analysis (Spearman, Linear Regression).
- Apply multiple-comparison correction.
- Generate final report with "associational" labeling.

## Execution Strategy
1. **Data Source**: Use `datasets.load_dataset("openalex/works", streaming=True)` to fetch the **OpenAlex-derived Subgraph**.
2. **Sampling**: Apply Snowball Sampling to ensure local topology preservation.
3. **Clustering**: Use `community_louvain` for structural clustering and `sklearn` for text clustering.
4. **Analysis**: Use `scipy.stats` for correlations and `statsmodels` for regression.

## Risk Mitigation
- **Memory**: Use streaming and generator-based processing.
- **Data Quality**: Validate schema and handle nulls explicitly.
- **Reproducibility**: Pin seeds and log all random states.
