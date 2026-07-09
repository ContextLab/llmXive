# PROJ-532: Predicting Material Degradation Pathways

## Overview
This project implements an automated pipeline for predicting material degradation pathways from compositional data using machine learning.

## Structure
- `code/`: Python source modules for ingestion, preprocessing, training, and analysis
- `data/`: Raw and processed datasets (managed via DVC or git-lfs)
- `results/`: Model artifacts, metrics, and plots
- `specs/`: Feature specifications and data models
- `tests/`: Unit and integration tests

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run ingestion: `python code/ingestion.py`
3. Run preprocessing: `python code/preprocessing.py`
4. Run training: `python code/training.py`

## Environment
- Python 3.11+
- CPU-only execution (no GPU dependencies)
