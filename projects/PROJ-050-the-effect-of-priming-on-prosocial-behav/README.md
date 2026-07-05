# PROJ-050: The Effect of Priming on Prosocial Behavior in Online Communities

## Project Overview
This project investigates the effect of priming (specifically, exposure to negative sentiment) on prosocial behavior in online Reddit communities.
It implements a reproducible data pipeline for ingestion, classification, anonymization, scoring, and statistical analysis.

## Directory Structure
- `specs/`: Research design documents, user stories, and data models.
- `code/`: Python implementation of the research pipeline.
- `data/`: Raw and processed datasets (generated during execution).
- `results/`: Statistical reports and visualizations.
- `tests/`: Unit and integration tests.

## Execution Flow
1. **Power Analysis**: `code/00_power_analysis.py`
2. **Ingestion**: `code/01_ingest.py`
3. **Scoring**: `code/02_score.py`
4. **Analysis**: `code/03_analyze.py`

## Dependencies
See `code/requirements.txt` for the pinned dependency list.
