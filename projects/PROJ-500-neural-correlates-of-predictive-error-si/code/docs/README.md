# Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Project ID**: PROJ-500-neural-correlates-of-predictive-error-si

## Overview

This project implements an automated pipeline to analyze EEG data from tactile discrimination tasks.
It investigates the neural correlates of predictive error signals (MMN) and their relationship with
behavioral accuracy using Gaussian Linear Mixed Effects (LME) models.

## Key Features

- **Automated Data Ingestion**: Streaming download from OpenNeuro/HuggingFace (T014).
- **Preprocessing**: Filtering, ICA artifact removal, and epoching (T015-T018).
- **Lagged Alignment**: Correlating MMN amplitudes with subsequent behavioral blocks (T024).
- **Statistical Modeling**: Gaussian LME fitting with permutation testing (T029-T031).
- **Performance Optimized**: Designed to run within 6 hours on 2-core CPU (T037).

## Architecture

The project follows a modular structure:

- `src/data/`: Ingestion, preprocessing, and alignment logic.
- `src/analysis/`: Statistical modeling and robustness checks.
- `src/utils/`: Configuration, logging, and environment validation.
- `tests/`: Contract, integration, and unit tests.
- `data/`: Raw and processed data artifacts.
- `analysis/results/`: Final model outputs.

## Getting Started

See `docs/quickstart.md` for installation and execution instructions.

## Performance Guarantee

The pipeline is optimized to complete the full analysis (Ingest → Align → Model) within **6 hours**
on a standard 2-core CPU with 7GB RAM, as verified by `tests/unit/test_t037_performance.py`.

## License

MIT License
