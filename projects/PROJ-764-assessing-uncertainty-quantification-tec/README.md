# Assessing Uncertainty Quantification Techniques for Machine-Learning Predicted Material Properties

## Overview
This project assesses various Uncertainty Quantification (UQ) techniques (Deep Ensembles, MC Dropout, Sparse Gaussian Processes) applied to machine learning models predicting material properties (specifically formation energy from the OQMD dataset).

## Project Structure
- `code/`: Source code for data processing, model training, UQ inference, and evaluation.
- `data/`: Raw and processed data artifacts.
- `results/`: Model checkpoints, predictions, and evaluation reports.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Feature specifications and design documents.

## Requirements
- Python 3.9+
- See `requirements.txt` for dependencies.

## Usage
1. **Setup**: Install dependencies `pip install -r requirements.txt`.
2. **Download Data**: Run `python code/data/download.py` to fetch the OQMD dataset.
3. **Preprocess**: Run `python code/data/preprocess.py` to clean and transform data.
4. **Train & Evaluate**: Run `python code/main.py` to execute the full pipeline (training, UQ inference, calibration, and screening).

## License
MIT
