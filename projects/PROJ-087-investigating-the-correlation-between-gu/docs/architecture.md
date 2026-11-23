# Project Architecture

## Directory Structure

```
.
├── code/
│ ├── src/ # Core source code
│ │ ├── config.py # Configuration loader
│ │ ├── ingestion.py # Data ingestion and filtering
│ │ ├── diversity.py # Alpha-diversity calculations
│ │ ├── correlation.py # Statistical analysis
│ │ ├── viz.py # Visualization generation
│ │ ├── report.py # Text report generation
│ │ ├── report_final.py # HTML/PDF report generation
│ │ ├── logging_config.py # Logger setup
│ │ ├── models/
│ │ │ └── schemas.py # Pydantic data models
│ │ └── utils/
│ │ └── hashing.py # Utility for file hashing
│ ├── tests/ # Test suite
│ │ ├── unit/ # Unit tests
│ │ └── integration/ # Integration tests
│ └──... (other utilities)
├── data/
│ ├── raw/ # Raw downloaded data (gitignored)
│ ├── processed/ # Cleaned data and results
│ │ └── plots/ # Generated visualizations
│ └──...
├── docs/ # Documentation
│ ├── pipeline_flow.md
│ └── architecture.md
├── requirements.txt # Python dependencies
├── pyproject.toml # Linting/Formatting config
└── README.md # Project overview
```

## Component Interactions

1. **Config**: `config.py` is the entry point for environment variables, ensuring consistent settings across modules.
2. **Ingestion**: `ingestion.py` is the gatekeeper; it fails fast if data is missing or malformed, preventing downstream errors.
3. **Analysis Chain**: `diversity.py` -> `correlation.py` -> `viz.py` -> `report.py`. Each step depends on the successful completion of the previous one.
4. **Models**: `schemas.py` defines strict data contracts used for validation and serialization.

## Error Handling Strategy

- **Fail Loudly**: Missing data or schema mismatches raise `FileNotFoundError` or `ValueError` immediately.
- **Logging**: All stages use the configured root logger to record progress and errors.
- **Reproducibility**: Hashing utilities allow verification of output consistency across runs.
