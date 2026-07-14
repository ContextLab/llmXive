# Assessing Uncertainty Quantification Techniques for Machine-Learning Predicted Material Properties

## Overview
This project assesses various Uncertainty Quantification (UQ) techniques applied to machine learning models predicting material properties, specifically using the OQMD Formation Energy dataset. The goal is to evaluate the calibration and reliability of different UQ methods (Deep Ensembles, MC Dropout, Sparse GP) and demonstrate their utility in downstream material screening tasks.

## Project Structure
- `code/`: Source code for data processing, model training, UQ inference, and evaluation.
- `data/`: Raw and processed datasets.
- `results/`: Output artifacts including predictions, reports, and figures.
- `tests/`: Unit and contract tests.
- `specs/`: Design documents and requirements.

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the main pipeline:
```bash
python code/main.py
```

## License
MIT License
