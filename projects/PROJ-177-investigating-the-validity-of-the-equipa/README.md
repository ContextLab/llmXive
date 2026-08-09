# Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

This project implements an automated science pipeline to analyze particle tracking data from driven granular systems. It tests whether energy distributions follow the Maxwell-Boltzmann prediction (thermal) or deviate significantly (non-thermal).

## Project Structure

- `code/`: Python modules for ingestion, statistics, sensitivity, and regression.
- `data/`: Raw input data and derived intermediate/final datasets.
- `artifacts/`: Logs, metadata, statistical reports, and hashes.
- `tests/`: Unit and integration tests.

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Place raw data in `data/raw/`.

## Usage

See `quickstart.md` for detailed execution commands.

## Key Outputs

- `data/derived/energy_samples.csv`: Calculated energy components per particle.
- `artifacts/statistical_results.json`: Results of KS and Chi-squared tests.
- `artifacts/regression_results.json`: Regression analysis of deviation drivers.