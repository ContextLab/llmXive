# Polymer Degradation Pathways Prediction Pipeline

## Overview
This project implements an automated pipeline to predict polymer degradation pathways using Graph Neural Networks (GNNs).

## Setup
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Run linting and formatting:
 ```bash
 # Check formatting
 black --check code/
 # Fix formatting
 black code/

 # Check linting
 ruff check code/
 # Fix linting issues automatically
 ruff check --fix code/
 ```

3. Run tests:
 ```bash
 pytest tests/
 ```

## Project Structure
- `code/`: Source code
- `data/raw/`: Raw downloaded data
- `data/processed/`: Processed datasets
- `data/reports/`: Analysis reports
- `tests/`: Test suite

## Configuration
Configuration is handled via environment variables and `code/utils.py`'s `load_config`.

## Development
Ensure all code passes `black` and `ruff` before committing.