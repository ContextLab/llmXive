# PROJ-008: Mindfulness Components and Delivery Formats in ASD Social Skills

## Overview
This project implements a systematic review and meta-analysis of mindfulness-based interventions for improving social skills in children aged 6-12 with Autism Spectrum Disorder (ASD).

## Project Structure
```
projects/PROJ-008-psychology-research/
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── data/ # Data collection and cleaning
│ ├── utils/ # Utility functions
│ └── viz/ # Visualization modules
├── data/ # Data artifacts
│ ├── raw/ # Raw data from APIs and PDFs
│ ├── processed/ # Cleaned and analyzed data
│ └── interim/ # Intermediate data files
├── docs/ # Documentation
├── tests/ # Test suites
├── contracts/ # Schema definitions
├── scripts/ # Utility scripts
└──.github/workflows/ # CI/CD pipelines
```

## Installation
```bash
pip install -e.
```

## Development Tools
- **Black**: Code formatter (configured in `pyproject.toml`)
- **Ruff**: Linter (configured in `.ruff.toml`)

### Formatting
```bash
black.
```

### Linting
```bash
ruff check.
```

### Running Tests
```bash
pytest
```

## Data Sources
- ClinicalTrials.gov
- Open Science Framework (OSF)

## Ethics
This study uses secondary analysis of de-identified public registry data and is exempt from IRB review (see `docs/ethics_determination.md`).