# Predicting the Impact of Residual Stress on Fatigue Life

This project investigates the mediating role of residual stress in the relationship between manufacturing process parameters and the fatigue life of materials, specifically focusing on steels and aluminum alloys.

## Research Question
To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across different material classes, and how much predictive value does stress-mediated estimation add beyond direct process-to-fatigue modeling?

## Data Sources
The pipeline ingests data from the following public repositories:
- **NIST Materials Data Repository**: Fatigue life and stress data.
- **UCI Machine Learning Repository**: Fatigue-related datasets.
- **OpenML**: Publicly available fatigue test archives.

Raw data is programmatically downloaded during the ingestion phase (`code/ingest/ingest.py`) and stored in `data/raw/`.

## Getting Started
Please refer to [quickstart.md](quickstart.md) for detailed instructions on environment setup and running the analysis pipeline.

## Project Structure
- `code/`: Implementation of the science pipeline (ingestion, preprocessing, modeling, and evaluation).
- `data/`: Raw and processed datasets.
- `results/`: Performance metrics, statistical tests, and figures.
- `specs/`: Feature specifications and contracts.
- `tests/`: Unit and integration tests.
