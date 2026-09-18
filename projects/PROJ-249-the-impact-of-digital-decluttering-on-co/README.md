# The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Project ID**: PROJ-249
**Status**: Research Pipeline Implementation

## Overview

This project implements an automated research pipeline to analyze the impact of digital decluttering interventions on cognitive performance (SART, Ospan) and well-being metrics (PSS-10, PANAS). The pipeline handles data collection, compliance logging, statistical analysis (bootstrapping, effect sizes), and report generation.

## Quick Start

### Prerequisites

- Python 3.9+
- `pip` package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-249-the-impact-of-digital-decluttering-on-co

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

1. **Generate Synthetic Baseline Data** (for validation):
 ```bash
 python code/pipeline/collect_baseline.py
 ```
 *Outputs*: `data/raw/synthetic_baseline.csv`

2. **Validate Instruments**:
 ```bash
 python code/validation/validate_instruments.py
 ```

3. **Run Compliance Aggregation**:
 ```bash
 python code/pipeline/aggregate_compliance.py
 ```

4. **Perform Analysis**:
 ```bash
 python code/analysis/statistical_summary.py
 ```

5. **Generate Final Report**:
 ```bash
 python code/report/generate_report.py
 ```
 *Outputs*: `results/final_report.md`, `results/statistical_summary.json`

## Project Structure

```
.
├── code/
│ ├── analysis/ # Statistical analysis modules
│ ├── compliance/ # Compliance logging and validation
│ ├── config/ # Environment configuration
│ ├── pipeline/ # End-to-end pipeline scripts
│ ├── report/ # Report generation
│ ├── scoring/ # Psychometric scoring functions
│ ├── setup/ # Project setup utilities
│ ├── utils/ # Shared utilities (random seeds, etc.)
│ ├── validation/ # Data validation scripts
│ └── viz/ # Visualization generation
├── data/
│ ├── raw/ # Raw data (baseline, compliance logs)
│ ├── processed/ # Processed datasets
│ └── compliance/ # Compliance-specific data
├── results/ # Analysis outputs and reports
├── tests/ # Unit and contract tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Key Features

- **Pseudonymous ID Generation**: Ensures participant privacy while allowing data linkage (FR-001).
- **Instrument Scoring**: Implements SART, Ospan, PSS-10, and PANAS scoring logic.
- **Robust Statistics**: Primary bootstrapped confidence intervals (10,000 resamples) with Wilcoxon fallback.
- **Multiple Testing Correction**: Holm-Bonferroni step-down procedure.
- **Compliance Monitoring**: Automated rule engine for digital decluttering adherence.

## Documentation

- **API Docs**: See `docs/` for generated documentation.
- **Quickstart Guide**: `quickstart.md` provides detailed step-by-step instructions.
- **Data Schema**: `contracts/dataset.schema.yaml` defines data structures.

## Contributing

1. Ensure all unit tests pass (`pytest tests/`).
2. Follow the existing code structure and naming conventions.
3. Update `requirements.txt` if adding new dependencies.

## License

[Insert License Information Here]
