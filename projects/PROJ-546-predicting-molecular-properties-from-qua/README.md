# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

## Overview
This project implements a pipeline to predict molecular properties using semi-empirical and DFT quantum chemical calculations, followed by machine learning modeling.

## Directory Structure
- `code/`: Source code for the pipeline (downloaders, calculators, models, evaluators).
- `data/`: Raw and processed data artifacts.
- `tests/`: Unit and integration tests.
- `reports/`: Generated evaluation and sensitivity reports.
- `docs/`: Project documentation.
- `logs/`: Execution logs.

## Prerequisites
- Python 3.11+
- DFTB+ (for semi-empirical calculations)
- Psi4 (for DFT calculations)

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate`
3. Install dependencies: `pip install -r code/requirements.txt`

## Running the Pipeline
Refer to `docs/reproducibility.md` for the standard execution order.