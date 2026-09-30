# Predicting Material Stability using Machine Learning and DFT Calculations

## Project Overview
This project implements a machine learning pipeline to predict material stability,
focusing on Li-rich rock-salt structures. It utilizes DFT calculation data from
the OQMD dataset and combines bulk compositional descriptors with local coordination
features to improve prediction accuracy.

## Structure
- `code/`: Python source code, scripts, and utilities
- `data/`: Raw and processed datasets, models
- `outputs/`: Logs, metrics, figures, and reports
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Download data: `python code/download_data.py`
3. Run baseline model: `python code/train_baseline.py`
4. Run augmented model: `python code/train_augmented.py`
5. Evaluate results: `python code/evaluate.py`

See `quickstart.md` for detailed instructions.
