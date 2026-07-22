# Quickstart Guide

## Installation

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

1. Download data: `python code/data/download.py`
2. Preprocess data: `python code/data/preprocess.py`
3. Generate fingerprints: `python code/data/fingerprints.py`
4. Train model: `python code/models/random_forest.py`
5. Analyze results: `python code/analysis/stats.py` and `python code/analysis/explainability.py`

## Output

Results are saved in `data/derived/` and `figures/`.
