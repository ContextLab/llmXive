# llmXive: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Project Structure

This project follows a standard data science pipeline structure:

- `code/` - Source code for data processing, modeling, and utilities
 - `models/` - Pydantic data models
 - `data/` - Data download and preprocessing scripts
 - `modeling/` - Machine learning and phylogenetic analysis
 - `utils/` - Utility functions
 - `scripts/` - CLI entry points
- `data/` - Data storage
 - `raw/` - Raw downloaded data (FASTA, GFF, metabolite tables)
 - `processed/` - Processed and aligned datasets
 - `interim/` - Intermediate data files (e.g., PCA features)
- `tests/` - Test suite
 - `unit/` - Unit tests
 - `integration/` - Integration tests
- `figures/` - Generated plots and visualizations
- `specs/` - Feature specifications and design documents
- `docs/` - Documentation

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the project structure setup script (if not already done):
 ```bash
 python code/scripts/setup_project_structure.py
 ```

## Usage

See individual task documentation for specific execution instructions.

## License

MIT License