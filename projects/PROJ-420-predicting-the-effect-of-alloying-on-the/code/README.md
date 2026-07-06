# Code Directory

This directory contains the source code for the Aluminum Alloy Poisson's Ratio Prediction Pipeline.

## Structure

- `__init__.py`: Package initialization
- `config.py`: Configuration management
- `logging_config.py`: Logging infrastructure
- `data_extraction.py`: Data fetching from external sources
- `data_cleaning.py`: Data validation, filtering, and transformation
- `modeling.py`: Machine learning model training and evaluation
- `analysis.py`: Feature importance and statistical analysis
- `main.py`: Pipeline orchestration
- `schemas/`: Pydantic data models
- `utils/`: Utility functions (checksums, etc.)

## Running the Pipeline

```bash
python -m code.main
```

See `docs/quickstart.md` for detailed instructions.
