# Architecture Overview

## High-Level Design

The system follows a modular, pipeline-based architecture where each stage transforms data into a more refined state.

1. **Ingestion Layer**: `download.py` handles external data retrieval.
2. **Processing Layer**: `preprocess.py` cleans and structures raw signals.
3. **Feature Layer**: `metrics.py` extracts graph-theoretic and signal-theoretic features.
4. **Analysis Layer**: `analysis.py` performs statistical inference.
5. **Presentation Layer**: `report.py` synthesizes findings.

## Component Interactions

- **Configuration**: `config.yaml` drives all parameters (filtering, bands, paths).
- **Logging**: Centralized logging in `main.py` captures progress and errors.
- **Data Integrity**: `integrity.py` ensures file checksums match before processing.

## Scalability

The pipeline is designed for CPU-only execution with memory constraints (<4GB RAM). It processes subjects sequentially to minimize memory footprint, though individual steps (like epoching) are optimized for vectorization.

## Extensibility

New metrics can be added to `metrics.py` without altering the analysis pipeline, provided they conform to the `SubjectMetrics.csv` schema. New statistical tests can be integrated into `analysis.py` by extending the `run_lme_analysis` or adding new functions.
