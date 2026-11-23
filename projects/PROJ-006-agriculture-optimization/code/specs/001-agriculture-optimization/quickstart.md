# Quick Start Guide

## Prerequisites
- Python 3.9+
- pip package manager

## Installation
```bash
cd code
pip install -r requirements.txt
```

## Running the Pipeline
1. **Initialize Structure** (if not done):
 ```bash
 python scripts/create_project_structure.py
 ```

2. **Run Tests**:
 ```bash
 pytest
 ```

3. **Execute Full Pipeline**:
 ```bash
 python scripts/run_pipeline.py
 ```

## Generating Reports
After pipeline execution, reports are available in `reports/`.

## Validation
Use the Reference-Validator Agent to check citations:
```bash
python scripts/validate_quickstart.py
```
