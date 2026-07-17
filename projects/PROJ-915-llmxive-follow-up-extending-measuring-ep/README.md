# PROJ-915: llmXive Follow-up: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

## Overview
This project extends the "Measuring Epistemic Resilience of LLMs" study by implementing a full pipeline for data ingestion, feature extraction, model inference, and statistical analysis.

## Directory Structure
- `data/raw`: Raw datasets (e.g., MedMisBench subset)
- `data/processed`: Cleaned and feature-engineered data
- `data/interim`: Intermediate data (annotations, labeled responses)
- `data/results`: Final analysis results and reports
- `code`: Python modules for the pipeline
- `tests`: Unit and integration tests
- `specs`: Design documents and specifications
- `state`: Checksums and runtime state

## Quick Start
1. Ensure Python 3.11 is installed.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the ingestion pipeline: `python code/ingestion.py`
4. Run feature extraction: `python code/features.py`
5. Run modeling: `python code/modeling.py`

## Configuration
See `code/config.py` for seed, path, and timeout configurations.
