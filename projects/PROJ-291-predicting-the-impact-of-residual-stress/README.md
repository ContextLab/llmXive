# Predicting the Impact of Residual Stress on Fatigue Life

## Project Overview
This project investigates the extent to which residual stress mediates the relationship between manufacturing process parameters and fatigue life across different material classes (specifically steels and aluminum alloys).

The goal is to determine if explicitly modeling the residual stress mediator adds significant predictive value (measured by MAPE reduction) compared to direct process-to-fatigue modeling.

## Data Sources
The pipeline ingests data from the following public repositories:
- **NIST Materials Data Repository**: High-fidelity materials properties and fatigue data.
- **UCI Machine Learning Repository**: Fatigue-life collections.
- **OpenML**: Publicly shared fatigue datasets.

## Obtaining Raw Data
Raw data is programmatically fetched by the ingestion pipeline (`code/ingest/ingest.py`). The script downloads version-pinned CSV/JSON files from canonical URLs and stores them in `data/raw/` before processing.

## Reproducibility
To ensure reproducibility, all random seeds are fixed to `SEED=42`, and all dependencies are pinned in `requirements.txt`.
