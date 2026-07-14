# The Impact of Perceived Agency in AI-Driven Cognitive Behavioral Therapy on Treatment Adherence

**Project ID:** PROJ-547
**Status:** Active Research Pipeline
**Python Version:** 3.11+

## Overview

This project investigates whether perceived agency in an AI-driven CBT therapist influences patient treatment adherence. The pipeline ingests conversation transcripts, computes linguistic agency scores, extracts adherence metrics from usage logs, and performs regression analysis to test the hypothesis that higher perceived agency correlates with better adherence outcomes.

## Quick Start

### 1. Environment Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Full Pipeline

The pipeline executes in sequential stages. Run the main orchestration script:

```bash
python code/pipeline/run_pipeline.py
```

**Note:** Ensure `configs/pipeline_config.yaml` is configured with valid input paths before running.

### 3. Output Location

All processed data, statistical results, and visualizations are written to the `output/` directory:

- `output/processed/`: Cleaned and merged datasets
- `output/results/`: Regression summaries and statistical tables
- `output/plots/`: Visualization figures (PNG)
- `output/validation/`: Validation reports and metrics
- `output/provenance.yaml`: Metadata linking results to source data

See `docs/quickstart.md` for detailed step-by-step instructions.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── agency_scoring/ # Linguistic marker detection & scoring
│ ├── adherence_extraction/ # Usage metric extraction
│ ├── analysis/ # Regression models & statistical tests
│ ├── validation/ # Reliability & validity checks
│ ├── data_acquisition/ # External data download & verification
│ ├── logging/ # Centralized logging infrastructure
│ ├── utils/ # Shared utilities & error handling
│ └── pipeline/ # Orchestration scripts
├── data/
│ ├── external/ # External agency scale datasets
│ ├── raw/ # Downloaded raw data
│ └── processed/ # Intermediate processed files
├── configs/ # YAML configuration files
├── docs/ # Documentation
├── logs/ # Runtime logs (JSON lines)
├── output/ # Final results and figures
├── tests/ # Unit and integration tests
└── contracts/ # JSON schema definitions
```

## Key Modules

### Agency Scoring (US1)
- `code/agency_scoring/ingest_transcripts.py`: Parses CSV/JSON transcripts
- `code/agency_scoring/detect_markers.py`: Detects modal verbs, choice constructions
- `code/agency_scoring/compute_scores.py`: Aggregates weighted markers into [0,1] scores

### Adherence Extraction (US2)
- `code/adherence_extraction/extract_metrics.py`: Computes session completion rates
- `code/adherence_extraction/impute_confounders.py`: Handles missing confounder data

### Regression Analysis (US3)
- `code/analysis/run_regression.py`: Executes model selection, fitting, FDR correction
- `code/analysis/generate_results.py`: Produces human-readable summaries and plots

### Validation (US4)
- `code/validation/compute_reliability.py`: Split-half reliability (Spearman-Brown)
- `code/validation/compute_convergent.py`: Pearson correlation with external scale

## Verification

Run the test suite to verify functionality:

```bash
pytest tests/
```

To check logging completeness:

```bash
python code/logging/verify_logging.py
```

## License & Ethics

This research adheres to ethical guidelines for AI in mental health. All data processing includes consent verification (see `data/consent/`). Refer to `docs/ethics_statement.md` for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure `pre-commit` hooks pass (`ruff`, `black`, `mypy`)
4. Submit a pull request with test coverage
