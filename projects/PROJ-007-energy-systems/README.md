# PROJ-007: Energy Systems Inequity Research

This project implements a scientific pipeline to analyze energy inequity in low-income communities using causal inference and scaling law analysis.

## Project Structure

- `src/`: Source code for the pipeline
 - `data/`: Ingestion and preprocessing
 - `analysis/`: Causal inference (PSM, OLS, DiD)
 - `scaling/`: Scaling law analysis
 - `models/`: Pydantic schemas
 - `utils/`: Utilities and configuration
- `tests/`: Test suite
- `data/`: Generated data artifacts (gitignored)
- `specs/`: Project specifications and planning

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run tests:
 ```bash
 pytest
 ```

## Pipeline Overview

The pipeline consists of three main phases:
1. **Data Ingestion**: Fetch EIA RECS and ACS data
2. **Causal Inference**: Propensity Score Matching and OLS/DiD estimation
3. **Scaling Analysis**: Descriptive power-law analysis (non-causal)

## Reviewer Notes

This project incorporates feedback from Geoffrey West regarding the importance of scaling laws in understanding urban energy systems. The scaling law module (Phase 6) is strictly descriptive and does not make causal claims.

## License

MIT License