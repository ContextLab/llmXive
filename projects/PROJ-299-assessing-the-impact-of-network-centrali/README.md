# PROJ-299: Assessing the Impact of Network Centrality on Age-Related Cognitive Decline

## Overview
This project investigates the relationship between network centrality metrics (derived from rs-fMRI data) and age-related cognitive decline using ADNI data.

## Project Structure
- `code/`: Source code for the pipeline (download, preprocess, centrality, analysis, viz)
- `data/`: Data storage (raw, processed, analysis)
- `tests/`: Unit and integration tests
- `docs/`: Documentation and reports
- `logs/`: Pipeline execution logs
- `outputs/`: Generated visualizations and final reports

## Setup
1. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment: Copy `.env.example` to `.env` and fill in ADNI credentials.

## Execution
Run the main pipeline scripts in order:
1. `python code/main_us1.py` (Download, Preprocess, Centrality)
2. `python code/main_us2.py` (Regression, Diagnostics)
3. `python code/main_us3.py` (Visualization, Report)

## License
MIT
