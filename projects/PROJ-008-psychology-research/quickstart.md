# Quickstart Guide

## Environment Setup

1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-008-psychology-research
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. (Optional) Install development tools:
 ```bash
 pip install -e ".[dev]"
 ```

## Verification

Run the test suite to verify the environment:
```bash
pytest
```

## Pipeline Execution

The main pipeline is executed via the `scripts/run_pipeline.py` entry point
(to be implemented in subsequent tasks).

## Data Sources

- **ClinicalTrials.gov**:
- **Open Science Framework**: https://api.osf.io/v2/

Note: API rate limits apply. The collector implements exponential backoff.
