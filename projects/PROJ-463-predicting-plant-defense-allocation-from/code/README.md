# Predicting Plant Defense Allocation

This project implements an automated pipeline to predict plant defense allocation
from publicly available transcriptomic data using machine learning and statistical modeling.

## Project Structure

- `src/` - Source code for the pipeline
 - `utils/` - Configuration, logging, schemas
 - `data/` - Data acquisition and preprocessing
 - `analysis/` - Differential expression, feature engineering, modeling
 - `cli/` - Command line interface
- `tests/` - Unit, integration, and contract tests
- `data/` - Data storage
 - `raw/` - Raw FASTQ files
 - `processed/` - Processed TPM matrices and features
 - `traits/` - Defense trait data
 - `manifests/` - Data provenance and checksums
 - `synthetic/` - Synthetic data for testing

## Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the setup script to create directories:
 ```bash
 python setup_directories.py
 ```

## Running Tests

```bash
pytest
```

## Configuration

Edit `config.json` or use environment variables to override defaults.

## License

MIT License
