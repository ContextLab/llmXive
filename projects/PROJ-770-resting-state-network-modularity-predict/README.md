# PROJ-770: Resting-State Network Modularity Predicts Social Network Size

## Overview
This project investigates the relationship between resting-state functional network modularity (Q) and social network size (friends/acquaintances) using data from the Human Connectome Project (HCP).

## Prerequisites
- Python 3.11+
- `pip`

## Installation
```bash
pip install -r requirements.txt
```

## Project Structure
- `code/`: Source code for data ingestion, preprocessing, analysis, and visualization.
- `data/`:
  - `raw/`: Raw data downloaded from HCP (S3/HuggingFace).
  - `processed/`: Intermediate processed data (cleaned behavioral, correlation matrices, modularity values).
  - `results/`: Final analysis results (regression coefficients, sensitivity analysis).
- `tests/`: Unit and integration tests.
- `specs/`: Project specifications and design documents.

## Execution
See `quickstart.md` for detailed pipeline execution instructions.

## Data License
This project uses data from the Human Connectome Project (HCP). Users must comply with the HCP data use terms and conditions.
