# PROJ-021: Understanding Oceanic Phytoplankton Communities

## Overview
This project implements an automated science pipeline to analyze oceanic phytoplankton communities using remote sensing and oceanographic data.

## Structure
- `code/`: Source code for data ingestion, preprocessing, model training, and evaluation
- `data/`: Raw and processed datasets
- `specs/`: Feature specifications, contracts, and data models
- `tests/`: Unit and integration tests
- `docs/`: Documentation

## Quickstart
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run data ingestion: `python code/01_fetch_modis.py`
3. Run preprocessing: `python code/02_preprocessing.py`
4. Train models: `python code/03_model_training.py`
5. Evaluate: `python code/04_evaluation.py`
