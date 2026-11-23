# PROJ-163: Exploring the Role of Network Structure in Superconducting Qubit Coupling

This project analyzes the relationship between the connectivity graph topology of superconducting qubit devices and their performance metrics.

## Prerequisites

- Python 3.11 or higher
- Access to an IBM Quantum account (API token required)

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure your IBM Quantum token:
 - Set the environment variable `IBM_QUANTUM_TOKEN`
 - Or configure via `code/config.py` if using the local config loader.

## Project Structure

- `code/`: Source code modules
- `data/raw/`: Raw data snapshots from IBM Quantum API
- `data/processed/`: Processed CSVs and analysis results
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and contracts

## Running the Pipeline

Refer to `quickstart.md` for the full execution order.
Generally, the pipeline runs in phases:
1. Fetch calibration data (`code/fetcher.py`)
2. Build graphs and compute metrics (`code/graph_builder.py`)
3. Run statistical correlations (`code/stats_engine.py`)

## License

Internal Research Use Only.