# Quick Start Guide

## Prerequisites
- Python 3.11+
- DFTB+ installed and in PATH
- Psi4 installed and in PATH
- pip and virtual environment tools

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. Install Python dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Download
Run the data download script to fetch the experimental barrier dataset:
```bash
python code/download_data.py
```
This will create `data/raw/experimental_barriers.csv`.

## Generate Descriptors
Run the descriptor generation script for the semi-empirical method:
```bash
python code/generate_descriptors.py --method dftb --subset 50
```
This will create `data/processed/descriptors_semi.csv`.

## Train Models
Train the Random Forest models:
```bash
python code/train_models.py
```
This will train models on both semi-empirical and DFT data (if available) and save results to `data/processed/model_outputs/`.

## Evaluate
Evaluate the models and generate the report:
```bash
python code/evaluate_models.py
```

## Run Tests
Run the test suite:
```bash
pytest tests/
```

## Troubleshooting
- **DFTB+ not found**: Ensure DFTB+ is installed and in your PATH.
- **OOM Error**: Reduce the subset size or increase system memory.
- **Convergence Failure**: Check log files in `logs/` for details.
