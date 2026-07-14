# llmXive Agency CBT Project

**Project ID:** PROJ-547
**Title:** The Impact of Perceived Agency in AI-Driven Cognitive Behavioral Therapy on Treatment Adherence

## Overview

This research project investigates how perceived agency in AI-driven Cognitive Behavioral Therapy (CBT) influences treatment adherence. The pipeline processes conversation transcripts to compute agency scores, extracts adherence metrics from usage logs, and performs statistical analysis to determine correlations.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### Install via pip

From the project root directory:

```bash
pip install.
```

Or in editable mode for development:

```bash
pip install -e.
```

### Manual Dependencies

If you prefer to install dependencies manually:

```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── code/ # Source code modules
│ ├── adherence_extraction/
│ ├── agency_scoring/
│ ├── analysis/
│ ├── config/
│ ├── data_acquisition/
│ ├── logging/
│ ├── utils/
│ └── validation/
├── data/ # Data files (raw, processed, external)
├── configs/ # Configuration YAML files
├── logs/ # Pipeline execution logs
├── output/ # Analysis results and plots
├── validation/ # Validation reports
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── pyproject.toml # Build and project configuration
├── setup.py # Legacy setup script
└── README.md # This file
```

## Quick Start

### 1. Download Datasets

```bash
download-datasets --config configs/datasets/sources.yaml
```

### 2. Validate Metadata

```bash
validate-metadata --metadata datasets/metadata.yaml
```

### 3. Compute Agency Scores

```bash
ingest-transcripts --input data/raw/transcripts.csv --output data/processed/transcripts_ingested.csv
detect-markers --input data/processed/transcripts_ingested.csv --output data/processed/markers_detected.csv
compute-agency-scores --input data/processed/markers_detected.csv --output data/processed/agency_scores.csv
```

### 4. Extract Adherence Metrics

```bash
extract-metrics --input data/raw/usage_logs.json --output data/processed/adherence_metrics.csv
ingest-demographics --input data/raw/demographics.csv --output data/processed/demographics.csv
```

### 5. Merge and Analyze

```bash
merge-datasets --agency data/processed/agency_scores.csv --adherence data/processed/adherence_metrics.csv --demographics data/processed/demographics.csv --output data/processed/merged_data.csv
run-regression --input data/processed/merged_data.csv --output output/regression_results/
```

### 6. Validate Agency Scores

```bash
compute-reliability --input data/processed/validation_subset.csv --output validation/reliability_results.yaml
compute-convergent --input data/processed/validation_subset.csv --output validation/convergent_results.yaml
generate-validation-report --reliability validation/reliability_results.yaml --convergent validation/convergent_results.yaml --output validation/report.pdf
```

## Command-Line Interface

The project provides several command-line entry points:

- `download-datasets`: Download raw datasets from configured sources
- `validate-metadata`: Verify dataset checksums against metadata
- `ingest-transcripts`: Parse conversation transcripts
- `detect-markers`: Identify linguistic markers of agency
- `compute-agency-scores`: Calculate agency scores per session
- `extract-metrics`: Extract adherence metrics from usage logs
- `merge-datasets`: Combine agency, adherence, and demographic data
- `run-regression`: Perform regression analysis
- `compute-reliability`: Compute split-half reliability
- `compute-convergent`: Compute convergent validity
- `generate-validation-report`: Generate validation report PDF

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=code --cov-report=html
```

## Configuration

Configuration files are stored in the `configs/` directory:

- `agency_weights.yaml`: Weights for linguistic markers in agency scoring
- `datasets/sources.yaml`: URLs and metadata for dataset downloads
- Other YAML files for specific module configurations

## Logging

All pipeline operations are logged to `logs/run_<timestamp>.log` in JSON-lines format. Use the `verify_logging` tool to check log completeness:

```bash
python -m code.logging.verify_logging
```

## License

MIT License

## Contributors

llmXive Research Team