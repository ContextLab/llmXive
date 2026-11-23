# Project Architecture

## Overview

This document describes the architectural decisions and data flow of the llmXive pipeline for investigating network centrality and motor memory consolidation.

## High-Level Design

The project follows a modular, pipeline-based architecture:

1. **Data Ingestion Layer**: Handles downloading and initial validation.
2. **Preprocessing Layer**: Converts raw fMRI data into analyzable formats.
3. **Feature Extraction Layer**: Computes behavioral and network metrics.
4. **Analysis Layer**: Fits statistical models and performs validation.
5. **Reporting Layer**: Aggregates results into final artifacts.

## Module Responsibilities

### `code/data/`

- **`download.py`**: Interfaces with `openneuro-cli` to fetch datasets.
- **`preprocess.py`**: Wraps fMRIPrep execution, handles memory constraints, and extracts behavioral metrics.
- **`behavioral_extraction.py`**: Parses metadata to derive motor scores and demographics.
- **`exclusion_logging.py`**: Tracks subject exclusions based on retention and data quality.
- **`retention_validation.py`**: Enforces hard gates for data quality (e.g., >80% retention).

### `code/analysis/`

- **`centrality.py`**: Calculates graph-theoretic metrics (degree, betweenness, eigenvector) from connectivity matrices.
- **`regression.py`**: Fits linear and GAM models, handles VIF checks, and generates plots.
- **`validation.py`**: Implements Freedman-Lane permutation tests and k-fold cross-validation.
- **`exclusion.py`**: Summarizes exclusion logs and generates reports.
- **`optimization_utils.py`**: Provides utilities for memory-efficient processing (float32, batching).

### `code/utils/`

- **`logging.py`**: Centralized logging setup, resource usage tracking (RAM, time).
- **`config.py`**: Dataclasses for configuration management (paths, thresholds, seeds).
- **`metrics.py`**: Generates reproducibility reports, checksums, and aggregates validation metrics.

## Data Flow

1. **Raw Data**: Downloaded to `data/raw/`.
2. **Preprocessed Data**: fMRIPrep outputs stored in `data/processed/fmriprep/`.
3. **Behavioral Metrics**: Saved to `data/processed/behavioral/`.
4. **Centrality Metrics**: Saved to `data/processed/centrality/`.
5. **Model Outputs**: Regression and validation results in `data/processed/regression/` and `data/processed/validation/`.
6. **Final Artifacts**: Reports and figures in `data/artifacts/`.

## Key Architectural Decisions

- **Modularity**: Each analysis step is a standalone script, allowing independent execution and testing.
- **Configuration**: Centralized configuration ensures reproducibility and ease of parameter tuning.
- **Validation**: Hard gates (Phase 0) prevent downstream processing on invalid data.
- **Reproducibility**: Automated checksums and resource logging ensure auditability.
- **Memory Efficiency**: Use of `float32` and batch processing to handle large datasets within constrained environments.

## Error Handling

- **Fatal Gates**: Missing data or low retention triggers immediate exit with clear error messages.
- **Graceful Degradation**: Warnings for underpowered studies or motion artifacts, allowing continuation with flags.
- **Logging**: Comprehensive logging at all stages for debugging and auditing.

## Future Considerations

- **Scalability**: Potential for distributed processing using Dask or Spark for larger datasets.
- **Advanced Models**: Integration of machine learning models (e.g., Random Forests, Neural Networks) for prediction.
- **Real-time Analysis**: Potential for streaming analysis of incoming data.
