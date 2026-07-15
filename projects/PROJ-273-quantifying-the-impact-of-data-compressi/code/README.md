# Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## Project Structure
- `src/`: Source code for data processing, compression, and parameter estimation
- `tests/`: Unit, integration, and contract tests
- `data/`: Raw, interim, and processed data
- `reports/`: Final analysis reports
- `figures/`: Generated plots and visualizations

## Setup
1. Install dependencies: `pip install -e.`
2. Run setup script: `python setup_data_dirs.py`

## Running Tests
`pytest`

## Running the Pipeline
See `src/data/main.py`, `src/compression/main.py`, and `src/pe/main.py` for entry points.
