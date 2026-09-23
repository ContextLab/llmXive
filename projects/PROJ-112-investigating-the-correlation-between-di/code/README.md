# llmXive Project: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

## Overview
This project implements a pipeline to analyze the correlation between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and UK Biobank (UKBB).

## Project Structure
- `src/`: Source code for the pipeline
 - `ingestion/`: Data loading and harmonization
 - `preprocessing/`: Data cleaning, imputation, and transformation
 - `analysis/`: Statistical analysis and correlation testing
 - `utils/`: Utility functions (logging, power analysis)
- `tests/`: Unit, integration, and contract tests
- `data/`: Raw and processed data
 - `raw/`: Downloaded raw data
 - `processed/`: Cleaned and transformed data
- `docs/`: Documentation
- `state/`: State files and checksums

## Requirements
- Python 3.11+
- See `requirements.txt` for dependencies

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Run the setup script to create the directory structure:
```bash
python src/setup_data_structure.py
```

## Testing
```bash
pytest
```
