# Assessing Uncertainty Quantification Techniques for Machine-Learning Predicted Material Properties

## Project Overview
This project implements a pipeline to assess uncertainty quantification (UQ) techniques for machine learning models predicting material properties, specifically formation energy from the OQMD dataset.

## Directory Structure
- `code/`: Source code for data processing, model training, and UQ analysis
- `data/`: Raw and processed datasets
- `results/`: Model checkpoints, predictions, and evaluation reports
- `tests/`: Unit and integration tests
- `docs/`: Documentation and design rationale
- `logs/`: Pipeline execution logs

## Requirements
Install dependencies:
```bash
pip install -r code/requirements.txt
```

## Usage
Run the full pipeline:
```bash
python code/main.py
```

## Key Components
- **Data Pipeline**: Download and preprocess OQMD formation energy data
- **Baseline Models**: Heteroscedastic neural networks
- **UQ Techniques**: Deep Ensembles, MC Dropout, Sparse Gaussian Processes
- **Evaluation**: Calibration metrics (ECE, Interval Score), uncertainty decomposition
- **Screening**: Expected loss ranking for material discovery

## License
[Insert License Information]