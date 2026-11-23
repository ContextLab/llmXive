# Implementation Plan: Interdisciplinary Bridging Coefficient Analysis

## Overview
This project analyzes the relationship between topological bridging in a scientific citation graph (OpenAlex-derived Subgraph) and research outcomes (citations, novelty).

## Data Source
- **Source**: OpenAlex-derived Subgraph (replacing PubGraph).
- **Access**: Via `datasets.load_dataset("openalex/works", streaming=True)`.

## User Stories
1. **US1**: Ingest OpenAlex data, compute topological clusters (Louvain), and bridging coefficients.
2. **US2**: Compute text-based novelty scores using embeddings and K-Means clustering.
3. **US3**: Perform statistical analysis (correlation, regression) and generate reports.

## Phases
- **Phase 1**: Setup
- **Phase 2**: Foundational (Data Ingestion & Sampling)
- **Phase 3**: US1 - Topological Metrics
- **Phase 4**: US2 - Novelty Derivation
- **Phase 5**: US3 - Statistical Validation

## Key Decisions
- Use OpenAlex as the primary data source.
- Streaming ingestion to manage memory.
- Snowball sampling for subgraph extraction.
- Cosine distance to cluster centroid for novelty.

## Risks
- Memory constraints during ingestion.
- API rate limits for OpenAlex.
- Computational cost of embeddings.
