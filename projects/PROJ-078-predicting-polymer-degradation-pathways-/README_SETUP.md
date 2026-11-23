# Project Setup Instructions

This project uses a Python script to initialize the required directory structure.

## Prerequisites

- Python 3.11+
- Standard library permissions to create directories in the current working directory

## How to Run

1. Navigate to the project root directory.
2. Execute the setup script:
 ```bash
 python code/setup_project.py
 ```

## Expected Output

The script will create the following directories:
- `code/` - Source code for the project
- `data/raw/` - Raw data downloads
- `data/processed/` - Processed data for modeling
- `data/reports/` - Generated reports and logs
- `tests/` - Test suite
- `state/` - Intermediate state files

## Verification

After running, verify the structure with:
```bash
ls -R
```
Or use the provided tests:
```bash
pytest tests/
```