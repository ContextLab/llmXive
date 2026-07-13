# Predicting the Diffusion of Carbon in BCC Metals

This project implements a machine learning pipeline to predict carbon diffusion coefficients in BCC metals based on compositional data.

## Project Structure

- `code/`: Python source code for scripts and utilities.
- `data/`: Raw, processed, and output data files.
- `tests/`: Unit and integration tests.
- `contracts/`: Data schema definitions.
- `docs/`: Documentation.

## Setup

1. Create a virtual environment:
 `python -m venv venv && source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
2. Install dependencies:
 `pip install -r code/requirements.txt`

## Usage

Run the pipeline scripts in order:
1. `python code/01_download.py`
2. `python code/02_preprocess.py`
3. `python code/03_train.py`
4. `python code/04_evaluate.py`
