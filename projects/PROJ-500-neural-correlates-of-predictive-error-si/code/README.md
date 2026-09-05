# Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

This project implements an automated pipeline for analyzing neural correlates of predictive error signals during tactile discrimination learning, with a focus on mismatch negativity (MMN) amplitude and behavioral accuracy alignment.

## Overview

The pipeline processes EEG data from OpenNeuro/Hugging Face datasets to:
1. Ingest and preprocess raw EEG data with strict memory management
2. Compute MMN amplitudes at specific electrodes (CP3, CP4, C3, C4)
3. Align neural responses with behavioral accuracy using lagged alignment
4. Fit statistical models to identify significant correlates

## Key Features

- **Streaming Data Ingestion**: Processes large datasets in chunks to maintain peak RAM usage under 7GB
- **Automated Preprocessing**: Filtering, ICA artifact removal, and bad channel interpolation
- **Lagged Alignment**: Correlates MMN amplitudes with subsequent behavioral performance
- **Statistical Modeling**: Gaussian LME models with multiple-comparison correction
- **Robustness Analysis**: Sensitivity analysis across time windows

## Project Structure

```
code/
├── src/
│ ├── data/
│ │ ├── ingest.py # Streaming data download and validation
│ │ ├── preprocess.py # EEG preprocessing pipeline
│ │ ├── align.py # MMN amplitude calculation and alignment
│ │ ├── clean.py # Data cleaning and filtering
│ │ └── finalize.py # Final dataset generation
│ ├── analysis/
│ │ ├── model.py # Statistical modeling (LME, permutation tests)
│ │ └── robustness.py # Sensitivity analysis
│ └── utils/
│ ├── config.py # Configuration management
│ ├── logging.py # Structured logging
│ ├── env_config.py # Environment validation
│ └── checksum.py # Data integrity checks
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── data/ # Generated data artifacts
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

See [docs/quickstart.md](docs/quickstart.md) for a quick start guide.

## Running the Pipeline

1. **Data Ingestion**:
 ```bash
 python code/src/data/ingest.py
 ```

2. **Preprocessing**:
 ```bash
 python code/src/data/preprocess.py
 ```

3. **Alignment**:
 ```bash
 python code/src/data/align.py
 ```

4. **Statistical Modeling**:
 ```bash
 python code/src/analysis/model.py
 ```

## Testing

Run all tests:
```bash
pytest code/tests/
```

Run specific test suites:
```bash
# Unit tests
pytest code/tests/unit/

# Integration tests
pytest code/tests/integration/

# Contract tests
pytest code/tests/contract/
```

## Memory Management

The pipeline is designed to operate within a 7GB RAM limit by:
- Using streaming APIs for data download
- Processing data in configurable chunks
- Forcing garbage collection between processing steps
- Monitoring memory usage and raising errors if limits are exceeded

## License

This project is licensed under the MIT License.

## Acknowledgments

This research is supported by [Funding Source] and uses data from OpenNeuro and Hugging Face datasets.