# llmXive: Assessing Uncertainty Quantification Techniques for ML Predicted Material Properties

## Overview
This project implements a pipeline to assess various Uncertainty Quantification (UQ) techniques
(Deep Ensembles, MC Dropout, Sparse GP) applied to Machine Learning models predicting material properties.

## Project Structure
- `code/`: Source code for data processing, models, and UQ methods
- `data/`: Raw and processed datasets
- `results/`: Model artifacts, predictions, and evaluation reports
- `tests/`: Unit, contract, and integration tests
- `specs/`: Project specifications and design documents
- `logs/`: Pipeline execution logs
- `figures/`: Generated plots and diagrams

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python code/main.py`

## Pipeline Phases
1. **Setup**: Project initialization
2. **Foundational**: Data download, preprocessing, and configuration
3. **User Story 1**: Baseline model training and UQ application
4. **User Story 2**: Calibration and reliability evaluation
5. **User Story 3**: Downstream screening case study

## Requirements
- Python 3.9+
- PyTorch 2.0+
- GPyTorch 1.10+
- HuggingFace Datasets
