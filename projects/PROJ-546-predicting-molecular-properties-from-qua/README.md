# PROJ-546: Predicting Molecular Properties from Quantum Chemical Calculations

This project implements a pipeline to predict molecular properties using semi-empirical and high-level DFT quantum chemical calculations.

## Project Structure

- `code/`: Python source modules for the pipeline
- `data/`: Input datasets, downloaded data, and generated artifacts
- `tests/`: Unit and integration tests
- `logs/`: Execution logs and failure reports
- `reports/`: Final evaluation and sensitivity analysis reports
- `docs/`: Project documentation and design decisions
- `specs/`: Feature specifications and requirements

## Quick Start

1. Install dependencies: `pip install -r code/requirements.txt`
2. Download data: `python code/download_data.py`
3. Generate descriptors: `python code/generate_descriptors.py --method dftb`
4. Train models: `python code/train_models.py`
5. Evaluate: `python code/evaluate_models.py`

## License

Internal research use only.
