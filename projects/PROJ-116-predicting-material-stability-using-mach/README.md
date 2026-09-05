# Predicting Material Stability using Machine Learning and DFT Calculations

## Project Overview
This project implements a pipeline to predict material stability using machine learning models trained on DFT-calculated formation energies. It utilizes bulk compositional descriptors (Magpie features) and local coordination environment features (Voronoi statistics) to train Gradient Boosting Regressors.

## Structure
- `code/`: Python source code, utilities, and scripts
- `data/`: Raw and processed datasets, trained models
- `outputs/`: Logs, evaluation metrics, figures, and reports
- `specs/`: Feature specifications and design documents
- `tests/`: Unit and integration tests

## Prerequisites
- Python 3.11+
- Dependencies listed in `code/requirements.txt`

## Usage
1. Install dependencies: `pip install -r code/requirements.txt`
2. Configure environment: Set `DATA_PATH` and `SEED` in `code/config.py` or environment variables.
3. Run the pipeline:
 - Download data: `python code/download_data.py`
 - Feature engineering: `python code/feature_engineering.py`
 - Train baseline: `python code/train_baseline.py`
 - Evaluate: `python code/evaluate.py`

## License
MIT
