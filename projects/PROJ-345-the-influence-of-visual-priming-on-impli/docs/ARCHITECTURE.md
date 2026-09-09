# Architecture Overview

This document provides a high-level overview of the project's architecture, including the design principles, component interactions, and data flow.

## Design Principles

- **Modularity**: Each component is self-contained and can be developed, tested, and deployed independently.
- **Reproducibility**: All random seeds are pinned, data sources are verified, and state is managed rigorously.
- **Scalability**: The pipeline is designed to handle large datasets using chunked processing where necessary.
- **Transparency**: All analyses are associational, with explicit limitations and assumptions documented.

## Component Overview

### Data Ingestion (`code/data/ingest.py`)

- Downloads IAT datasets from verified OSF/HF sources.
- Extracts trial-level response times and maps them to stimulus metadata.
- Validates data integrity and handles missing images.

### Preprocessing (`code/data/preprocess.py`)

- Derives prime valence using CPU-optimized VAD regression models.
- Handles ambiguity scores (human-rated or synthetic derivation).
- Checks for confounding variables.

### Modeling (`code/models/lmm.py`)

- Fits Linear Mixed-Effects Models (LMM) with proper random effects.
- Implements optimizer retry logic for convergence failures.
- Calculates VIF, effect sizes, and applies FDR correction.

### Visualization (`code/viz/plots.py`)

- Generates interaction plots and coefficient tables.
- Supports customization for different analysis outputs.

### Reporting (`code/reports/generate_report.py`)

- Compiles plots, tables, and sensitivity analyses into a PDF report.
- Explicitly cites limitations and the observational nature of the study.

### State Management (`code/state_management.py`)

- Tracks all artifacts and their versions.
- Records execution logs and checksums for reproducibility.

### Security (`code/security/pii_scanner.py`)

- Scans data for PII and generates security reports.
- Ensures no sensitive information is leaked in outputs.

## Data Flow

1. **Ingestion**: Raw data is downloaded and validated.
2. **Preprocessing**: Data is cleaned, enriched, and checked for confounding.
3. **Modeling**: Statistical models are fitted and evaluated.
4. **Visualization**: Results are visualized.
5. **Reporting**: Final reports are generated.

## Configuration

All configuration is centralized in `code/config.py`. This includes:
- Paths to data directories.
- Random seed values.
- Thresholds for missing data and convergence.

## Testing Strategy

- **Unit Tests**: Test individual functions and classes.
- **Integration Tests**: Test interactions between components.
- **Validation Scripts**: Ensure end-to-end pipeline correctness.

## Future Enhancements

- Support for additional data sources.
- Enhanced visualization options.
- Real-time monitoring of pipeline execution.
