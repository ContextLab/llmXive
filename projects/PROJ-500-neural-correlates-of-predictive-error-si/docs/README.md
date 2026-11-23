# Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Project ID**: PROJ-500-neural-correlates-of-predictive-error-si

## Overview

This project implements an automated pipeline to analyze neural correlates of predictive error signals (MMN - Mismatch Negativity) during tactile discrimination learning. The pipeline ingests EEG data from OpenNeuro, preprocesses signals, aligns MMN amplitudes with behavioral accuracy using lagged alignment, and fits statistical models to identify learning-related neural signatures.

## Architecture

The pipeline follows a modular design with distinct phases:

- **Phase 0**: Dataset validation and variable fit determination
- **Phase 1**: Project setup and configuration
- **Phase 2**: Foundational infrastructure (schemas, logging, environment)
- **Phase 3**: Data ingestion and preprocessing (US1)
- **Phase 4**: MMN amplitude calculation and behavioral alignment (US2)
- **Phase 5**: Statistical modeling and validation (US3)
- **Phase 6**: Polish and cross-cutting concerns

## Directory Structure

```
.
├── code/
│ ├── setup_project.py # Project initialization
│ ├── src/
│ │ ├── analysis/
│ │ │ ├── model.py # Statistical modeling (LME, permutation tests)
│ │ │ └── robustness.py # Sensitivity analysis
│ │ ├── data/
│ │ │ ├── ingest.py # Data download and metadata validation
│ │ │ ├── preprocess.py # EEG preprocessing (filter, ICA, epoching)
│ │ │ ├── align.py # MMN calculation and lagged alignment
│ │ │ ├── clean.py # Data cleaning and filtering
│ │ │ └── finalize.py # Final dataset generation
│ │ └── utils/
│ │ ├── logging.py # Structured JSON logging
│ │ ├── env_config.py # Environment variable validation
│ │ ├── config.py # Configuration management
│ │ └── checksum.py # Data integrity verification
│ └── tests/
│ ├── contract/ # Schema validation tests
│ ├── integration/ # End-to-end pipeline tests
│ └── unit/ # Unit tests for individual components
├── data/
│ ├── validation_report.json # Dataset metadata analysis
│ ├── excluded_subjects.csv # Underpowered subject exclusions
│ ├── accuracy_blocks.csv # 10-trial behavioral accuracy blocks
│ ├── interim_lagged_mmns.csv # Lagged MMN-accuracy alignments
│ └── aligned_data.csv # Final aligned dataset for modeling
├── analysis/
│ └── results/
│ └── model_output.json # Model coefficients and p-values
├── specs/
│ └── 001-neural-correlates-of-predictive-error-si/
│ ├── spec.md # Feature specification (SSoT)
│ ├── plan.md # Implementation plan
│ └── data-model.md # Data entity definitions
├── contracts/
│ ├── aligned_data.schema.yaml # Schema for aligned dataset
│ └── model_output.schema.yaml # Schema for model output
├── docs/
│ ├── README.md # This file
│ └── quickstart.md # Quick start guide
├── pyproject.toml # Python project configuration
├── requirements.txt # Dependencies
├── ruff.toml # Linting configuration
└──.gitignore # Git ignore rules
```

## Key Components

### Data Ingestion (`src/data/ingest.py`)
- Downloads EEG data from OpenNeuro/HuggingFace with streaming support
- Validates dataset metadata for required variables
- Determines analysis mode (error-signal vs stimulus-driven)
- Enforces RAM limits (≤7GB) through chunked buffering

### Preprocessing (`src/data/preprocess.py`)
- Bandpass filtering (-40 Hz)
- ICA artifact removal
- Bad channel interpolation
- Epoching (-200ms to 500ms)
- Artifact rejection (trial loss ≤5%)
- Underpowered subject flagging (<20 subjects)

### Alignment (`src/data/align.py`)
- MMN amplitude calculation at CP3, CP4, C3, C4 electrodes
- 10-trial behavioral binning for accuracy
- Lagged alignment: 50-trial MMN window → subsequent 10-trial accuracy block
- NaN handling and invalid block filtering

### Statistical Modeling (`src/analysis/model.py`)
- Gaussian Linear Mixed Effects: `MMN ~ Accuracy + Learning_Phase + (1|Subject)`
- FDR correction (Benjamini-Hochberg) for multiple comparisons
- Permutation testing (n=1000) for significance validation
- Sensitivity analysis on time windows (±10ms)

## User Stories

### US1: Data Ingestion and Preprocessing
- Download and preprocess EEG data with ≥95% epoch success rate
- Exclude underpowered datasets automatically
- Generate clean, filtered, and epoched data

### US2: MMN Amplitude and Behavioral Alignment
- Compute MMN amplitudes in early-latency windows
- Align neural and behavioral data using lagged methodology
- Handle missing logs via stimulus-driven fallback

### US3: Statistical Modeling and Validation
- Fit LME models with proper random effects
- Apply multiple-comparison correction
- Validate results with permutation tests

## Testing Strategy

- **Contract Tests**: Validate data schemas against YAML definitions
- **Integration Tests**: End-to-end pipeline execution on sample data
- **Unit Tests**: Individual component functionality
- **Performance Tests**: Memory and runtime constraints verification

## Constraints

- **Hardware**: CPU-only execution (2-core minimum), no GPU required
- **Memory**: Peak RAM ≤7GB through streaming and chunking
- **Runtime**: Full pipeline ≤6 hours on specified hardware
- **Data**: Real external data only; no synthetic fallbacks
- **Reproducibility**: Checksums and structured logging for traceability

## License

This project is part of the llmXive automated science pipeline.
