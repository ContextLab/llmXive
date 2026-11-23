# Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Project ID**: PROJ-340
**Status**: MVP Implementation Complete (US1, US2, US3)

## Overview

This project implements an automated pipeline to investigate correlations between gut microbiome composition and sleep architecture. It includes:
- Data ingestion and validation (US1)
- Robust associational correlation analysis (US2)
- Diagnostics, sensitivity, and power analysis (US3)

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
pip install -r requirements.txt
```

### Synthetic Data Generation (Validation Mode)
```bash
python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv
```

### Run Pipeline
```bash
python code/main.py --input data/raw/synthetic_test_data.csv --output data/results/ --allow-synthetic-fallback
```

### Verify Artifacts
```bash
python scripts/verify_integrity.py
python scripts/final_validation.py
```

## Directory Structure
```
.
├── code/ # Source code
├── data/ # Data directories
│ ├── raw/ # Raw input data
│ ├── processed/ # Processed data
│ ├── results/ # Analysis outputs
│ └── config/ # Configuration files
├── tests/ # Test suites
├── scripts/ # Utility scripts
└── state/ # Pipeline state tracking
```

## Key Artifacts
- `data/results/significance_summary.md`: Summary of significant correlations.
- `data/results/final_report.md`: Final interpretation report.
- `data/results/power_analysis_report.json`: Power analysis results.

## License
MIT
