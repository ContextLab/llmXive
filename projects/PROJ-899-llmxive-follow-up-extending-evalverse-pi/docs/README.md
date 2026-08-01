# llmXive: Extending EvalVerse with CPU-tractable Feature Distillation

## Project Overview

This project implements a CPU-tractable pipeline to analyze video dimensions using low-level features (optical flow, audio spectra, etc.) against human expert scores. The goal is to determine which dimensions are "feature-sufficient" (correlation r ≥ 0.85) versus those requiring Vision-Language Models (VLMs).

## Architecture

The pipeline is organized into distinct phases:
1. **Setup**: Project initialization and dependency configuration.
2. **Foundational**: Data fetching, checksum verification, and environment setup.
3. **User Story 1**: Dimensional Viability Analysis (Correlation & Classification).
4. **User Story 2**: Compute Feasibility Profiling (Memory & Timing).
5. **User Story 3**: Sensitivity Analysis of Feature Thresholds.

## Directory Structure

```text
.
├── code/
│ ├── src/
│ │ ├── cli/ # Command-line interface entry points
│ │ ├── data/ # Data loading, preprocessing, and profiling
│ │ ├── models/ # Training, evaluation, and metrics
│ │ ├── reports/ # Report generation logic
│ │ ├── config.py # Global configuration and paths
│ │ └── utils.py # Logging, I/O helpers
│ ├── scripts/ # Standalone execution scripts
│ └── tests/ # Unit, integration, and contract tests
├── data/
│ ├── raw/ # Downloaded EvalVerse dataset
│ ├── processed/ # Extracted feature vectors
│ └── results/ # Model outputs and CSV artifacts
├── reports/ # Final JSON/Markdown reports
├── state/ # Intermediate gate status and hashes
├── specs/ # Design documents and requirements
└── docs/ # This documentation
```

## Prerequisites

- Python 3.11+
- CPU-only environment (optimized for < 7GB RAM usage)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure the environment is set up:
 ```bash
 python code/scripts/setup_environment.py
 ```

## Usage

### Data Fetching
Download the EvalVerse dataset from the configured source:
```bash
python code/scripts/run_pipeline.py --stage fetch
```

### Full Pipeline Execution
Run the complete analysis (Fetch → Preprocess → Train → Evaluate → Report):
```bash
python code/scripts/run_pipeline.py
```

### Specific Stages
- **Feature Extraction**: `python code/scripts/run_pipeline.py --stage extract`
- **Model Training**: `python code/scripts/run_pipeline.py --stage train`
- **Sensitivity Analysis**: `python code/scripts/generate_sensitivity_matrix.py`

## Key Artifacts

The pipeline produces the following outputs:
- `data/results/correlation_results.csv`: Dimension correlations and confidence intervals.
- `data/timing_profile.csv`: Projected inference times for 10k clips.
- `data/sensitivity_matrix_full.csv`: Classification stability across thresholds.
- `reports/feasibility_profile.json`: CPU feasibility summary.
- `state/validation_status.json`: Gate status for VLM proxy validity.

## Validation Gates

The pipeline includes mandatory gates to ensure data quality and feasibility:
- **T040 (Quality Gate)**: Excludes samples with error rates > 5%.
- **T041 (Validation Gate)**: Halts if VLM proxy correlation r < 0.70.
- **T021 (Feasibility Gate)**: Halts if peak memory > 7GB or projected time > 6 hours.

## Testing

Run the test suite:
```bash
pytest code/tests/
```

Specific test suites:
- **Unit Tests**: `pytest code/tests/unit/`
- **Integration Tests**: `pytest code/tests/integration/`
- **Contract Tests**: `pytest code/tests/contract/`

## Contributing

1. Create a feature branch.
2. Ensure all tests pass (`pytest`).
3. Run linter and formatter:
 ```bash
 ruff check code/
 black code/
 ```
4. Submit a pull request.

## License

[Insert License Here]
