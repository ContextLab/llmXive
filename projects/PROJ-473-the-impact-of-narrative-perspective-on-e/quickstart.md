# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Create virtual environment: `python -m venv code/.venv`
2. Activate: `source code/.venv/bin/activate` (Linux/Mac) or `code\.venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Download spaCy model: `python -m spacy download en_core_web_sm`

## Running the Pipeline
1. **Extraction**: Run `python code/main.py extract`
 - Reads `data/raw/*.txt`
 - Outputs `data/processed/perspective_features.json`
2. **Matching**: Run `python code/main.py match`
 - Reads `data/processed/perspective_features.json`
 - Outputs `data/processed/matching_results.json`

## Testing
Run `pytest tests/` to execute the test suite.
