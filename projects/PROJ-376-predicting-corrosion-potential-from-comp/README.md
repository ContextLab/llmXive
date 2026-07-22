# Predicting Corrosion Potential from Composition and Environment

This project implements an automated science pipeline for predicting corrosion potential based on alloy composition and environmental factors.

## Project Structure

The project follows a standardized directory structure:

- `code/` - Source code for the pipeline
 - `data/` - Data ingestion and preprocessing scripts
 - `models/` - Model training and evaluation scripts
 - `utils/` - Utility functions and helpers
 - `tests/` - Test suites
- `data/` - Data storage
 - `raw/` - Raw downloaded datasets
 - `processed/` - Preprocessed and cleaned datasets
 - `logs/` - Pipeline execution logs
- `state/` - Pipeline state tracking
- `contracts/` - Schema contracts for data validation
- `config/` - Configuration files

## Setup

To initialize the project directory structure, run:

```bash
python code/setup_directories.py
```

Or run the test suite which will also create the directories:

```bash
pytest tests/unit/test_setup_directories.py
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the setup script to create directories

## Usage

Follow the tasks in `tasks.md` to implement the pipeline step by step.

## Contributing

See CONTRIBUTING.md for development guidelines.